# -*- coding: utf-8 -*-
from odoo import api, models


class WorkItemMixin(models.AbstractModel):
    _name = 'work.item.mixin'
    _description = 'Contrato de work item trabajable desde el Work Item Systray'

    def _work_item_label(self):
        """dict {name, icon, css_class, description, **extra} para mostrar
        este registro como work item activo en el systray. Default: nombre
        del registro, sin decoración. Los proveedores pueden agregar claves
        propias (p. ej. allocated_hours/remaining_hours) que el core ignora
        y que solo consume el JS del propio proveedor."""
        self.ensure_one()
        return {
            'name': self.display_name,
            'icon': '',
            'css_class': '',
            'description': '',
        }

    def _work_item_close(self, start_datetime, intent_note, outcome_note, outcome_blocked):
        """Qué hacer cuando termina un período activo sobre este registro
        (registrar horas, postear en el chatter, etc). Default: no-op."""
        self.ensure_one()

    @api.model
    def _work_item_candidates(self):
        """Mis work items disponibles para elegir, para el usuario actual:
        lista de dicts {res_id, name, icon, css_class}. Default: []."""
        return []
