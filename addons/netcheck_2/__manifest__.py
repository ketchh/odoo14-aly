# -*- coding: utf-8 -*-
{
    'name': "Netcheck 2.0",
    'summary': """
        Netcheck
    """,
    'description': """
        Netcheck
    """,
    'author': "Bloomup, Matteo Piciucchi",
    'website': "http://bloomup.it",
    'category': 'Tools',
    'version': '14.3.0',
    'depends': [
        'base',
        'mail',
        'portal'
    ],
    'data': [
       'views/assets.xml',
       'report/report.xml',
       'data/data.xml',
       'views/config.xml',
       'views/models.xml',
       'views/checklist.xml',
       'views/registrations.xml',
       'security/ir.model.access.csv',
       'views/templates.xml'
    ],
    "qweb": [
        'static/src/xml/precompiled.xml',
        'static/src/xml/widget.xml',
    ], 
    'application': True,
    'installable': True,
}
