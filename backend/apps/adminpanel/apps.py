from django.apps import AppConfig


class AdminPanelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.adminpanel'
    verbose_name = 'Panel Administrativo ClienBeat (No Técnico)'
    label = 'adminpanel'

    def ready(self):
        from django.contrib.admin.sites import site as default_admin_site
        from core.admin import ClientBeatSuperAdminSite
        default_admin_site.__class__ = ClientBeatSuperAdminSite
