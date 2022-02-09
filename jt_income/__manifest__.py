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
    'name': 'Income',
    'summary': 'Income',
    'version': '13.0.0.1.0',
    'category': 'Income',
    'author': 'Jupical Technologies Pvt. Ltd.',
    'maintainer': 'Jupical Technologies Pvt. Ltd.',
    'website': 'http://www.jupical.com',
    'license': 'AGPL-3',
    'depends': ['jt_supplier_payment', 'jt_budget_mgmt','l10n_mx_edi','jt_finance'],
    'data': [
        'data/ir_sequence.xml',
        'data/data.xml',
        'views/activity_catalog_views.xml',
        'views/deposit_certificate_views.xml',
        'views/product_views.xml',
        'views/res_partner_views.xml',
        'views/sub_origin_resource_views.xml',
        'views/association_distribution_ie_accounts_views.xml',
        'views/sender_recipient_trades.xml',
        'views/invoice_views.xml',
        'views/income_cash_cut_view.xml',
        'views/account_payment_view.xml',
        'views/res_partner_bank_view.xml',
        'views/account_journal.xml',
        'views/payment_of_income_view.xml',
        'security/ir.model.access.csv',
        'reports/template_1.xml',
        'reports/invoice_format_1.xml',
        'reports/invoice_format_2.xml',
        'reports/invoice_format_3.xml',
        'reports/invoice_format_4.xml',
        'reports/invoice_format_5.xml',
        'reports/invoice_format_6.xml',
        'reports/invoice_format_7.xml', 
        'views/res_company.xml',
        'wizard/liquid_adjstments_manual_deposite_view.xml',
        
        'reports/income_annual_report_view.xml',
        'reports/income_by_item_month.xml',
        'reports/pdf_income_by_item_report.xml',
        'reports/pdf_income_annual_report.xml',
        'reports/menu_new_income_report.xml',
        
        'views/bank_statement_view.xml',
    ],

    "qweb": [
        "static/src/xml/*.xml",
    ],
    
    'application': True,
    'installable': True,
    'auto_install': False,
}
