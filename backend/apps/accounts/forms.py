import secrets
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class RegistroUsuarioForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Mínimo 8 caracteres',
            'autocomplete': 'new-password',
        }),
        help_text='Debe contener al menos 8 caracteres y no ser solo numérica.',
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Repite la misma contraseña',
            'autocomplete': 'new-password',
        }),
    )
    es_mayor_18 = forms.BooleanField(
        label='Declaro que soy mayor de 18 años',
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'w-4 h-4 accent-indigo-600'}),
        error_messages={'required': 'Debes declarar que eres mayor de 18 años para registrarte.'},
    )
    acepto_terminos = forms.BooleanField(
        label='Acepto los Términos y Condiciones y la Política de Privacidad de Client Beat',
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'w-4 h-4 accent-indigo-600'}),
        error_messages={'required': 'Debes aceptar los Términos y Condiciones para continuar.'},
    )

    field_order = ['first_name', 'last_name', 'email', 'telefono', 'password1', 'password2', 'es_mayor_18', 'acepto_terminos']

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'telefono']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej: María',
                'autocomplete': 'given-name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej: González Pérez',
                'autocomplete': 'family-name',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'tu@tuempresa.cl',
                'autocomplete': 'email',
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '+56 9 1234 5678',
                'autocomplete': 'tel',
            }),
        }
        labels = {
            'first_name': 'Nombre',
            'last_name': 'Apellido(s)',
            'email': 'Correo electrónico',
            'telefono': 'Teléfono de contacto',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                _('Este correo electrónico ya está registrado. Inicia sesión o usa otro email.'),
                code='email_duplicado',
            )
        return email

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise ValidationError(_('Las contraseñas no coinciden.'), code='password_mismatch')
        if p2 and len(p2) < 8:
            raise ValidationError(_('La contraseña debe tener al menos 8 caracteres.'), code='password_corta')
        return p2

    def save(self, commit=True):
        from datetime import date
        user = super().save(commit=False)
        user.username = self.cleaned_data['email'].split('@')[0] + '_' + secrets.token_hex(3)
        user.set_password(self.cleaned_data['password1'])
        user.rol = User.RolChoices.DUENO
        user.es_mayor_18 = True
        user.acepto_terminos = date.today()
        user.is_active = True
        user.is_staff = True
        if commit:
            user.save()
        return user
