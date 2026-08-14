# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import _, api, fields, models

POMODORO_ACTIVE_MINUTES = 25
POMODORO_GRACE_MINUTES = 5


class WorkItemSession(models.Model):
    _name = 'work.item.session'
    _description = 'Sesión activa de work item (systray)'

    user_id = fields.Many2one(
        'res.users', required=True, default=lambda self: self.env.user, index=True,
    )
    state = fields.Selection(
        [('active', 'Trabajando'), ('break', 'Descanso')],
        default='break', required=True,
    )
    start_datetime = fields.Datetime(default=fields.Datetime.now)
    pomodoro_deadline = fields.Datetime(
        string='Vencimiento del pomodoro activo',
        help='Cuándo termina el período activo de 25\' y empieza a titilar '
             'pidiendo confirmación. Separado de start_datetime para que '
             'confirmar "seguir" no fragmente el período real de trabajo.',
    )
    intent_note = fields.Text(
        string='Qué se va a hacer',
        help='Lo que el usuario dijo que iba a hacer en work_item_ref al '
             'empezar este período; cada proveedor decide cómo usarlo al '
             'cerrar el período (ver el contrato _work_item_close en el '
             'README de este addon).',
    )
    work_item_ref = fields.Reference(
        selection='_selection_work_item_models', string='Work item activo',
    )

    _sql_constraints = [
        ('user_uniq', 'unique(user_id)', 'Cada usuario tiene una única sesión activa.'),
    ]

    @api.model
    def _selection_work_item_models(self):
        return [
            (model_name, self.env['ir.model']._get(model_name).name)
            for model_name in self._get_work_item_provider_models()
        ]

    def _get_work_item_provider_models(self):
        """Modelos instalados que implementan el contrato de work item,
        descubiertos vía el registry por duck typing: cualquier modelo con
        el atributo de clase `_work_item_provider = True`.

        No se usa `_inherit` de un AbstractModel mixin a propósito: combinar
        una clase con `_inherit = ['project.task', 'work.item.mixin']' (o
        equivalente sobre helpdesk.ticket) dispara, en algunas imágenes de
        Odoo, un bug de setup de Many2many cuando el modelo ya tiene un
        campo M2M sobreescrito de forma implícita por otro addon (p. ej.
        project_enterprise redeclarando `user_ids` sin repetir su relación).
        El duck typing por atributo de clase logra el mismo descubrimiento
        sin pasar por esa combinación de herencia."""
        return [
            model_name for model_name, model_cls in self.env.registry.items()
            if getattr(model_cls, '_work_item_provider', False)
        ]

    @api.model
    def _get_or_create_for_user(self):
        session = self.search([('user_id', '=', self.env.uid)], limit=1)
        if not session:
            session = self.create({})
        return session

    @api.model
    def get_systray_state(self):
        return self._get_or_create_for_user().get_systray_data()

    @api.model
    def action_switch_work_item(self, model, res_id, outcome_note=None, outcome_blocked=None, intent_note=None):
        session = self._get_or_create_for_user()
        session.switch_work_item(
            model, res_id, outcome_note=outcome_note,
            outcome_blocked=outcome_blocked, intent_note=intent_note,
        )
        return session.get_systray_data()

    @api.model
    def action_take_break(self, outcome_note=None, outcome_blocked=None):
        session = self._get_or_create_for_user()
        session.take_break(outcome_note=outcome_note, outcome_blocked=outcome_blocked)
        return session.get_systray_data()

    @api.model
    def action_confirm_pomodoro(self):
        session = self._get_or_create_for_user()
        session.confirm_pomodoro()
        return session.get_systray_data()

    def switch_work_item(self, model, res_id, outcome_note=None, outcome_blocked=None, intent_note=None):
        """Cierra el período activo (si existe) y abre uno nuevo sobre
        model,res_id (con la nota de intención)."""
        self.ensure_one()
        self._close_active_period(outcome_note, outcome_blocked)
        self.write({
            'work_item_ref': f'{model},{res_id}',
            'start_datetime': fields.Datetime.now(),
            'state': 'active',
            'intent_note': intent_note or False,
            'pomodoro_deadline': fields.Datetime.now() + timedelta(minutes=POMODORO_ACTIVE_MINUTES),
        })
        activate = getattr(self.work_item_ref, '_work_item_activate', None)
        if activate:
            activate()
        self._notify_systray()

    def take_break(self, outcome_note=None, outcome_blocked=None):
        """Cierra el período activo (si existe) y pasa a estado Descanso."""
        self.ensure_one()
        self._close_active_period(outcome_note, outcome_blocked)
        self.write({
            'work_item_ref': False,
            'start_datetime': fields.Datetime.now(),
            'state': 'break',
            'intent_note': False,
            'pomodoro_deadline': False,
        })
        self._notify_systray()

    def confirm_pomodoro(self):
        """Empuja pomodoro_deadline otros 25' sin tocar start_datetime — a
        diferencia de switch_work_item/take_break, que sí cierran y abren
        períodos, confirmar que se sigue trabajando en lo mismo no debe
        ensuciar el historial que consume _work_item_close con
        sub-períodos artificiales cada 25 minutos."""
        self.ensure_one()
        if self.state != 'active':
            return
        self.pomodoro_deadline = fields.Datetime.now() + timedelta(minutes=POMODORO_ACTIVE_MINUTES)
        self._notify_systray()

    @api.model
    def _cron_close_expired_pomodoros(self):
        """Backstop server-side: si el margen de gracia titilando venció
        sin confirmación (pestaña cerrada, laptop suspendida — el
        setInterval client-side nunca llega a correr), cierra la sesión
        igual que un take_break manual."""
        limit = fields.Datetime.now() - timedelta(minutes=POMODORO_GRACE_MINUTES)
        expired = self.search([
            ('state', '=', 'active'),
            ('pomodoro_deadline', '!=', False),
            ('pomodoro_deadline', '<', limit),
        ])
        for session in expired:
            session.take_break(outcome_note=_('En descanso pomodoro, sin continuar'))

    def _notify_systray(self):
        """Empuja el nuevo estado por el bus para que el widget del systray
        del propio usuario se refresque sin recargar la página."""
        self.ensure_one()
        self.env['bus.bus']._sendone(
            self.user_id.partner_id, 'work_item_systray.session_updated', self.get_systray_data()
        )

    def _close_active_period(self, outcome_note=None, outcome_blocked=None):
        """Delega en el work item activo (si lo hay) cómo registrar el
        trabajo hecho durante el período que se cierra."""
        self.ensure_one()
        if self.state != 'active' or not self.work_item_ref or not self.start_datetime:
            return
        self.work_item_ref._work_item_close(
            self.start_datetime, self.intent_note, outcome_note, outcome_blocked,
        )

    def get_systray_data(self):
        """Estado actual + work items disponibles para el widget del systray."""
        self.ensure_one()
        label = self.work_item_ref._work_item_label() if self.work_item_ref else {
            'name': _('Sin actividad'), 'icon': '', 'css_class': '', 'description': '',
        }
        data = {
            'state': self.state,
            'work_item_model': self.work_item_ref._name if self.work_item_ref else False,
            'work_item_id': self.work_item_ref.id if self.work_item_ref else False,
            'start_datetime': fields.Datetime.to_string(self.start_datetime) if self.start_datetime else False,
            'pomodoro_deadline': fields.Datetime.to_string(self.pomodoro_deadline) if self.pomodoro_deadline else False,
            'work_items': self._get_switchable_work_items(),
        }
        data.update(label)
        return data

    def _get_switchable_work_items(self):
        """Combina los candidatos de todos los proveedores instalados, sin
        duplicados (mismo model+res_id, por si dos proveedores llegaran a
        coincidir), con las tareas de hoy (date_deadline == hoy) primero y
        el resto ordenado por prioridad — el resto de items sin
        date_deadline (p. ej. tickets de helpdesk) cae directo en el grupo
        'resto', también ordenado por prioridad."""
        today = fields.Date.to_string(fields.Date.context_today(self))
        seen = set()
        items = []
        for model_name in self._get_work_item_provider_models():
            for candidate in self.env[model_name]._work_item_candidates():
                candidate = dict(candidate)
                candidate.setdefault('model', model_name)
                key = (candidate['model'], candidate['res_id'])
                if key in seen:
                    continue
                seen.add(key)
                candidate['is_today'] = candidate.get('date_deadline') == today
                items.append(candidate)
        items.sort(key=lambda it: (not it['is_today'], -int(it.get('priority') or 0)))
        return items
