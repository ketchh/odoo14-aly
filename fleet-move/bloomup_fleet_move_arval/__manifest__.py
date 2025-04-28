# -*- coding: utf-8 -*-
{
    'name': "Bloomup Fleet Move ARVAL",
    'summary': """
        Movimentazioni veicoli. ARVAL
    """,
    'description': """
        Movimentazioni veicoli. ARVAL
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
        'netcheck_automotive',
        'fleet',
        'bloomup_ipat'
    ],
    'data': [
        'data/actions.xml',
        'data/ir_cron_data.xml',
        'views/views.xml',
        'report/arval_report.xml',
        'security/ir.model.access.csv',
        'views/queue.xml'
    ],
    'application': True,
    'installable': True,
}
