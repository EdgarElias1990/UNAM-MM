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
from odoo import models, fields,api,_
from odoo.exceptions import ValidationError, UserError
class Quotes(models.Model):

    _name = 'quote'
    _description = 'Quotes'

    bank_id = fields.Many2one('res.bank','Bank')
    bank_account_id = fields.Many2one('account.journal','Retirement account')
    exchange_rate = fields.Many2one('res.currency.rate',string='Exchange Rate',default=lambda self: fields.Datetime.now())
    no_of_currencies = fields.Float('Number Of Currencies')
    bank_ref = fields.Char('Bank Reference')
    shedule_date = fields.Date('Shedule Date')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.user.company_id.currency_id, string="Currency")
    amount = fields.Monetary("Amount",compute="_compute_amount",currency_field='currency_id')
    status = fields.Selection([('draft','Draft'),('approve','Approved'),('reject','Rejected'),('validate','Validated')],string='Status',default='draft')
    
    def approve(self):

        for record in self:

            record.status = 'approve'

    def reject(self):
        for record in self:
            record.status = 'reject'


    def validate(self):

        for record in self:
            record.status = 'validate'

    @api.depends('no_of_currencies','exchange_rate','currency_id')
    def _compute_amount(self):
        for rec in self:
            if rec.exchange_rate and rec.exchange_rate.rate:
                rec.amount = (1/rec.exchange_rate.rate)*rec.no_of_currencies
            else:
                rec.amount = 0

    def generate_modification_request(self):
        message = "Check the '" + "' Request for a Quote"
        user = self.env.user
        self.env['bus.bus'].sendone(
            (self._cr.dbname, 'res.partner', user.partner_id.id),
            {'type': 'simple_notification', 'title': _('Request'), 'message': message, 'sticky': True,
             'info': True})
            

    @api.constrains('shedule_date')
    def _project_number_unique(self):
        for record in self:
            create_date = self.create_date.date()
            if  create_date > record.shedule_date:
                raise ValidationError(_('date should be after deterioration to the posting date'))