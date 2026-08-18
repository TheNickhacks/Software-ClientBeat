import sys
import io
import secrets
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from apps.businesses.models import Negocio, Local, MiembroEquipo
from apps.billing.models import Plan, Suscripcion
from apps.geo.models import Comuna, Rubro

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea datos demo iniciales: 3 usuarios (ADMIN_SOPORTE, DUEÑO, USUARIO_EQUIPO), Negocio, Local, Plan MVP y Suscripción activa.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Elimina usuarios demo existentes antes de crear nuevos.',
        )
        parser.add_argument(
            '--pw',
            type=str,
            default=None,
            help='Contraseña fija para todos los usuarios demo (default: ClienBeat2026!).',
        )

    def handle(self, *args, **options):
        from apps.businesses.models import Negocio, Local, MiembroEquipo
        from apps.billing.models import (
            Plan,
            Suscripcion,
            EstadoSuscripcionChoices,
            MonedaChoices,
        )

        pw = options.get('pw') or 'ClienBeat2026!'
        reset = options.get('reset')

        demo_emails = [
            'admin@clientbeat.cl',
            'super@clientbeat.cl',
            'dueno@negociodemo.cl',
            'usuario.equipo@negociodemo.cl',
        ]

        if reset:
            self.stdout.write('🧹 Eliminando datos demo existentes...')
            Suscripcion.objects.filter(negocio__email_contacto='demo@clientbeat.cl').delete()
            Negocio.objects.filter(email_contacto='demo@clientbeat.cl').delete()
            User.objects.filter(email__in=demo_emails).delete()
            Plan.objects.filter(nombre__in=[
                'MVP_BASICO',
                'BASICO',
                'EMPRESARIAL',
                'PROFESIONAL',
            ]).delete()

        # ======== 0. SUPERUSER Django (SOLO TÉCNICO, entra a /admin/ raw) ========
        self.stdout.write('\n🔐 Creando usuario SUPERUSER Django (solo técnico)...')
        super_user, created = User.objects.get_or_create(
            email='super@clientbeat.cl',
            defaults={
                'username': 'super_clientbeat',
                'first_name': 'Super',
                'last_name': 'Administrador Técnico',
                'rol': User.RolChoices.ADMIN_SOPORTE,
                'telefono': '+56 9 0000 0000',
                'es_mayor_18': True,
                'acepto_terminos': datetime.now().date(),
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        if created:
            super_user.set_password(pw)
            super_user.save()
        elif not super_user.is_superuser:
            super_user.is_superuser = True
            super_user.is_staff = True
            super_user.save(update_fields=['is_superuser', 'is_staff'])
        self.stdout.write(self.style.SUCCESS(f'  ✅ {super_user.email} (SUPERUSER Django) | pw: {pw} | entra a /admin/ raw'))

        # ======== 1. ADMIN SOPORTE CLIENT BEAT (NO TÉCNICO, entra a /admin-panel/) ========
        self.stdout.write('\n🛠 Creando usuario ADMIN_SOPORTE (Panel Admin no-técnico)...')
        admin_user, created = User.objects.get_or_create(
            email='admin@clientbeat.cl',
            defaults={
                'username': 'admin_clientbeat',
                'first_name': 'Admin',
                'last_name': 'ClienBeat Soporte',
                'rol': User.RolChoices.ADMIN_SOPORTE,
                'telefono': '+56 9 0000 0001',
                'es_mayor_18': True,
                'acepto_terminos': datetime.now().date(),
                'is_staff': True,
                'is_superuser': False,
                'is_active': True,
            }
        )
        if created:
            admin_user.set_password(pw)
            admin_user.save()
        else:
            actualizar = False
            if admin_user.is_superuser:
                admin_user.is_superuser = False
                actualizar = True
            if not admin_user.is_staff:
                admin_user.is_staff = True
                actualizar = True
            if actualizar:
                admin_user.save(update_fields=['is_superuser', 'is_staff'])
        self.stdout.write(self.style.SUCCESS(f'  ✅ {admin_user.email} (ADMIN_SOPORTE, NO superuser) | pw: {pw} | entra a /admin-panel/'))

        # ======== 2. DUEÑO DE NEGOCIO ========
        self.stdout.write('\n👤 Creando usuario DUEÑO...')
        dueno_user, created = User.objects.get_or_create(
            email='dueno@negociodemo.cl',
            defaults={
                'username': 'dueno_negocio_demo',
                'first_name': 'María',
                'last_name': 'González',
                'rol': User.RolChoices.DUENO,
                'telefono': '+56 9 8765 4321',
                'es_mayor_18': True,
                'acepto_terminos': datetime.now().date(),
                'is_staff': True,
                'is_superuser': False,
                'is_active': True,
            }
        )
        if created:
            dueno_user.set_password(pw)
            dueno_user.save()
        self.stdout.write(self.style.SUCCESS(f'  ✅ {dueno_user.email} | pw: {pw}'))

        # ======== 3. USUARIO EQUIPO ========
        self.stdout.write('\n👥 Creando usuario USUARIO_EQUIPO...')
        equipo_user, created = User.objects.get_or_create(
            email='usuario.equipo@negociodemo.cl',
            defaults={
                'username': 'usuario_equipo_demo',
                'first_name': 'Javier',
                'last_name': 'Muñoz',
                'rol': User.RolChoices.USUARIO_EQUIPO,
                'telefono': '+56 9 1234 5678',
                'es_mayor_18': True,
                'acepto_terminos': datetime.now().date(),
                'is_staff': False,
                'is_superuser': False,
                'is_active': True,
            }
        )
        if created:
            equipo_user.set_password(pw)
            equipo_user.save()
        self.stdout.write(self.style.SUCCESS(f'  ✅ {equipo_user.email} | pw: {pw}'))

        # ======== 3.5 PLANES REALES CLIENT BEAT (Doc: Prompt Tipos de planes) ========
        self.stdout.write('\n💼 Creando Planes Reales (Básico $25k / Empresarial $60k / Profesional $75k) + cobros extras escalonados...')
        planes_reales = [
            {
                'nombre': 'BASICO',
                'nombre_mostrar': 'Plan Básico',
                'descripcion': 'Plan 1 (Doc Descripción App): solo métricas y satisfacción DE TU EMPRESA. Sin benchmarking, sin encuestas custom. Ideal para emprendimientos y negocios locales 1-3 locales.',
                'caracteristicas': [
                    '📊 Panel de métricas en tiempo real (Solo tu empresa)',
                    '📝 Encuestas NPS + CSAT ILIMITADAS (plantillas estándar por rubro)',
                    '📱 Generador códigos QR por local',
                    '👥 2 usuarios del panel (dueño + 1 colaborador)',
                    '📍 Hasta 3 locales incluidos SIN COSTO EXTRA',
                    '💸 Desde 4° local: $30.000 CLP / local / mes',
                    '🌐 Hasta 3 rubros online incluidos',
                    '💸 Desde 4° rubro online: $30.000 CLP / rubro / mes',
                    '📧 Soporte email prioritario',
                    '❌ Sin benchmarking sectorial',
                    '❌ Sin encuestas custom',
                ],
                'precio_clp': 25000,
                'locales_permitidos': 3,
                'locales_gratis_incluidos': 3,
                'costo_local_adicional_clp': 30000,
                'rubros_permitidos': 3,
                'rubros_gratis_incluidos': 3,
                'costo_rubro_adicional_clp': 30000,
                'usuarios_permitidos': 2,
                'dias_prueba_gratis': 14,
                'tiene_benchmarking_rubro': False,
                'tiene_encuestas_custom': False,
                'max_preguntas_encuesta_custom': 0,
                'es_plan_default': False,
                'es_lanzamiento_gratis': False,
                'orden': 10,
                'activo': True,
            },
            {
                'nombre': 'EMPRESARIAL',
                'nombre_mostrar': 'Plan Empresarial',
                'descripcion': 'Plan 2 (Doc Descripción App): todo el Básico + BENCHMARKING SECTORIAL vs empresas del MISMO RUBRO. Ideal para cadenas medianas y multi-locales.',
                'caracteristicas': [
                    '📊 TODO lo del Plan Básico',
                    '🏆 BENCHMARKING SECTORIAL en tiempo real (vs empresas de tu mismo rubro en Chile)',
                    '📈 KPIs comparativos: rating Google promedio, NPS/CSAT vs percentiles rubro, velocidad respuesta reseñas',
                    '👥 5 usuarios del panel',
                    '📍 Hasta 3 locales incluidos SIN COSTO EXTRA',
                    '💸 Desde 4° local: $25.000 CLP / local / mes (tarifa reducida)',
                    '🌐 Hasta 3 rubros online incluidos',
                    '💸 Desde 4° rubro online: $25.000 CLP / rubro / mes (tarifa reducida)',
                    '📞 Soporte teléfono + email prioritario',
                    '❌ Sin encuestas custom',
                ],
                'precio_clp': 60000,
                'locales_permitidos': 3,
                'locales_gratis_incluidos': 3,
                'costo_local_adicional_clp': 25000,
                'rubros_permitidos': 3,
                'rubros_gratis_incluidos': 3,
                'costo_rubro_adicional_clp': 25000,
                'usuarios_permitidos': 5,
                'dias_prueba_gratis': 14,
                'tiene_benchmarking_rubro': True,
                'tiene_encuestas_custom': False,
                'max_preguntas_encuesta_custom': 0,
                'es_plan_default': False,
                'es_lanzamiento_gratis': False,
                'orden': 20,
                'activo': True,
            },
            {
                'nombre': 'PROFESIONAL',
                'nombre_mostrar': 'Plan Profesional',
                'descripcion': 'Plan 3 (Doc Descripción App): TODO Empresarial + ENCUESTAS CUSTOM de HASTA 5 PREGUNTAS para sondear productos, lanzamientos, atención. Ideal retail, salud, educación, franquicias.',
                'caracteristicas': [
                    '📊 TODO lo del Plan Empresarial',
                    '✍️  ENCUESTAS CUSTOM ILIMITADAS (máx 5 preguntas por encuesta)',
                    '🎯 Preguntas abiertas / escala 1-5 / SI-NO / múltiple opción',
                    '🧠 Análisis de sentimiento incorporado en respuestas abiertas',
                    '🔗 Redirección condicional post-encuesta (clientes felices → Google; insatisfechos → formulario atención)',
                    '👥 10 usuarios del panel',
                    '📍 Hasta 3 locales incluidos SIN COSTO EXTRA',
                    '💸 Desde 4° local: $20.000 CLP / local / mes (tarifa enterprise)',
                    '🌐 Hasta 3 rubros online incluidos',
                    '💸 Desde 4° rubro online: $20.000 CLP / rubro / mes (tarifa enterprise)',
                    '🤝 Customer Success Manager dedicado + soporte WhatsApp',
                ],
                'precio_clp': 75000,
                'locales_permitidos': 3,
                'locales_gratis_incluidos': 3,
                'costo_local_adicional_clp': 20000,
                'rubros_permitidos': 3,
                'rubros_gratis_incluidos': 3,
                'costo_rubro_adicional_clp': 20000,
                'usuarios_permitidos': 10,
                'dias_prueba_gratis': 14,
                'tiene_benchmarking_rubro': True,
                'tiene_encuestas_custom': True,
                'max_preguntas_encuesta_custom': 5,
                'es_plan_default': False,
                'es_lanzamiento_gratis': False,
                'orden': 30,
                'activo': True,
            },
        ]
        for p_def in planes_reales:
            nombre = p_def['nombre']
            p, created_p = Plan.objects.get_or_create(
                nombre=nombre,
                defaults={k: v for k, v in p_def.items() if k != 'nombre'}
            )
            if not created_p:
                # Actualizar campos importantes (no se toca es_plan_default de otros)
                for k, v in p_def.items():
                    if k in ['es_plan_default']:
                        continue
                    if getattr(p, k, None) != v:
                        setattr(p, k, v)
                p.save()
            self.stdout.write(self.style.SUCCESS(
                f'  ✅ {p.get_nombre_mostrar()} | ${p.precio_clp:,} CLP base | 4° loc ${p.costo_local_adicional_clp:,} | 4° rubro ${p.costo_rubro_adicional_clp:,} | Benchmark:{p.tiene_benchmarking_rubro} Custom:<={p.max_preguntas_encuesta_custom}p'.replace(',', '.')
            ))

        # ======== 4. PLAN MVP BÁSICO (LANZAMIENTO 365 DÍAS GRATIS - Demo onboarding) ========
        self.stdout.write('\n💼 Creando Plan MVP_BÁSICO (Lanzamiento 365 días gratis, default onboarding)...')
        caracteristicas_default = [
            "🎉 LANZAMIENTO 365 DÍAS 100% GRATIS (precio simbólico $6.990 NO SE COBRA durante lanzamiento)",
            "📊 Panel de métricas en tiempo real",
            "📝 Encuestas NPS y CSAT ilimitadas",
            "📱 Generador de códigos QR por local",
            "📈 Benchmarking sectorial básico",
            "👥 2 usuarios (dueño + 1 colaborador)",
            "📍 1 local comercial",
            "📧 Soporte por email prioritario",
            "💡 Acceso anticipado a nuevas funcionalidades",
        ]
        plan_mvp, created = Plan.objects.get_or_create(
            nombre='MVP_BASICO',
            defaults={
                'nombre_mostrar': 'MVP Básico (Lanzamiento 365 días)',
                'descripcion': 'Plan lanzamiento 365 días GRATIS para primeros 1.000 clientes. 1 local, 2 usuarios. Incluye todo el Básico + benchmarking. Luego pasas al Plan Básico si quieres continuar.',
                'caracteristicas': caracteristicas_default,
                'precio_uf': '0.12',
                'precio_clp': 6990,
                'moneda': MonedaChoices.CLP,
                'locales_permitidos': 1,
                'locales_gratis_incluidos': 1,
                'costo_local_adicional_clp': 0,
                'rubros_permitidos': 1,
                'rubros_gratis_incluidos': 1,
                'costo_rubro_adicional_clp': 0,
                'usuarios_permitidos': 2,
                'dias_prueba_gratis': 365,
                'tiene_benchmarking_rubro': True,
                'tiene_encuestas_custom': False,
                'max_preguntas_encuesta_custom': 0,
                'es_lanzamiento_gratis': True,
                'es_plan_default': True,
                'orden': 1,
                'activo': True,
            }
        )
        if not created:
            actualizados = False
            if not plan_mvp.nombre_mostrar:
                plan_mvp.nombre_mostrar = 'MVP Básico (Lanzamiento 365 días)'
                actualizados = True
            if not plan_mvp.caracteristicas:
                plan_mvp.caracteristicas = caracteristicas_default
                actualizados = True
            if not plan_mvp.es_plan_default and not Plan.objects.filter(es_plan_default=True).exclude(id=plan_mvp.id).exists():
                plan_mvp.es_plan_default = True
                actualizados = True
            if not getattr(plan_mvp, 'es_lanzamiento_gratis', False):
                plan_mvp.es_lanzamiento_gratis = True
                actualizados = True
            if getattr(plan_mvp, 'locales_gratis_incluidos', 0) != 1:
                plan_mvp.locales_gratis_incluidos = 1
                actualizados = True
            if not plan_mvp.tiene_benchmarking_rubro:
                plan_mvp.tiene_benchmarking_rubro = True
                actualizados = True
            if actualizados:
                plan_mvp.save()
        self.stdout.write(self.style.SUCCESS(f'  ✅ Plan {plan_mvp.get_nombre_mostrar()} (default: {plan_mvp.es_plan_default} | {plan_mvp.dias_prueba_gratis} días gratis | LANZAMIENTO: {plan_mvp.es_lanzamiento_gratis})'))

        # ======== 5. NEGOCIO DEMO ========
        self.stdout.write('\n🏪 Creando Negocio Demo...')
        comuna_rancagua = Comuna.objects.filter(nombre__iexact='Rancagua').first()
        rubro_cafeteria = (
            Rubro.objects.filter(activo=True, nombre__icontains='cafeter').first()
            or Rubro.objects.filter(activo=True, nombre__icontains='restaur').first()
            or Rubro.objects.filter(activo=True, es_otro=False).order_by('orden').first()
        )
        negocio, created = Negocio.objects.get_or_create(
            dueño=dueno_user,
            nombre='Café del Centro Demo',
            defaults={
                'rut': '76.123.456-7',
                'rubro_google': 'cafe_brunch_restaurant',
                'direccion': 'Plaza de Armas 123, Piso 1',
                'ciudad': 'Rancagua',
                'telefono': '+56 72 212 3456',
                'email_contacto': 'demo@clientbeat.cl',
                'verificado': True,
                'fecha_verificacion': datetime.now(),
                'estado': Negocio.EstadoChoices.ACTIVO,
                'comuna': comuna_rancagua,
                'rubro': rubro_cafeteria,
            }
        )
        if not negocio.comuna and comuna_rancagua:
            negocio.comuna = comuna_rancagua
            negocio.save(update_fields=['comuna'])
        if not negocio.rubro and rubro_cafeteria:
            negocio.rubro = rubro_cafeteria
            negocio.save(update_fields=['rubro'])
        extra_rubro = f' | Rubro: {negocio.rubro.nombre}' if negocio.rubro else ''
        extra_comuna = f' | Comuna: {negocio.comuna.nombre}' if negocio.comuna else ''
        self.stdout.write(self.style.SUCCESS(f'  ✅ Negocio: {negocio.nombre}{extra_comuna}{extra_rubro}'))

        # ======== 6. LOCAL PRINCIPAL ========
        self.stdout.write('\n📍 Creando Local Demo...')
        qr_tok = f'CB-DEMO-{secrets.token_urlsafe(16).upper()[:10]}'
        local, created = Local.objects.get_or_create(
            negocio=negocio,
            nombre='Café del Centro - Local Plaza',
            defaults={
                'direccion': 'Plaza de Armas 123',
                'ciudad': 'Rancagua',
                'latitud': '-34.1704100',
                'longitud': '-70.7423600',
                'google_place_id': 'demo_place_id_12345',
                'horario': {
                    'Lunes-Viernes': '08:00-21:00',
                    'Sabado': '09:00-22:00',
                    'Domingo': '09:30-14:30',
                },
                'qr_token': qr_tok,
                'estado': Local.EstadoChoices.ACTIVO,
                'comuna': comuna_rancagua,
            }
        )
        if not local.comuna and comuna_rancagua:
            local.comuna = comuna_rancagua
            local.save(update_fields=['comuna'])
        self.stdout.write(self.style.SUCCESS(f'  ✅ Local: {local.nombre} | QR: {local.qr_token}{f" | Comuna: {local.comuna.nombre}" if local.comuna else ""}'))

        # ======== 7. MIEMBROS EQUIPO ========
        self.stdout.write('\n🤝 Asignando miembros al equipo...')
        # Equipo usuario -> invitado por dueño
        _, created = MiembroEquipo.objects.get_or_create(
            negocio=negocio,
            usuario=equipo_user,
            defaults={
                'rol': MiembroEquipo.RolChoices.USUARIO_EQUIPO,
                'estado': MiembroEquipo.EstadoChoices.ACTIVO,
                'permisos': [
                    MiembroEquipo.PermisosChoices.VER_TODO,
                    MiembroEquipo.PermisosChoices.GESTIONAR_ENCUESTAS,
                    MiembroEquipo.PermisosChoices.CORREGIR_SENTIMIENTO,
                ],
                'fecha_aceptacion': datetime.now(),
                'invitado_por': dueno_user,
            }
        )
        self.stdout.write(self.style.SUCCESS('  ✅ Javier Muñoz agregado al equipo (Permisos: VER_TODO + GESTIONAR_ENCUESTAS + CORREGIR_SENTIMIENTO)'))

        # ======== 8. SUSCRIPCIÓN ACTIVA ========
        self.stdout.write('\n💳 Creando Suscripción activa Plan MVP...')
        hoy = datetime.now().date()
        susc, created = Suscripcion.objects.get_or_create(
            negocio=negocio,
            defaults={
                'plan': plan_mvp,
                'estado': EstadoSuscripcionChoices.ACTIVA,
                'fecha_inicio': datetime.now(),
                'fecha_vencimiento': datetime.now() + timedelta(days=365),
                'proximo_ciclo': datetime.now() + timedelta(days=30),
                'renovacion_automatica': True,
            }
        )
        if not created:
            susc.estado = EstadoSuscripcionChoices.ACTIVA
            susc.save()
        self.stdout.write(self.style.SUCCESS(f'  ✅ Suscripción: {susc.get_estado_display()} | Vence: {susc.fecha_vencimiento.strftime("%d/%m/%Y")}'))

        # ======== RESUMEN ========
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.MIGRATE_HEADING('   🎉 DATOS DEMO LISTOS - CLIENT BEAT 🎉'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'  Empresa: {settings.EMPRESA.get("NOMBRE")}')
        self.stdout.write(f'  Negocio demo: {negocio.nombre} ({negocio.ciudad})')
        self.stdout.write(f'  Plan contratado: {plan_mvp.nombre}')
        self.stdout.write(f'  Contraseña común: {pw}')
        self.stdout.write('')
        self.stdout.write('  🔐 USUARIOS CREADOS:')
        self.stdout.write(f'  0. SUPERUSER TÉCNICO → super@clientbeat.cl  / {pw}')
        self.stdout.write(f'     → Superusuario: SÍ | Staff: SÍ | Rol: ADMIN_SOPORTE')
        self.stdout.write(f'     → ACCESO EXCLUSIVO A: /admin/  (Django Admin raw)')
        self.stdout.write(f'     → ACCESO TAMBIÉN A: /admin-panel/  (Panel no-técnico ClienBeat)')
        self.stdout.write(f'  1. ADMIN SOPORTE   → admin@clientbeat.cl  / {pw}')
        self.stdout.write(f'     → Superusuario: NO | Staff: SÍ | Rol: ADMIN_SOPORTE')
        self.stdout.write(f'     → ACCESO EXCLUSIVO A: /admin-panel/  (Panel no-técnico ClienBeat)')
        self.stdout.write(f'     → ACCESO BLOQUEADO A: /admin/  (Django Admin raw, es solo SUPERUSER)')
        self.stdout.write(f'  2. DUEÑO NEGOCIO   → dueno@negociodemo.cl  / {pw}')
        self.stdout.write(f'     → Superusuario: NO | Staff: SÍ (solo sus datos)')
        self.stdout.write(f'     → Puede: GESTIONAR todo su negocio, configuración de CUENTA y FACTURACIÓN')
        self.stdout.write(f'     → PERMISO_gestionar_cuenta = SÍ')
        self.stdout.write(f'  3. USUARIO EQUIPO  → usuario.equipo@negociodemo.cl  / {pw}')
        self.stdout.write(f'     → Superusuario: NO | Staff: NO')
        self.stdout.write(f'     → Puede: Ver indicadores, gestionar encuestas, corregir sentimiento')
        self.stdout.write(f'     → NO PUEDE: Configuración de cuenta + facturación (gestion_cuenta = NO)')
        self.stdout.write('=' * 60)
        self.stdout.write(f'  SuperAdmin Técnico (raw): http://127.0.0.1:8000/admin/       → super@clientbeat.cl')
        self.stdout.write(f'  Admin Panel ClienBeat (no técnico): http://127.0.0.1:8000/admin-panel/ → admin@clientbeat.cl / super@clientbeat.cl')
        self.stdout.write('=' * 60)
