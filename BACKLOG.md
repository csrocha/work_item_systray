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

## 2. Tareas sin proyecto, "hoy" separado, y sin duplicados (2026-07-28)

Pendiente, no implementado.

- Mostrar también las tareas que no tienen proyecto asignado (hoy el
  systray solo lista tareas con proyecto).
- Mostrar aparte las tareas cuya fecha de acción es hoy, separadas del
  resto.
- Evitar tareas duplicadas en el listado.
- Orden esperado: primero las tareas de hoy, luego el resto de las
  tareas con fecha de acción (con y sin proyecto mezcladas), ordenadas
  por prioridad.

_Fuente: pedido del usuario (2026-07-28), a implementar más adelante._
