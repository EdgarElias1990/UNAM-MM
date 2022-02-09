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
from odoo import models, fields


class FavouriteSummaryReport(models.Model):

    _name = 'favourite.summary.report'
    _description = 'Favourite Summary Report'
    _rec_name = 'favourite_name'

    state = fields.Selection([('draft', 'Draft'), ('request', 'Request'),
                              ('download', 'Download')], default='draft')
    name = fields.Char("Name")
    report_file = fields.Binary("Download Report", filters='.xls')

    # Date period related fields
    filter_date = fields.Selection([
        ('this_month', 'This Month'),
        ('this_quarter', 'This Quarter'),
        ('this_year', 'This Financial Year'),
        ('last_month', 'Last Month'),
        ('last_quarter', 'Last Quarter'),
        ('last_year', 'Last Financial Year'),
        ('custom', 'Custom'),
    ])

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    # Budget Control Related fields
    budget_control_ids = fields.Many2many(
        'budget.control', string='Budget Control')

    # Program Code Section Related fields
    code_section_ids = fields.Many2many(
        'code.structure', string='Programming Code Section', translate=True)
    program_ids = fields.Many2many('program', string='Program')
    sub_program_ids = fields.Many2many('sub.program', string='Sub-Program')
    dependency_ids = fields.Many2many('dependency', string='Dependency')
    sub_dependency_ids = fields.Many2many(
        'sub.dependency', string='Sub-Dependency')
    item_ids = fields.Many2many('expenditure.item', string='Expense Item')
    origin_ids = fields.Many2many('resource.origin', string='Origin Resource')
    activity_ids = fields.Many2many(
        'institutional.activity', string='Institutional Activity')
    conpp_ids = fields.Many2many(
        'budget.program.conversion', string='Budget Program Conversion (CONPP)')
    conpa_ids = fields.Many2many(
        'departure.conversion', string='SHCP Games (CONPA)')
    expense_type_ids = fields.Many2many(
        'expense.type', string='Type of Expense (TG)')
    location_ids = fields.Many2many(
        'geographic.location', string='Geographic Location (UG)')
    wallet_ids = fields.Many2many('key.wallet', string='Wallet Key (CC)')
    project_type_ids = fields.Many2many(
        'project.type', string='Project Type (TP)')
    stage_ids = fields.Many2many('stage', string='Stage (E)')
    agreement_type_ids = fields.Many2many(
        'agreement.type', string='Type of agreement (TC)')

    favourite_user_id = fields.Many2one('res.users', string='User')
    favourite_name = fields.Char('Name')
