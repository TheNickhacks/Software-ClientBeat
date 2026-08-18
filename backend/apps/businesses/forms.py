import secrets
from django import forms
from .models import Negocio, Local, MiembroEquipo
from apps.geo.models import Region, Provincia, Comuna, Rubro


class NegocioOnboardingForm(forms.ModelForm):
    region = forms.ModelChoiceField(
        queryset=Region.objects.filter(activo=True).order_by('orden', 'nombre'),
        label='Región *',
        required=True,
        empty_label='Selecciona una región',
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'id_region'}),
    )
    provincia = forms.ModelChoiceField(
        queryset=Provincia.objects.select_related('region').all().order_by('region__orden', 'nombre'),
        label='Provincia *',
        required=True,
        empty_label='Selecciona una provincia',
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'id_provincia'}),
    )

    class Meta:
        model = Negocio
        fields = ['nombre', 'rut', 'rubro_google', 'direccion', 'telefono', 'email_contacto', 'comuna', 'rubro']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej: Café del Centro Ltda.',
            }),
            'rut': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '76.123.456-7 (opcional)',
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Calle, número, piso, depto. / oficina',
                'autocomplete': 'street-address',
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '+56 XX XXX XXXX',
                'autocomplete': 'tel',
            }),
            'email_contacto': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'contacto@tuempresa.cl',
            }),
            'comuna': forms.Select(attrs={
                'class': 'form-input',
                'id': 'id_comuna',
            }),
            'rubro': forms.Select(attrs={
                'class': 'form-input',
                'id': 'id_rubro',
            }),
        }
        labels = {
            'nombre': 'Nombre legal o comercial del negocio *',
            'rut': 'RUT (Formato XX.XXX.XXX-X, opcional)',
            'direccion': 'Dirección de tu local principal *',
            'telefono': 'Teléfono del negocio',
            'email_contacto': 'Email de atención al cliente',
            'rubro_google': 'Rubro detallado (Google Places, opcional)',
            'comuna': 'Comuna *',
            'rubro': 'Rubro del negocio *',
        }
        help_texts = {
            'rubro_google': 'Campo automático, puedes dejarlo en blanco. Lo usaremos después al conectar Google Places API.',
            'comuna': 'Selecciona primero la Región y luego la Provincia para filtrar la comuna.',
            'rubro': 'Elige la categoría que mejor describa tu negocio. Si no la encuentras, selecciona "Otro".',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rubro_google'].required = False
        self.fields['rut'].required = False
        self.fields['telefono'].required = False
        self.fields['email_contacto'].required = False
        self.fields['comuna'].required = True
        self.fields['comuna'].queryset = Comuna.objects.select_related('provincia', 'provincia__region').all().order_by('provincia__region__orden', 'provincia__nombre', 'nombre')
        self.fields['comuna'].empty_label = 'Selecciona una comuna'
        self.fields['rubro'].required = True
        self.fields['rubro'].queryset = Rubro.objects.filter(activo=True).order_by('tipo', 'orden', 'nombre')
        self.fields['rubro'].empty_label = 'Selecciona un rubro'
        if self.instance and self.instance.pk and self.instance.comuna:
            self.initial['provincia'] = self.instance.comuna.provincia_id
            self.initial['region'] = self.instance.comuna.provincia.region_id

    def clean(self):
        cleaned = super().clean()
        comuna = cleaned.get('comuna')
        region = cleaned.get('region')
        provincia = cleaned.get('provincia')
        if comuna and comuna.provincia_id != provincia:
            self.add_error('comuna', 'La comuna no coincide con la provincia seleccionada.')
        if provincia and provincia.region_id != region:
            self.add_error('provincia', 'La provincia no coincide con la región seleccionada.')
        return cleaned

    def save_negocio(self, dueño, commit=True):
        negocio = super().save(commit=False)
        negocio.dueño = dueño
        if not negocio.rubro_google and negocio.rubro:
            negocio.rubro_google = negocio.rubro.nombre
        negocio.estado = Negocio.EstadoChoices.ACTIVO
        negocio.verificado = False
        if commit:
            negocio.save()
        return negocio


class LocalOnboardingForm(forms.ModelForm):
    class Meta:
        model = Local
        fields = ['nombre', 'direccion', 'comuna']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej: Café del Centro - Local Matriz',
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Misma dirección del negocio (puedes editarla luego)',
                'autocomplete': 'street-address',
            }),
            'comuna': forms.Select(attrs={
                'class': 'form-input',
            }),
        }
        labels = {
            'nombre': 'Nombre de tu local #1 *',
            'direccion': 'Dirección del local *',
            'comuna': 'Comuna del local *',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['comuna'].required = True
        self.fields['comuna'].queryset = Comuna.objects.select_related('provincia', 'provincia__region').all().order_by('provincia__region__orden', 'provincia__nombre', 'nombre')
        self.fields['comuna'].empty_label = 'Selecciona una comuna'

    def save_local(self, negocio, commit=True):
        local = super().save(commit=False)
        local.negocio = negocio
        if not local.qr_token:
            local.qr_token = f'CB-{secrets.token_urlsafe(16).upper()[:12]}'
        local.estado = Local.EstadoChoices.ACTIVO
        if not local.comuna and negocio.comuna:
            local.comuna = negocio.comuna
        if commit:
            local.save()
        return local
