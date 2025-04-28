# -*- coding: utf-8 -*-
{
    'name': "Netcheck 2.0 - Automotive Update",
    'summary': """
        Netcheck - Automotive Update
    """,
    'description': """
        Netcheck - Automotive Update
    """,
    'author': "Bloomup, Matteo Piciucchi",
    'website': "http://bloomup.it",
    'category': 'Tools',
    'version': '14.1.0',
    'depends': [
        'base',
        'mail',
        'netcheck_2'
    ],
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/assets.xml'
    ],
    "qweb": [
        'static/src/xml/widget.xml'
    ], 
    'application': True,
    'installable': True,
}
