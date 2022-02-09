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
    'name': 'Investment',
    'summary': 'Investment',
    'version': '13.0.0.1.0',
    'category': 'Investment',
    'author': 'Jupical Technologies Pvt. Ltd.',
    'maintainer': 'Jupical Technologies Pvt. Ltd.',
    'website': 'http://www.jupical.com',
    'license': 'AGPL-3',
    'depends': ['account_accountant','jt_payroll_payment','jt_agreement','calendar'],
    'data': [
        'security/ir_rules.xml',
        'data/sequence.xml',
        'data/data.xml',
        'data/cron.xml',
        'data/decimal_precision.xml',
        'security/ir.model.access.csv',
        'views/account_journal_view.xml',
        'views/investment_rate.xml',
        'views/investment_menu.xml',
        'views/financial_product.xml',
        'views/cetes_view.xml',
        'views/udibonos.xml',
        'views/bonds.xml',
        'views/will_pay.xml',
        'views/calendar_control.xml',
        'views/investment_contract.xml',
        'views/purchase_sale_security.xml',
        'views/stock_quotation.xml',
        'views/increases_and_withdrawals.xml',
        'views/investment_view.xml',
        'views/agreement_trust_view.xml',
        'views/investment_fund_view.xml',
        'views/distribution_of_income.xml',
        'views/request_open_balance_finance.xml',
        'wizard/approve_inv_bal_req_view.xml',
        'wizard/agreements_approve_bal_view.xml',
        'wizard/inv_transfer_request_view.xml',
        'wizard/distribution_transfer_request_view.xml',
        'reports/header_template.xml',
        'reports/menu_report.xml',
        'reports/filter_template.xml',
        'views/maturity_report_views.xml',
        'views/assets.xml'
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
