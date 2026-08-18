from django.shortcuts import render
from django.views import View


class ReputationHomeView(View):
    def get(self, request):
        return render(request, 'reputation/home.html')
