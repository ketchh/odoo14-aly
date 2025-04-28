# -*- coding: utf-8 -*-
{
    'name': "Bloomup Fleet Move",
    'summary': """
        Movimentazioni veicoli.
    """,
    'description': """
        Movimentazioni veicoli.
    """,
    'author': "Bloomup",
    'website': "http://bloomup.it",
    'category': 'Services/Project',
    'version': '0.1',
    'depends': [
        'base',
        'contacts',
        'fleet',
        'project',
        'hr',
        'sale_management',
        'partner_firstname',
        'l10n_it_fiscalcode',
        'bloomup_owl_components',
        'sale_project'
    ],
    'data': [
       'data/data.xml',
       'security/ir.model.access.csv',
       'views/fleet_partner.xml',
       'views/fleet_move.xml',
       'views/partner.xml',
       'views/fleet_vehicle.xml',
       'views/assets.xml',
       'views/template.xml',
       'views/planner_requests.xml',
       'views/hub.xml',
       'views/unify_fleet_data.xml',
       'views/move_report.xml'
    ],
    'qweb':[
        'static/src/xml/planner.xml',
    ],
    'application': True,
    'installable': True,
}
