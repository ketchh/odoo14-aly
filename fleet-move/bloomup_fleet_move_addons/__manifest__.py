# -*- coding: utf-8 -*-
{
    'name': "Bloomup Fleet Move ADDONS",
    'summary': """
        Movimentazioni veicoli. ADDONS
    """,
    'description': """
        Movimentazioni veicoli. ADDONS
    """,
    'author': "Bloomup",
    'website': "http://bloomup.it",
    'category': 'Services/Project',
    'version': '0.1',
    'depends': [
        'base',
        'contacts',
        'bloomup_fleet_move',
        'netcheck_2',
        'netcheck_automotive'
    ],
    'data': [
       'views/views.xml',
       'data/actions.xml',
       'security/ir.model.access.csv'
    ],
    'application': True,
    'installable': True,
}
