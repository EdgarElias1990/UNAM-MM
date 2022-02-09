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
from odoo.exceptions import ValidationError ,UserError
from datetime import datetime

class RequestOpenBalanceInvestment(models.Model):

    _inherit = 'request.open.balance.invest'

    type_of_investment = fields.Selection([('productive_account','Productive Account'),
                                           ('securities','Securities'),('money_market','Money Market')
                                           ],string="Type Of Investment")
    
    type_of_financial_products = fields.Selection([
                                           ('CETES','CETES'),('UDIBONOS','UDIBONOS'),
                                           ('BondsNotes','BondsNotes'),('Promissory','Promissory'),
                                           ],string="Type Of Financial Products")

    contract_id = fields.Many2one('investment.contract','Contract')

    finance_investment_id = fields.Many2one('investment.investment', 'First Number:')
    finance_investment_fund_id = fields.Many2one('investment.funds', 'Fund')
    finance_bank_account_id = fields.Many2one(
        'account.journal', "Bank and Origin Account")
    finance_date_required = fields.Date("Date Required")
    finance_desti_bank_account_id = fields.Many2one(
        'account.journal', "Destination Bank and Account")
    
    @api.onchange('contract_id')
    def onchange_contract_id(self):
        if self.contract_id:
            self.fund_type_id = self.contract_id.fund_type_id and self.contract_id.fund_type_id.id or False 
            self.type_of_agreement_id = self.contract_id.agreement_type_id and self.contract_id.agreement_type_id.id or False
            self.fund_id = self.contract_id.fund_id and self.contract_id.fund_id.id or False
            self.base_collabaration_id = self.contract_id.base_collabaration_id and self.contract_id.base_collabaration_id.id or False
        else:
            self.fund_type_id = False
            self.type_of_agreement_id = False
            self.fund_id = False
            self.base_collabaration_id = False

    def unlink(self):
        for rec in self:
            if rec.state not in ['draft']:
                raise UserError(_('You can delete only draft status data.'))
        return super(RequestOpenBalanceInvestment, self).unlink()
            
    def set_to_requested(self):
        self.state = 'requested'
        
    @api.model
    def create(self,vals):
        res = super(RequestOpenBalanceInvestment,self).create(vals)
        if not res.name and res.fund_id:
            res.name = res.fund_id.name
        return res
    
    def resend_reject_request(self):
        finance_id = self.env['request.open.balance.finance'].search([('request_id','=',self.id),('state','=','rejected')],limit=1)
        if finance_id:
            self.state = 'approved'
            if self.balance_req_id:
                self.balance_req_id.state = 'approved'
            
            finance_id.state='requested' 
            finance_id.investment_id = self.finance_investment_id and self.finance_investment_id.id or False
            finance_id.investment_fund_id = self.finance_investment_fund_id and self.finance_investment_fund_id.id or False
            finance_id.bank_account_id = self.finance_bank_account_id and self.finance_bank_account_id.id or False
            finance_id.date_required = self.finance_date_required
            finance_id.desti_bank_account_id = self.finance_desti_bank_account_id and self.finance_desti_bank_account_id.id or False 
             
               