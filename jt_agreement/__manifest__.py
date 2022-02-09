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
    'name': 'Agreements',
    'summary': 'Agreements',
    'version': '13.0.0.1.0',
    'category': 'Agreements',
    'author': 'Jupical Technologies Pvt. Ltd.',
    'maintainer': 'Jupical Technologies Pvt. Ltd.',
    'website': 'http://www.jupical.com',
    'license': 'AGPL-3',
    'depends': ['jt_income', 'jt_payroll_payment','web_notify'],
    'data': [
        'data/sequence.xml',
        'data/cron.xml',
        'views/fund_type.xml',
        'views/agreement_type.xml',
        'views/recurring_payment_temp.xml',
        'views/bases_collaboration.xml',
        'wizard/reason_rejected_open_bal.xml',
        'wizard/approve_inv_bal_req_view.xml',
        'views/collaboration_modification.xml',
        'views/create_payment_request.xml',
        'wizard/cancel_collaboration.xml',
        'wizard/closing_collaboration.xml',
        'wizard/generate_account_statement.xml',
        'views/ir_sequence.xml',
        'views/funds.xml',
        'views/menus.xml',
        'views/trust_request_open_balance.xml',
        'views/agreement_trust.xml',
        'views/trust_modification.xml',
        'views/background_project.xml',
        'views/specific_projects.xml',
        'wizard/cancel_trust_wizard.xml',
        'views/patrimonial_resources.xml',
        'views/patrimonial_request_open_balance.xml',
        'wizard/cancel_patrimonial_resource.xml',
        'reports/account_statement_report.xml',
        'reports/menu_reports.xml',
        'reports/bases_collaboration_report.xml',
        'reports/base_collaboration_report_view.xml',
        'reports/account_operations_increase_report.xml',
        'wizard/bases_collaboration_resemble.xml',
        'wizard/contract_assistant.xml',
        'wizard/bases_collaboration.xml',
        'data/data.xml',
        'reports/header_agree.xml',
        'security/ir.model.access.csv',
        'wizard/amounts_to_invest.xml',
        'reports/bases_collaboration_amounts_to_invest.xml',
        'views/res_partner_bank.xml',
        'views/agree_sign_view.xml',
        'reports/contract_ass_report_view.xml',
        'wizard/mass_approve_transfer_wizard.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
