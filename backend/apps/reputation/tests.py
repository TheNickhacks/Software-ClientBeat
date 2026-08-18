from django.test import TestCase


class ReputationModelsTest(TestCase):
    def test_resena_str(self):
        from .models import ResenaGoogle
        resena = ResenaGoogle(autor_nombre='Juan Perez', calificacion=5)
        self.assertEqual(str(resena), 'Juan Perez - 5★')
