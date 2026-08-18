from django.test import TestCase


class BillingModelsTest(TestCase):
    def test_plan_str(self):
        from .models import Plan
        plan = Plan(nombre='MVP_BASICO')
        self.assertEqual(str(plan), 'MVP_BASICO')
