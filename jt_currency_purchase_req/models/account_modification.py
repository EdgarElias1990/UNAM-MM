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
from odoo import models, fields, api,_
class AccountModification(models.Model):

    _inherit = 'request.accounts'

    move_type = fields.Selection(selection_add=[
        ('account_modify', 'Account Modification')])
    no_trade = fields.Char('No. Trade')
    legal_number = fields.Char('legal Number')
    modification_date = fields.Date("Date",default=fields.Date.context_today)
    request_line_ids = fields.One2many('request.accounts.line','request_id',string='request line')
    cancellation_date = fields.Date('Date',default=fields.Date.context_today)

    @api.model
    def create(self, vals):
        res = super(AccountModification,self).create(vals)
        if res.move_type == 'account_modify':
            invoice = self.env['ir.sequence'].next_by_code('request.accounts.modification')
            res.invoice = invoice        
        if res.invoice:
            res.invoice = res.invoice.zfill(8)
        return res

    def generate_modification_request(self):
        if self.move_type == 'account open':
            message = "Check the '" + self.invoice + "' Request for a account"
        elif self.move_type == 'account_modify':
            message = "Check the '" + self.invoice + "' Request for the modification in account"
        user = self.env.user
        self.env['bus.bus'].sendone(
            (self._cr.dbname, 'res.partner', user.partner_id.id),
            {'type': 'simple_notification', 'title': _('Request'), 'message': message, 'sticky': True,
             'info': True})

    def action_confirm_modification(self):
        self.write({'status': 'confirmed'})


class AccountModificationLine(models.Model):

    _name = 'request.accounts.line'
    _description = 'Account modification line'


    project_id = fields.Many2one('project.project', "Project Number")
    bank_account_id = fields.Many2one(
        "account.journal", string="Bank", domain=[('type', '=', 'bank')])
    bank_acc_number_id = fields.Many2one('res.partner.bank',
                                         related='bank_account_id.bank_account_id', string="Bank Account")
    user_id = fields.Many2one('hr.employee',
                              related='project_id.responsible_name', string="Project Manager")
    request_id = fields.Many2one('request.accounts','account request')