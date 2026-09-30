from django import template

register = template.Library()


@register.filter(name='clp_format')
def clp_format(value):
    """Formatea enteros/floats con punto (.) como separador de miles estándar chileno (ej: 50.000)."""
    if value is None or value == '':
        return ''
    try:
        val = int(value)
        return f"{val:,}".replace(',', '.')
    except (ValueError, TypeError):
        return value
