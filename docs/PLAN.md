# Plan de trabajo (2 personas)

Actualizado el 2026-10-05. El proyecto arrancó desde cero; el código viejo de SysCol se borró.
`AUDITORIA.md`, `EVALUACION-TECNOLOGIAS.md`, `REUSO.md` y `PLAN-MIGRACION.md` quedan como registro de la auditoría y de las decisiones. **Este archivo es el plan vigente.**

## Decisiones tomadas

| Tema | Decisión |
|---|---|
| Varios colmados | Sí: tabla `negocios` + `id_negocio` en las tablas raíz |
| WhatsApp | Cloud API de Meta, directa (sin Twilio) |
| UI | Angular Material + PWA |
| Roles | `dueno` (todo) y `cajero` (vender, cobrar) |
| Compras y proveedores | Fuera del MVP. Se hacen al final si sobra tiempo |

## Ya hecho (base)

- [x] Docker Compose (db + backend + frontend con nginx), migraciones automáticas al arrancar
- [x] CI: ruff, `alembic check`, una sola cabeza de migraciones, pytest con Postgres, build y tests de Angular
- [x] Modelo de datos completo en la migración `0001` (11 tablas con CHECK, FK e índices) → `docs/modelo-datos.dbml`
- [x] Auth: login JWT, `/me`, el dueño crea usuarios, `requiere_rol()`, usuarios inactivos bloqueados
- [x] Script `crear_negocio` para dar de alta un colmado con su dueño
- [x] Frontend: login, guard, interceptor (token + cierre de sesión con 401), inicio, PWA

## Reparto

| Persona A | Persona B |
|---|---|
| 1. **Inventario**: CRUD de categorías y productos, búsqueda por nombre o código de barras, `GET /productos/bajo-stock` | 1. **Clientes**: CRUD con `limite_credito`, `telefono` y `acepta_whatsapp` |
| 2. **Ventas/POS**: `services/ventas_service.py` y la pantalla del carrito | 2. **Fiao**: `services/fiao_service.py` (deudas, abonos, límite de crédito) |
| 3. **Reportes**: ventas por período, más vendidos, ganancia | 3. **WhatsApp**: servicio + cron de recordatorios |

**Hoy mismo (Persona B):**
- Crear la cuenta de Meta Business y la app de WhatsApp.
- Pedir la aprobación de la plantilla `recordatorio_deuda`.

La aprobación tarda y bloquea el paso B3.

## Contrato entre los dos

- La venta al fiao la registra A (`ventas_service`). La deuda la crea una función de B: `fiao_service.crear_deuda(db, venta)`, que lanza un error si el cliente pasa su límite. A la llama dentro de la misma transacción.
- Hasta que B la termine, A puede usar una versión mínima que solo inserte la deuda.

## Reglas de negocio que no se pueden olvidar

**Venta** (una sola transacción):
1. Bloquea los productos (`SELECT … FOR UPDATE`).
2. Valida el stock.
3. Congela `precio_unitario`.
4. Descuenta el stock.
5. Calcula el total **en el servidor**.
6. Si es fiao, crea la deuda.

**Anular una venta:** devuelve el stock. Si era fiao, solo se puede anular si la deuda no tiene abonos.

**Abono:**
1. Bloquea la deuda.
2. Rechaza el abono si el `monto` es mayor que el saldo.
3. Inserta el abono y baja `saldo_pendiente` en la misma transacción.

**Estado de la deuda** (se calcula, no se guarda):

| Estado | Condición |
|---|---|
| `pagada` | saldo = 0 |
| `vencida` | saldo > 0 y `fecha_limite` < hoy |
| `parcial` | saldo < total |
| `pendiente` | cualquier otro caso |

**Recordatorio de WhatsApp:**
- Solo a clientes con `acepta_whatsapp` y con deuda vencida (o de más de N días).
- Nunca dos avisos de la misma deuda en menos de N días (se revisa `recordatorios_whatsapp`).
- Se corre una vez al día:

```bash
docker compose exec -T backend python -m app.tareas.recordatorios
```
Esa línea va en el cron del servidor.

## Pendiente para más adelante

- Variables de WhatsApp en `.env.example` (`WHATSAPP_TOKEN`, `WHATSAPP_PHONE_ID`): se agregan con el paso B3.
- Despliegue: un VPS con `docker compose up -d` y HTTPS (Caddy). Quitar el puerto `55432` del compose de producción.
- Pasar el token a cookie `httpOnly` si da tiempo (ver EVALUACION §6).
