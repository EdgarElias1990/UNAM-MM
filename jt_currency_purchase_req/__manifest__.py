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
    'name': 'Currency Purchase Request',
    'summary': 'Account Base',
    'version': '13.0.0.1.0',
    'category': 'Invoicing',
    'author': 'Jupical Technologies Pvt. Ltd.',
    'maintainer': 'Jupical Technologies Pvt. Ltd.',
    'website': 'http://www.jupical.com',
    'license': 'AGPL-3',
    'depends': ['jt_finance','jt_budget_mgmt','jt_projects','jt_account_module_design'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'wizard/open_account_request_confirm.xml',
        'views/account_request.xml',
        'views/bank_modification_view.xml',
        'views/office_signature_view.xml',
        'views/open_account_checking_view.xml',
        'views/check_accounting_cancel_view.xml',
        'report/open_checking_account_report.xml',
        'views/other_procedure_view.xml',
        'views/menu.xml',
        'views/account_cancellation_view.xml',
        'views/comission_profit.xml',
        'views/account_journal_view.xml',
        'views/sender_reciept_trade_view.xml',
        'views/application_request.xml',
        'views/quote_view.xml',
        'views/dollar_fund.xml',
        'views/trasfer_request.xml',
        'views/project_menu.xml',
        'report/office_cancellation_check_account.xml',
        'report/office_other_formalities.xml',
        'report/office_of_updating_signature.xml',
        'report/menu_report.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
