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


class AccountMove(models.Model):

    _inherit = 'account.move'

    leaves = fields.Integer('Leaves')
    project_code = fields.Char('Project Code')
    #exchange_rate = fields.Char('Exchange Rate')
    foreign_currency_amount = fields.Monetary('Foreign currency amount')
    project_number_id = fields.Many2one(
        'project.project', string='Project Number')
    is_papiit_project = fields.Boolean(
        related='project_number_id.is_papiit_project', string='Is Papiit Project')
    agreement_number = fields.Char(
        related='project_number_id.number_agreement', string='Agreement Number')
    # stage = fields.Char(
    #     related='project_number_id.stage_identifier', string='Stage',readonly=False)
    stage = fields.Many2one(
        related='project_number_id.stage_identifier_id', string='Stage',readonly=False)
    excercise = fields.Char('excercise')
    invoice_vault_folio = fields.Char('Invoice vault folio')
    req_registration_date = fields.Date('Request Registration Date')
    status = fields.Selection(
        [('accept', 'Accepted'), ('reject', 'Rejected')], string='Status')
    line = fields.Integer("Header")
    previous = fields.Monetary('Previous')
    agreement_type_id = fields.Many2one('agreement.type',string="Agreement Type")

    # More info Tab
    # responsible_category_key = fields.Char("Responsible category key")
    responsible_job_position = fields.Many2one(
        'hr.job', 'Responsible job position')
    operation_name = fields.Char(related='operation_type_id.name')
    
class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    concept = fields.Char('Concept')
    bill = fields.Many2one('account.account')
    vat = fields.Char('Vat')
    retIVA = fields.Char('RetIVA')
    line = fields.Integer("Line")
    # stage = fields.Char(related='move_id.stage', string='Stage')
    stage = fields.Many2one(related='move_id.stage', string='Stage',readonly=False)
    excercise = fields.Char(related='move_id.excercise', string='excercise',readonly=False)
    operation_type_id = fields.Many2one('operation.type',
                                        related='move_id.operation_type_id', string="Operation Type")
    operation_type_name = fields.Char(
        related='move_id.operation_type_id.name', string='name')
    project_key = fields.Char(string='Project Key')
    invoice_vault_folio = fields.Char('Invoice vault folio')
    uuid_invoice = fields.Char(string='UUID Invoice')
    invoice_series = fields.Char(string='Invoice Series')
    invoice_folio = fields.Char(string='Invoice Folio')
    #other_amounts = fields.Monetary("Other Amounts")
    # price_payment = fields.Monetary("Price")

    open_request_id = fields.Many2one('request.accounts','Open Request')
    transfer_request_id = fields.Many2one('request.transfer','Transfer Request')
    