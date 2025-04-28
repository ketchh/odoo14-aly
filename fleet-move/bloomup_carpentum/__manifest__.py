# -*- coding: utf-8 -*-
{
    'name': "Bloomup Fleet Move Carpentum",
    'summary': """
        Bloomup Fleet Move Carpentum
    """,
    'description': """
        Bloomup Fleet Move Carpentum
    """,
    'author': "Bloomup",
    'website': "http://bloomup.it",
    'category': 'Services/Project',
    'version': '0.1',
    'depends': [
        'base',
        'bloomup_fleet_move',
        'bloomup_fleet_move_arval',
        'bloomup_ipat',
        'netcheck_2'
    ],
    'data': [
        'data/status.xml',
        'views/config.xml',
        'views/partner.xml',
        'views/fleetmove.xml',
        'views/hub.xml',
        'views/status.xml',
        'views/task.xml',
        'views/assets.xml',
        'views/cron.xml',
        'views/checklist.xml',
        'data/mail_template.xml',
        'security/ir.model.access.csv'
    ],
    'application': True,
    'installable': True,
}
