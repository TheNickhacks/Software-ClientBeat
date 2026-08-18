from django import forms
from .models import RespuestaEncuesta, EmocionCSATChoices, PlantillaEncuesta
from apps.businesses.models import Local


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

    def save_respuesta(self, local: Local, plantilla: PlantillaEncuesta, commit=True):
        resp = super().save(commit=False)
        resp.local = local
        resp.plantilla = plantilla
        resp.origen = resp.origen or 'QR_IMPRESO'
        if not resp.origen:
            resp.origen = 'QR_IMPRESO'
        if resp.es_anonima:
            resp.email_opcional = None
        if commit:
            resp.save()
        return resp
