from django.conf import settings


def client_empresa(request):
    return {
        'EMPRESA': getattr(settings, 'EMPRESA', {}),
    }
