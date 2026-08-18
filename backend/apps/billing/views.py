from django.shortcuts import render
from django.views import View


class BillingHomeView(View):
    def get(self, request):
        return render(request, 'billing/home.html')
