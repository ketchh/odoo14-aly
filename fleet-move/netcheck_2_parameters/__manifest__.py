# -*- coding: utf-8 -*-
{
    'name': "netcheck_2_parameters",

    'summary': """
        Customizzazione del modulo netcheck per inserire i parametri(variabili)""",

    'description': """
        Customizzazione del modulo netcheck:
        1) aggiunto campo alla linea "variabile" univoco per modello che si propaga sulla registrazione collegata
        2) Inserito metodo nella checklist per estrarre un dizionario chiave(variabile), valore(valore registrazione)
        3) Inserito metodo che passato un modello crea un record di quel modello prendendo i dati dalle variabili delle registrazioni
        4) Inserito metodo che passato un modello e un id aggiorna un record di quel modello prendendo i dati dalle variabili delle registrazioni
    """,

    'author': "Bloomup S.r.l., Daniele La Martina",
    'website': "https://www.bloomup.it",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Tools',
    'version': '14.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'netcheck_2'],

    # always loaded
    'data': [
        'views/checklist_checklist.xml',
        'views/checklist_registration.xml',
    ],
}
