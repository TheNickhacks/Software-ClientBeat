from django import forms
from .models import RespuestaEncuesta, EmocionCSATChoices, PlantillaEncuesta
from apps.businesses.models import Local


class PlantillaEncuestaCustomForm(forms.ModelForm):
    class Meta:
        model = PlantillaEncuesta
        fields = [
            'nombre_mostrar',
            'descripcion',
            'activar_nps',
            'titulo_nps',
            'activar_csat',
            'titulo_csat',
            'activar_comentario',
            'titulo_comentario',
            'comentario_requerido',
            'color_primario',
            'color_secundario',
            'color_fondo',
            'logo_custom',
        ]
        widgets = {
            'nombre_mostrar': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: ¡Tu opinión nos importa!'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-input', 'rows': 2, 'placeholder': 'Mensaje de bienvenida para tus clientes'}),
            'titulo_nps': forms.TextInput(attrs={'class': 'form-input'}),
            'titulo_csat': forms.TextInput(attrs={'class': 'form-input'}),
            'titulo_comentario': forms.TextInput(attrs={'class': 'form-input'}),
            'color_primario': forms.TextInput(attrs={'type': 'color', 'class': 'h-10 w-20 p-1 rounded border border-slate-300 cursor-pointer'}),
            'color_secundario': forms.TextInput(attrs={'type': 'color', 'class': 'h-10 w-20 p-1 rounded border border-slate-300 cursor-pointer'}),
            'color_fondo': forms.TextInput(attrs={'type': 'color', 'class': 'h-10 w-20 p-1 rounded border border-slate-300 cursor-pointer'}),
            'logo_custom': forms.FileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
        }
        labels = {
            'nombre_mostrar': 'Título de la Encuesta',
            'descripcion': 'Descripción / Subtítulo',
            'activar_nps': 'Activar pregunta de recomendación NPS (0 a 10)',
            'titulo_nps': 'Pregunta NPS',
            'activar_csat': 'Activar caritas de satisfacción CSAT',
            'titulo_csat': 'Pregunta CSAT',
            'activar_comentario': 'Activar campo de comentario libre',
            'titulo_comentario': 'Pregunta Comentario',
            'comentario_requerido': '¿El comentario es obligatorio?',
            'color_primario': 'Color Primario',
            'color_secundario': 'Color Secundario / Acento',
            'color_fondo': 'Color de Fondo',
            'logo_custom': 'Logo Personalizado',
        }


class RespuestaEncuestaPublicaForm(forms.ModelForm):
    nps_puntaje = forms.IntegerField(
        min_value=0,
        max_value=10,
        required=True,
        label='¿Qué tan probable es que nos recomiendes?',
        widget=forms.HiddenInput(attrs={'id': 'nps_puntaje_hidden'}),
    )
    csat_emocion = forms.ChoiceField(
        choices=[('', 'Selecciona una emoción')] + list(EmocionCSATChoices.choices),
        required=False,
        label='¿Qué tan satisfecho estás?',
        widget=forms.RadioSelect(attrs={'class': 'csat-radio sr-only'}),
    )

    class Meta:
        model = RespuestaEncuesta
        fields = ['nps_puntaje', 'csat_emocion', 'comentario', 'email_opcional', 'es_anonima']
        widgets = {
            'comentario': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-input',
                'placeholder': 'Cuéntanos más sobre tu experiencia... (opcional)',
            }),
            'email_opcional': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'tu@email.cl (solo si quieres que te contactemos)',
            }),
        }
        labels = {
            'comentario': '¿Quieres agregar un comentario?',
            'email_opcional': 'Tu email (opcional)',
            'es_anonima': 'Prefiero que esta respuesta sea anónima (no usar mi email)',
        }

    def __init__(self, *args, plantilla=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.plantilla = plantilla
        if not (plantilla and plantilla.activar_nps):
            self.fields['nps_puntaje'].required = False
        if not (plantilla and plantilla.activar_csat):
            self.fields['csat_emocion'].required = False
            self.fields['csat_emocion'].widget = forms.HiddenInput()
        if not (plantilla and plantilla.activar_comentario):
            self.fields['comentario'].widget = forms.HiddenInput()
            self.fields['comentario'].required = False
        if plantilla and plantilla.comentario_requerido:
            self.fields['comentario'].required = True

        # Custom extra questions dynamic generation
        if plantilla and plantilla.preguntas_extra:
            for idx, q in enumerate(plantilla.preguntas_extra):
                field_name = f'custom_q_{idx}'
                q_text = q.get('texto', f'Pregunta {idx+1}')
                q_type = q.get('tipo', 'TEXTO')
                q_req = q.get('requerido', False)

                if q_type == 'ESTRELLAS_1_5':
                    self.fields[field_name] = forms.IntegerField(
                        min_value=1, max_value=5, required=q_req, label=q_text,
                        widget=forms.HiddenInput(attrs={'id': f'{field_name}_hidden'})
                    )
                elif q_type == 'SI_NO':
                    self.fields[field_name] = forms.ChoiceField(
                        choices=[('SI', 'Sí'), ('NO', 'No')],
                        widget=forms.RadioSelect(attrs={'class': 'custom-radio'}),
                        required=q_req, label=q_text
                    )
                elif q_type == 'OPCIONES':
                    opts = [(o, o) for o in q.get('opciones', [])]
                    self.fields[field_name] = forms.ChoiceField(
                        choices=[('', 'Selecciona una opción...')] + opts,
                        widget=forms.Select(attrs={'class': 'form-input rounded-xl border-slate-200'}),
                        required=q_req, label=q_text
                    )
                else:  # TEXTO
                    self.fields[field_name] = forms.CharField(
                        widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-input rounded-xl border-slate-200', 'placeholder': 'Escribe tu respuesta...'}),
                        required=q_req, label=q_text
                    )

    def save_respuesta(self, local: Local, plantilla: PlantillaEncuesta, commit=True):
        resp = super().save(commit=False)
        resp.local = local
        resp.plantilla = plantilla
        resp.origen = resp.origen or 'QR_IMPRESO'
        if resp.es_anonima:
            resp.email_opcional = None

        # Extract custom responses into metadata
        respuestas_custom = {}
        if plantilla and plantilla.preguntas_extra:
            for idx, q in enumerate(plantilla.preguntas_extra):
                field_name = f'custom_q_{idx}'
                if field_name in self.cleaned_data:
                    respuestas_custom[q.get('texto', f'Pregunta_{idx}')] = self.cleaned_data[field_name]

        if not isinstance(resp.metadata, dict):
            resp.metadata = {}
        resp.metadata['respuestas_custom'] = respuestas_custom

        if commit:
            resp.save()
        return resp

