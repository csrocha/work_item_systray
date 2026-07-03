# Work Item Systray

Addon base y genérico de Odoo 17: un cronómetro de systray que encasilla al
usuario en un único "work item" activo por vez ("trabajando" / "descanso") y
deja cambiar de work item con notas de inicio/cierre.

No sabe nada de `project.task`, `helpdesk.ticket` ni de ningún otro modelo de
dominio — no depende de `project` ni de `helpdesk`. Cualquier modelo se
vuelve elegible como work item implementando el contrato `work.item.mixin`:

```python
class MyDomainModel(models.Model):
    _inherit = ['my.domain.model', 'work.item.mixin']

    def _work_item_label(self):
        # dict {name, icon, css_class, description, **extra} para mostrarlo activo
        ...

    def _work_item_close(self, start_datetime, intent_note, outcome_note, outcome_blocked):
        # qué hacer cuando termina un período activo sobre este registro
        ...

    def _work_item_candidates(self):
        # lista de dicts {res_id, name, icon, css_class} para el usuario actual
        ...
```

`work.item.session` descubre en runtime, vía el registry de Odoo, qué
modelos implementan el mixin — ningún addon proveedor toca `work.item.session`
directamente.

El cronómetro del systray **siempre cuenta hacia adelante** por defecto. Los
proveedores que quieran cuenta regresiva (p. ej. contra un presupuesto de
horas) lo hacen parcheando `_tick()` del componente OWL desde su propio addon
(ver `work_item_task`).

Proveedores conocidos: [`work_item_task`](https://github.com/csrocha/work_item_task)
(tareas de `project`), [`work_item_helpdesk`](https://github.com/csrocha/work_item_helpdesk)
(tickets de `helpdesk`).

## License

OPL-1 — Cristian S. Rocha <csrocha@gmail.com>
