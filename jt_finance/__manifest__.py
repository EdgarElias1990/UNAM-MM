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
    'name': 'UNAM Finance',
    'summary': 'Finance Management System for UNAM',
    'version': '13.0.0.1.1',
    'category': 'Accounting',
    'author': 'Jupical Technologies Pvt. Ltd.',
    'maintainer': 'Jupical Technologies Pvt. Ltd.',
    'website': 'http://www.jupical.com',
    'license': 'AGPL-3',
    'depends': ['account_accountant', 'project', 'jt_budget_mgmt'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/control_assigned_amount_view.xml',
        'views/calendar_assigned_amounts_view.xml',
        'views/budget_view.xml',
        'wizard/import_control_amount_received_lines_view.xml',
        'wizard/calendar_assign_amount_import_view.xml',
        'views/account_journal.xml',
		'reports/assign_amount_control_report_views.xml',
        'views/assest.xml',
        'wizard/excel_export_assign_view.xml',
        
        #Reports
        'reports/search_template.xml', 
        'reports/menu_reports.xml',
        'reports/pdf_report_header_layout.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
