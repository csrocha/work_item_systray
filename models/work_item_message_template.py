# -*- coding: utf-8 -*-
from odoo import fields, models


class WorkItemMessageTemplate(models.Model):
    _name = 'work.item.message.template'
    _description = 'Plantilla de mensaje de inicio/cierre de work item (systray)'
    _order = 'direction, sequence, id'

    name = fields.Char(required=True, string='Texto')
    direction = fields.Selection([
        ('enter', 'Al entrar'),
        ('leave', 'Al salir'),
    ], required=True)
    requires_detail = fields.Boolean(
        string='Requiere detalle',
        help='Si está marcado, se espera que el usuario complete el texto '
             'libre además de elegir esta plantilla (ej. "Se bloqueó porque: ___").',
    )
    sets_blocked = fields.Boolean(
        string='Marca el work item como bloqueado',
        help='Solo aplica a plantillas "Al salir". Cada proveedor decide qué '
             'significa "bloqueado" para su propio modelo (p. ej. '
             'project.task.blocked = True) dentro de su _work_item_close. '
             'No hay opción de "desbloquear" acá porque retomar un work item '
             'activamente ya lo desbloquea.')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
