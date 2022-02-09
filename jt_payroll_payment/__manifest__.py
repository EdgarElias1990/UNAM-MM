# -*- coding: utf-8 -*-
##############################################################################
#
#    Jupical Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Jupical Technologies(<http://www.jupical.com>).
#    Author: Jupical Technologies Pvt. Ltd.(<http://www.jupical.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Payroll Payment',
    'summary': 'Payroll Payment',
    'version': '13.0.0.1.0',
    'category': 'Payroll',
    'author': 'Jupical Technologies Pvt. Ltd.',
    'maintainer': 'Jupical Technologies Pvt. Ltd.',
    'website': 'http://www.jupical.com',
    'license': 'AGPL-3',
    'depends': ['account_accountant', 'jt_hr_base', 'jt_account_base'],
    'data': [
        'views/main_menus.xml',
        'views/policy_keys_view.xml',
        'views/operation_type_view.xml',
        'views/egress_keys_view.xml',
        'views/upa_catalog_view.xml',
        'views/upa_document_type.xml',
        'views/calendar_payment_reg_views.xml',
        'views/preception_deduction.xml',
        'views/res_partner_view.xml',
        'views/employee_payroll_view.xml',
        'views/employee_menus.xml',
        'views/account_menus.xml',
        'wizard/bank_layout_employee_view.xml',
        'wizard/payroll_payment_bank_format_view.xml',
        'wizard/load_employee_bank_response_file.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/ir_sequence.xml',
        'data/cron.xml',
        'views/assets.xml',
        'views/adjustments_cases_view.xml',
        'views/payroll_processing_view.xml',
        'wizard/generate_payroll_wizard.xml',
        'wizard/adjusted_payroll_view.xml',
        'wizard/lows_and_cancellations_view.xml',
        
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
