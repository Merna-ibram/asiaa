# -*- coding: utf-8 -*-
{
    'name': "invoic",
    'author': "My Company",
    'website': "https://www.yourcompany.com",
    'version': '0.1',
    'license': 'LGPL-3',
    'application': True,
    'installable': True,
    'category': 'Healthcare',

    # 'post_init_hook': 'assign_country_codes_on_install',



    'depends': [
        'base','account','account_commission'
    ],

    'data': [
        # Security
        'security/security_groups.xml',
        'security/ir.model.access.csv',


    ],


}
