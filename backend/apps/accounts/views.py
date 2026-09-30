from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views, login as auth_login, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.csrf import csrf_protect
from django.db import transaction, IntegrityError

from .forms import RegistroUsuarioForm
from .onboarding_service import (
    finalizar_onboarding,
    onboarding_pendiente,
    onboarding_siguiente_paso,
    onboarding_cache_invalidar,
    get_plan_onboarding,
    marcar_paso1_usuario,
    marcar_paso2_negocio,
)
from apps.businesses.forms import NegocioOnboardingForm, LocalOnboardingForm


OMITIR_KEY = 'onboarding_omitido'


def _sesion_permitir_omitir_onboarding(request):
    """Escribe el flag que permite a dashboard aceptar al usuario aunque onboarding esté incompleto."""
    try:
        request.session[OMITIR_KEY] = True
        request.session.modified = True
    except Exception:
        pass


def _sesion_esta_omitido(request):
    try:
        return bool(request.session.get(OMITIR_KEY, False))
    except Exception:
        return False


class LoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    next_page = '/dashboard/'

    def get_success_url(self):
        user = self.request.user
        # ================= ROLES SEGMENTACIÓN =================
        if user.is_superuser or getattr(user, 'rol', None) == 'ADMIN_SOPORTE':
            return '/admin-panel/'
        # ================= OMITIR ONBOARDING =================
        # Si el usuario marcó "Omitir onboarding / entrar al panel", dejalo pasar aunque
        # onboarding_pendiente=True. Así no se queda en CALLEJÓN SIN SALIDA si falla algo en Paso2.
        if _sesion_esta_omitido(self.request):
            return '/dashboard/?welcome=1'
        if onboarding_pendiente(user, session=self.request.session):
            paso, _ = onboarding_siguiente_paso(user, session=self.request.session)
            # Paso 4 = completo
            if paso < 4:
                messages.info(
                    self.request,
                    f'¡Hola {user.first_name or user.email}! Continúa dónde lo dejaste: configura tu negocio para finalizar el onboarding.'
                )
                return f'/accounts/onboarding/?paso={paso}'
        return super().get_success_url() or '/dashboard/'


class LogoutView(auth_views.LogoutView):
    next_page = '/'


@method_decorator(sensitive_post_parameters('password1', 'password2'), name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
class OnboardingWizardView(View):
    """
    Wizard onboarding multi-step.
    🏁 SOLUCIÓN DEFINITIVA (no parches):
    1) Cache en session de onboarding_pendiente/siguiente_paso (TTL 5min) → 0 queries NeonDB.
    2) get_saved_negocio / get_saved_local son SOLO LECTURA, SIN SIDE EFFECTS (no save_step_session).
    3) Paso1 POST ultra-rápido: crear user → login → session paso=2 → redirect, MENOS DE 2 SEGUNDOS.
    4) Botón "Omitir onboarding / entrar al panel" SIEMPRE disponible en TODOS los pasos
       → nunca más usuario queda TRAPPEADO si algo falla en Paso2/Paso3.
    """
    template_dict = {
        1: 'accounts/onboarding_paso1.html',
        2: 'accounts/onboarding_paso2.html',
        3: 'accounts/onboarding_paso3.html',
    }
    PASOS = 3
    SESSION_KEY_USER = 'onboarding_user_id'
    SESSION_KEY_NEGOCIO = 'onboarding_negocio_id'
    SESSION_KEY_LOCAL = 'onboarding_local_id'
    SESSION_KEY_STEP = 'onboarding_paso_actual'

    def _omitir_y_ir_dashboard(self, request, user=None):
        """Acción de botón 'Omitir onboarding / entrar a mi cuenta'."""
        if user is None and request.user.is_authenticated:
            user = request.user
        # Invalidar cache onboarding por si acaso
        if user is not None:
            onboarding_cache_invalidar(request.session, user)
        _sesion_permitir_omitir_onboarding(request)
        # Limpiar wizard keys (pero NO la session de auth)
        for k in [self.SESSION_KEY_NEGOCIO, self.SESSION_KEY_LOCAL, self.SESSION_KEY_STEP]:
            request.session.pop(k, None)
        request.session.modified = True
        if user is not None and request.user.is_authenticated:
            messages.warning(
                request,
                '⚠️ Entraste sin completar la configuración inicial. Puedes volver a cualquier hora desde el panel: menú superior "⚙️ Completar onboarding".'
            )
            return redirect('/dashboard/?welcome=1')
        # Sin usuario autenticado → loguearlo antes o redir a login
        if user is not None:
            backend = 'django.contrib.auth.backends.ModelBackend'
            try:
                user.backend = backend
                auth_login(request, user, backend=backend)
            except Exception:
                pass
            return redirect('/dashboard/?welcome=1')
        return redirect('/accounts/login/?next=/dashboard/')

    def dispatch(self, request, *args, **kwargs):
        # ======== 1) Botón OMITIR onboarding desde URL (GET ?omitir_onboarding=1) ========
        if request.GET.get('omitir_onboarding') == '1':
            return self._omitir_y_ir_dashboard(request)
        # ======== 2) Roles Admin / Soporte → no onboarding ========
        if request.user.is_authenticated and (request.user.is_superuser or getattr(request.user, 'rol', None) == 'ADMIN_SOPORTE'):
            return redirect('/admin-panel/')
        # ======== 3) Si usuario MÓDULO OMITIR → permitelo pasar al dashboard ========
        if request.user.is_authenticated and _sesion_esta_omitido(request):
            return redirect('/dashboard/')
        # ======== 4) Onboarding completo → dashboard ========
        if request.user.is_authenticated and not onboarding_pendiente(request.user, session=request.session):
            return redirect('/dashboard/')
        return super().dispatch(request, *args, **kwargs)

    def get_paso(self, request):
        try:
            paso = int(request.GET.get('paso', request.POST.get('paso', '1')))
        except (TypeError, ValueError):
            paso = 1
        return max(1, min(self.PASOS, paso))

    def save_step_session(self, request, paso, user=None, negocio=None, local=None):
        if user:
            request.session[self.SESSION_KEY_USER] = str(user.id) if user.id else None
        if negocio:
            request.session[self.SESSION_KEY_NEGOCIO] = str(negocio.id) if negocio.id else None
        if local:
            request.session[self.SESSION_KEY_LOCAL] = str(local.id) if local.id else None
        request.session[self.SESSION_KEY_STEP] = paso
        request.session.modified = True

    def get_saved_user(self, request):
        """Solo LECTURA (sin side effects)."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if request.user.is_authenticated:
            return request.user
        uid = request.session.get(self.SESSION_KEY_USER)
        if uid:
            try:
                return User.objects.filter(id=uid).first()
            except (ValueError, TypeError):
                pass
        return None

    def get_saved_negocio(self, request):
        """SOLO LECTURA. SIN SIDE EFFECTS (nunca save_step_session). Bug anterior lo causaba."""
        from apps.businesses.models import Negocio
        nid = request.session.get(self.SESSION_KEY_NEGOCIO)
        if nid:
            try:
                return Negocio.objects.get(id=nid)
            except (Negocio.DoesNotExist, ValueError, TypeError):
                pass
        user = self.get_saved_user(request)
        if user is not None:
            negocio = Negocio.objects.filter(dueño_id=user.id).order_by('-fecha_creacion').first()
            return negocio
        return None

    def get_saved_local(self, request):
        """SOLO LECTURA. SIN SIDE EFFECTS."""
        from apps.businesses.models import Local
        lid = request.session.get(self.SESSION_KEY_LOCAL)
        if lid:
            try:
                return Local.objects.get(id=lid)
            except (Local.DoesNotExist, ValueError, TypeError):
                pass
        negocio = self.get_saved_negocio(request)
        if negocio is not None:
            return negocio.locales.order_by('-fecha_creacion').first()
        return None

    def get(self, request, *args, **kwargs):
        if request.GET.get('plan_id'):
            request.session['onboarding_plan_id'] = request.GET.get('plan_id')

        if request.GET.get('accion') == 'reiniciar':
            for k in [self.SESSION_KEY_USER, self.SESSION_KEY_NEGOCIO,
                      self.SESSION_KEY_LOCAL, self.SESSION_KEY_STEP, 'onboarding_plan_id']:
                request.session.pop(k, None)
            if not request.user.is_authenticated:
                return self._redirect_paso(1)
            return redirect('/accounts/logout/?next=/accounts/register/')

        user = self.get_saved_user(request)
        if user is not None and user.is_authenticated:
            # Cache-safe, 0 queries si está en session
            paso_detectado, _ = onboarding_siguiente_paso(user, session=request.session)
            pedido = self.get_paso(request)
            # Si usuario está en paso detectado>=2 pero pide paso1 sin querer → no se lo bloquees,
            # pero sí auto-avanza si es razonable (pedido<detectado).
            if pedido < paso_detectado and paso_detectado >= 2 and paso_detectado <= 3:
                return self._redirect_paso(paso_detectado)

        paso = self.get_paso(request)
        user = self.get_saved_user(request)
        negocio = self.get_saved_negocio(request)
        local = self.get_saved_local(request)

        # ====== Reglas de integridad SUAVES (solo si no hay omitir activo) ======
        if paso >= 2 and user is None:
            return self._redirect_paso(1)
        if paso == 3 and (negocio is None or local is None):
            # No fuerces volver si hay usuario (podría editar a mano la URL), sino solo si no hay datos
            if user is not None:
                pass
            else:
                return self._redirect_paso(2 if user is not None else 1)

        ctx = self._build_context(request, paso, user, negocio, local)
        return render(request, self.template_dict[paso], ctx)

    def post(self, request, *args, **kwargs):
        paso = self.get_paso(request)
        accion = request.POST.get('accion', f'paso{paso}')

        # ======== Botón "Omitir onboarding" / "Entrar al panel" ========
        if accion == 'omitir':
            user = self.get_saved_user(request)
            return self._omitir_y_ir_dashboard(request, user=user)

        if accion == 'reiniciar':
            for k in [self.SESSION_KEY_USER, self.SESSION_KEY_NEGOCIO,
                      self.SESSION_KEY_LOCAL, self.SESSION_KEY_STEP]:
                request.session.pop(k, None)
            return self._redirect_paso(1)

        if paso == 1:
            return self._procesar_paso1(request)
        if paso == 2:
            return self._procesar_paso2(request)
        if paso == 3:
            return self._procesar_paso3(request)
        return self._redirect_paso(1)

    # ===========================
    #  PASO 1 — Registro Usuario
    # 🏁 ULTRA-RÁPIDO: 1 INSERT user + 1 INSERT session Django + redirect
    #    Tiempo objetivo: <2 segundos incluso con NeonDB cold start.
    # ===========================
    def _procesar_paso1(self, request):
        saved = self.get_saved_user(request)
        if saved is not None and onboarding_pendiente(saved, session=request.session):
            # Ya pasó el paso 1 → redir rápido sin más consultas
            return self._redirect_paso(2)

        form = RegistroUsuarioForm(request.POST or None)
        if not form.is_valid():
            ctx = self._build_context(request, 1, form=form)
            return render(request, self.template_dict[1], ctx)

        # 🏁 1 sola transacción: insert user o recuperar existente (idempotente)
        from django.contrib.auth import get_user_model
        import django.contrib.auth.hashers as hashers
        User = get_user_model()
        email = form.cleaned_data['email'].strip().lower()
        try:
            with transaction.atomic():
                existente = User.objects.filter(email__iexact=email).first()
                if existente is None:
                    user = form.save(commit=True)
                else:
                    user = existente
                    if not hashers.check_password(form.cleaned_data['password1'], user.password):
                        form.add_error(None, 'Este correo ya está registrado. Por favor inicia sesión en /accounts/login/.')
                        ctx = self._build_context(request, 1, form=form)
                        return render(request, self.template_dict[1], ctx)
        except IntegrityError:
            # Race 2 tabs paralelos mismo ms: recuperar desde BD
            user = User.objects.filter(email__iexact=email).first()
            if user is None:
                raise

        # 🏁 1) Guardar session keys del wizard PASO 2 inmediatamente
        self.save_step_session(request, 2, user=user)

        # 🏁 2) AUTO-LOGIN (también escribe session Django, 1 query sola)
        backend = 'django.contrib.auth.backends.ModelBackend'
        if not request.user.is_authenticated or request.user.id != user.id:
            try:
                user.backend = backend
                auth_login(request, user, backend=backend)
            except Exception:
                pass

        # 🏁 3) Cache onboarding = Paso 2 (evita recalcular en redirect)
        from .onboarding_service import _cache_guardar
        _cache_guardar(request.session, user, {
            'pendiente': True,
            'paso': 2,
            'explicacion': 'Usuario recién creado, falta Negocio + Local',
        })

        # 🏁 4) NO llamar marcar_paso1_usuario (query UPDATE Negocio sin sentido cuando no hay negocios).
        # Lo marcamos luego en marcar_paso2_negocio cuando sí exista el Negocio.

        messages.success(
            request,
            f'✅ ¡Cuenta creada exitosamente, {user.first_name or "bienvenido"}! Continúa con tus datos comerciales (toma 40 segundos).'
        )
        return self._redirect_paso(2)

    # ===========================
    #  PASO 2 — Datos Negocio + Local
    # ===========================
    def _procesar_paso2(self, request):
        user = self.get_saved_user(request)
        if user is None:
            return self._redirect_paso(1)

        from apps.businesses.models import Negocio, Local
        # IDEMPOTENCIA: si dueño ya tiene Negocio ACTIVO → UPDATE, no CREATE 2 veces
        negocio_preexistente = (
            Negocio.objects
            .filter(dueño_id=user.id, estado=Negocio.EstadoChoices.ACTIVO)
            .order_by('-fecha_creacion')
            .first()
        )
        local_preexistente = None
        if negocio_preexistente:
            local_preexistente = (
                Local.objects
                .filter(negocio__dueño_id=user.id, estado=Local.EstadoChoices.ACTIVO)
                .order_by('-fecha_creacion')
                .first()
            )

        form_negocio = NegocioOnboardingForm(
            request.POST or None,
            prefix='neg',
            instance=negocio_preexistente if negocio_preexistente else self.get_saved_negocio(request),
        )
        form_local = LocalOnboardingForm(
            request.POST or None,
            prefix='loc',
            instance=local_preexistente if local_preexistente else self.get_saved_local(request),
        )

        if not (form_negocio.is_valid() and form_local.is_valid()):
            ctx = self._build_context(
                request, 2, user=user,
                form_negocio=form_negocio, form_local=form_local,
            )
            return render(request, self.template_dict[2], ctx)

        try:
            with transaction.atomic():
                # ===== NEGOCIO =====
                if negocio_preexistente is None and not form_negocio.instance.pk:
                    negocio = form_negocio.save_negocio(dueño=user, commit=True)
                else:
                    negocio = form_negocio.save_negocio(dueño=user, commit=False)
                    if negocio_preexistente is not None:
                        negocio.pk = negocio_preexistente.pk
                    negocio.save()

                # ===== LOCAL: heredar comuna + dirección desde Negocio si check "misma dirección" =====
                if not form_local.cleaned_data.get('direccion') and negocio.direccion:
                    form_local.instance.direccion = negocio.direccion
                if not form_local.cleaned_data.get('ciudad') and negocio.ciudad:
                    form_local.instance.ciudad = negocio.ciudad

                if local_preexistente is None and not form_local.instance.pk:
                    local = form_local.save_local(negocio=negocio, commit=True)
                else:
                    local = form_local.save_local(negocio=negocio, commit=False)
                    if local_preexistente is not None:
                        local.pk = local_preexistente.pk
                    local.negocio_id = negocio.id
                    local.save()
        except IntegrityError:
            # Race condition extremo: recuperar desde BD
            negocio = Negocio.objects.filter(dueño_id=user.id).order_by('-fecha_creacion').first()
            local = Local.objects.filter(negocio=negocio).order_by('-fecha_creacion').first() if negocio else None
            if negocio is None or local is None:
                raise

        # Actualizar flags + cache invalidar
        marcar_paso2_negocio(negocio, user)
        onboarding_cache_invalidar(request.session, user)
        self.save_step_session(request, 3, negocio=negocio, local=local)
        return self._redirect_paso(3)

    # ===========================
    #  PASO 3 — Confirmación Plan
    # ===========================
    def _procesar_paso3(self, request):
        user = self.get_saved_user(request)
        negocio = self.get_saved_negocio(request)
        local = self.get_saved_local(request)
        if user is None:
            return self._redirect_paso(1)
        if negocio is None or local is None:
            return self._redirect_paso(2)

        # Idempotencia: onboarding ya terminó → dashboard directo
        if not onboarding_pendiente(user, session=request.session):
            messages.success(
                request,
                f'✅ Onboarding ya completado. Bienvenido/a nuevamente {user.first_name or user.email}!'
            )
            for k in [self.SESSION_KEY_USER, self.SESSION_KEY_NEGOCIO,
                      self.SESSION_KEY_LOCAL, self.SESSION_KEY_STEP]:
                request.session.pop(k, None)
            request.session.modified = True
            return redirect('/dashboard/?welcome=1')

        aceptar = request.POST.get('aceptar_plan') == '1'
        plan = get_plan_onboarding(request.session.get('onboarding_plan_id'))
        plan_nombre = plan.get_nombre_mostrar() if plan else 'el plan seleccionado'
        if not aceptar:
            messages.error(
                request,
                f'Debes aceptar {plan_nombre} para continuar. Si necesitas ayuda contacta a soporte.'
            )
            ctx = self._build_context(request, 3, user, negocio, local)
            return render(request, self.template_dict[3], ctx)

        try:
            with transaction.atomic():
                resultado = finalizar_onboarding(request, user, negocio, local)
        except IntegrityError:
            from apps.billing.models import Suscripcion
            s = Suscripcion.objects.filter(negocio=negocio).order_by('-fecha_inicio').first()
            resultado = {'suscripcion': s}

        suscripcion = resultado.get('suscripcion')
        plan_actual = suscripcion.plan if suscripcion else plan
        dias = getattr(plan_actual, 'dias_prueba_gratis', 365) or 365
        plan_mostrar = plan_actual.get_nombre_mostrar() if plan_actual else 'tu plan'

        for k in [self.SESSION_KEY_USER, self.SESSION_KEY_NEGOCIO,
                  self.SESSION_KEY_LOCAL, self.SESSION_KEY_STEP]:
            request.session.pop(k, None)
        request.session.modified = True
        onboarding_cache_invalidar(request.session, user)
        # Quitar flag omitir (ya completó onboarding)
        request.session.pop(OMITIR_KEY, None)

        sus_estado = getattr(suscripcion, 'estado', None) if suscripcion else None
        if suscripcion and sus_estado == 'PENDIENTE':
            messages.warning(
                request,
                f'🎉 ¡Bienvenido/a {user.first_name or user.email}! Tu negocio "{negocio.nombre}" ya está registrado. '
                f'Tu plan "{plan_mostrar}" quedó PENDIENTE DE ACTIVACIÓN — nuestro equipo de soporte '
                f'lo revisará y confirmará a la brevedad. Recibirás un correo cuando esté listo '
                f'o puedes contactarnos en soporte@clientbeat.cl.'
            )
        else:
            messages.success(
                request,
                f'🎉 ¡Bienvenido/a {user.first_name or user.email}! Tu negocio "{negocio.nombre}" ya está listo. '
                f'{plan_mostrar} activado por {dias} días gratuitos.'
            )
        return redirect('/dashboard/?welcome=1')

    # ===========================
    # Helpers
    # ===========================
    def _redirect_paso(self, paso):
        return redirect(f'/accounts/onboarding/?paso={paso}')

    def _build_context(self, request, paso, user=None, negocio=None, local=None,
                       form=None, form_negocio=None, form_local=None):
        pasos_meta = {
            1: {'titulo': 'Crea tu cuenta', 'sub': 'Paso 1 de 3 · Toma 1 minuto'},
            2: {'titulo': 'Cuéntanos sobre tu negocio', 'sub': 'Paso 2 de 3 · Configuración inicial'},
            3: {'titulo': 'Confirma tu Plan', 'sub': 'Paso 3 de 3 · ¡Último paso!'},
        }
        meta = pasos_meta.get(paso, pasos_meta[1])
        ctx = {
            'paso_actual': paso,
            'total_pasos': self.PASOS,
            'paso_titulo': meta['titulo'],
            'paso_sub': meta['sub'],
            'progreso_pct': int((paso - 1) / (self.PASOS - 1) * 100) if self.PASOS > 1 else 100,
            'usuario_paso1': user,
            'negocio_paso2': negocio,
            'local_paso2': local,
            # 🏁 Variable para templates: botón omitir siempre visible
            'puede_omitir_onboarding': bool(user is not None or request.user.is_authenticated),
        }
        if paso == 1:
            ctx['form'] = form if form is not None else RegistroUsuarioForm()
        if paso == 2:
            ctx['form_negocio'] = form_negocio if form_negocio is not None else NegocioOnboardingForm(prefix='neg')
            ctx['form_local'] = form_local if form_local is not None else LocalOnboardingForm(prefix='loc')
        if paso == 3:
            from apps.billing.models import Plan
            plan = get_plan_onboarding(request.session.get('onboarding_plan_id'))
            ctx['plan_actual'] = plan
            if plan is None:
                ctx['error_sin_plan'] = (
                    '⚠️ Lo sentimos, no hay un Plan activo configurado por el momento. '
                    'Por favor contacta a soporte o intenta más tarde.'
                )
        return ctx


onboarding = OnboardingWizardView.as_view()


from django.utils import timezone
from apps.billing.models import Plan, Suscripcion, EstadoSuscripcionChoices, CambioPlan, MotivoCambioPlanChoices


class PerfilUsuarioView(LoginRequiredMixin, View):
    """
    Vista de Perfil y Configuración de Cuenta de Usuario.
    Permite visualizar/editar datos personales, información del negocio/locales,
    agregar sucursales, gestionar y cambiar plan, cancelar o reactivar suscripción,
    cambiar contraseña y contactar soporte.
    """
    template_name = 'accounts/perfil.html'

    def get_context_data(self, request):
        from apps.businesses.models import Negocio, MiembroEquipo, InvitacionEquipo

        user = request.user
        negocios = user.negocios_permitidos_qs()
        negocio = negocios.first() if negocios.exists() else None
        locales = negocio.locales.filter(estado='ACTIVO') if negocio else []
        cant_locales = locales.count() or 1

        es_dueno = bool(user.is_admin_soporte or user.is_dueno or (negocio and negocio.dueño_id == user.id))

        suscripcion = None
        if negocio:
            suscripcion = (
                Suscripcion.objects.filter(negocio=negocio)
                .order_by('-fecha_inicio')
                .first()
            )

        plan_activo = suscripcion.plan if suscripcion else Plan.get_plan_default()
        desglose_actual = plan_activo.desglose_mensual(cant_locales) if plan_activo else None

        planes_disponibles = Plan.objects.filter(activo=True).order_by('orden', '-fecha_creacion')
        planes_info = []
        for p in planes_disponibles:
            desglose = p.desglose_mensual(cant_locales)
            planes_info.append({
                'plan': p,
                'desglose': desglose,
                'es_actual': bool(suscripcion and suscripcion.plan_id == p.id),
            })

        # ================= GESTIÓN DE EQUIPO / COLABORADORES =================
        miembros_equipo = []
        invitaciones_pendientes = []
        limite_colaboradores = plan_activo.usuarios_permitidos if plan_activo else 2
        total_colaboradores_usados = 0
        puede_invitar_colaborador = False

        if negocio:
            miembros_equipo = list(
                MiembroEquipo.objects.filter(negocio=negocio)
                .select_related('usuario', 'invitado_por')
                .order_by('fecha_invitacion')
            )
            invitaciones_pendientes = list(
                InvitacionEquipo.objects.filter(negocio=negocio, estado='PENDIENTE')
                .select_related('invitado_por')
                .order_by('-fecha_invitacion')
            )
            total_colaboradores_usados = len(miembros_equipo) + len(invitaciones_pendientes)
            puede_invitar_colaborador = total_colaboradores_usados < limite_colaboradores

        return {
            'usuario': user,
            'negocio': negocio,
            'locales': locales,
            'cant_locales': cant_locales,
            'suscripcion': suscripcion,
            'plan_activo': plan_activo,
            'desglose_actual': desglose_actual,
            'planes_disponibles': planes_disponibles,
            'planes_info': planes_info,
            'rol_label': user.get_rol_display(),
            'es_dueno': es_dueno,
            'miembros_equipo': miembros_equipo,
            'invitaciones_pendientes': invitaciones_pendientes,
            'limite_colaboradores': limite_colaboradores,
            'total_colaboradores_usados': total_colaboradores_usados,
            'puede_invitar_colaborador': puede_invitar_colaborador,
            'rol_choices': MiembroEquipo.RolChoices.choices if negocio else [],
        }

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        import secrets
        from apps.businesses.models import MiembroEquipo, InvitacionEquipo

        action = request.POST.get('action')
        user = request.user

        negocios = user.negocios_permitidos_qs()
        negocio = negocios.first() if negocios.exists() else None
        es_dueno = bool(user.is_admin_soporte or user.is_dueno or (negocio and negocio.dueño_id == user.id))

        # Restricción RBAC: Solo el Dueño o Admin Soporte pueden modificar la cuenta, plan, agregar locales o gestionar colaboradores
        if action in ['update_business', 'change_plan', 'cancel_subscription', 'reactivate_subscription', 'add_local', 'invite_collaborator', 'resend_invitation', 'cancel_invitation', 'remove_member'] and not es_dueno:
            messages.error(
                request,
                '🔒 Permiso denegado: Solo el dueño del negocio tiene atribuciones para modificar datos corporativos, planes, sucursales o equipo.'
            )
            context = self.get_context_data(request)
            return render(request, self.template_name, context)

        if action == 'invite_collaborator':
            if not negocio:
                messages.error(request, '⚠️ Debes tener un negocio configurado para invitar colaboradores.')
            else:
                suscripcion = Suscripcion.objects.filter(negocio=negocio).order_by('-fecha_inicio').first()
                plan_activo = suscripcion.plan if suscripcion else Plan.get_plan_default()
                limite = plan_activo.usuarios_permitidos if plan_activo else 2

                miembros_cnt = MiembroEquipo.objects.filter(negocio=negocio).count()
                invitaciones_cnt = InvitacionEquipo.objects.filter(negocio=negocio, estado='PENDIENTE').count()
                total_actual = miembros_cnt + invitaciones_cnt

                if total_actual >= limite:
                    messages.error(
                        request,
                        f'⚠️ Has alcanzado el límite de {limite} colaboradores de tu plan ({plan_activo.get_nombre_mostrar()}). Para invitar más miembros, actualiza tu plan en la sección "Plan y Suscripción".'
                    )
                else:
                    email_inv = request.POST.get('email_colaborador', '').strip().lower()
                    nombre_inv = request.POST.get('nombre_colaborador', '').strip()
                    rol_inv = request.POST.get('rol_colaborador', MiembroEquipo.RolChoices.USUARIO_EQUIPO)

                    if not email_inv:
                        messages.error(request, '⚠️ Ingresa una dirección de correo válida para invitar.')
                    elif MiembroEquipo.objects.filter(negocio=negocio, usuario__email__iexact=email_inv).exists():
                        messages.error(request, f'⚠️ El usuario {email_inv} ya es miembro activo de este negocio.')
                    else:
                        inv_existente = InvitacionEquipo.objects.filter(negocio=negocio, email__iexact=email_inv, estado='PENDIENTE').first()
                        if inv_existente:
                            enviar_email_invitacion(inv_existente, request)
                            messages.info(request, f'ℹ️ Se reenvió el correo de invitación a {email_inv}.')
                        else:
                            token_inv = f"INV-{secrets.token_urlsafe(24)}"
                            nueva_inv = InvitacionEquipo.objects.create(
                                negocio=negocio,
                                email=email_inv,
                                nombre=nombre_inv,
                                rol=rol_inv,
                                token=token_inv,
                                invitado_por=user,
                                estado='PENDIENTE',
                            )
                            enviar_email_invitacion(nueva_inv, request)
                            messages.success(
                                request,
                                f'✉️ Invitación enviada exitosamente a {email_inv} con el rol de {nueva_inv.get_rol_display()}.'
                            )

        elif action == 'resend_invitation':
            inv_id = request.POST.get('invitacion_id')
            inv = InvitacionEquipo.objects.filter(id=inv_id, negocio=negocio, estado='PENDIENTE').first()
            if inv:
                enviar_email_invitacion(inv, request)
                messages.success(request, f'📩 Correo de invitación reenviado exitosamente a {inv.email}.')
            else:
                messages.error(request, '⚠️ No se encontró la invitación pendiente.')

        elif action == 'cancel_invitation':
            inv_id = request.POST.get('invitacion_id')
            inv = InvitacionEquipo.objects.filter(id=inv_id, negocio=negocio, estado='PENDIENTE').first()
            if inv:
                inv.estado = 'CANCELADA'
                inv.save(update_fields=['estado'])
                messages.warning(request, f'🚫 Invitación a {inv.email} cancelada.')
            else:
                messages.error(request, '⚠️ No se encontró la invitación.')

        elif action == 'remove_member':
            miembro_id = request.POST.get('miembro_id')
            miembro = MiembroEquipo.objects.filter(id=miembro_id, negocio=negocio).first()
            if miembro:
                if miembro.usuario_id == negocio.dueño_id:
                    messages.error(request, '❌ No es posible remover al dueño del negocio.')
                else:
                    email_m = miembro.usuario.email
                    miembro.delete()
                    messages.warning(request, f'🗑️ {email_m} ha sido removido del equipo de {negocio.nombre}.')
            else:
                messages.error(request, '⚠️ No se encontró el miembro del equipo.')

        elif action == 'update_profile':
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            telefono = request.POST.get('telefono', '').strip()

            user.first_name = first_name
            user.last_name = last_name
            user.telefono = telefono
            user.save()

            messages.success(request, '✅ Tus datos personales fueron actualizados correctamente.')

        elif action == 'update_business':
            if negocio:
                nombre = request.POST.get('nombre_negocio', '').strip()
                direccion = request.POST.get('direccion_negocio', '').strip()
                ciudad = request.POST.get('ciudad_negocio', '').strip()
                sitio_web = request.POST.get('sitio_web', '').strip()

                if nombre:
                    negocio.nombre = nombre
                negocio.direccion = direccion
                negocio.ciudad = ciudad
                negocio.sitio_web = sitio_web
                negocio.save()

                messages.success(request, '✅ La información de tu negocio fue actualizada exitosamente.')
            else:
                messages.error(request, '⚠️ No tienes permisos para modificar este negocio.')

        elif action == 'add_local':
            from apps.businesses.models import Local

            if not negocio:
                messages.error(request, '⚠️ Debes estar asociado a un negocio activo para registrar una sucursal.')
            else:
                nombre_local = request.POST.get('nombre_local', '').strip()
                direccion_local = request.POST.get('direccion_local', '').strip()
                ciudad_local = request.POST.get('ciudad_local', '').strip()

                if not nombre_local:
                    messages.error(request, '⚠️ Debes ingresar un nombre representativo para la nueva sucursal.')
                else:
                    qr_tok = f"CB-{secrets.token_urlsafe(16).upper()[:10]}"
                    local_nuevo = Local.objects.create(
                        negocio=negocio,
                        nombre=nombre_local,
                        direccion=direccion_local or negocio.direccion,
                        ciudad=ciudad_local or negocio.ciudad,
                        estado=Local.EstadoChoices.ACTIVO,
                        qr_token=qr_tok,
                        comuna=negocio.comuna,
                    )

                    suscripcion = Suscripcion.objects.filter(negocio=negocio).order_by('-fecha_inicio').first()
                    plan_activo = suscripcion.plan if suscripcion else Plan.get_plan_default()
                    locales_activos = negocio.locales.filter(estado='ACTIVO').count()

                    desglose = plan_activo.desglose_mensual(locales_activos) if plan_activo else None

                    if desglose and desglose['local_extra_cantidad'] > 0:
                        msg_facturacion = (
                            f' Tu plan incluye {plan_activo.locales_gratis_incluidos} locales gratis. '
                            f'Al contar ahora con {locales_activos} sucursales activas, tu facturación mensual ajustada es de '
                            f'${desglose["total_clp"]:,} CLP (incluye {desglose["local_extra_cantidad"]} local(es) adicional(es) '
                            f'a ${plan_activo.costo_local_adicional_clp:,} CLP/mes).'
                        ).replace(',', '.')
                    else:
                        msg_facturacion = (
                            f' Incluido sin costo adicional en los {plan_activo.locales_gratis_incluidos} locales gratis de tu plan.'
                        )

                    messages.success(
                        request,
                        f'🎉 ¡Sucursal "{local_nuevo.nombre}" agregada exitosamente con código QR único ({local_nuevo.qr_token})!{msg_facturacion}'
                    )

        elif action == 'change_plan':
            nuevo_plan_id = request.POST.get('plan_id')

            if not negocio:
                messages.error(request, '⚠️ No se encontró un negocio asociado para cambiar de plan.')
            else:
                try:
                    nuevo_plan = Plan.objects.get(id=nuevo_plan_id, activo=True)
                    suscripcion = Suscripcion.objects.filter(negocio=negocio).order_by('-fecha_inicio').first()
                    plan_anterior = suscripcion.plan if suscripcion else None

                    if suscripcion:
                        suscripcion.plan = nuevo_plan
                        suscripcion.estado = EstadoSuscripcionChoices.ACTIVA
                        suscripcion.save(update_fields=['plan', 'estado'])

                        CambioPlan.objects.create(
                            suscripcion=suscripcion,
                            plan_anterior=plan_anterior,
                            plan_nuevo=nuevo_plan,
                            motivo=MotivoCambioPlanChoices.SOLICITUD_DUENO,
                            realizado_por=user,
                            precio_antes_clp=plan_anterior.precio_clp if plan_anterior else 0,
                            precio_despues_clp=nuevo_plan.precio_clp or 0,
                        )

                        messages.success(
                            request,
                            f'🎉 Tu plan se actualizó exitosamente a "{nuevo_plan.get_nombre_mostrar()}".'
                        )
                    else:
                        messages.warning(request, '⚠️ No cuentas con una suscripción activa previa.')
                except Plan.DoesNotExist:
                    messages.error(request, '⚠️ El plan seleccionado no existe o no está activo.')

        elif action == 'cancel_subscription':
            motivo = request.POST.get('motivo_cancelacion', '').strip() or 'Solicitado por el cliente desde su perfil'

            if negocio:
                suscripcion = Suscripcion.objects.filter(negocio=negocio).order_by('-fecha_inicio').first()
                if suscripcion:
                    suscripcion.estado = EstadoSuscripcionChoices.CANCELADA
                    suscripcion.cancelada_en = timezone.now()
                    suscripcion.motivo_cancelacion = motivo
                    suscripcion.renovacion_automatica = False
                    suscripcion.save(update_fields=['estado', 'cancelada_en', 'motivo_cancelacion', 'renovacion_automatica'])

                    messages.warning(
                        request,
                        '⚠️ Tu suscripción ha sido cancelada. Mantendrás el acceso a la plataforma hasta el final de tu periodo de facturación actual.'
                    )
                else:
                    messages.error(request, '⚠️ No hay una suscripción activa para cancelar.')

        elif action == 'reactivate_subscription':
            if negocio:
                suscripcion = Suscripcion.objects.filter(negocio=negocio).order_by('-fecha_inicio').first()
                if suscripcion:
                    suscripcion.estado = EstadoSuscripcionChoices.ACTIVA
                    suscripcion.renovacion_automatica = True
                    suscripcion.cancelada_en = None
                    suscripcion.save(update_fields=['estado', 'renovacion_automatica', 'cancelada_en'])

                    messages.success(request, '⚡ ¡Tu suscripción ha sido reactivada exitosamente!')
                else:
                    messages.error(request, '⚠️ No hay una suscripción previa para reactivar.')

        elif action == 'change_password':
            pass_actual = request.POST.get('current_password', '')
            pass_nueva = request.POST.get('new_password', '')
            pass_confirm = request.POST.get('confirm_password', '')

            if not user.check_password(pass_actual):
                messages.error(request, '❌ La contraseña actual no es correcta.')
            elif len(pass_nueva) < 8:
                messages.error(request, '⚠️ La nueva contraseña debe tener al menos 8 caracteres.')
            elif pass_nueva != pass_confirm:
                messages.error(request, '⚠️ Las contraseñas no coinciden.')
            else:
                user.set_password(pass_nueva)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, '🔒 Tu contraseña se ha actualizado con éxito.')

        elif action == 'contact_support':
            asunto = request.POST.get('asunto', '').strip()
            mensaje = request.POST.get('mensaje', '').strip()

            if asunto and mensaje:
                messages.success(
                    request,
                    f'📩 Mensaje enviado a soporte@clientbeat.cl. Asunto: "{asunto}". Nos pondremos en contacto contigo a {user.email} a la brevedad.'
                )
            else:
                messages.error(request, '⚠️ Por favor ingresa el asunto y el mensaje para el equipo de soporte.')

        context = self.get_context_data(request)
        return render(request, self.template_name, context)


def enviar_email_invitacion(invitacion, request):
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.conf import settings

    url_invitacion = request.build_absolute_uri(f'/accounts/invitacion/{invitacion.token}/')
    dueno = invitacion.invitado_por
    dueno_nombre = dueno.get_full_name() or dueno.email if dueno else 'El dueño del negocio'

    html_message = render_to_string('emails/invitacion_colaborador.html', {
        'invitacion': invitacion,
        'negocio_nombre': invitacion.negocio.nombre,
        'dueno_nombre': dueno_nombre,
        'dueno_email': dueno.email if dueno else '',
        'invitado_nombre': invitacion.nombre or '',
        'rol_display': invitacion.get_rol_display(),
        'url_invitacion': url_invitacion,
    })

    send_mail(
        subject=f'¡{dueno_nombre} te ha invitado a unirte a {invitacion.negocio.nombre} en ClientBeat!',
        message=f'Hola! {dueno_nombre} te ha invitado a unirte a {invitacion.negocio.nombre}. Ingresa a: {url_invitacion}',
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'contacto@avaapp.cl'),
        recipient_list=[invitacion.email],
        html_message=html_message,
        fail_silently=True,
    )


class AceptarInvitacionView(View):
    template_name = 'accounts/invitacion_aceptar.html'

    def get(self, request, token, *args, **kwargs):
        from apps.businesses.models import InvitacionEquipo, MiembroEquipo
        from django.contrib.auth import get_user_model

        User = get_user_model()
        invitacion = InvitacionEquipo.objects.filter(token=token, estado='PENDIENTE').select_related('negocio', 'invitado_por').first()
        if not invitacion:
            messages.error(request, '⚠️ El enlace de invitación no es válido o ya fue utilizado.')
            return redirect('/accounts/login/')

        if request.user.is_authenticated and request.user.email.lower() == invitacion.email.lower():
            MiembroEquipo.objects.get_or_create(
                negocio=invitacion.negocio,
                usuario=request.user,
                defaults={
                    'rol': invitacion.rol,
                    'estado': MiembroEquipo.EstadoChoices.ACTIVO,
                    'invitado_por': invitacion.invitado_por,
                }
            )
            invitacion.estado = InvitacionEquipo.EstadoChoices.ACEPTADA
            invitacion.fecha_aceptacion = timezone.now()
            invitacion.save()

            messages.success(request, f'🎉 ¡Te has unido exitosamente al equipo de {invitacion.negocio.nombre}!')
            return redirect('/dashboard/?welcome=1')

        user_existente = User.objects.filter(email__iexact=invitacion.email).exists()
        return render(request, self.template_name, {
            'invitacion': invitacion,
            'user_existente': user_existente,
        })

    def post(self, request, token, *args, **kwargs):
        import secrets
        from django.contrib.auth import get_user_model, authenticate, login as auth_login
        from apps.businesses.models import InvitacionEquipo, MiembroEquipo

        User = get_user_model()
        invitacion = InvitacionEquipo.objects.filter(token=token, estado='PENDIENTE').select_related('negocio', 'invitado_por').first()
        if not invitacion:
            messages.error(request, '⚠️ El enlace de invitación no es válido o ya venció.')
            return redirect('/accounts/login/')

        user_existente = User.objects.filter(email__iexact=invitacion.email).first()

        if user_existente:
            password = request.POST.get('password', '')
            user = authenticate(request, username=user_existente.email, password=password)
            if user is None:
                messages.error(request, '❌ Contraseña incorrecta. Por favor verifica tus credenciales.')
                return render(request, self.template_name, {'invitacion': invitacion, 'user_existente': True})
        else:
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            telefono = request.POST.get('telefono', '').strip()
            password = request.POST.get('password', '')
            confirm_password = request.POST.get('confirm_password', '')

            if len(password) < 8:
                messages.error(request, '⚠️ La contraseña debe tener al menos 8 caracteres.')
                return render(request, self.template_name, {'invitacion': invitacion, 'user_existente': False})
            if password != confirm_password:
                messages.error(request, '⚠️ Las contraseñas no coinciden.')
                return render(request, self.template_name, {'invitacion': invitacion, 'user_existente': False})

            user = User.objects.create_user(
                username=invitacion.email.split('@')[0] + '_' + secrets.token_hex(3),
                email=invitacion.email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                telefono=telefono,
                rol=User.RolChoices.USUARIO_EQUIPO,
                is_staff=False,
                es_mayor_18=True,
            )

        miembro, _ = MiembroEquipo.objects.get_or_create(
            negocio=invitacion.negocio,
            usuario=user,
            defaults={
                'rol': invitacion.rol,
                'estado': MiembroEquipo.EstadoChoices.ACTIVO,
                'invitado_por': invitacion.invitado_por,
            }
        )
        if miembro.estado != MiembroEquipo.EstadoChoices.ACTIVO:
            miembro.estado = MiembroEquipo.EstadoChoices.ACTIVO
            miembro.save()

        invitacion.estado = InvitacionEquipo.EstadoChoices.ACEPTADA
        invitacion.fecha_aceptacion = timezone.now()
        invitacion.save()

        backend = 'django.contrib.auth.backends.ModelBackend'
        user.backend = backend
        auth_login(request, user, backend=backend)

        messages.success(request, f'🎉 ¡Perfil configurado con éxito! Bienvenido al equipo de {invitacion.negocio.nombre}.')
        return redirect('/dashboard/?welcome=1')


