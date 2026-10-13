from django.test import TestCase
from django.urls import reverse
from apps.accounts.models import User
from apps.adminpanel.models import ConfiguracionMetricas


class MetricasConfiguracionSeparadaTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin_test',
            email='admin@clientbeat.test',
            password='testpassword123',
            rol=User.RolChoices.ADMIN_SOPORTE,
            is_active=True
        )
        self.client.force_login(self.admin)
        self.config = ConfiguracionMetricas.get_solo()

    def test_get_views_render_successfully(self):
        """Verifica que las 4 vistas independientes respondan 200 con sus templates."""
        url_bm_google = reverse('adminpanel:metricas_criterios_benchmark_google')
        resp = self.client.get(url_bm_google)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'admin_panel/metricas/criterios_benchmark_google.html')

        url_bm_cb = reverse('adminpanel:metricas_criterios_benchmark_clientbeat')
        resp = self.client.get(url_bm_cb)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'admin_panel/metricas/criterios_benchmark_clientbeat.html')

        url_csat = reverse('adminpanel:metricas_csat')
        resp = self.client.get(url_csat)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'admin_panel/metricas/csat.html')

        url_nps = reverse('adminpanel:metricas_nps')
        resp = self.client.get(url_nps)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'admin_panel/metricas/nps.html')

    def test_post_criterios_benchmark_google_independent(self):
        """Guardar criterios de Benchmark Google debe ser independiente de ClientBeat."""
        # Estado inicial ClientBeat
        self.config.bm_clientbeat_min_empresas = 7
        self.config.bm_clientbeat_min_respuestas = 25
        self.config.save()

        url = reverse('adminpanel:metricas_criterios_benchmark_google')
        data = {
            'bm_google_min_empresas': '8',
            'bm_google_min_valoraciones': '30',
            'bm_google_dias_sin_valoraciones_excluir': '120',
            'bm_google_filtro_temporal_default': 'SEMANAL',
            'bm_google_filtro_geografico_default': 'NACIONAL',
            'bm_google_criterio_desempate': 'POSITIVAS_PERIODO',
            'bm_google_nota_explicativa_usuario': 'Nota personalizada Google',
        }
        resp = self.client.post(url, data)
        self.assertRedirects(resp, url)

        self.config.refresh_from_db()
        self.assertEqual(self.config.bm_google_min_empresas, 8)
        self.assertEqual(self.config.bm_google_min_valoraciones, 30)
        self.assertEqual(self.config.bm_google_dias_sin_valoraciones_excluir, 120)
        self.assertEqual(self.config.bm_google_filtro_temporal_default, 'SEMANAL')
        self.assertEqual(self.config.bm_google_filtro_geografico_default, 'NACIONAL')
        self.assertEqual(self.config.bm_google_criterio_desempate, 'POSITIVAS_PERIODO')
        self.assertEqual(self.config.bm_google_nota_explicativa_usuario, 'Nota personalizada Google')

        # ClientBeat NO fue modificado
        self.assertEqual(self.config.bm_clientbeat_min_empresas, 7)
        self.assertEqual(self.config.bm_clientbeat_min_respuestas, 25)

    def test_post_criterios_benchmark_clientbeat_independent(self):
        """Guardar criterios de Benchmark ClientBeat debe ser independiente de Google."""
        self.config.bm_google_min_empresas = 4
        self.config.save()

        url = reverse('adminpanel:metricas_criterios_benchmark_clientbeat')
        data = {
            'bm_clientbeat_min_empresas': '12',
            'bm_clientbeat_min_respuestas': '40',
            'bm_clientbeat_dias_sin_respuestas_excluir': '45',
            'bm_clientbeat_filtro_temporal_default': 'ANUAL',
            'bm_clientbeat_filtro_geografico_default': 'REGIONAL',
            'bm_clientbeat_criterio_desempate': 'DECIMAS',
            'bm_clientbeat_nota_explicativa_usuario': 'Nota personalizada ClientBeat',
        }
        resp = self.client.post(url, data)
        self.assertRedirects(resp, url)

        self.config.refresh_from_db()
        self.assertEqual(self.config.bm_clientbeat_min_empresas, 12)
        self.assertEqual(self.config.bm_clientbeat_min_respuestas, 40)
        self.assertEqual(self.config.bm_clientbeat_dias_sin_respuestas_excluir, 45)
        self.assertEqual(self.config.bm_clientbeat_filtro_temporal_default, 'ANUAL')
        self.assertEqual(self.config.bm_clientbeat_filtro_geografico_default, 'REGIONAL')
        self.assertEqual(self.config.bm_clientbeat_nota_explicativa_usuario, 'Nota personalizada ClientBeat')

        # Google no cambió
        self.assertEqual(self.config.bm_google_min_empresas, 4)

    def test_post_csat_independent_from_nps(self):
        """Guardar criterios de CSAT debe ser independiente de NPS."""
        self.config.nps_min_empresas_benchmark = 5
        self.config.nps_min_respuestas = 20
        self.config.save()

        url = reverse('adminpanel:metricas_csat')
        data = {
            'csat_criterio_metodologico': 'Fórmula CSAT específica',
            'csat_min_empresas_benchmark': '6',
            'csat_min_respuestas': '15',
            'csat_dias_sin_respuestas_excluir': '90',
            'csat_filtro_temporal_default': 'SEMESTRAL',
            'csat_filtro_geografico_default': 'COMUNAL',
            'csat_criterio_desempate': 'POSITIVAS_PERIODO',
            'csat_nota_explicativa_usuario': 'Nota explicativa CSAT',
        }
        resp = self.client.post(url, data)
        self.assertRedirects(resp, url)

        self.config.refresh_from_db()
        self.assertEqual(self.config.csat_criterio_metodologico, 'Fórmula CSAT específica')
        self.assertEqual(self.config.csat_min_empresas_benchmark, 6)
        self.assertEqual(self.config.csat_min_respuestas, 15)
        self.assertEqual(self.config.csat_dias_sin_respuestas_excluir, 90)
        self.assertEqual(self.config.csat_filtro_temporal_default, 'SEMESTRAL')
        self.assertEqual(self.config.csat_filtro_geografico_default, 'COMUNAL')
        self.assertEqual(self.config.csat_criterio_desempate, 'POSITIVAS_PERIODO')
        self.assertEqual(self.config.csat_nota_explicativa_usuario, 'Nota explicativa CSAT')

        # NPS permanece inalterado
        self.assertEqual(self.config.nps_min_empresas_benchmark, 5)
        self.assertEqual(self.config.nps_min_respuestas, 20)

    def test_post_nps_independent_from_csat(self):
        """Guardar criterios de NPS debe ser independiente de CSAT."""
        self.config.csat_min_empresas_benchmark = 8
        self.config.save()

        url = reverse('adminpanel:metricas_nps')
        data = {
            'nps_criterio_metodologico': 'Fórmula NPS específica',
            'nps_min_empresas_benchmark': '10',
            'nps_min_respuestas': '25',
            'nps_dias_sin_respuestas_excluir': '30',
            'nps_filtro_temporal_default': 'MENSUAL',
            'nps_filtro_geografico_default': '5KM',
            'nps_criterio_desempate': 'DECIMAS',
            'nps_nota_explicativa_usuario': 'Nota explicativa NPS',
        }
        resp = self.client.post(url, data)
        self.assertRedirects(resp, url)

        self.config.refresh_from_db()
        self.assertEqual(self.config.nps_criterio_metodologico, 'Fórmula NPS específica')
        self.assertEqual(self.config.nps_min_empresas_benchmark, 10)
        self.assertEqual(self.config.nps_min_respuestas, 25)
        self.assertEqual(self.config.nps_dias_sin_respuestas_excluir, 30)
        self.assertEqual(self.config.nps_filtro_temporal_default, 'MENSUAL')
        self.assertEqual(self.config.nps_filtro_geografico_default, '5KM')
        self.assertEqual(self.config.nps_criterio_desempate, 'DECIMAS')
        self.assertEqual(self.config.nps_nota_explicativa_usuario, 'Nota explicativa NPS')

        # CSAT permanece inalterado
        self.assertEqual(self.config.csat_min_empresas_benchmark, 8)
