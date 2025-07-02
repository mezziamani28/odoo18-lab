# -*- coding: utf-8 -*-
{
    'name': 'Base siren',
    'version': '18.0.1.0.0',
    'summary': 'Base siren',
    'sequence': 10,
    'description': """ Base siren """,
    'depends': ['base','base_setup','crm'],
    "author": "YZYdidital",
    'data': [
        "security/ir.model.access.csv",
        'views/base_siren_views.xml',
        'data/cron.xml',
        'views/res_partner_views.xml',
        'views/qualification_views.xml',
        'views/crm_lead_views.xml',

    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
