# -*- coding: utf-8 -*-
{
    'name': "Bloomup Fleet Move Tyre",
    'summary': """
        Bloomup Fleet Move tyre
    """,
    'description': """
        Bloomup Fleet Move tyre
        
        - gestione gommisti
        - winter kit
        - pneumatici
    """,
    'author': "Bloomup, Matteo Piciucchi",
    'website': "http://bloomup.it",
    'category': 'Fleet Move Tyre',
    'version': '0.1',
    'depends': [
        'base',
        'bloomup_fleet_move',
        'bloomup_fleet_move_addons',
        'bloomup_fleet_move_arval',
        'bloomup_ipat',
        'netcheck_2',
        'base_geolocalize',
        'bloomup_rest_queue'
    ],
    'data': [
        'data/action.xml',
        'data/groups.xml',
        'views/assets.xml',
        'security/ir.model.access.csv',
        'views/tyre_repairer.xml',
        'views/tire.xml',
        'views/vehicle.xml',
        'views/config.xml',
        'data/ipat_gommista.xml',
        'report/delivery_complete.xml',
        'views/fleet_move.xml',
        'views/fleet_partner.xml',
        'views/radius.xml',
        'views/favorite.xml',
        'data/ipat_radius.xml',
        'data/ipat_favorite.xml',
        'data/cron.xml',
        'views/mail_template.xml',
        'views/project_task.xml',
        'views/partner.xml',
    ],
    "qweb": [
        'static/src/xml/map.xml',
    ], 
    'application': True,
    'installable': True,
}
