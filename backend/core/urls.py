from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin-panel/', include('apps.adminpanel.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('', include('apps.pages.urls')),
    path('negocios/', include('apps.businesses.urls')),
    path('billing/', include('apps.billing.urls')),
    path('encuestas/', include('apps.surveys.urls')),
    path('e/', include('apps.encuestas.urls')),
    path('reputacion/', include('apps.reputation.urls')),
    path('api/api-auth/', obtain_auth_token),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
