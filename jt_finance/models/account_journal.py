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
from odoo import models, fields, api

class AccountJournal(models.Model):

    _inherit = 'account.journal'


    estimated_credit_account_id = fields.Many2one('account.account', "Default Credit Account")
    conac_estimated_credit_account_id = fields.Many2one('coa.conac', "CONAC Credit Account")
    estimated_debit_account_id = fields.Many2one('account.account', "Default Debit Account")
    conac_estimated_debit_account_id = fields.Many2one('coa.conac', "CONAC Debit Account")
    
    collected_credit_account_id = fields.Many2one('account.account', "Default Credit Account")
    conac_collected_credit_account_id = fields.Many2one(related='collected_credit_account_id.coa_conac_id', string="CONAC Credit Account")
    collected_debit_account_id = fields.Many2one('account.account', "Default Debit Account")
    conac_collected_debit_account_id = fields.Many2one(related='collected_debit_account_id.coa_conac_id', string="CONAC Debit Account")
     
    
    @api.onchange('estimated_credit_account_id', 'estimated_debit_account_id')
    def onchange_estimated_account(self):
        if self.estimated_credit_account_id and self.estimated_credit_account_id.coa_conac_id:
            self.conac_estimated_credit_account_id = self.estimated_credit_account_id.coa_conac_id
        else:
            self.conac_estimated_credit_account_id = False
        if self.estimated_debit_account_id and self.estimated_debit_account_id.coa_conac_id:
            self.conac_estimated_debit_account_id = self.estimated_debit_account_id.coa_conac_id
        else:
            self.conac_estimated_debit_account_id = False

    def write(self, vals):
        res = super(AccountJournal, self).write(vals)
        acc_obj = self.env['account.account']
        for record in self:
            if vals.get('estimated_credit_account_id'):
                estimated_credit_account_id = acc_obj.browse(vals.get('estimated_credit_account_id'))
                if estimated_credit_account_id.coa_conac_id:
                    record.conac_estimated_credit_account_id = estimated_credit_account_id.coa_conac_id
            if vals.get('estimated_debit_account_id'):
                estimated_debit_account_id = acc_obj.browse(vals.get('estimated_debit_account_id'))
                if estimated_debit_account_id.coa_conac_id:
                    record.conac_estimated_debit_account_id = estimated_debit_account_id.coa_conac_id
        return res

class AccountPayment(models.Model): 
    
    _inherit = 'account.payment'
    
    @api.depends('amount','currency_id')
    def get_amount_payyment_currency_custom(self):
        for rec in self:
            amount = rec.amount
            if rec.currency_id and rec.company_id and rec.company_id.currency_id and rec.company_id.currency_id.id != rec.currency_id.id:
                amount = rec.currency_id._convert(amount, rec.company_id.currency_id, rec.company_id, rec.payment_date) 
            rec.amount_payment_company_currency = amount 
            
    amount_payment_company_currency = fields.Monetary(string='Amount',compute='get_amount_payyment_currency_custom',store=True)
    
    
               