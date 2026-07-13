# BACKLOG

Ideas y mejoras propuestas para `work_item_systray` que todavía no se
implementaron. Primer archivo de este tipo para este módulo (mismo
formato que `insight_project/BACKLOG.md`).

---

## Del backlog de ecosistema (2026-07-13)

Propuesta de "nivel profesional superior" para todo el ecosistema. Visión
completa en la memoria `project_ecosystem_roadmap`.

### 1. Unificar `_html_to_text()` duplicada entre proveedores

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
