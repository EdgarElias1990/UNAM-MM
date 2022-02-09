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
    'name': 'Projects',
    'summary': 'Projects',
    'version': '13.0.0.1.0',
    'category': 'Invoicing',
    'author': 'Jupical Technologies Pvt. Ltd.',
    'maintainer': 'Jupical Technologies Pvt. Ltd.',
    'website': 'http://www.jupical.com',
    'license': 'AGPL-3',
    'depends': ['jt_finance', 'jt_payroll_payment', 'jt_agreement', 'project'],
    'data': [
        'data/ir_cron.xml',
        'data/data.xml',
        'security/project_security.xml',
        'reports/header_template.xml',
        'views/rejection_checks_views.xml',
        'views/project_registry_views.xml',
        'views/request_trasfer_view.xml',
        'wizard/reason_of_rejection.xml',
        'views/verification_of_expense_view.xml',
        'views/request_for_payment.xml',
        'wizard/request_reject_view.xml',
        'wizard/request_confirm_view.xml',
        'views/request_account_views.xml',
        'views/account_cancellation.xml',
        'views/remaining_resource_view.xml',
        'wizard/project_close.xml',
        'views/papiit_project.xml',
        'views/base_menu_view.xml',
        'views/project_payment_management_view.xml',
        'views/budget_adjustments.xml',
        'reports/travel_request.xml',
        'reports/menu_view.xml',
        'reports/supplier_request.xml',
        'reports/request_field_work.xml',
        'reports/request_reimbursement.xml',
        'reports/school_internship_request.xml',
        'reports/school_internship_request.xml',
        'reports/exchange_request.xml',
        'reports/filter_template.xml',
        'security/ir.model.access.csv',
        'views/upa_payment_request.xml',
        'views/account_journal_view.xml',
        'views/bank_transfer_request.xml',
        'views/project_stage_view.xml',
        'views/project_custom_type_view.xml',
        'wizard/program_code_create_view.xml',
        'views/income_invoice_view.xml',
        'views/project_view_inherit.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
