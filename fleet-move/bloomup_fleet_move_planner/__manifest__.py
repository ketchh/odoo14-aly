# -*- coding: utf-8 -*-
{
    'name': "Bloomup Fleet Move Pianificatore",
    'summary': """
        Bloomup Fleet Move Pianificatore
    """,
    'description': """
        Bloomup Fleet Move Pianificatore
    """,
    'author': "Bloomup, Matteo Piciucchi",
    'website': "http://bloomup.it",
    'category': 'Fleet Move Planner',
    'version': '0.1',
    'depends': [
        'base',
        'bloomup_fleet_move',
        'bloomup_fleet_move_arval',
        'bloomup_ipat',
        'netcheck_2',
    ],
    'data': [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "security/rules.xml",
        "views/partner.xml",
        "views/planner.xml",
        "views/fleet_move.xml",
        'wizard/wizard.xml'
    ],
    'application': True,
    'installable': True,
}
