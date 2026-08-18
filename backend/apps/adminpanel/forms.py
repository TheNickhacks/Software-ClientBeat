from django import forms
from apps.billing.models import Plan


class PlanForm(forms.ModelForm):
    """Formulario de Planes del panel Admin ClienBeat (no técnico).
    Orientado a ADMIN_SOPORTE: sin IDs brutos, labels en español,
    ordenado por secciones lógicas igual que el fieldset de Django Admin.
    """
    class Meta:
        model = Plan
        fields = [
            'nombre',
            'nombre_mostrar',
            'descripcion',
            'caracteristicas',
            'precio_clp',
            'precio_uf',
            'moneda',
            'dias_prueba_gratis',
            'usuarios_permitidos',
            'locales_permitidos',
            'locales_gratis_incluidos',
            'costo_local_adicional_clp',
            'rubros_permitidos',
            'rubros_gratis_incluidos',
            'costo_rubro_adicional_clp',
            'rubros',
            'tiene_benchmarking_rubro',
            'tiene_encuestas_custom',
            'max_preguntas_encuesta_custom',
            'es_lanzamiento_gratis',
            'es_plan_default',
            'activo',
            'orden',
        ]
        labels = {
            'nombre': 'Nombre interno del Plan (slug-like)',
            'nombre_mostrar': 'Nombre público amigable (UI)',
            'descripcion': 'Descripción corta',
            'caracteristicas': 'Lista de características (una por línea)',
            'precio_clp': 'Precio base mensual (CLP)',
            'precio_uf': 'Precio base mensual (UF, opcional)',
            'moneda': 'Moneda predeterminada',
            'dias_prueba_gratis': 'Duración prueba gratis (días)',
            'usuarios_permitidos': 'Usuarios del equipo permitidos',
            'locales_permitidos': 'Locales físicos máximos (0 = ilimitado)',
            'locales_gratis_incluidos': 'Locales gratis incluidos en precio base',
            'costo_local_adicional_clp': 'Costo extra CLP por local sobre el límite',
            'rubros_permitidos': 'Rubros online máximos (0 = ilimitado)',
            'rubros_gratis_incluidos': 'Rubros online gratis incluidos',
            'costo_rubro_adicional_clp': 'Costo extra CLP por rubro online sobre el límite',
            'rubros': 'Rubros incluidos en el plan (opcional)',
            'tiene_benchmarking_rubro': 'Incluye benchmarking de rubro (competencia anónima)',
            'tiene_encuestas_custom': 'Permite encuestas con preguntas custom',
            'max_preguntas_encuesta_custom': 'Máx. preguntas custom por encuesta (0 = sin límite)',
            'es_lanzamiento_gratis': 'Plan de lanzamiento (365 días gratis, no visible en precios públicos)',
            'es_plan_default': 'Plan default para onboarding (solo 1 default activo)',
            'activo': 'Plan activo (visible y utilizable)',
            'orden': 'Orden de visualización (menor = primero)',
        }
        help_texts = {
            'caracteristicas': 'Escribe una línea por cada característica del plan. Se guardará como lista JSON y se mostrará como bullet points.',
            'nombre': 'Solo uso interno. Ej: MVP_BASICO, BASICO_2026, EMPRESARIAL, PROFESIONAL.',
            'nombre_mostrar': 'Nombre visible en UI: "Plan MVP Básico (Lanzamiento 365 días)", "Plan Profesional ClienBeat".',
            'locales_gratis_incluidos': 'Desde el local N° siguiente empieza a cobrar el costo extra (ej: 3 → 4° cobra extra).',
            'costo_local_adicional_clp': 'Según doc ClienBeat: Básico $30.000 / Empresarial $25.000 / Profesional $20.000.',
            'rubros_gratis_incluidos': 'Mismo cálculo escalonado que locales pero para rubros online/e-commerce.',
            'dias_prueba_gratis': 'MVP = 365 días gratis. Planes pagos = 30 días ciclo normal.',
            'es_plan_default': 'Marca SOLO 1 plan. Si marcas otro, el default anterior se desmarca automáticamente.',
        }
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'caracteristicas': forms.Textarea(attrs={'rows': 7, 'placeholder': '- Dashboard propio\n- Encuestas QR ilimitadas\n- ...'}),
            'rubros': forms.SelectMultiple(attrs={'class': 'w-full'}),
        }

    def clean_caracteristicas(self):
        """Convierte el textarea multilínea (una característica por línea) a JSONField list.
        Ignora líneas vacías y limpia espacios. Si es lista ya (por data anterior), la devuelve tal cual."""
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
        max_preg = cleaned_data.get('max_preguntas_encuesta_custom') or 0
        custom = cleaned_data.get('tiene_encuestas_custom')
        if custom and max_preg <= 0:
            self.add_error(
                'max_preguntas_encuesta_custom',
                'Si habilitas encuestas custom, debes indicar máx. preguntas (>0). Ej: Plan Profesional = 5.'
            )
        if not custom and max_preg > 0:
            cleaned_data['max_preguntas_encuesta_custom'] = 0
        return cleaned_data
