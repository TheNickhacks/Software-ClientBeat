from django import forms
from django.core.exceptions import ValidationError
from django.conf import settings
from apps.billing.models import Plan, MotivoCambioPlanChoices
from django.contrib.auth import get_user_model
User = get_user_model()


class PlanForm(forms.ModelForm):
    """Formulario de Planes del panel Admin ClienBeat (no técnico).
    Orientado a ADMIN_SOPORTE: sin IDs brutos, labels en español,
    ordenado por secciones lógicas igual que el fieldset de Django Admin.
    Incluye LOS 15 FEATURE FLAGS del modelo Plan (3 legacy + 12 nuevos Fase3).
    """
    class Meta:
        model = Plan
        fields = [
            # ======= DATOS BÁSICOS =======
            'nombre', 'nombre_mostrar', 'descripcion', 'caracteristicas',
            # ======= PRECIOS Y MONEDA =======
            'precio_clp', 'precio_uf', 'moneda', 'dias_prueba_gratis',
            # ======= LÍMITES DE USO =======
            'usuarios_permitidos',
            'locales_permitidos', 'locales_gratis_incluidos', 'costo_local_adicional_clp',
            'rubros_permitidos', 'rubros_gratis_incluidos', 'costo_rubro_adicional_clp',
            'rubros',
            # ======= FEATURE FLAGS LEGACY (Fase1) =======
            'tiene_benchmarking_rubro',
            'tiene_encuestas_custom', 'max_preguntas_encuesta_custom',
            # ======= FEATURE FLAGS NUEVOS (Fase3 - Planes Excel 3 niveles) =======
            'tiene_analisis_google',
            'tiene_benchmark_google',
            'tiene_notificaciones',
            'tiene_qr_clientbeat',
            'tiene_segmentacion_demografica',
            'tiene_encuestas_custom_rubro',
            'max_preguntas_adicionales',
            'tiene_benchmark_clientbeat',
            'tiene_export_excel',
            # ======= FLAGS DE COMPORTAMIENTO =======
            'es_lanzamiento_gratis', 'es_plan_default', 'activo', 'orden',
        ]
        labels = {
            # ======= DATOS BÁSICOS =======
            'nombre': 'Nombre interno del Plan (slug-like)',
            'nombre_mostrar': 'Nombre público amigable (UI)',
            'descripcion': 'Descripción corta',
            'caracteristicas': 'Lista de características (una por línea)',
            # ======= PRECIOS Y MONEDA =======
            'precio_clp': 'Precio base mensual (CLP)',
            'precio_uf': 'Precio base mensual (UF, opcional)',
            'moneda': 'Moneda predeterminada',
            'dias_prueba_gratis': 'Duración prueba gratis (días)',
            # ======= LÍMITES DE USO =======
            'usuarios_permitidos': 'Usuarios del equipo permitidos',
            'locales_permitidos': 'Locales físicos máximos (0 = ilimitado)',
            'locales_gratis_incluidos': 'Locales gratis incluidos en precio base',
            'costo_local_adicional_clp': 'Costo extra CLP por local sobre el límite',
            'rubros_permitidos': 'Rubros online máximos (0 = ilimitado)',
            'rubros_gratis_incluidos': 'Rubros online gratis incluidos',
            'costo_rubro_adicional_clp': 'Costo extra CLP por rubro online sobre el límite',
            'rubros': 'Rubros incluidos en el plan (opcional)',
            # ======= FEATURE FLAGS LEGACY (Fase1) =======
            'tiene_benchmarking_rubro': '🔄 Benchmarking Rubro (competencia anónima cross-sector)',
            'tiene_encuestas_custom': '📝 Encuestas Custom (preguntas libres del dueño)',
            'max_preguntas_encuesta_custom': 'Máx. preguntas custom por encuesta (0 = sin límite)',
            # ======= FEATURE FLAGS NUEVOS Fase3 =======
            'tiene_analisis_google': '🔍 Análisis Google (rating + reseñas + evolución histórica)',
            'tiene_benchmark_google': '📊 Benchmark Google (competencia rating + nº opiniones)',
            'tiene_notificaciones': '🔔 Notificaciones Eventos (planes/pagos/reseñas/CSAT-NPS)',
            'tiene_qr_clientbeat': '📱 QR ClientBeat (encuestas NPS/CSAT por local físico)',
            'tiene_segmentacion_demografica': '👥 Segmentación Demográfica (edad/género desde QR)',
            'tiene_encuestas_custom_rubro': '🎯 Encuestas x Rubro (preguntas según 4D + dimensión 5ta)',
            'max_preguntas_adicionales': '➕ Preguntas Adicionales permitidas (fuera del set rubro)',
            'tiene_benchmark_clientbeat': '🏆 Benchmark ClientBeat (NPS/CSAT vs red CB comuna/región)',
            'tiene_export_excel': '📤 Exportar Excel/CSV (métricas y listados)',
            # ======= FLAGS DE COMPORTAMIENTO =======
            'es_lanzamiento_gratis': '🎁 Plan Lanzamiento (365 días gratis, no visible públicamente)',
            'es_plan_default': '⭐ Plan Default Onboarding (SOLO 1 activo a la vez)',
            'activo': '✅ Plan Activo (visible y utilizable por negocios)',
            'orden': '🔢 Orden visualización (menor = primero)',
        }
        help_texts = {
            # ======= DATOS BÁSICOS =======
            'caracteristicas': 'Escribe una línea por cada característica. Se guarda como JSON y se muestra como bullet points en UI cliente.',
            'nombre': 'Solo uso interno Admin. Ej: MVP_BASICO, GOOGLE_SOLO_2026, PROFESIONAL_FULL.',
            'nombre_mostrar': 'Nombre visible al cliente. Ej: "Plan Solo Google Reseñas", "Plan Profesional ClientBeat Full".',
            # ======= LÍMITES =======
            'locales_gratis_incluidos': 'Desde el local N° siguiente cobra extra (ej: 3 → 4° local cobra costo_local_adicional_clp).',
            'costo_local_adicional_clp': 'Doc ClienBeat: Básico $30.000 / Empresarial $25.000 / Profesional $20.000 CLP.',
            'rubros_gratis_incluidos': 'Mismo cálculo escalonado que locales pero para rubros online/e-commerce cross-sector.',
            'dias_prueba_gratis': 'MVP = 365 días gratis lanzamiento. Planes pagos regulares = 30 días ciclo.',
            'es_plan_default': 'Marca SOLO 1 plan. Al marcar otro, el default anterior se desmarca automáticamente en la vista POST.',
            # ======= FEATURE FLAGS NUEVOS — GUÍA RÁPIDA POR PLAN =======
            'tiene_analisis_google': 'PLAN 1 (Solo Google) = ✅. Todos los niveles = ✅.',
            'tiene_benchmark_google': 'PLAN 1 = ✅. Todos los niveles = ✅.',
            'tiene_notificaciones': 'TODOS los planes = ✅. Eventos: vencimientos, reseñas nuevas, hitos CSAT-NPS.',
            'tiene_qr_clientbeat': 'PLAN 1 = ❌. PLAN 2 (QR+Rubro) y PLAN 3 Full = ✅.',
            'tiene_segmentacion_demografica': 'PLAN 1 = ❌. PLAN 2 y PLAN 3 = ✅ (edad, género, etc.).',
            'tiene_encuestas_custom_rubro': 'PLAN 1 = ❌. PLAN 2 y PLAN 3 = ✅ (4D + dimensión 5ta específica rubro).',
            'max_preguntas_adicionales': 'PLAN 1 = 0, PLAN 2 = 0, PLAN 3 Full = 3 preguntas extra libres por encuesta.',
            'tiene_benchmark_clientbeat': 'PLAN 1 y 2 = ❌. Solo PLAN 3 Full = ✅ (comparativa NPS/CSAT red CB).',
            'tiene_export_excel': 'TODOS los planes = ✅. Exportar métricas y listados a Excel/CSV.',
        }
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'caracteristicas': forms.Textarea(attrs={
                'rows': 8,
                'placeholder': '- Dashboard métricas en vivo\n- Análisis Google reseñas\n- Encuestas QR por local\n- ...',
            }),
            'rubros': forms.SelectMultiple(attrs={'class': 'w-full'}),
            'max_preguntas_encuesta_custom': forms.NumberInput(attrs={'min': 0, 'max': 50, 'step': 1}),
            'max_preguntas_adicionales': forms.NumberInput(attrs={'min': 0, 'max': 20, 'step': 1}),
            'orden': forms.NumberInput(attrs={'min': 0, 'step': 1}),
            'precio_clp': forms.NumberInput(attrs={'min': 0, 'step': 500}),
            'locales_permitidos': forms.NumberInput(attrs={'min': 0, 'step': 1}),
            'locales_gratis_incluidos': forms.NumberInput(attrs={'min': 0, 'step': 1}),
            'costo_local_adicional_clp': forms.NumberInput(attrs={'min': 0, 'step': 500}),
            'rubros_permitidos': forms.NumberInput(attrs={'min': 0, 'step': 1}),
            'rubros_gratis_incluidos': forms.NumberInput(attrs={'min': 0, 'step': 1}),
            'costo_rubro_adicional_clp': forms.NumberInput(attrs={'min': 0, 'step': 500}),
            'usuarios_permitidos': forms.NumberInput(attrs={'min': 1, 'step': 1}),
            'dias_prueba_gratis': forms.NumberInput(attrs={'min': 0, 'step': 1}),
        }

    def clean_caracteristicas(self):
        """Convierte textarea multilínea → JSONField list. Ignora líneas vacías."""
        data = self.cleaned_data.get('caracteristicas')
        if data is None or data == '':
            return []
        if isinstance(data, list):
            return [str(x).strip() for x in data if str(x).strip()]
        if isinstance(data, str):
            lineas = [linea.strip(' \t-*•') for linea in data.splitlines()]
            return [x for x in lineas if x]
        return []

    def clean(self):
        cleaned_data = super().clean()
        # ========== VALIDACIÓN 1: Encuestas Custom LEGACY ↔ max_preguntas ==========
        max_preg_legacy = cleaned_data.get('max_preguntas_encuesta_custom') or 0
        custom_legacy = cleaned_data.get('tiene_encuestas_custom')
        if custom_legacy and max_preg_legacy <= 0:
            self.add_error(
                'max_preguntas_encuesta_custom',
                'Si habilitas "📝 Encuestas Custom" (legacy), debes indicar máx. preguntas > 0. Ej: Plan Profesional = 5.'
            )
        if not custom_legacy and max_preg_legacy > 0:
            cleaned_data['max_preguntas_encuesta_custom'] = 0

        # ========== VALIDACIÓN 2: Encuestas x Rubro NUEVO ↔ max_preguntas_adicionales ==========
        max_preg_adicional = cleaned_data.get('max_preguntas_adicionales') or 0
        custom_rubro = cleaned_data.get('tiene_encuestas_custom_rubro')
        if custom_rubro is False and max_preg_adicional > 0:
            cleaned_data['max_preguntas_adicionales'] = 0
        if custom_rubro and max_preg_adicional < 0:
            self.add_error(
                'max_preguntas_adicionales',
                'Preguntas adicionales no puede ser negativo. Si no quieres extras, marca 0.'
            )

        # ========== VALIDACIÓN 3: Plan Default ÚNICO (no hay 2 defaults activos) ==========
        es_default = cleaned_data.get('es_plan_default')
        activo = cleaned_data.get('activo')
        if es_default and not activo:
            self.add_error(
                'es_plan_default',
                'No puede haber Plan Default inactivo. Activa el plan primero, o desmarca default.'
            )

        # ========== VALIDACIÓN 4: Precio mínimo definido (al menos CLP o UF) ==========
        precio_clp = cleaned_data.get('precio_clp')
        precio_uf = cleaned_data.get('precio_uf')
        if (precio_clp is None or precio_clp <= 0) and (precio_uf is None or precio_uf <= 0):
            if not cleaned_data.get('es_lanzamiento_gratis'):
                self.add_error(
                    'precio_clp',
                    'Plan pago debe tener Precio CLP o Precio UF definido > 0. '
                    'Solo planes de lanzamiento (365 gratis) pueden omitir precio base.'
                )

        # ========== VALIDACIÓN 5: QR CB requiere al menos Google Análisis (sinergia) ==========
        qr_cb = cleaned_data.get('tiene_qr_clientbeat')
        analisis_google = cleaned_data.get('tiene_analisis_google')
        if qr_cb and not analisis_google:
            self.add_error(
                'tiene_qr_clientbeat',
                'No puedes activar QR ClientBeat sin Análisis Google. '
                'La sinergia Google Reviews + QR en local es core del producto.'
            )

        return cleaned_data


# ======================================================================
# FORMS AUXILIARES ADMIN SOPORTE (sin pasar por vistas genéricas Django)
# ======================================================================

class SuscripcionCambiarPlanForm(forms.Form):
    """Formulario inline para cambiar plan de una suscripción existente.
    Crea registro CambioPlan automáticamente con snapshot precios INMUTABLES."""
    plan_nuevo_id = forms.UUIDField(
        label='Nuevo Plan a asignar',
        widget=forms.Select(attrs={'class': 'input w-full !py-2 text-sm'})
    )
    motivo = forms.ChoiceField(
        label='Motivo del cambio',
        choices=MotivoCambioPlanChoices.choices,
        initial=MotivoCambioPlanChoices.CORRECION_ADMIN,
        widget=forms.Select(attrs={'class': 'input w-full !py-2 text-sm'})
    )
    nota_admin = forms.CharField(
        label='Nota interna (opcional)',
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'class': 'input w-full text-sm',
            'placeholder': 'Ej: Corrección por error humano asignación plan inicial. Se cobrará diferencia prorrata próximo ciclo.',
        })
    )
    extender_dias_gratis = forms.IntegerField(
        label='Días de regalo adicionales (opcional, 0 = ninguno)',
        required=False,
        initial=0,
        min_value=0,
        max_value=365,
        widget=forms.NumberInput(attrs={'class': 'input w-full !py-2 text-sm', 'min': 0, 'max': 365, 'step': 1})
    )

    def __init__(self, *args, **kwargs):
        planes_queryset = kwargs.pop('planes_queryset', None)
        super().__init__(*args, **kwargs)
        if planes_queryset is not None:
            self.fields['plan_nuevo_id'].widget.choices = [
                (str(p.id), f'{p.get_nombre_mostrar()} · ${p.precio_clp or 0:,} CLP'.replace(',', '.'))
                for p in planes_queryset
            ]

    def clean_extender_dias_gratis(self):
        valor = self.cleaned_data.get('extender_dias_gratis') or 0
        if valor < 0:
            raise ValidationError('Días de regalo no puede ser negativo.')
        return valor


class NegocioReasignarDuenoForm(forms.Form):
    """Formulario para reasignar el Dueño de un negocio (rol DUEÑO).
    Solo Admin Soporte o SuperUser. Valida email exista y no tenga otro negocio asignado ya."""
    email_nuevo_dueno = forms.EmailField(
        label='Email del nuevo Dueño (Usuario debe existir en ClienBeat)',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'input w-full !py-2 text-sm',
            'placeholder': 'nuevo.dueno@empresa.cl',
            'autocomplete': 'email',
        })
    )
    mantener_dueno_anterior_colaborador = forms.BooleanField(
        label='Mantener Dueño anterior como Gestor del equipo (recomendado)',
        required=False,
        initial=True,
        help_text='Si marcas NO, el dueño anterior queda sin relación con este negocio (solo acceso como usuario plataforma sin negocio).',
    )
    motivo = forms.CharField(
        label='Motivo reasignación (obligatorio para auditoría)',
        required=True,
        max_length=300,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'class': 'input w-full text-sm',
            'placeholder': 'Ej: Traspaso sociedad, fundador se retira, cambio de titularidad documentado legalmente.',
        })
    )

    def clean_email_nuevo_dueno(self):
        email = self.cleaned_data.get('email_nuevo_dueno', '').strip().lower()
        try:
            usuario = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError(
                f'No existe usuario registrado con email "{email}". '
                'El nuevo Dueño debe crear cuenta primero en el onboarding público (o créalo manualmente en módulo Usuarios).'
            )
        if not usuario.is_active:
            raise ValidationError(
                f'El usuario "{email}" está INACTIVO. Actívalo primero en módulo Usuarios antes de asignarle negocio.'
            )
        self.cleaned_data['usuario_nuevo_dueno'] = usuario
        return email

