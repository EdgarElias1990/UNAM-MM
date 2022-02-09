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
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError , UserError
from datetime import datetime

class InvestmentFunds(models.Model):

    _inherit = 'investment.funds'
    
         
    fund_type_id = fields.Many2one('fund.type','Type of Fund')
    type_of_agreement_id = fields.Many2one('agreement.agreement.type','Type of Agreement')
    bases_collaboration_id = fields.Many2one('bases.collaboration','Name of Agreement')
    is_fund = fields.Boolean(default=False,string="Fund")
    state = fields.Selection([('draft', 'Draft'),
                               ('confirmed', 'Confirmed'),
                               ('canceled', 'Canceled')], string="Status", default="draft")


    
    dependency_id = fields.Many2one('dependency', "Dependency")
    subdependency_id = fields.Many2one('sub.dependency', "Sub Dependency")
    dependency_holder = fields.Char("Dependency Holder")
    responsible_user_id = fields.Many2one('res.users',string='Responsible')
    type_of_resource = fields.Char("Type Of Resource")

    journal_id = fields.Many2one('account.journal','Bank')
    bank_account_id = fields.Many2one(related='journal_id.bank_account_id',string="Account Number")
    
    request_office = fields.Char("Request Office")
    permanent_instructions =fields.Text("Permanent Instructions")
    fund_observation = fields.Text("Observations")
    
    contract_id = fields.Many2one('investment.contract','Contract')

    request_date = fields.Date("Request Date")
    trade_number = fields.Char("Trade Number")
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.user.company_id.currency_id)
    opening_balance = fields.Monetary("Opening Amount")
    observations = fields.Text("Observations")
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id,
                              string="Requesting User")
    
    origin_resource_id = fields.Many2one('sub.origin.resource', "Origin of the resource")
    cbc_format = fields.Binary("CBC Format")
    cbc_shipping_office = fields.Binary("CBC Shipping Office")
    liability_account_id = fields.Many2one('account.account', "Liability Accounting Account")
    investment_account_id = fields.Many2one('account.account', "Investment Accounting Account")
    interest_account_id = fields.Many2one('account.account', "Interest Accounting Account")
    availability_account_id = fields.Many2one('account.account', "Availability Accounting Account")
    supporting_documentation = fields.Binary("Supporting Documentation")

    type_of_investment = fields.Selection([('productive_account','Productive Account'),
                                           ('securities','Securities'),('money_market','Money Market')
                                           ],string="Type Of Investment")
    
    type_of_financial_products = fields.Selection([
                                           ('CETES','CETES'),('UDIBONOS','UDIBONOS'),
                                           ('BondsNotes','BondsNotes'),('Promissory','Promissory'),
                                           ],string="Type Of Financial Products")

    
    purchase_sale_ids = fields.One2many('purchase.sale.security','investment_fund_id')
    cetes_ids = fields.One2many('investment.cetes','investment_fund_id')
    udibonos_ids = fields.One2many('investment.udibonos','investment_fund_id')
    bonds_ids = fields.One2many('investment.bonds','investment_fund_id')
    will_pay_ids = fields.One2many('investment.will.pay','investment_fund_id')
    productive_ids = fields.One2many('investment.investment','investment_fund_id')
    inv_operation_ids = fields.One2many('investment.operation','investment_fund_id')
    
    request_finance_ids = fields.One2many(
        'request.open.balance.finance', 'investment_fund_id')
    yield_id = fields.Many2one('yield.destination',string="Yield Destination")
    rate_of_returns = fields.Many2one('rate.of.returns', string="Rate Of Returns")


    @api.model
    def create(self, vals):
        res = super(InvestmentFunds, self).create(vals)
        if vals.get('fund_request_date'):
            pay_regis_obj = self.env['calendar.payment.regis']
            pay_regis_rec = pay_regis_obj.search([('date', '=', vals.get('fund_request_date')),
                                           ('type_pay', '=', 'Non Business Day')], limit=1)
            if pay_regis_rec:
                raise ValidationError(_("You are creating Fund Request on Non-Business Day!"))
        return res

    def write(self, vals):
        res = super(InvestmentFunds, self).write(vals)
        if vals.get('fund_request_date'):
            pay_regis_obj = self.env['calendar.payment.regis']
            pay_regis_rec = pay_regis_obj.search([('date', '=', vals.get('fund_request_date')),
                                           ('type_pay', '=', 'Non Business Day')], limit=1)
            if pay_regis_rec:
                raise ValidationError(_("You are creating Fund Request on Non-Business Day!"))
        return res

    def unlink(self):
        for rec in self:
            if rec.state not in ['draft']:
                raise UserError(_('You can delete only draft status data.'))
        return super(InvestmentFunds, self).unlink()

    def approve_fund(self):
        self.state = 'confirmed'
        maturity_report_id = self.env['maturity.report'].search([('fund_id','=',self.id)],limit=1)
        
        vals = {
            'name': self.first_number,
            'fund_id': self.id,
            'partner_id': self.responsible_user_id.partner_id.id,
            'date': datetime.today().date()
        }
        
        if maturity_report_id:
            maturity_report_id.write(vals)
        else:
            self.env['maturity.report'].create(vals)

    def reset_fund(self):
        self.state = 'draft'
        
#         today = datetime.today().date()
#         user = self.env.user
#         employee = self.env['hr.employee'].search(
#             [('user_id', '=', user.id)], limit=1)
#         fund_type = False
#         if self.contract_id and self.contract_id.fund_id:
#             fund_type = self.contract_id.fund_id.id
#         
#         amount = 0
#         
#         amount += sum(x.amount for x in self.purchase_sale_ids)
#         amount += sum(x.amount_invest for x in self.cetes_ids)
#         amount += sum(x.amount_invest for x in self.udibonos_ids)
#         amount += sum(x.amount_invest for x in self.bonds_ids)
#         amount += sum(x.amount_invest for x in self.will_pay_ids)
#         amount += sum(x.amount_to_invest for x in self.productive_ids)
#         
#         return {
#             'name': 'Approve Request',
#             'view_type': 'form',
#             'view_mode': 'form',
#             'view_id': False,
#             'res_model': 'approve.money.market.bal.req',
#             'type': 'ir.actions.act_window',
#             'target': 'new',
#             'context': {
#                 'default_amount': amount,
#                 'default_date': today,
#                 'default_employee_id': employee.id if employee else False,
#                 'default_investment_fund_id': self.id,
#                 'default_fund_type': fund_type,
#                 'default_bank_account_id' : self.journal_id and self.journal_id.id or False,
#                 'show_for_supplier_payment': 1,
#                 'default_fund_id' : self.fund_id and self.fund_id.id or False,
#             }
#         }

    def action_requested(self):
#        self.state = 'requested'
        if self.env.context and not self.env.context.get('call_from_product'):
            for rec in self.purchase_sale_ids.filtered(lambda x:x.state != 'requested'):
                rec.dependency_id = self.dependency_id and self.dependency_id.id or False
                rec.sub_dependency_id = self.subdependency_id and self.subdependency_id.id or False
                rec.action_requested()
            for rec in self.cetes_ids.filtered(lambda x:x.state != 'requested'):
                rec.dependency_id = self.dependency_id and self.dependency_id.id or False
                rec.sub_dependency_id = self.subdependency_id and self.subdependency_id.id or False            
                rec.action_requested()
            for rec in self.udibonos_ids.filtered(lambda x:x.state != 'requested'):
                rec.dependency_id = self.dependency_id and self.dependency_id.id or False
                rec.sub_dependency_id = self.subdependency_id and self.subdependency_id.id or False            
                rec.action_requested()
            for rec in self.bonds_ids.filtered(lambda x:x.state != 'requested'):
                rec.dependency_id = self.dependency_id and self.dependency_id.id or False
                rec.sub_dependency_id = self.subdependency_id and self.subdependency_id.id or False            
                rec.action_requested()
            for rec in self.will_pay_ids.filtered(lambda x:x.state != 'requested'):
                rec.dependency_id = self.dependency_id and self.dependency_id.id or False
                rec.sub_dependency_id = self.subdependency_id and self.subdependency_id.id or False            
                rec.action_requested()
            for rec in self.productive_ids.filtered(lambda x:x.state != 'requested'):
                rec.dependency_id = self.dependency_id and self.dependency_id.id or False
                rec.sub_dependency_id = self.subdependency_id and self.subdependency_id.id or False            
                rec.action_requested()

    def action_approved(self):
        #self.state = 'approved'
        if self.env.context and not self.env.context.get('call_from_product'):        
            for rec in self.purchase_sale_ids.filtered(lambda x:x.state != 'approved'):
                rec.action_approved()
            for rec in self.cetes_ids.filtered(lambda x:x.state != 'approved'):
                rec.action_approved()
            for rec in self.udibonos_ids.filtered(lambda x:x.state != 'approved'):
                rec.action_approved()
            for rec in self.bonds_ids.filtered(lambda x:x.state != 'approved'):
                rec.action_approved()
            for rec in self.will_pay_ids.filtered(lambda x:x.state != 'approved'):
                rec.action_approved()
            for rec in self.productive_ids.filtered(lambda x:x.state != 'approved'):
                rec.action_approved()

    def action_confirmed(self):
        self.state = 'confirmed'
        if self.env.context and not self.env.context.get('call_from_product'):
            for rec in self.purchase_sale_ids.filtered(lambda x:x.state != 'confirmed'):
                rec.action_confirmed()
            for rec in self.cetes_ids.filtered(lambda x:x.state != 'confirmed'):
                rec.action_confirmed()
            for rec in self.udibonos_ids.filtered(lambda x:x.state != 'confirmed'):
                rec.action_confirmed()
            for rec in self.bonds_ids.filtered(lambda x:x.state != 'confirmed'):
                rec.action_confirmed()
            for rec in self.will_pay_ids.filtered(lambda x:x.state != 'confirmed'):
                rec.action_confirmed()
            for rec in self.productive_ids.filtered(lambda x:x.state != 'confirmed'):
                rec.action_confirmed()


    def action_canceled(self):
        self.state = 'canceled'
        if self.env.context and not self.env.context.get('call_from_product'):
            for rec in self.purchase_sale_ids.filtered(lambda x:x.state != 'canceled'):
                rec.action_canceled()
            for rec in self.cetes_ids.filtered(lambda x:x.state != 'canceled'):
                rec.action_canceled()
            for rec in self.udibonos_ids.filtered(lambda x:x.state != 'canceled'):
                rec.action_canceled()
            for rec in self.bonds_ids.filtered(lambda x:x.state != 'canceled'):
                rec.action_canceled()
            for rec in self.will_pay_ids.filtered(lambda x:x.state != 'canceled'):
                rec.action_canceled()
            for rec in self.productive_ids.filtered(lambda x:x.state != 'canceled'):
                rec.action_canceled()