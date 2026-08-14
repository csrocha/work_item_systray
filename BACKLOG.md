# BACKLOG

Ideas y mejoras propuestas para `work_item_systray` que todavía no se
implementaron. Primer archivo de este tipo para este módulo (mismo
formato que `insight_project/BACKLOG.md`).

---

## Del backlog de ecosistema (2026-07-13)

Propuesta de "nivel profesional superior" para todo el ecosistema. Visión
completa en la memoria `project_ecosystem_roadmap`.

### ~~1. Unificar `_html_to_text()` duplicada entre proveedores~~ — RESUELTO

Resuelto (2026-07-18): la función se movió a `work_item_systray/utils.py`
(`html_to_text`), agregado a `__init__.py` (`from . import utils`, mismo
patrón ya usado en `fop_odoo_chart/utils/`). `work_item_task/models/
project_task.py` y `work_item_helpdesk/models/helpdesk_ticket.py` ahora
importan `from odoo.addons.work_item_systray.utils import html_to_text as
_html_to_text` — ambos ya dependían de `work_item_systray` en su
manifest, no hizo falta agregar dependencia nueva.
`work_item_enterprise_task` no tenía copia propia, no se tocó. Verificado
que `work_item_task` y `work_item_helpdesk` siguen instalando limpio
(`make test-local`, 0 tests/0 fallos en ambos — ninguno tiene tests
automatizados sobre esta función).

Confirmado por auditoría de código (2026-07-13):
`_html_to_text(html_value, max_len=280)` está copiada byte a byte entre
`work_item_task/models/project_task.py:12` y
`work_item_helpdesk/models/helpdesk_ticket.py:11` — mismo regex, misma
lógica, como función a nivel de módulo (no compartida). `work_item_systray`
es el módulo base del que dependen ambos proveedores (`work_item_task`,
`work_item_helpdesk`, `work_item_enterprise_task`), así que es el lugar
natural para mover esta utilidad antes de que aparezca un tercer
proveedor con la misma necesidad y la copie una vez más.

_Fuente: backlog de ecosistema propuesto por el usuario (2026-07-13,
"Épica 6" ítem 2)._

---

## ~~2. Tareas sin proyecto, "hoy" separado, y sin duplicados~~ — RESUELTO

Resuelto (2026-08-11):

- **Tareas sin proyecto**: verificado que `_work_item_search_week_tasks`
  (`work_item_task/models/project_task.py`) nunca filtró por `project_id`
  — una tarea sin proyecto ya aparecía si cumplía el resto de condiciones
  (asignada al usuario, no cerrada, `date_deadline` en la semana). No
  hacía falta cambiar el dominio; se agregó un test que fija este
  comportamiento como contrato (`work_item_task/tests/
  test_project_task.py::test_candidates_include_tasks_without_project`).
- **Hoy separado + orden por prioridad**: `_get_switchable_work_items`
  (`work_item_systray/models/work_item_session.py`) ahora marca cada
  candidato con `is_today` (comparando `date_deadline` contra
  `fields.Date.context_today`) y ordena `(not is_today, -priority)` —
  hoy primero, dentro de cada grupo por prioridad descendente. Cada
  proveedor pasa a declarar `priority`/`date_deadline` en su candidato
  (`work_item_task/models/project_task.py`,
  `work_item_helpdesk/models/helpdesk_ticket.py` — este último sin
  `date_deadline`, los tickets no tienen ese concepto en el listado, caen
  directo al grupo "resto"). El frontend (`work_item_systray.js`/`.xml`)
  separa la lista en dos secciones ("Hoy"/"Resto") vía los getters
  `todayItems`/`otherItems`.
- **Sin duplicados**: `_get_switchable_work_items` dedupea por clave
  `(model, res_id)` antes de ordenar — defensivo (hoy no hay dos
  proveedores que puedan devolver la misma clave), pero cierra la puerta
  si un futuro proveedor llegara a solaparse.
- Tests nuevos: `work_item_task/tests/test_work_item_session.py`
  (aggregación: hoy-primero, prioridad, dedup, mockeando los candidatos
  para no depender del día de la semana en que corre el test) y
  `work_item_helpdesk/tests/test_helpdesk_ticket.py::
  TestHelpdeskTicketWorkItemCandidates` (prioridad en el candidato de
  ticket). 8/8 tests OK (`make test-local
  MODULE=work_item_task,work_item_helpdesk,work_item_systray`).

_Fuente: pedido del usuario (2026-07-28)._

---

## ~~3. Pomodoro: detectar si el usuario sigue trabajando (2026-08-06)~~ — RESUELTO

Resuelto en v17.0.1.2.0 (2026-08-12): período activo de 25' hardcodeado
(sin configurabilidad, corre para todos los usuarios por defecto —
decisiones confirmadas con el usuario al implementar). Campo
`pomodoro_deadline` en `work.item.session` (separado de `start_datetime`
para no fragmentar el período real), método `confirm_pomodoro()`
(botón "Sí, seguir" en el dropdown del systray, vía
`action_confirm_pomodoro`) que lo empuja 25' más, y
`_cron_close_expired_pomodoros` (cada 1') como backstop server-side que
cierra con `take_break(outcome_note='En descanso pomodoro, sin
continuar')` si vencen los 5' de gracia sin confirmación — cubre el gap
de diseño de que el `setInterval` client-side no alcanza si se cierra la
pestaña o la laptop suspende. El chip del systray titila (CSS
`@keyframes`, nuevo en este addon) desde que vence el deadline hasta que
se confirma o el cron cierra la sesión. 6 tests nuevos en
`work_item_task/tests/test_work_item_session.py::TestPomodoro` (se
prueba ahí y no en `work_item_systray` porque ese módulo base no depende
de ningún proveedor real — mismo motivo que los tests de agregación ya
existentes en ese archivo). 11/11 tests OK (`make test-local
MODULE=work_item_task,work_item_systray`).

Objetivo original: identificar de forma no invasiva si la persona sigue
trabajando en el work item activo, sin vigilar mouse/teclado.

Propuesta funcional: el período activo dura 25 minutos por defecto; al
vencer, el ítem del systray empieza a titilar durante 5 minutos pidiendo
confirmación explícita ("¿seguís?"); si no se confirma en ese margen, el
período se cierra solo, vía el mismo mecanismo que ya usa `take_break()`,
con `outcome_note='En descanso pomodoro, sin continuar'`.

Puntos de diseño a resolver antes de implementar:

- **El cierre real no puede ser solo client-side.** El titileo en OWL es
  la señal de UX, pero si se cierra la pestaña o la laptop suspende, el
  `setInterval` del componente no corre. Se necesita un cron server-side
  (`ir.cron`) como backstop que cierre sesiones `active` con
  `start_datetime` + margen vencido, notificando por el mismo bus
  (`work_item_systray.session_updated`) que ya usa `_notify_systray()`.
- **"Seguir" no debería fragmentar el período de trabajo.** Si cada
  confirmación de las 25' cerrara y reabriera el work item vía
  `switch_work_item`, se ensuciaría el historial que consume
  `_work_item_close` con sub-períodos artificiales cada 25 minutos. Mejor
  un campo/deadline separado de `start_datetime` (p. ej.
  `pomodoro_deadline` en `work.item.session`) que la confirmación
  simplemente empuja hacia adelante, dejando el período real intacto.
- Duración (25') y margen de gracia (5') deberían poder configurarse
  (¿por usuario? ¿por compañía?) en vez de quedar hardcodeados — a
  decidir si vale la pena la complejidad para la v1.
- Evaluar si conviene que sea opt-in (no todos los usuarios van a querer
  que se les corte el work item activo a la fuerza).

_Fuente: pedido del usuario (2026-08-06), a diseñar en detalle más
adelante._
