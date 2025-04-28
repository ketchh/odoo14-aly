# -*- coding: utf-8 -*-
{
    'name': "bloomup_ars_reminders",

    'summary': """
        Reminders per ARS""",

    'description': """
        Reminders per ARS
    """,

    'author': "Bloomup Srl",
    'website': "http://www.bloomup.it",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','bloomup_fleet_move'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'data/cron.xml',
    ],
   
}
