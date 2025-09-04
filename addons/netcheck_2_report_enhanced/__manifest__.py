# -*- coding: utf-8 -*-
{
    'name': 'Netcheck 2 Enhanced Reports',
    'version': '14.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Enhanced reporting system for Netcheck 2 with optimized data structure',
    'description': """
Enhanced Reporting System for Netcheck 2
=========================================

This module extends the Netcheck 2 checklist system with an optimized data structure 
specifically designed for reporting. Features include:

* Dedicated report data structure for completed checklists
* Support for multiple registrations per field (especially photos)
* Optimized QWeb templates for better report rendering
* Automatic data archiving when checklist is completed
* Enhanced photo display with gallery support
* Better performance for large reports

Installation:
- This module depends on netcheck_2
- Automatically creates report data when checklists are completed
- Provides new report templates optimized for the enhanced data structure
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['netcheck_2'],
    'data': [
        'security/ir.model.access.csv',
        'reports/report_actions.xml',
        'reports/report_template.xml',
        'wizards/migration_wizard_views.xml',
        'views/checklist_report_data_views.xml',
        'views/checklist_enhanced_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
