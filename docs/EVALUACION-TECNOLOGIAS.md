# Evaluación de tecnologías

Fecha: 2026-10-05. Las versiones "actuales" se verificaron ese día en PyPI, npm, nodejs.org y endoflife.date. Las vulnerabilidades, en api.osv.dev.

Criterios, en orden: (1) que 4 estudiantes lo terminen en el curso, (2) que funcione bien en el celular, (3) que tenga mantenimiento activo, (4) costo y despliegue, (5) curva de aprendizaje.

## 1. Tabla pieza por pieza

| Pieza | Actual (repo) | Propuesta | Decisión | Razón |
|---|---|---|---|---|
| Python | 3.12 | 3.12 | **Mantener** | Soportado hasta 2028-10. Es la versión de la imagen `slim` y del CI. Subir a 3.13 no aporta nada al proyecto. |
| FastAPI | 0.115.0 | 0.142.x | **Actualizar** | 0.115.0 obliga a usar starlette <0.39, que tiene 14 avisos de seguridad (ver AUDITORIA C4). |
| Uvicorn | 0.30.6 | 0.54.x | **Actualizar** | Mantenimiento al día. |
| SQLAlchemy | 2.0.35, estilo `Column` + `db.query` | 2.1.x, estilo `Mapped[]` + `select()`, **síncrono** | **Actualizar** | 2.1 requiere Python ≥3.11 (cumple). El estilo tipado da autocompletado y menos errores. Se usa **sync**: async le duplica la dificultad al equipo y un colmado no necesita esa concurrencia. |
| Alembic | 1.13.2 | 1.20.x | **Actualizar** | Agrega `alembic check` para detectar desfases entre modelo y BD en el CI. |
| Driver PostgreSQL | psycopg2-binary 2.9.9 | psycopg[binary] 3.3.x | **Cambiar** | psycopg 3 es la línea activa. El cambio es una línea: `postgresql+psycopg://` en la URL. Permite quitar `gcc` y `libpq-dev` del Dockerfile. |
| Pydantic | 2.9.2 | 2.13.x + `pydantic[email]` | **Actualizar** | Ya es v2. Hay que pasar `class Config` a `model_config` y agregar `EmailStr`. |
| pydantic-settings | 2.5.2 | 2.15.x | **Actualizar** | — |
| JWT | python-jose 3.3.0 (+ecdsa) | **PyJWT 2.15.x** | **Cambiar** | python-jose tiene 6 avisos y su dependencia ecdsa tiene un timing attack sin parche. PyJWT es lo que usa hoy la documentación oficial de FastAPI. El código cambia en 2 líneas (`import jwt`, `jwt.InvalidTokenError`). |
| Hash de contraseñas | passlib 1.7.4 + bcrypt 4.0.1 fijado | **pwdlib[argon2] 0.3.x** | **Cambiar** | passlib está abandonado (última versión de 2020) y obliga a fijar bcrypt viejo. pwdlib es lo que recomienda la documentación de FastAPI. Como no hay usuarios reales, no hace falta migrar hashes. |
| python-multipart | 0.0.9 | 0.0.32 | **Actualizar** | 16 avisos. Lo necesita el formulario OAuth2 del login. |
| python-dotenv | 1.0.1 fijado | quitar del `requirements.txt` | **Descartar pin** | pydantic-settings ya lo instala como dependencia propia. Fijarlo a mano dejó una versión vulnerable. |
| pytest / httpx / ruff | sin versión, en requirements de producción | `requirements-dev.txt` con versiones fijadas (pytest 9.1, ruff 0.16, **httpx2** porque Starlette 1.x marcó `httpx` como obsoleto en su cliente de tests) | **Mantener, ordenar** | Son buenas herramientas. Solo hace falta separarlas de producción y fijar versiones. |
| PostgreSQL | 16 | **17** | **Actualizar** | 16 está soportado hasta 2028, pero el proyecto arranca sin datos. 17 tiene soporte hasta 2029-11 y usa la misma ruta de volumen. 18 cambia la ruta del volumen en la imagen oficial, un tropiezo innecesario para el equipo. |
| Angular | (no existe) | **Angular 22**, standalone components + signals | **Adoptar** | v22 es la versión activa (soporte hasta 2027-06, LTS hasta 2028-06). Standalone y signals son el estándar actual: no requieren NgModules y tienen menos boilerplate. |
| Node.js | (no existe) | **24 LTS** | **Adoptar** | Angular 22 exige `^22.22.3 \|\| ^24.15.0 \|\| >=26`. Node 24 es el LTS vigente (hasta 2028-04). Node 26 pasa a LTS el 2026-10-28: se puede subir después, sin urgencia. |
| Librería de UI | "Material o PrimeNG" | **Angular Material 22** | **Decidir: Material** | Ver §2. |
| PWA | — | `ng add @angular/pwa` | **Adoptar** | Permite instalar la app en el celular desde el navegador, sin tienda. Es un comando. |
| WhatsApp | "Twilio o Meta", `WHATSAPP_PROVIDER=twilio` en `.env.example` | **WhatsApp Cloud API (Meta) directa** | **Decidir: Meta** | Ver §3. Es la decisión de mayor riesgo. |
| Scheduler de avisos | — | **Script + cron** | **Adoptar** | Ver §4. |
| Docker / Compose | compose con `db` + `backend` | igual, corregido (ver AUDITORIA I11/I12) + servicio `frontend` (nginx) | **Mantener** | Le sirve al equipo y al despliegue. |
| GitHub Actions | lint + tests (rotos) | ver §5 | **Mantener, arreglar** | — |
| dbdiagram.io (DBML + PNG) | `docs/` | igual | **Mantener** | Le da al equipo una fuente de verdad visual del modelo. |
| Despliegue | no definido | 1 VPS pequeño con `docker compose` (o una plataforma con cron incluido) | **Proponer** | Un solo servidor barato aloja BD, API y frontend estático. Evita pagar servicios separados. |

## 2. Angular Material vs PrimeNG

| Criterio | Angular Material 22 | PrimeNG 22 |
|---|---|---|
| Mantenimiento | Lo hace el equipo de Angular. Sale el mismo día que Angular (ambos 22.2.1) | Lo hace PrimeTek. Va detrás de cada major de Angular (`peer ^22.1.0`) |
| Móvil | Componentes táctiles, accesibles, livianos, tipografía y espaciado pensados para móvil | Más componentes y más pesados. Varias tablas y overlays están pensados primero para escritorio |
| Tablas | `mat-table` + `MatPaginator` + `MatSort`: el filtrado se arma a mano (poco código) | `p-table` trae filtros, paginación, orden y exportación listos |
| Formularios | Reactive Forms + `mat-form-field`, bien documentado | Equivalente |
| Estabilidad entre versiones | Alta | Históricamente rompe temas y APIs entre majors |
| Curva | Baja: la misma documentación de angular.dev | Media |

**Decisión (opinión): Angular Material.**
- La prioridad es el celular y que el equipo termine a tiempo.
- El POS y el fiao son pantallas de listas y botones grandes, no grillas de escritorio.
- La única ventaja clara de PrimeNG, `p-table`, pesa solo en Reportes, y ahí `mat-table` con un filtro de texto alcanza.

## 3. Twilio vs WhatsApp Business Cloud API (Meta)

Contexto:
- Los recordatorios de deuda son **plantillas de categoría "utility"**, enviadas fuera de la ventana de 24 h porque el cliente no escribió antes.
- Con cualquiera de los dos proveedores, **Meta tiene que aprobar la plantilla** y **cobra el mensaje**.
- Desde el **2026-10-01**, Meta también cobra las plantillas utility enviadas dentro de una ventana abierta, que antes eran gratis.

| Criterio | Twilio | Meta Cloud API directa |
|---|---|---|
| Costo por mensaje | Tarifa de Meta **+ USD 0.005 de Twilio** por mensaje, entrante o saliente | Solo la tarifa de Meta según categoría y país. Para RD hay que consultar la tabla oficial de Meta (no se encontró una cifra confiable para "Rest of Latin America") |
| Pruebas | Sandbox inmediato: el teléfono se une con un código, sin aprobar plantillas | Número de prueba gratis de Meta con hasta 5 destinatarios verificados. Alcanza para el curso |
| Aprobación de plantillas | La tramita Meta a través de Twilio | Se tramita en WhatsApp Manager |
| Verificación para producción | Registrar el número del negocio vía Twilio, más la verificación de Meta | Cuenta de Meta Business, verificación del negocio y número propio |
| Integración | SDK `twilio` | Un `POST` HTTPS con `httpx` (ya está en el proyecto), sin SDK |
| Dependencia extra | Sí (cuenta Twilio y facturación aparte) | No |

**Decisión (opinión): Meta Cloud API directa.**
- No paga el recargo de Twilio, que en un negocio que no paga mucho importa.
- No agrega otro proveedor ni otro SDK.
- El número de prueba gratis cubre las demos del curso.

**Mitigación del riesgo:**
- Todo envío pasa por **una sola función** en `services/whatsapp_service.py`: `enviar_recordatorio(telefono, nombre, saldo)`. Si Meta se traba, cambiar a Twilio toca un solo archivo.
- Pedir la aprobación de la plantilla **en la primera semana del módulo Fiao**, porque es la ruta crítica.
- Guardar el consentimiento del cliente (opt-in) en `clientes`.

## 4. Tareas programadas (aviso de deuda)

| Opción | Evaluación |
|---|---|
| Celery + Redis/RabbitMQ | ❌ Descartar: dos servicios más para un solo trabajo diario |
| APScheduler dentro de FastAPI | ⚠️ Corre una vez por cada worker de uvicorn: con 2 workers se envían avisos duplicados. Solo sirve con exactamente 1 worker |
| **Script + cron** | ✅ **Elegido.** `python -m app.tareas.recordatorios` lo dispara el cron del host (o el cron de la plataforma) una vez al día |

- **Para evitar envíos duplicados:** el script registra cada envío en la tabla `recordatorios_whatsapp` y no reenvía a un cliente dentro de N días. Así también se puede correr a mano en las demos.

## 5. CI/CD: qué sí y qué no

| Sí correr | Por qué |
|---|---|
| `ruff check` + `ruff format --check` (backend) | Rápido, atrapa errores reales |
| `pytest` con un servicio `postgres:17` en el job | Las reglas de negocio (stock, límite de crédito, abonos) viven en la BD |
| `alembic upgrade head` + `alembic check` | Detecta migraciones rotas, múltiples `heads` entre los 4 integrantes y desfases entre modelo y BD |
| `ng build` (+ `ng test` cuando haya tests) | Que el frontend compile en cada PR |
| Dependabot semanal (pip, npm, actions) | Evita volver a quedar con dependencias vulnerables. Es un archivo YAML |

| Exagerado para este proyecto | Por qué |
|---|---|
| Matrices de versiones, umbrales de cobertura, tests E2E con navegador | Mucho mantenimiento para 4 estudiantes |
| Publicar imágenes en un registry y despliegue automático | Bastan `git pull` + `docker compose up -d --build` en el VPS |
| La rama `develop` | No existe. Con PR hacia `main` es suficiente |

## 6. Auth: JWT casero vs librería

- **Opinión:** el JWT "casero" del repo son 7 líneas sobre una librería (`security.py`), y está bien. No vale la pena meter fastapi-users ni Keycloak: es más que aprender y más difícil de depurar.
- **Cambiar:** python-jose → PyJWT, y passlib → pwdlib (§1).
- **Token:** un access token **sin refresh**, con vida de **12 h** (una jornada del colmado), `sub = id_usuario` y un claim `rol`.
- **Dónde guardarlo en el frontend:** `localStorage` + interceptor de Angular, para que la PWA no pida login cada vez que se abre en el celular.
  - **Límite conocido:** un XSS podría leerlo. Angular escapa el HTML por defecto, y no se debe usar `innerHTML` con datos de usuarios.
  - **Mejora futura:** pasar a cookie `httpOnly` + `SameSite=Strict` si API y frontend quedan en el mismo dominio.

## 7. Tecnologías del repo viejo que no están en el stack vigente

| Tecnología | Decisión |
|---|---|
| ruff | **Adoptar** (lint y formato) |
| pytest + httpx | **Adoptar** |
| python-jose, passlib | **Descartar** (reemplazadas, §1) |
| psycopg2 | **Reemplazar** por psycopg 3 |
| python-dotenv como pin directo | **Descartar** (viene con pydantic-settings) |
| dbdiagram.io | **Adoptar** para documentar el modelo |

## Fuentes

- PyPI JSON API (`pypi.org/pypi/<paquete>/json`), npm registry, `nodejs.org/dist/index.json`, `endoflife.date/api/{python,postgresql,angular,nodejs}.json`, `api.osv.dev/v1/querybatch` (consultados el 2026-10-05).
- [Twilio – WhatsApp pricing](https://www.twilio.com/en-us/whatsapp/pricing)
- [Zenvia – New WhatsApp Business pricing rules for 2026](https://zenvia.com/en/new-whatsapp-business-pricing-rules-for-2026/)
- [Blueticks – WhatsApp pricing categories 2026](https://blueticks.co/blog/whatsapp-business-pricing-categories-2026-utility-marketing-authentication)
- [Landbot – Twilio WhatsApp pricing 2026](https://landbot.io/blog/twilio-whatsapp-pricing)
- Tabla oficial de tarifas de Meta: developers.facebook.com → WhatsApp Business Platform → Pricing. **Pendiente: confirmar ahí la tarifa utility para República Dominicana.**
