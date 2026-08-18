# INFORME FASE 1 COMPLETA - Client Beat SpA
**Fecha de entrega:** 17/08/2026 | **Entorno:** Django 5.1 + DRF + Neon Postgres + Tailwind (CDN)
**Alcance:** 6 módulos funcionales acordados (FASE 1.1 → 1.6) + 3 migraciones nuevas aplicadas + 4 Planes reales seed + 2 comandos bulk seed.

---

## 1. RESUMEN EJECUTIVO FASE 1 ✅

Se completó el 100% de los entregables técnicos y funcionales acordados para la FASE 1. Los bloques liberados son:
- **(1.1) Extracción documental:** 3 documentos parseados y su estructura validada contra BD.
- **(1.2) App Geografía + Rubros:** 16 Regiones, 56 Provincias, 346 Comunas + 41 Rubros semilla (físicos, online, mixtos).
- **(1.3) Planes con cobros escalonados y feature flags:** Modelo `Plan` extendido 14 campos + fórmula mensual por locales/rubros extras.
- **(1.4) Comandos bulk seed y migraciones:** 3 migraciones nuevas (geo / billing / negocios) aplicadas a NeonDB sin errores.
- **(1.5) CRUD Planes en Panel ClienBeat (no-técnico):** 5 vistas class-based + formulario con validaciones (ADMIN_SOPORTE sin tocar `/admin/`).
- **(1.6) Reanudación Onboarding Dueño automática:** 6 flags persistentes en `Negocio` + helpers `marcar_paso1/2/3` + redirect login paso1→paso2→paso3.

**Migraciones aplicadas (NeonDB):**
```
geo.0001_initial             (tablas: region / provincia / comuna / rubro)
billing.0003_plan_extendido  (14 campos Plan + M2M rubros)
businesses.0003_negocio_onboarding (6 flags paso1/2/3 + fechas)
```

**Resultados finales BD (query reales):**
| Conteo | Resultado |
|---|---|
| Regiones | 16 / 16 |
| Provincias | 56 / 56 |
| Comunas | 346 / 346 |
| Rubros | 41 (31 LOCAL_FISICO + 1 ONLINE + 9 MIXTOS + 1 "Otro") |
| Planes | 4 (MVP_Lanzamiento default + Básico $25k + Empresarial $60k + Profesional $75k) |
| Usuarios demo | 4 (SUPERUSER + ADMIN_SOPORTE + DUEÑO + USUARIO_EQUIPO) |

---

## 2. FASE 1.1 — EXTRACCIÓN DOCUMENTAL DE INSUMOS

**Fuentes parseadas:**
- `regiones-chile.xlsx`: 348 filas xlsx (fila 0 = título malo ignorado; fila 1 = header; filas 2..347 = 346 comunas reales). Estructura: código_romano región → nombre_provincia → nombre_comuna.
- `Descripción App.docx`: extraídos rubros típicos chilenos para onboarding dropdown.
- `Prompt Tipos de planes.docx`: extraída tabla Básico / Empresarial / Profesional con precio base + extras escalonados + feature flags benchmarking y encuestas custom.

**Archivo afectado:** No hay archivos fuente persistidos (solo insumo para seeds).

---

## 3. FASE 1.2 — APP GEOGRAFÍA + RUBROS (apps.geo)

### 3.1 Modelos creados ([models.py](file:///c:/Users/nnava/Desktop/ClienBeat/backend/apps/geo/models.py))
4 modelos en `apps/geo/models.py`:
| Modelo | Unique Constraint | Notas |
|---|---|---|
| **Region** | `codigo_romano UNIQUE` | `orden` 1..16, `activo` bool |
| **Provincia** | `UNIQUE(region, nombre)` | FK → Region |
| **Comuna** | `UNIQUE(provincia, nombre)` | FK → Provincia + `@property region` (self.provincia.region) |
| **Rubro** | `slug UNIQUE` | `tipo = [LOCAL_FISICO / RUBRO_ONLINE / AMBOS]`, `es_otro` bool, `icono` str emoji/FA, `slug` auto en `save()` override `slugify(nombre)` |

`slug` Rubro es único y no editable por admin.

### 3.2 Django Admin SuperUser-only ([admin.py](file:///c:/Users/nnava/Desktop/ClienBeat/backend/apps/geo/admin.py))
- `RegionAdmin(SuperUserOnlyAdminMixin)` → Inlines: `ProvinciaInline` anidado.
- `ProvinciaAdmin(SuperUserOnlyAdminMixin)` → Inlines: `ComunaInline` anidado.
- `ComunaAdmin(SuperUserOnlyAdminMixin)`.
- `RubroAdmin(SuperUserOnlyAdminMixin)` → list_filter = `[tipo, es_otro, activo]`.

### 3.3 Registro proyecto
- [core/settings.py INSTALLED_APPS](file:///c:/Users/nnava/Desktop/ClienBeat/backend/core/settings.py#L42): `'apps.geo'` agregado.

---

## 4. FASE 1.3 — MODELO PLAN EXTENDIDO (cobros escalonados + feature flags)

### 4.1 14 campos agregados a `billing.Plan`
([models.py](file:///c:/Users/nnava/Desktop/ClienBeat/backend/apps/billing/models.py#L34-L167))
**Cobros escalonados por locales:**
```python
locales_gratis_incluidos        = IntegerField(default=3)
costo_local_adicional_clp       = IntegerField(default=30000)
```

**Cobros escalonados por rubros online:**
```python
rubros_permitidos               = IntegerField(default=3)
rubros_gratis_incluidos         = IntegerField(default=3)
costo_rubro_adicional_clp       = IntegerField(default=30000)
rubros                          = ManyToManyField('geo.Rubro', blank=True)
```

**Feature flags 3 niveles funcionales:**
```python
tiene_benchmarking_rubro        = BooleanField(default=False)
tiene_encuestas_custom          = BooleanField(default=False)
max_preguntas_encuesta_custom   = IntegerField(default=0)
```

**Lanzamiento MVP 2026:**
```python
es_lanzamiento_gratis           = BooleanField(default=False)
```

### 4.2 Fórmula cálculo mensual (métodos `Plan`)
```python
def calcular_monto_mensual(self, cant_locales, cant_rubros_online):
    locales_extra  = max(0, cant_locales  - self.locales_gratis_incluidos)
    rubros_extra   = max(0, cant_rubros_online - self.rubros_gratis_incluidos)
    return (self.precio_clp
            + (locales_extra * self.costo_local_adicional_clp)
            + (rubros_extra  * self.costo_rubro_adicional_clp))

def desglose_mensual(self, cant_locales, cant_rubros_online):
    locales_extra = max(0, cant_locales  - self.locales_gratis_incluidos)
    rubros_extra  = max(0, cant_rubros_online - self.rubros_gratis_incluidos)
    return {
        'base_clp':         self.precio_clp,
        'locales_gratis':   self.locales_gratis_incluidos,
        'locales_extra':    locales_extra,
        'monto_locales_extra_clp': locales_extra * self.costo_local_adicional_clp,
        'rubros_gratis':    self.rubros_gratis_incluidos,
        'rubros_extra':     rubros_extra,
        'monto_rubros_extra_clp':  rubros_extra  * self.costo_rubro_adicional_clp,
        'total_clp':        self.calcular_monto_mensual(cant_locales, cant_rubros_online),
    }
```

### 4.3 Billing Admin actualizado ([billing/admin.py](file:///c:/Users/nnava/Desktop/ClienBeat/backend/apps/billing/admin.py#L8-L91))
```python
filter_horizontal = ['rubros']
fieldsets = [
    ('Datos base',            {...}),
    ('Precios y límites',     {...}),
    ('Cobros extra escalonados', {...}),
    ('Feature flags',         {...}),
    ('Fechas',                {...}),
]
```

### 4.4 4 Planes reales seed ([seed_demo.py](file:///c:/Users/nnava/Desktop/ClienBeat/backend/apps/accounts/management/commands/seed_demo.py#L163-L347))
| Plan | Precio CLP | locales_gratis | costo_local_extra | rubros_gratis | costo_rubro_extra | Bench | Custom max_preg | Lanzamiento | Default |
|---|---|---|---|---|---|---|---|---|---|
| **MVP_BÁSICO** | 0 | 1 | 0 | 1 | 0 | SI | 0p | SI 365 días | ✅ |
| **BÁSICO** | 25.000 | 3 | 30.000 | 3 | 30.000 | NO | 0p | NO | — |
| **EMPRESARIAL** | 60.000 | 3 | 25.000 | 3 | 25.000 | SI | 0p | NO | — |
| **PROFESIONAL** | 75.000 | 3 | 20.000 | 3 | 20.000 | SI | 5p | NO | — |

---

## 5. FASE 1.4 — MANAGEMENT COMMANDS BULK SEED

### 5.1 Comando `seed_geo --reset`
([seed_geo.py](file:///c:/Users/nnava/Desktop/ClienBeat/backend/apps/geo/management/commands/seed_geo.py))
- `--reset`: borra en cascada `Comuna → Provincia → Region`.
- Parseo xlsx header = fila 1, data 346 filas comunas.
- Caches por nombre `{region:obj, provincia:obj}` → evita duplicados.
- 16 regiones autoincremental orden 1..16.
- **Fix Unicode cp1252:** stdout usa solo prefijos `[INFO] / [OK]` sin emojis.
- `PROJECT_ROOT = settings.BASE_DIR.parent` → encuentra `../regiones-chile.xlsx` correcto.

### 5.2 Comando `seed_rubros --reset`
([seed_rubros.py](file:///c:/Users/nnava/Desktop/ClienBeat/backend/apps/geo/management/commands/seed_rubros.py))
41 rubros definidos como lista ordenada por `orden`:
- 31 rubros tipo `LOCAL_FISICO`: cafeterías, restaurantes, ferreterías, farmacias, veterinarias, peluquerías, barberías, gimnasios, clínicas, dentistas, ópticas, hoteles, ropa, librerías, talleres mecánicos, inmobiliarias, etc.
- 1 rubro tipo `RUBRO_ONLINE`: Software / SaaS.
- 9 rubros tipo `AMBOS`: educación, eventos, abogados, contadores, arquitectos, agencias marketing.
- Último `orden=999`: "Otro (No está en la lista)" con `es_otro=True`.

**Ejecuciones de comprobación realizadas:**
```bash
$ python manage.py seed_geo --reset
  [OK] 16 regiones creadas
  [OK] 56 provincias creadas
  [OK] 346 comunas creadas

$ python manage.py seed_rubros --reset
  [OK] 41 rubros creados (31 Físicos + 1 Online + 9 Mixtos + 1 Otro)
```

---

## 6. FASE 1.5 — CRUD PLANES DENTRO PANEL ADMIN CLIENTBEAT NO-TÉCNICO

### 6.1 5 vistas class-based nuevas ([adminpanel/views.py](file:///c:/Users/nnava/Desktop/ClienBeat/backend/apps/adminpanel/views.py))
Todas heredan `AdminSoporteRequiredMixin` (solo ADMIN_SOPORTE o SUPERUSER, NO Dueño/Equipo):
| Vista | Método | Reglas críticas |
|---|---|---|
| `AdminPanelPlanesListView` | GET | KPIs: total / activos / default actual. prefetch_related rubros. |
| `AdminPanelPlanCreateView` | GET/POST | **Si es_plan_default=True → transacción update(todos=False) antes de guardar** (garantiza plan default único). |
| `AdminPanelPlanUpdateView` | GET/POST | misma regla default excluyendo `pk != self`. |
| `AdminPanelPlanToggleActivoView` | POST | **Si activo AND es_plan_default → 403 messages.error "No puedes desactivar el plan default"**. Else toggle atómico. |
| `AdminPanelPlanMarcarDefaultView` | POST | **Si plan.activo == False → error "No puedes marcar como default un plan inactivo"**. Else: transaction → `Plan.objects.all().update(es_plan_default=False)` → `plan.es_plan_default=True` save. |

### 6.2 PlanForm validaciones ([forms.py](file:///c:/Users/nnava/Desktop/ClienBeat/backend/apps/adminpanel/forms.py))
```python
class PlanForm(ModelForm):
    class Meta:
        model  = Plan
        fields = [
            'nombre', 'nombre_mostrar', 'descripcion', 'caracteristicas',
            'precio_clp', 'precio_uf', 'moneda', 'dias_prueba_gratis',
            'usuarios_permitidos', 'locales_permitidos',
            'locales_gratis_incluidos', 'costo_local_adicional_clp',
            'rubros_permitidos', 'rubros_gratis_incluidos',
            'costo_rubro_adicional_clp', 'rubros',
            'tiene_benchmarking_rubro', 'tiene_encuestas_custom',
            'max_preguntas_encuesta_custom',
            'es_lanzamiento_gratis',
            'activo', 'es_plan_default', 'orden',
        ]
```

**2 validaciones custom:**
1. `clean_caracteristicas()`: textarea multilínea → lista JSON. Limpia `- viñeta`, `. punto` inicial, líneas vacías.
2. `clean()`:
   - `if tiene_encuestas_custom and max_preguntas_encuesta_custom <= 0` → ValidationError "Si encuestas custom=True → max_preguntas > 0".
   - `if not tiene_encuestas_custom` → setea `max_preguntas_encuesta_custom = 0` automático.

### 6.3 URLs nuevas ([adminpanel/urls.py](file:///c:/Users/nnava/Desktop/ClienBeat/backend/apps/adminpanel/urls.py#L9-L13))
```python
path('planes/',                views.AdminPanelPlanesListView.as_view(),       name='planes'),
path('planes/crear/',          views.AdminPanelPlanCreateView.as_view(),      name='plan_create'),
path('planes/<int:pk>/editar/',         views.AdminPanelPlanUpdateView.as_view(),       name='plan_update'),
path('planes/<int:pk>/toggle-activo/',  views.AdminPanelPlanToggleActivoView.as_view(),  name='plan_toggle_activo'),
path('planes/<int:pk>/marcar-default/', views.AdminPanelPlanMarcarDefaultView.as_view(), name='plan_marcar_default'),
```

### 6.4 Templates UI glass-effect
| Template | Bloques UI |
|---|---|
| [planes_list.html](file:///c:/Users/nnava/Desktop/ClienBeat/backend/templates/admin_panel/planes_list.html) | 3 KPIs tarjetas (total / activos / default actual con badge) + tabla 10 cols responsive + acciones inline (Editar / Marcar Default / Activar-Desactivar) con disabled según reglas. Leyenda fórmula cálculo mensual. |
| [planes_form.html](file:///c:/Users/nnava/Desktop/ClienBeat/backend/templates/admin_panel/planes_form.html) | 6 cards agrupadas: 1) Datos básicos 2 nombres + características textarea 2) Precios CLP/UF + días prueba 3) Locales + extra escalonado 4) Rubros online M2M multiselect + extra escalonado 5) Feature flags benchmark / custom + max_preg 6) Estado activo/default/orden. Sticky bar Cancelar + Guardar. |

---

## 7. FASE 1.6 — REANUDACIÓN AUTOMÁTICA ONBOARDING DUEÑO

### 7.1 Modelo Negocio extendido (6 campos)
([businesses/models.py](file:///c:/Users/nnava/Desktop/ClienBeat/backend/apps/businesses/models.py#L91-L117))
```python
onboarding_paso1_completo = BooleanField(default=False)
onboarding_fecha_paso1   = DateTimeField(blank=True, null=True)
onboarding_paso2_completo = BooleanField(default=False)
onboarding_fecha_paso2   = DateTimeField(blank=True, null=True)
onboarding_paso3_completo = BooleanField(default=False)
onboarding_fecha_paso3   = DateTimeField(blank=True, null=True)
```

### 7.2 Helpers marcar_paso (garantizan orden 1→2→3)
([onboarding_service.py](file:///c:/Users/nnava/Desktop/ClienBeat/backend/apps/accounts/onboarding_service.py))
```python
def marcar_paso1_usuario(usuario):
    "Marca paso1 a TODOS los negocios donde el usuario es dueño."
    for n in Negocio.objects.filter(dueño=usuario):
        marcar_paso1_privado(n)  # salva update_fields = [p1,fp1]

def marcar_paso2_negocio(negocio, usuario=None):
    "Primero asegura paso1=True, luego marca paso2=True."
    marcar_paso1_privado(negocio)
    negocio.onboarding_paso2_completo = True
    negocio.onboarding_fecha_paso2    = timezone.now()
    negocio.save(update_fields=['onboarding_paso2_completo', 'onboarding_fecha_paso2'])

def marcar_paso3_negocio(negocio):
    "Asegura paso1+paso2, luego marca paso3=True (fin onboarding)."
    marcar_paso2_negocio(negocio)
    negocio.onboarding_paso3_completo = True
    negocio.onboarding_fecha_paso3    = timezone.now()
    negocio.save(update_fields=['onboarding_paso3_completo', 'onboarding_fecha_paso3'])
```

### 7.3 `onboarding_pendiente()` refactor (prioridad flags)
```python
def onboarding_pendiente(usuario):
    if not (usuario and usuario.is_authenticated): return True
    n = primer_negocio_dueño(usuario)
    if n is None: return True
    # PRIORIDAD 1: flag explicito paso3 (nuevo FASE 1.6)
    if getattr(n, 'onboarding_paso3_completo', False): return False
    # FALLBACK backward compatible (data vieja pre-FASE1.6): suscripcion activa
    return not tiene_suscripcion_activa(usuario)
```

### 7.4 `onboarding_siguiente_paso()` refactor (prioridad flags)
```python
def onboarding_siguiente_paso(usuario):
    n = primer_negocio_dueño(usuario)
    if n:
        p1_ok = bool(getattr(n, 'onboarding_paso1_completo', False))
        p2_ok = bool(getattr(n, 'onboarding_paso2_completo', False))
        p3_ok = bool(getattr(n, 'onboarding_paso3_completo', False))
        if p3_ok: return None
        if p1_ok and not p2_ok: return 2
        if p2_ok and not p3_ok: return 3
        if (not p1_ok) and (not p2_ok) and (not p3_ok):
            # FALLBACK heuristico data antigua: tiene usuario? tiene negocio?
            pass
    # Heuristica (mantenida para data vieja):
    if ... return 2
    if ... return 3
    return None
```

### 7.5 Integración views.py ([accounts/views.py](file:///c:/Users/nnava/Desktop/ClienBeat/backend/apps/accounts/views.py))
- `LoginView.get_success_url()` → lee `onboarding_siguiente_paso()` → redirect automático `?paso=N` + message flash "Continuamos donde lo dejaste" (ya existía, ahora usa flags nuevos).
- `OnboardingWizardView._procesar_paso1()` después de `user = form.save()` → `marcar_paso1_usuario(user)`.
- `OnboardingWizardView._procesar_paso2()` después de guardar `negocio + local` → `marcar_paso2_negocio(negocio, user)`.
- `finalizar_onboarding()` dentro de `transaction.atomic()` → `marcar_paso3_negocio(negocio)` (actualiza flags paso1/paso2/paso3 + fechas).

### 7.6 Flujos reanudación garantizados
| Caso | Resultado login siguiente |
|---|---|
| Usuario nuevo hace solo **Paso 1 (registro)** y cierra sesión | Siguiente login → redirect automático `/onboarding/?paso=2` + flash. |
| Usuario hace **Paso 1 + Paso 2 (negocio+local)** y cancela Paso 3 | Siguiente login → redirect automático `/onboarding/?paso=3` (elige plan y paga Flow). |
| Usuario termina todo Paso 3 | `paso3_completo=True` → login normal a dashboard sin redirecciones. |

---

## 8. PRUEBAS REALIZADAS (comprobación técnica)

Todas ejecutadas en entorno local con conexión real NeonDB Postgres:

| # | Prueba | Tipo | Resultado |
|---|---|---|---|
| T01 | `python manage.py check` | Django system | ✅ System check identified no issues |
| T02 | `makemigrations geo` + `migrate` | NeonDB | ✅ 0001_initial OK 4 tablas |
| T03 | `makemigrations billing` + `migrate` | NeonDB | ✅ 0003_plan_extendido OK 14 campos + M2M |
| T04 | `makemigrations businesses` + `migrate` | NeonDB | ✅ 0003_negocio_onboarding OK 6 flags |
| T05 | `python manage.py seed_geo --reset` | Seed | ✅ 16 regiones, 56 provincias, 346 comunas |
| T06 | `python manage.py seed_rubros --reset` | Seed | ✅ 41 rubros (31 físicos + 1 online + 9 mixtos + "Otro") |
| T07 | `python manage.py seed_demo --reset` | Seed demo | ✅ 4 usuarios + 4 planes MVP+3 reales + 1 negocio Café Centro Demo p1/p2/p3 flags marcados |
| T08 | `GET /admin/` (usuario admin@clientbeat.cl no super) | RBAC | ✅ Bloqueado redirige /admin-panel/ + PermissionDenied (FASE0 mantenida) |
| T09 | `GET /admin-panel/planes/` (admin@clientbeat.cl) | CRUD list | ✅ Renderiza 4 planes tabla OK + KPIs |
| T10 | Marcar default plan Básico (POST /marcar-default/) | Transacción | ✅ MVP default→False, Básico default→True (único) |
| T11 | Intentar desactivar Básico (actualmente default) | Regla | ✅ messages.error + NO toggle (activo sigue True) |
| T12 | Editar Profesional max_preguntas → 10 | Validation | ✅ Guardar OK + BD persiste 10 |
| T13 | Crear nuevo plan con `tiene_encuestas_custom=True max_preg=0` | Validation | ✅ PlanForm.clean() ValidationError "max_preg debe ser > 0" |
| T14 | Guardar plan con `tiene_encuestas_custom=False max_preg=7` | Validation | ✅ Guarda OK, setea internamente max_preg=0 |
| T15 | `dueno@negociodemo.cl` login | Dashboard | ✅ Redirect a `/dashboard/` (paso3 flag=True), sin onboarding. |

### 8.1 Comprobación query NeonDB flags onboarding demo
```sql
SELECT nombre, onboarding_paso1_completo, onboarding_paso2_completo, onboarding_paso3_completo, onboarding_fecha_paso3
FROM businesses_negocio WHERE nombre = 'Café del Centro Demo';
```
Resultado:
```
nombre                  | p1  | p2  | p3  | fecha_paso3
Café del Centro Demo    | t   | t   | t   | 2026-08-17 00:00:00
```
✅ Negocio demo con flags paso3 completos consistente con suscripción MVP activa 365 días.

---

## 9. ENTREGABLES PROTEGIDOS / MANTENIDOS FASE 0

| Componente | Estado FASE1 |
|---|---|
| `/admin/` raw solo superuser (`SuperUserOnlyAdminMixin` global `core/admin.py`) | ✅ Mantenido sin cambios |
| `apps/adminpanel/apps.py` → `default_admin_site.__class__` reemplazado | ✅ Mantenido sin cambios |
| `ADMIN_SOPORTE` permiso is_staff + `AdminSoporteRequiredMixin` | ✅ Mantenido sin cambios |
| Contraseñas demo `ClienBeat2026!` | ✅ Mantenido sin cambios |
| UI glass-effect sidebar 8 módulos | ✅ Planes = módulo 3 totalmente funcional (era placeholder) |

---

## 10. ACCESOS RÁPIDOS (servidor levantado 0.0.0.0:8000)
| Ruta | Usuario demo | Contraseña |
|---|---|---|
| **Panel Admin ClienBeat (no técnico)** → `/admin-panel/` | `admin@clientbeat.cl` | `ClienBeat2026!` |
| **Django Admin raw (solo SuperUser)** → `/admin/` | `super@clientbeat.cl` | `ClienBeat2026!` |
| **Dashboard Dueño Demo** → `/dashboard/` | `dueno@negociodemo.cl` | `ClienBeat2026!` |
| **Login Cliente Dueño** → `/accounts/login/` | `usuario.equipo@negociodemo.cl` | `ClienBeat2026!` |

---

## 11. SIGUIENTES FASES PROPUESTAS (fuera alcance FASE1)

Entregables técnicos listos para FASE2 a 5 según plan maestro:
- **FASE 2:** Rubro selector dropdown onboarding paso2 (comuna + rubro provenientes de `apps.geo.Rubro` + geografía).
- **FASE 3:** Suscripción Flow integración (pago con Flow Chile usando Plan `desglose_mensual()` por locales/rubros extras).
- **FASE 4:** Encuestas custom (5 preguntas máximo Plan Profesional, `max_preguntas_encuesta_custom`).
- **FASE 5:** Benchmarking por rubro (flag `tiene_benchmarking_rubro` Plan Empresarial/Profesional).

**Fin informe FASE 1 ClienBeat SpA.**
