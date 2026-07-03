# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class WorkItemSessionSwitchWizard(models.TransientModel):
    _name = 'work.item.session.switch.wizard'
    _description = 'Cambiar de work item / tomar descanso (systray) con notas'

    mode = fields.Selection([
        ('switch', 'Cambiar de work item'),
        ('break', 'Tomar descanso'),
    ], default='switch', required=True)

    current_work_item_ref = fields.Reference(
        selection='_selection_work_item_models', string='Work item actual', readonly=True,
        default=lambda self: self._default_session().work_item_ref,
    )
    previous_intent_note = fields.Text(
        string='Dijiste que ibas a hacer', readonly=True,
        default=lambda self: self._default_session().intent_note,
    )
    outcome_template_id = fields.Many2one(
        'work.item.message.template', string='Plantilla de cierre',
        domain=[('direction', '=', 'leave')],
    )
    outcome_text = fields.Text(string='¿Qué se logró?')

    target_ref = fields.Reference(
        selection='_selection_work_item_models', string='Work item a iniciar',
    )
    intent_template_id = fields.Many2one(
        'work.item.message.template', string='Plantilla de inicio',
        domain=[('direction', '=', 'enter')],
    )
    intent_text = fields.Text(string='¿Qué se va a hacer?')

    @api.model
    def _selection_work_item_models(self):
        return self.env['work.item.session']._selection_work_item_models()

    def _default_session(self):
        return self.env['work.item.session']._get_or_create_for_user()

    @api.onchange('outcome_template_id')
    def _onchange_outcome_template_id(self):
        if self.outcome_template_id:
            self.outcome_text = self.outcome_template_id.name

    @api.onchange('intent_template_id')
    def _onchange_intent_template_id(self):
        if self.intent_template_id:
            self.intent_text = self.intent_template_id.name

    def action_confirm(self):
        self.ensure_one()
        session = self._default_session()
        outcome_note = False
        if self.current_work_item_ref:
            outcome_note = (self.outcome_text or '').strip() or False
        outcome_blocked = self.outcome_template_id.sets_blocked or False

        if self.mode == 'break':
            session.take_break(outcome_note=outcome_note, outcome_blocked=outcome_blocked)
            return {'type': 'ir.actions.act_window_close'}

        target = self.target_ref
        if not target:
            raise UserError(_('Elija un work item existente para empezar.'))

        intent_note = (self.intent_text or '').strip() or False
        session.switch_work_item(
            target._name, target.id, outcome_note=outcome_note,
            outcome_blocked=outcome_blocked, intent_note=intent_note,
        )
        return {'type': 'ir.actions.act_window_close'}
