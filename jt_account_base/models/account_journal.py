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
from odoo.exceptions import UserError
import re
from datetime import datetime

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    account_type = fields.Selection([('check', 'Checks'), ('card', 'Card'),
                                     ('master', 'Master Account'),
                                     ('key', 'Key Account')],
                                    string='Type of Account')
    branch_number = fields.Char('Branch Number', size=4)

    #Bank Accounts
    customer_number = fields.Char('Customer number')
    branch_office = fields.Char('Branch office')
    unam_account_name = fields.Char("UNAM Account Name")
    contract_number = fields.Char('Contract number')
    opening_date = fields.Date('Opening date')
    cancellation_date = fields.Date('Cancellation date')
    concept_id = fields.Many2one('bank.account.concept',string='Concept')
    has_checkbook = fields.Boolean(
        default=False, string='Do you have a checkbook?')
    checkbook_type = fields.Selection(
        [('normal', 'Normal'), ('massive', 'Massive')], string='Type of checkbook')
    checkbook_no = fields.Char("Checkbook No.")
    signatures = fields.Binary('Account Authorization Signatures')
    contract = fields.Binary('Attach contract')
    min_balance = fields.Monetary(string='Minimum Balance', tracking=True)
    min_balance_start_date = fields.Date('Start Date')
    min_balance_end_date = fields.Date('End Date')
    executive_ids = fields.One2many('executive.data', 'journal_id')
    clabe_account = fields.Char(related='bank_account_id.l10n_mx_edi_clabe',string='CLABE')
    update_history_ids = fields.One2many('minimum.balance.history', 'journal_id')
    cost_per_check = fields.Monetary("Cost per check")
    
    is_federal_subsidy = fields.Boolean(string='Federal Subsidy',default=False,copy=False)
    
    @api.constrains('min_balance')
    def check_min_balance(self):
        if self.min_balance and self.min_balance < 0:
            raise UserError(_('The balance cannot be negative.'))

    @api.constrains('branch_number')
    def check_branch_number(self):
        if self.branch_number:
            pattern = "^[0-9]{4}$"
            if not re.match(pattern, self.branch_number):
                raise UserError(_('The Branch Number should be of 4 digits.'))
        if self.branch_number and len(self.branch_number) != 4:
            raise UserError(_('The Branch Number should be of 4 digits.'))

    def create_update_history_record(self):
        for record in self:
            start_date = 0
            end_date = 0
            if record.min_balance_start_date:
                start_date = record.min_balance_start_date.day
            if record.min_balance_end_date:
                end_date = record.min_balance_end_date.day
             
            vals = {'start':start_date,'ends':end_date,'journal_id':record.id,'amount':record.min_balance,'update_date':datetime.today()}
            self.env['minimum.balance.history'].create(vals)
            
    @api.model
    def create(self,vals):
        res = super(AccountJournal,self).create(vals)
        if 'min_balance' in vals and vals.get('min_balance',0) != 0:
            res.create_update_history_record()
        return res
        
    def write(self,vals):
        res = super(AccountJournal,self).write(vals)
        if 'min_balance' in vals:
            self.create_update_history_record()
        return res

    # 'branch_office', 'min_balance', 'currency_id',
    @api.onchange('bank_account_id')
    def auto_insert(self):
        self.branch_office = self.bank_account_id.branch_number
        self.min_balance = self.bank_account_id.minimum_balance

        moneda_value = self.bank_account_id.currency_id.name
        moneda = self.env['res.currency'].search([])
        for i in range(len(moneda)):
            if moneda[i].name == moneda_value:
                self.currency_id = moneda[i]
    
class ExecutiveData(models.Model):

    _name = 'executive.data'
    _description = "Executive Data"
    _rec_name = 'name'

    journal_id = fields.Many2one('account.journal')
    name = fields.Char('Name')
    position = fields.Char('Position')
    telephone = fields.Char('Telephone')
    address = fields.Char('Address')
    email = fields.Char('Email')
    recipient_executive = fields.Boolean("Recipient Executive")
    copied_executive = fields.Boolean("Copied Executive")


    # def name_get(self):
    #     if 'show_recipet' in self._context:
    #         res = []
    #         for base in self:
    #             base_name = ''
    #             base_position = ''
    #             if base.position and base.name:
    #                 base_position = base.position
    #                 base_name = base.name
    #                 res.append((base.id, '%s - %s' %
    #                         (base_name,base_position)))
    #             else:
    #                 res.append((base.id,base.name))
    #     else:
    #         res = super(ExecutiveData, self).name_get()
    #     return res

    
class MinimumBalanceHistory(models.Model):
    
    _name = 'minimum.balance.history' 
    _description = "Minimum Balance History"
        
    start = fields.Integer('Start')
    ends = fields.Integer('Ends')
    amount = fields.Monetary(string='Amount')
    update_date = fields.Date('Update Date')
    journal_id = fields.Many2one('account.journal','Journal')
    currency_id = fields.Many2one(related='journal_id.currency_id')

