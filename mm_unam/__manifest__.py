# -*- coding: utf-8 -*-
{
    'name': "mm_unam",

    'summary': """
        Módulo mm_unam""",

    'description': """
        Módulo de personalizaciones UNAM Mit-Mut
    """,

    'author': "MIT-MUT",
    'website': "http://www.mit-mut.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Mit-Mut',
    'version': '1.10.3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'jt_account_base',
        'jt_contact_base',
        'jt_check_controls',
        'account',
        'jt_hr_base',
        'jt_payroll_payment',
        'jt_conac',
        'jt_income',
        'jt_finance',
        'jt_supplier_payment',
        'jt_budget_mgmt',
        'jt_projects',
        'jt_agreement',
        'l10n_mx_edi',
    ],

    # always loaded
    'data': [
        'views/views.xml',
        'views/mm_fornight_views.xml',
        'views/mm_account_payment_view.xml',
	    'views/pension_payment_inherit.xml',
        'views/bank_inherit_view.xml',
        'views/mm_operation_type_view.xml',
        'views/mm_num_deposito_view.xml',
        'views/mm_button.xml'
    ],

    'installable': True

}
