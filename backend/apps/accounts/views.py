from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views
from django.contrib import messages
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.csrf import csrf_protect

from .forms import RegistroUsuarioForm
from .onboarding_service import (
    finalizar_onboarding,
    onboarding_pendiente,
    onboarding_siguiente_paso,
    get_plan_onboarding,
    marcar_paso1_usuario,
    marcar_paso2_negocio,
)
from apps.businesses.forms import NegocioOnboardingForm, LocalOnboardingForm


class LoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    next_page = '/dashboard/'

    def get_success_url(self):
        user = self.request.user
        if onboarding_pendiente(user):
            paso, _ = onboarding_siguiente_paso(user)
            messages.info(
                self.request,
                f'¡Hola {user.first_name or user.email}! Ve dónde lo dejaste: completa la configuración de tu negocio para finalizar el onboarding.'
            )
            return f'/accounts/onboarding/?paso={paso}'
        return super().get_success_url() or '/dashboard/'


class LogoutView(auth_views.LogoutView):
    next_page = '/'


@method_decorator(sensitive_post_parameters('password1', 'password2'), name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
class OnboardingWizardView(View):
    """
    Wizard onboarding multi-step:
    Paso 1 → Registro Usuario (email, password, nombre, T&C, mayor18)
    Paso 2 → Datos Negocio + Local #1
    Paso 3 → Confirmación Plan Default activo (días gratis según plan)

    Características reanudación:
    - Si el usuario ya inició sesión (cuenta creada en paso1 anterior), se le
      redirige automáticamente al paso 2 sin volver a registrarse.
    - Si ya creó negocio y local pero no finalizó suscripción, salta al paso 3.
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

    def dispatch(self, request, *args, **kwargs):
        # Si el usuario tiene onboarding COMPLETADO (no pendiente), va a dashboard
        if request.user.is_authenticated and not onboarding_pendiente(request.user):
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
        """
        Retorna el usuario del wizard. Prioriza:
        1) Usuario autenticado en request (cuando reanuda onboarding por login)
        2) Session key del wizard
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Caso reanudación: usuario ya logueado
        if request.user.is_authenticated and onboarding_pendiente(request.user):
            self.save_step_session(request, 2, user=request.user)
            return request.user

        uid = request.session.get(self.SESSION_KEY_USER)
        if uid:
            try:
                return User.objects.get(id=uid)
            except (User.DoesNotExist, ValueError, TypeError):
                pass
        return None

    def get_saved_negocio(self, request):
        from apps.businesses.models import Negocio
        nid = request.session.get(self.SESSION_KEY_NEGOCIO)
        if nid:
            try:
                return Negocio.objects.get(id=nid)
            except (Negocio.DoesNotExist, ValueError, TypeError):
                pass
        # Fallback por si el usuario ya tiene un negocio en BD pero perdió la sesión
        user = self.get_saved_user(request)
        if user is not None:
            negocio = Negocio.objects.filter(dueño_id=user.id).order_by('-fecha_creacion').first()
            if negocio:
                self.save_step_session(request, 3, negocio=negocio)
                return negocio
        return None

    def get_saved_local(self, request):
        from apps.businesses.models import Local
        lid = request.session.get(self.SESSION_KEY_LOCAL)
        if lid:
            try:
                return Local.objects.get(id=lid)
            except (Local.DoesNotExist, ValueError, TypeError):
                pass
        # Fallback por si ya hay locales en BD del negocio
        negocio = self.get_saved_negocio(request)
        if negocio is not None:
            local = negocio.locales.order_by('-fecha_creacion').first()
            if local:
                self.save_step_session(request, 3, local=local)
                return local
        return None

    def get(self, request, *args, **kwargs):
        if request.GET.get('accion') == 'reiniciar':
            for k in [self.SESSION_KEY_USER, self.SESSION_KEY_NEGOCIO,
                      self.SESSION_KEY_LOCAL, self.SESSION_KEY_STEP]:
                request.session.pop(k, None)
            # Si es usuario autenticado, no lo desloguea pero fuerza paso 1
            if not request.user.is_authenticated:
                return self._redirect_paso(1)
            return redirect('/accounts/logout/?next=/accounts/register/')

        # Detección automática de paso real por BD del usuario logueado
        user = self.get_saved_user(request)
        if user is not None and user.is_authenticated or user:
            paso_detectado, _ = onboarding_siguiente_paso(user)
            if paso_detectado >= 2:
                # Carga objetos por BD (por si la sesión se perdió)
                self.get_saved_negocio(request)
                self.get_saved_local(request)
                pedido = self.get_paso(request)
                # Si el usuario pide paso 1 pero tiene cuenta, lo subimos al paso que corresponde
                if pedido < paso_detectado:
                    return self._redirect_paso(paso_detectado)

        paso = self.get_paso(request)
        user = self.get_saved_user(request)
        negocio = self.get_saved_negocio(request)
        local = self.get_saved_local(request)

        # Seguridad del wizard: no saltes pasos sin los datos previos
        if paso >= 2 and user is None:
            return self._redirect_paso(1)
        if paso == 3 and (user is None or negocio is None or local is None):
            return self._redirect_paso(2)

        ctx = self._build_context(request, paso, user, negocio, local)
        return render(request, self.template_dict[paso], ctx)

    def post(self, request, *args, **kwargs):
        paso = self.get_paso(request)
        accion = request.POST.get('accion', f'paso{paso}')

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
    # ===========================
    def _procesar_paso1(self, request):
        # Si usuario ya autenticado con onboarding pendiente, no necesita registrarse
        saved = self.get_saved_user(request)
        if saved is not None and onboarding_pendiente(saved):
            return self._redirect_paso(2)

        form = RegistroUsuarioForm(request.POST or None)
        if form.is_valid():
            user = form.save(commit=True)
            marcar_paso1_usuario(user)
            self.save_step_session(request, 2, user=user)
            return self._redirect_paso(2)
        ctx = self._build_context(request, 1, form=form)
        return render(request, self.template_dict[1], ctx)

    # ===========================
    #  PASO 2 — Datos Negocio + Local
    # ===========================
    def _procesar_paso2(self, request):
        user = self.get_saved_user(request)
        if user is None:
            return self._redirect_paso(1)

        form_negocio = NegocioOnboardingForm(
            request.POST or None,
            prefix='neg',
            instance=self.get_saved_negocio(request),
        )
        form_local = LocalOnboardingForm(
            request.POST or None,
            prefix='loc',
            instance=self.get_saved_local(request),
        )

        if form_negocio.is_valid() and form_local.is_valid():
            negocio = form_negocio.save_negocio(dueño=user, commit=True)
            if not form_local.cleaned_data.get('direccion') and negocio.direccion:
                form_local.instance.direccion = negocio.direccion
            if not form_local.cleaned_data.get('ciudad') and negocio.ciudad:
                form_local.instance.ciudad = negocio.ciudad
            local = form_local.save_local(negocio=negocio, commit=True)
            marcar_paso2_negocio(negocio, user)
            self.save_step_session(request, 3, negocio=negocio, local=local)
            return self._redirect_paso(3)

        ctx = self._build_context(
            request, 2, user=user,
            form_negocio=form_negocio, form_local=form_local
        )
        return render(request, self.template_dict[2], ctx)

    # ===========================
    #  PASO 3 — Confirmación Plan
    # ===========================
    def _procesar_paso3(self, request):
        user = self.get_saved_user(request)
        negocio = self.get_saved_negocio(request)
        local = self.get_saved_local(request)
        if user is None or negocio is None or local is None:
            return self._redirect_paso(1)

        aceptar = request.POST.get('aceptar_plan') == '1'
        plan = get_plan_onboarding()
        plan_nombre = plan.get_nombre_mostrar() if plan else 'el plan seleccionado'
        if not aceptar:
            messages.error(
                request,
                f'Debes aceptar {plan_nombre} para continuar. Si necesitas ayuda contacta a soporte.'
            )
            ctx = self._build_context(request, 3, user, negocio, local)
            return render(request, self.template_dict[3], ctx)

        resultado = finalizar_onboarding(request, user, negocio, local)
        suscripcion = resultado.get('suscripcion')
        plan_actual = suscripcion.plan if suscripcion else plan
        dias = getattr(plan_actual, 'dias_prueba_gratis', 365) or 365
        plan_mostrar = plan_actual.get_nombre_mostrar() if plan_actual else 'tu plan'

        for k in [self.SESSION_KEY_USER, self.SESSION_KEY_NEGOCIO,
                  self.SESSION_KEY_LOCAL, self.SESSION_KEY_STEP]:
            request.session.pop(k, None)

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
        }
        if paso == 1:
            ctx['form'] = form if form is not None else RegistroUsuarioForm()
        if paso == 2:
            ctx['form_negocio'] = form_negocio if form_negocio is not None else NegocioOnboardingForm(prefix='neg')
            ctx['form_local'] = form_local if form_local is not None else LocalOnboardingForm(prefix='loc')
        if paso == 3:
            from apps.billing.models import Plan
            plan = get_plan_onboarding()
            ctx['plan_actual'] = plan
            if plan is None:
                ctx['error_sin_plan'] = (
                    '⚠️ Lo sentimos, no hay un Plan activo configurado por el momento. '
                    'Por favor contacta a soporte o intenta más tarde.'
                )
        return ctx


# Alias para URL pattern simple
onboarding = OnboardingWizardView.as_view()
