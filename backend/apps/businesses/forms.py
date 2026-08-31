import secrets
from django import forms
from django.core.exceptions import ValidationError
from datetime import date
from .models import Negocio, Local, MiembroEquipo
from apps.geo.models import Region, Provincia, Comuna, Rubro


class NegocioOnboardingForm(forms.ModelForm):
    region = forms.ModelChoiceField(
        queryset=Region.objects.filter(activo=True).order_by('orden', 'nombre'),
        label='Región *',
        required=True,
        empty_label='Selecciona una región',
        widget=forms.Select(attrs={
            'class': 'form-input',
            'id': 'id_neg-region',
            'hx-trigger': 'change',
            'hx-target': '#id_neg-provincia',
            'hx-swap': 'innerHTML',
            'hx-indicator': '#geoLoading',
        }),
    )
    provincia = forms.ModelChoiceField(
        queryset=Provincia.objects.none(),
        label='Provincia *',
        required=True,
        empty_label='Selecciona primero una región',
        widget=forms.Select(attrs={
            'class': 'form-input',
            'id': 'id_neg-provincia',
            'hx-trigger': 'change',
            'hx-target': '#id_neg-comuna',
            'hx-swap': 'innerHTML',
            'hx-indicator': '#geoLoading',
        }),
    )
    acepto_politica_datos_check = forms.BooleanField(
        label='Acepto la Política de Protección de Datos Personales (Ley N°19.628 / RGPD)',
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'w-4 h-4 accent-indigo-600'}),
        error_messages={'required': 'Debes aceptar la Política de Protección de Datos para continuar.'},
    )

    class Meta:
        model = Negocio
        fields = ['nombre', 'razon_social', 'rut', 'rango_empleados', 'rubro_google', 'direccion', 'telefono', 'email_contacto', 'comuna', 'rubro']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej: Café del Centro',
            }),
            'razon_social': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej: Café del Centro SpA.',
            }),
            'rut': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '76.123.456-7',
            }),
            'rango_empleados': forms.Select(attrs={
                'class': 'form-input',
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-input',
                'id': 'id_neg-direccion',
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
                'id': 'id_neg-comuna',
            }),
            'rubro': forms.Select(attrs={
                'class': 'form-input',
                'id': 'id_neg-rubro',
            }),
        }
        labels = {
            'nombre': 'Nombre comercial del negocio *',
            'razon_social': 'Razón Social (nombre legal empresa) *',
            'rut': 'RUT (Formato XX.XXX.XXX-X) *',
            'rango_empleados': 'Rango de empleados *',
            'direccion': 'Dirección de tu local principal *',
            'telefono': 'Teléfono del negocio',
            'email_contacto': 'Email de atención al cliente',
            'rubro_google': 'Rubro detallado (Google Places, opcional)',
            'comuna': 'Comuna *',
            'rubro': 'Rubro del negocio *',
        }
        help_texts = {
            'razon_social': 'Nombre legal registrado en el SII (SpA, Ltda, EIRL, etc.).',
            'rut': 'RUT del negocio (persona jurídica o natural con giro). Obligatorio por Ley.',
            'rango_empleados': 'Selecciona el tamaño actual de tu equipo.',
            'rubro_google': 'Campo automático, puedes dejarlo en blanco. Lo usaremos después al conectar Google Places API.',
            'comuna': 'Selecciona Región → Provincia → Comuna (se filtran automáticamente).',
            'rubro': 'Elige la categoría que mejor describa tu negocio. Si no la encuentras, selecciona "Otro".',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rubro_google'].required = False
        self.fields['rut'].required = True
        self.fields['razon_social'].required = True
        self.fields['rango_empleados'].required = True
        self.fields['rango_empleados'].choices = [('', 'Selecciona un rango')] + list(Negocio.RangoEmpleadosChoices.choices)
        self.fields['rango_empleados'].empty_label = 'Selecciona un rango'
        self.fields['telefono'].required = False
        self.fields['email_contacto'].required = False
        self.fields['comuna'].required = True
        self.fields['provincia'].queryset = Provincia.objects.all()
        self.fields['provincia'].empty_label = 'Selecciona una provincia'
        self.fields['comuna'].required = True
        self.fields['comuna'].queryset = Comuna.objects.all()
        self.fields['comuna'].empty_label = 'Selecciona una comuna'
        self.fields['rubro'].required = True
        self.fields['rubro'].queryset = Rubro.objects.filter(activo=True).order_by('tipo', 'orden', 'nombre')
        self.fields['rubro'].empty_label = 'Selecciona un rubro'

        region_id = self.data.get('neg-region') or self.data.get('region') or self.initial.get('region')
        provincia_id = self.data.get('neg-provincia') or self.data.get('provincia') or self.initial.get('provincia')

        if region_id:
            try:
                self.fields['provincia'].queryset = Provincia.objects.filter(region_id=region_id).order_by('orden', 'nombre')
            except (ValueError, TypeError):
                pass

        if provincia_id:
            try:
                self.fields['comuna'].queryset = Comuna.objects.filter(provincia_id=provincia_id).order_by('orden', 'nombre')
            except (ValueError, TypeError):
                pass

        if self.instance and self.instance.pk and self.instance.acepto_politica_datos:
            self.initial['acepto_politica_datos_check'] = True
        if self.instance and self.instance.pk and self.instance.comuna:
            prov = self.instance.comuna.provincia
            self.initial['provincia'] = prov.id
            self.initial['region'] = prov.region_id
            self.fields['provincia'].queryset = Provincia.objects.filter(region=prov.region).order_by('orden', 'nombre')
            self.fields['comuna'].queryset = Comuna.objects.filter(provincia=prov).order_by('orden', 'nombre')



    def clean_region(self):
        r = self.cleaned_data.get('region')
        if not r:
            raise ValidationError('Debes seleccionar una Región válida.')
        if not r.activo:
            raise ValidationError('Esta Región no está disponible actualmente.')
        return r

    def clean_provincia(self):
        p = self.cleaned_data.get('provincia')
        r = self.cleaned_data.get('region')
        if not p:
            raise ValidationError('Debes seleccionar una Provincia válida.')
        if r and p.region_id != r.id:
            raise ValidationError('La Provincia seleccionada no pertenece a la Región elegida.')
        return p

    def clean_comuna(self):
        c = self.cleaned_data.get('comuna')
        p = self.cleaned_data.get('provincia')
        r = self.cleaned_data.get('region')
        if not c:
            raise ValidationError('Debes seleccionar una Comuna válida.')
        cdb = Comuna.objects.select_related('provincia', 'provincia__region').filter(id=c.id).first()
        if not cdb:
            raise ValidationError('Comuna no encontrada en la base de datos.')
        if p:
            if cdb.provincia_id != p.id:
                raise ValidationError('La Comuna no pertenece a la Provincia seleccionada.')
        if r:
            if cdb.provincia.region_id != r.id:
                raise ValidationError('La Comuna no pertenece a la Región seleccionada.')
        if p and r:
            ok = Comuna.objects.filter(
                id=cdb.id,
                provincia__id=p.id,
                provincia__region__id=r.id,
            ).exists()
            if not ok:
                raise ValidationError('Combinación Región/Provincia/Comuna inválida. Por favor selecciona nuevamente desde la Región.')
        return c

    def clean(self):
        cleaned = super().clean()
        region = cleaned.get('region')
        provincia = cleaned.get('provincia')
        comuna = cleaned.get('comuna')
        if comuna and provincia:
            if comuna.provincia_id != provincia.id:
                self.add_error('comuna', 'La Comuna no pertenece a la Provincia seleccionada. Por favor selecciona desde la Región.')
            elif provincia.region_id and region and provincia.region_id != region.id:
                self.add_error('provincia', 'La Provincia no pertenece a la Región seleccionada.')
        if comuna and provincia and region:
            ok_chain = Comuna.objects.filter(
                id=comuna.id,
                provincia__id=provincia.id,
                provincia__region__id=region.id,
            ).exists()
            if not ok_chain:
                self.add_error('comuna', ValidationError(
                    'Combinación Región / Provincia / Comuna inválida. '
                    'Por favor re-selecciona desde la Región hasta la Comuna.',
                    code='geo_chain_invalid',
                ))
        return cleaned

    def clean_rut(self):
        rut = (self.cleaned_data.get('rut') or '').strip().replace('.', '').replace('-', '').upper()
        if not rut:
            return self.cleaned_data.get('rut')
        if len(rut) < 7 or len(rut) > 10:
            raise ValidationError('El RUT debe tener entre 7 y 10 dígitos (sin contar DV).')
        return self.cleaned_data.get('rut')

    def save_negocio(self, dueño, commit=True):
        negocio = super().save(commit=False)
        negocio.dueño = dueño
        if not negocio.rubro_google and negocio.rubro:
            negocio.rubro_google = negocio.rubro.nombre
        if self.cleaned_data.get('acepto_politica_datos_check') and not negocio.acepto_politica_datos:
            negocio.acepto_politica_datos = date.today()
        negocio.estado = Negocio.EstadoChoices.ACTIVO
        negocio.verificado = False
        if commit:
            negocio.save()
        return negocio


class LocalOnboardingForm(forms.ModelForm):
    region = forms.ModelChoiceField(
        queryset=Region.objects.filter(activo=True).order_by('orden', 'nombre'),
        label='Región Local',
        required=False,
        empty_label='Selecciona una región',
        widget=forms.Select(attrs={
            'class': 'form-input',
            'id': 'id_loc-region',
        }),
    )
    provincia = forms.ModelChoiceField(
        queryset=Provincia.objects.none(),
        label='Provincia Local',
        required=False,
        empty_label='Selecciona región primero',
        widget=forms.Select(attrs={
            'class': 'form-input',
            'id': 'id_loc-provincia',
        }),
    )
    usar_datos_negocio = forms.BooleanField(
        label='Usar la misma dirección y comuna de los datos del negocio (Sección 1)',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 accent-purple-600',
            'id': 'id_loc-usar_datos_negocio',
        }),
    )

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
                'id': 'id_loc-direccion',
                'placeholder': 'Misma dirección del negocio (puedes editarla luego)',
                'autocomplete': 'street-address',
            }),
            'comuna': forms.Select(attrs={
                'class': 'form-input',
                'id': 'id_loc-comuna',
            }),
        }
        labels = {
            'nombre': 'Nombre de tu local #1 *',
            'direccion': 'Dirección del local *',
            'comuna': 'Comuna del local *',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['provincia'].queryset = Provincia.objects.all()
        self.fields['comuna'].required = True
        self.fields['comuna'].queryset = Comuna.objects.all()
        self.fields['comuna'].empty_label = 'Selecciona una comuna'

        region_id = self.data.get('loc-region') or self.data.get('region') or self.initial.get('region')
        provincia_id = self.data.get('loc-provincia') or self.data.get('provincia') or self.initial.get('provincia')

        if region_id:
            try:
                self.fields['provincia'].queryset = Provincia.objects.filter(region_id=region_id).order_by('orden', 'nombre')
            except (ValueError, TypeError):
                pass
        if provincia_id:
            try:
                self.fields['comuna'].queryset = Comuna.objects.filter(provincia_id=provincia_id).order_by('orden', 'nombre')
            except (ValueError, TypeError):
                pass

        if self.instance and self.instance.pk and self.instance.comuna:
            prov = self.instance.comuna.provincia
            self.initial['provincia'] = prov.id
            self.initial['region'] = prov.region_id
            self.fields['provincia'].queryset = Provincia.objects.filter(region=prov.region).order_by('orden', 'nombre')
            self.fields['comuna'].queryset = Comuna.objects.filter(provincia=prov).order_by('orden', 'nombre')



    def clean(self):
        cleaned = super().clean()
        usar_mismos = cleaned.get('usar_datos_negocio')
        comuna = cleaned.get('comuna')
        region = cleaned.get('region')
        provincia = cleaned.get('provincia')

        if not usar_mismos:
            if region and provincia:
                if provincia.region_id != region.id:
                    self.add_error('provincia', 'Provincia no coincide con Región del local.')
            if comuna and provincia:
                if comuna.provincia_id != provincia.id:
                    self.add_error('comuna', 'Comuna no coincide con Provincia del local.')
            if not comuna:
                self.add_error('comuna', 'Debes seleccionar una Comuna para el local o marcar la casilla "Usar misma dirección del negocio".')
        return cleaned

    def save_local(self, negocio, commit=True):
        local = super().save(commit=False)
        local.negocio = negocio
        if not local.qr_token:
            local.qr_token = f'CB-{secrets.token_urlsafe(16).upper()[:12]}'
        local.estado = Local.EstadoChoices.ACTIVO

        if self.cleaned_data.get('usar_datos_negocio'):
            if negocio.comuna:
                local.comuna = negocio.comuna
            if negocio.direccion:
                local.direccion = negocio.direccion
        else:
            if not local.comuna and negocio.comuna:
                local.comuna = negocio.comuna

        if commit:
            local.save()
        return local
