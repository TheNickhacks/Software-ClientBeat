# Informe de Implementación — FASE 0 (Panel Admin Doble Capa)
**Cliente / Producto**: Client Beat  
**Fecha**: 16 de agosto de 2026  
**Versión implementada**: MVP_Básico + Capa Admin Separada (FASE 0 del Plan)  
**Ambiente**: Django 5.1 + DRF + NeonDB Postgres Serverless + Tailwind v3 + HTMX + FontAwesome 6

---

## 1. Objetivo de la FASE 0
Separar **completamente** la capa administrativa de Client Beat en dos niveles estancos, cumpliendo el requerimiento del cliente:
> *"Los administradores (ADMIN_SOPORTE) NO deben tener acceso a la capa técnica de Django Admin. Solo a una capa ClienBeat propia sin entrar en lo técnico."*

### Resultado: Arquitectura Admin de 2 Capas
| Capa | URL | Destinado a | Diseño | Tipo de acceso |
|---|---|---|---|---|
| 🔒 **CAPA TÉCNICA (raw)** | `/admin/` | **Solo SUPERUSER Django** (`is_superuser=True`) | Django Admin estándar (tablas raw, migrations, CRUD técnico) | **BLOQUEADA TOTALMENTE** para ADMIN_SOPORTE, DUEÑO, USUARIO_EQUIPO |
| 🧑‍💼 **CAPA CLIENTBEAT (no técnica)** | `/admin-panel/` | **ADMIN_SOPORTE** o **SUPERUSER** | UI propia ClienBeat (glass-effect, gradient purple/indigo, sidebar 8 módulos, KPIs visuales) | Solo usuarios con rol `ADMIN_SOPORTE` o superuser |

---

## 2. Credenciales Demo (Data Seed)
Contraseña común para todos los usuarios demo: **`ClienBeat2026!`**

| # | Email | Rol Django | `is_superuser` | `is_staff` | Acceso `/admin/` raw | Acceso `/admin-panel/` no técnico | Acceso `/dashboard/` cliente |
|---|---|---|---|---|---|---|---|
| 0 | `super@clientbeat.cl` | ADMIN_SOPORTE (técnico) | ✅ **SÍ** | SÍ | ✅ ENTRA | ✅ ENTRA | ✅ ENTRA |
| 1 | `admin@clientbeat.cl` | ADMIN_SOPORTE (soporte humano) | ❌ **NO** | SÍ | ❌ **BLOQUEADO** (redirect auto → `/admin-panel/`) | ✅ ENTRA | ✅ ENTRA |
| 2 | `dueno@negociodemo.cl` | DUEÑO (Café del Centro Demo) | NO | SÍ (solo datos propios) | ❌ BLOQUEADO | ❌ BLOQUEADO (redirect auto → `/dashboard/`) | ✅ ENTRA (bienvenida María González) |
| 3 | `usuario.equipo@negociodemo.cl` | USUARIO_EQUIPO (Javier Muñoz) | NO | NO | ❌ BLOQUEADO | ❌ BLOQUEADO | ✅ ENTRA |

### Nota irreversible sobre el Seed Demo
Antes de esta FASE 0, `admin@clientbeat.cl` históricamente **era superuser**. El comando `python manage.py seed_demo` ahora:
1. **Crea** `super@clientbeat.cl` con `is_superuser=True` si no existe.
2. Si `admin@clientbeat.cl` ya existía y **tenía superuser**, se lo **QUITA forzosamente** (`is_superuser=False`) y solo conserva `is_staff=True` + rol ADMIN_SOPORTE.
3. Si se ejecuta con flag `--reset`, borra los 4 correos demo (super, admin, dueño, equipo) y los recrea limpios.

---

## 3. Archivos creados y modificados

### 3.1 Nuevos archivos creados
| Archivo | Propósito |
|---|---|
| [core/admin.py](file:///c:/Users/nnava/Desktop/ClienBeat/backend/core/admin.py) | `ClientBeatSuperAdminSite(AdminSite)` custom. Sobreescribe `admin_view()` global para interceptar TODAS las rutas `/admin/*` y redirigir a `/admin-panel/` a todo usuario autenticado que NO sea `is_superuser=True`. |
| [apps/adminpanel/__init__.py](file:///c:/Users/nnava/Desktop/ClienBeat/backend/apps/adminpanel/__init__.py) | Init app nueva. |
| [apps/adminpanel/apps.py](file:///c:/Users/nnava/Desktop/ClienBeat/backend/apps/adminpanel/apps.py) | `AppConfig` con `ready()` que reemplaza `django.contrib.admin.site.__class__` por `ClientBeatSuperAdminSite` (garantiza carga global). |
| [apps/adminpanel/admin.py](file:///c:/Users/nnava/Desktop/ClienBeat/backend/apps/adminpanel/admin.py) | (vacío, sin registros — el panel es de vistas propias, no Django Admin). |
| [apps/adminpanel/mixins.py](file:///c:/Users/nnava/Desktop/ClienBeat/backend/apps/adminpanel/mixins.py) | `AdminSoporteRequiredMixin` (admin o super) y `SuperUserRequiredMixin` (solo super) para vistas class-based del panel no-técnico. |
| [apps/adminpanel/urls.py](file:///c:/Users/nnava/Desktop/ClienBeat/backend/apps/adminpanel/urls.py) | 8 rutas: `dashboard / rubros / planes / plantillas / negocios / usuarios / solicitudes_arco / super_salud`. |
| [apps/adminpanel/views.py](file:///c:/Users/nnava/Desktop/ClienBeat/backend/apps/adminpanel/views.py) | `AdminPanelDashboardView` con 4 KPIs + últimas 5 altas + vencimientos 7 días + tarjetas Planes; `PlaceholderView` para módulos en construcción; `SuperSaludView` healthcheck DB superuser-only. |
| [apps/accounts/admin_mixins.py](file:///c:/Users/nnava/Desktop/ClienBeat/backend/apps/accounts/admin_mixins.py) | `SuperUserOnlyAdminMixin`: mixin reusable que bloquea `has_module/view/add/change/delete_permission` y `get_queryset` a todo aquel que NO sea `is_superuser=True`. Se aplica a TODOS los ModelAdmin existentes. |
| [templates/admin_panel/base.html](file:///c:/Users/nnava/Desktop/ClienBeat/backend/templates/admin_panel/base.html) | **Layout AUTÓNOMO (standalone)**, NO extiende `base.html` (evita navbar cliente + footer). Sidebar fijo 64px con 8 módulos + logout inline + Toasts messages. Head propio Tailwind CDN + FontAwesome + HTMX. Design System ClienBeat (`.gradient-text`, `.glass-effect`, `.btn-primary`). |
| [templates/admin_panel/dashboard.html](file:///c:/Users/nnava/Desktop/ClienBeat/backend/templates/admin_panel/dashboard.html) | 4 tarjetas KPI (Negocios, Suscripciones activas, Usuarios plataforma, Planes disponibles). Grid últimas altas + vencimientos. Grid tarjetas Planes con badge `PLAN ONBOARDING DEFAULT`, precios, locales/usuarios/días prueba, features. Usa `{% load humanize %}`. |
| [templates/admin_panel/placeholder.html](file:///c:/Users/nnava/Desktop/ClienBeat/backend/templates/admin_panel/placeholder.html) | Template genérico "En construcción" (Rubros, Plantillas, Negocios, Usuarios, ARCOPB). |
| [templates/admin_panel/super_salud.html](file:///c:/Users/nnava/Desktop/ClienBeat/backend/templates/admin_panel/super_salud.html) | Vista solo superuser: healthcheck `SELECT 1` a NeonDB, DEBUG mode, `DATABASE_ENGINE`. Para diagnósticos rápidos. |

### 3.2 Archivos modificados existentes
| Archivo | Cambio aplicado |
|---|---|
| [core/settings.py](file:///c:/Users/nnava/Desktop/ClienBeat/backend/core/settings.py#L24-L48) | Agregado `apps.adminpanel` a `INSTALLED_APPS`; agregado `django.contrib.humanize` para template tags `|intcomma` y `|naturalday`. |
| [core/urls.py](file:///c:/Users/nnava/Desktop/ClienBeat/backend/core/urls.py#L7-L16) | Agregada ruta `path('admin-panel/', include('apps.adminpanel.urls'))`. |
| [apps/accounts/admin.py](file:///c:/Users/nnava/Desktop/ClienBeat/backend/apps/accounts/admin.py) | `UserAdmin` ahora hereda PRIMERO de `SuperUserOnlyAdminMixin`. Eliminado `has_module_permission` que permitía a ADMIN_SOPORTE acceder. `get_queryset` retorna `.none()` para no-superuser. |
| [apps/businesses/admin.py](file:///c:/Users/nnava/Desktop/ClienBeat/backend/apps/businesses/admin.py) | Aplicado `SuperUserOnlyAdminMixin` a 5 ModelAdmin: `NegocioAdmin`, `MiembroEquipoAdmin`, `LocalAdmin`, `CompetidorAdmin`, `SnapshotReputacionAdmin` + 2 Inlines (`MiembroEquipoInline`, `LocalInline`). Eliminados todos los `if request.user.is_admin_soporte or is_superuser` que daban acceso raw. |
| [apps/billing/admin.py](file:///c:/Users/nnava/Desktop/ClienBeat/backend/apps/billing/admin.py) | Aplicado `SuperUserOnlyAdminMixin` a 4 ModelAdmin: `PlanAdmin`, `SuscripcionAdmin`, `PagoAdmin`, `RegistroCobranzaAdmin`. Eliminados los 4 overrides `has_module/view/add_permission = is_admin_soporte`. Se conservan acciones del Plan (marcar default, activar/desactivar). |
| [apps/accounts/management/commands/seed_demo.py](file:///c:/Users/nnava/Desktop/ClienBeat/backend/apps/accounts/management/commands/seed_demo.py#L42-L314) | NUEVO usuario 0 `super@clientbeat.cl` (is_superuser=True). Usuario `admin@clientbeat.cl` → is_superuser=False (se le QUITA forzosamente si lo tenía). `demo_emails` incluye los 4 correos. Banner resumen final actualizado distinguiendo `/admin/` raw (super) vs `/admin-panel/` no-técnico (admin/super). |

---

## 4. Pruebas E2E Realizadas (3 flujos completos)
Fecha pruebas: 16-08-2026, servidor Django `runserver` en `http://127.0.0.1:8000`.

### 🔹 Prueba 1 — ADMIN_SOPORTE intenta entrar a `/admin/` raw
- **Actor**: `admin@clientbeat.cl` (is_superuser=False, is_admin_soporte=True)
- **Entrada**: Navegación directa a `http://127.0.0.1:8000/admin/`
- **Esperado**: Redirección automática al panel no-técnico `/admin-panel/`, sin error 403 ni página "no autorizado".
- **Resultado**: ✅ **EXITOSO**
  - Redirigido 302 → `/admin-panel/` sin mostrar el formulario de login Django raw.
  - Panel ClienBeat renderizado correctamente (sidebar 8 módulos, 4 KPIs, tarjetas Planes).

### 🔹 Prueba 2 — SUPERUSER entra a `/admin/` raw
- **Actor**: `super@clientbeat.cl` (is_superuser=True)
- **Entrada**: Login desde `http://127.0.0.1:8000/admin/login/?next=/admin/`
- **Esperado**: Acceso completo a Django Admin tradicional, mostrando TODAS las apps registradas.
- **Resultado**: ✅ **EXITOSO**
  - Header muestra `🔒 SuperAdmin Técnico Client Beat (Solo SuperUser)`.
  - Título página `Consola Técnica de Emergencia`.
  - Apps visibles correctamente: Análisis de Sentimiento, Autenticación y Autorización, Celery Results, Cuentas de Usuario, Encuestas, Facturación y Suscripciones, Negocios y Locales, Páginas, Reputación y Reseñas, Sitios, Tareas Periódicas, Token de Autenticación.

### 🔹 Prueba 3 — DUEÑO intenta entrar a `/admin-panel/`
- **Actor**: `dueno@negociodemo.cl` (is_admin_soporte=False, is_superuser=False)
- **Entrada**: Login normal en `/accounts/login/` → redirige a `/dashboard/` (OK). Luego navegación manual a `/admin-panel/`.
- **Esperado**: Redirección automática de vuelta a `/dashboard/` con mensaje flash "Sin permisos para Panel Admin ClienBeat".
- **Resultado**: ✅ **EXITOSO**
  - `AdminSoporteRequiredMixin.dispatch()` detecta `user.is_admin_soporte=False`, no tiene permiso.
  - Redirect `HttpResponseRedirect('/dashboard/')` con `messages.error()`.
  - Usuario queda en panel cliente "Bienvenido, María González" sin posibilidad de escalar.

### 🔹 Prueba adicional — shell unitaria `has_permission`
```python
from django.test import RequestFactory
from django.contrib.admin.sites import site
# super@  → site.has_permission(r) = True   ✅
# admin@  → site.has_permission(r) = False  ✅
# dueno@  → site.has_permission(r) = False  ✅
```

### 🔹 Prueba de integridad Django
```
python manage.py check        → System check identified no issues (0 silenced).  ✅
python manage.py makemigrations → No changes detected                            ✅
python manage.py migrate        → No migrations to apply                          ✅
python manage.py seed_demo      → 4 usuarios creados/actualizados OK             ✅
```

---

## 5. 8 módulos del Sidebar Panel ClienBeat (no-técnico)
Todos los módulos usan el diseño glass-effect del Design System ClienBeat.

| Ícono | Nombre | Permiso mínimo | Estado |
|---|---|---|---|
| 📊 | Dashboard | AdminSoporte o SuperUser | ✅ IMPLEMENTADO (KPIs + altas + vencimientos + planes) |
| 🏷️ | Rubros | AdminSoporte o SuperUser | ⏳ En construcción (FASE 1, desde doc `Descripción App.docx`) |
| 💰 | Planes y Precios | AdminSoporte o SuperUser | ⏳ En construcción (FASE 1, planes $25k/$60k/$75k + extras escalonados) |
| 📝 | Plantillas Encuestas | AdminSoporte o SuperUser | ⏳ En construcción |
| 🏢 | Negocios | AdminSoporte o SuperUser | ⏳ En construcción |
| 👥 | Usuarios | AdminSoporte o SuperUser | ⏳ En construcción |
| 🛡️ | Solicitudes ARCOPB | AdminSoporte o SuperUser | ⏳ En construcción |
| 🩺 | Salud Técnica | **Solo SuperUser** (badge sidebar) | ✅ IMPLEMENTADO (healthcheck DB + DEBUG) |

---

## 6. Reglas de Seguridad Implementadas
1. **Middleware de bloqueo total**: `ClientBeatSuperAdminSite.admin_view()` intercepta CUALQUIER ruta debajo de `/admin/*` (no solo el index). Cualquier usuario autenticado sin `is_superuser=True` es inmediatamente 302-redirectado a `/admin-panel/`.
2. **Login view defensiva**: Si un ADMIN_SOPORTE se loguea accidentalmente desde `/admin/login/`, el método `login()` del custom site también lo redirige.
3. **Defensa en profundidad (ModelAdmin)**: Todos los `ModelAdmin` heredan `SuperUserOnlyAdminMixin`. Incluso si el primer bloqueo fallara, cada modelo individual niega permisos y retorna `.none()` en `get_queryset`.
4. **AppConfig.ready() no transaccionable**: La asignación `default_admin_site.__class__ = ClientBeatSuperAdminSite` vive en `apps/adminpanel/apps.py` (`ready()`) → se ejecuta 1 vez al boot Django, no puede saltarse.
5. **Superuser email separado**: `super@clientbeat.cl` es el único con `is_superuser=True`. El rol `ADMIN_SOPORTE` por sí mismo ya NO da acceso a raw (solo a panel no-técnico).

---

## 7. Servidor
- **Estado**: 🛑 **APAGADO** (PID 26308 terminado, puerto TCP 127.0.0.1:8000 liberado).
- **Para volver a levantar**:
  ```powershell
  cd c:\Users\nnava\Desktop\ClienBeat\backend
  python manage.py runserver 127.0.0.1:8000
  ```
- **Para regenerar datos demo**:
  ```powershell
  cd c:\Users\nnava\Desktop\ClienBeat\backend
  python manage.py seed_demo --reset
  ```

---

## 8. Próximos pasos — FASE 1
Cuando se confirme, se ejecutará:
1. **Modelos Región / Provincia / Comuna** (348 filas desde `regiones-chile.xlsx`) con seed bulk.
2. **Rubros reales** extraídos desde `Descripción App.docx` (selección dropdown onboarding).
3. **3 Planes + precios + cobros extras escalonados** desde `Prompt Tipos de planes.docx`:
   - Básico $25.000 CLP
   - Empresarial $60.000 CLP
   - Profesional $75.000 CLP
   - Costo extra por local adicional (4°+): 30k / 25k / 20k escalonado
   - Costo extra por rubro online adicional (4°+): mismos valores
4. **CRUD Planes** dentro del Panel ClienBeat no-técnico (gestionable por ADMIN_SOPORTE sin entrar a raw).
5. **Reanudación onboarding paso 1 → paso 2** si usuario no completó el flujo.
