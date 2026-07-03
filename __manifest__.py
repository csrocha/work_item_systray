# -*- coding: utf-8 -*-
{
    'name': "Work Item Systray",
    'summary': "Cronómetro y cambio de work item activo (base genérica, sin project ni helpdesk)",
    'version': '17.0.1.0.0',
    'category': 'Productivity',
    'author': "Cristian S. Rocha <csrocha@gmail.com>",
    'website': "https://github.com/csrocha/work_item_systray",
    'license': 'OPL-1',
    'depends': ['base', 'bus'],
    'data': [
        'security/ir.model.access.csv',
        'security/work_item_session_security.xml',
        'views/work_item_message_template_views.xml',
        'views/work_item_session_switch_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'work_item_systray/static/src/**/*',
        ],
    },
    'installable': True,
    'application': False,
}
