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
    'name': 'CONAC',
    'summary': 'CONAC Accounting management',
    'version': '13.0.0.1.1',
    'category': 'Accounting',
    'author': 'Jupical Technologies Pvt. Ltd.',
    'maintainer': 'Jupical Technologies Pvt. Ltd.',
    'website': 'http://www.jupical.com',
    'license': 'AGPL-3',
    'depends': ['account_accountant', 'l10n_mx_reports', 'jt_supplier_payment'],
    'data': [
        'security/ir.model.access.csv',
        'views/report_template.xml',
        'views/coa_conac_view.xml',
        'views/coa_view.xml',
        'views/cog_conac_view.xml',
        'views/debt_statement_view.xml',
        'views/cash_statement_view.xml',
        'views/income_statement_view.xml',
        'views/expenditure_status_view.xml',
        'views/states_and_program_view.xml',
        'views/menus_actions.xml',
        'views/header.xml',
        'views/header_custom_mm.xml',
        # 'data/report_template.xml',
        'data/account_tags.xml',
        'data/financial_report_line.xml',
        'data/financial_reports.xml',
        'data/coa.conac.csv',
        'data/cog.conac.csv',
        'data/debt.statement.csv',
        'data/cash.statement.csv',
        'data/income.statement.csv',
        'data/status.expen.csv',
        'data/states.program.csv',

        'data/account_journal.xml',
        'views/account_journal.xml',
        'views/account_move.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
