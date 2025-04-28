# -*- coding: utf-8 -*-
{
    'name': "Bloomup Ars Fast api",
    'summary': """
        Bloomup Ars Fast api
    """,
    'description': """
       
    """,
    'author': "Bloomup",
    'website': "http://bloomup.it",
    'version': '0.1',
    'depends': [
        'base',
        'bloomup_fleet_move',
        'bloomup_fleet_move_addons',
        'bloomup_fleet_move_arval',
        'bloomup_fleet_move_tyre',
        'fastapi'
    ],
    'data': [
        'views/endpoint.xml',
        'data/users.xml',
        'views/actions.xml'
    ],
    'application': True,
    'installable': True,
}
