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
class OfficeSignature(models.Model):

    _name = 'office.signature'
    _description = 'Office Signature'
    _rec_name = 'name'
    account_modification_id = fields.Many2one('request.accounts',domain=[('move_type','=','account_modify')])
    name = fields.Char("Number")
    dependancy_id = fields.Many2one('dependency', string='Dependency')
    bank_id = fields.Many2one('res.bank',string='Bank')
    bank_account_id = fields.Many2one('account.journal',"Bank Account")
    user_id = fields.Many2one('res.users','Responsible User')

    @api.model
    def create(self, vals):
        res = super(OfficeSignature,self).create(vals)
        seq = self.env['ir.sequence'].next_by_code('request.accounts.modification')
        res.name = seq
        return res

    @api.onchange('account_modification_id')
    def onchange_account_modification(self):

        if self.account_modification_id:

            self.bank_account_id = self.account_modification_id.request_line_ids and self.account_modification_id.request_line_ids[0].bank_account_id.id or False


    def get_sender_recipet1(self):
        trade = self.env['finance.sender.recipient.trades'].search([('template', '=', 'sign_update')], limit=1)
        return trade

    @api.onchange('bank_id')
    def onchange_bank_id(self):
        busq = self.env['account.journal'].search([('type', '=', 'bank'), ('bank_id', '=', self.bank_id.id)])
        ids = []
        for dat in busq:
            ids.append(dat.id)
        return {'domain': {'bank_account_id': [('id', 'in', ids)]}}


class AccountOpenRequest(models.Model):

    _name = 'account.open'
    _description = 'Opening a checking account'
    _rec_name = 'name'
    
    name = fields.Char("Number")
    account_modification_id = fields.Many2one('request.accounts',domain=[('move_type','=','account open'),('status','=','confirmed')])
    dependancy_id = fields.Many2one('dependency', string='Dependency')
    bank_id = fields.Many2one('res.bank',string='Bank')
    bank_account_id = fields.Many2one('account.journal',"Bank Account")
    user_id = fields.Many2one('res.users','Responsible User')


    @api.model
    def create(self, vals):
        res = super(AccountOpenRequest,self).create(vals)
        seq = self.env['ir.sequence'].next_by_code('account.open')
        res.name = seq        
        return res


    def get_sender_recipet2(self):
        trade = self.env['finance.sender.recipient.trades'].search([('template', '=', 'open_check_acc')], limit=1)
        return trade

    @api.onchange('bank_id')
    def onchange_bank_id(self):
        busq = self.env['account.journal'].search([('type', '=', 'bank'), ('bank_id', '=', self.bank_id.id)])
        ids = []
        for dat in busq:
            ids.append(dat.id)
        return {'domain': {'bank_account_id': [('id', 'in', ids)]}}



class AccountCancellation(models.Model):

    _name = 'account.cancellation'
    _description = 'Checking account cancellation'

    name = fields.Char("Number")
    account_cancellation_id = fields.Many2one('request.accounts',domain=[('move_type','=','account cancel')])
    dependancy_id = fields.Many2one('dependency', string='Dependency')
    #bank_account_id = fields.Many2one('account.journal',related='account_cancellation_id.bank_account_id',string="Bank Account")
    #bank_id = fields.Many2one('res.bank',related='bank_account_id.bank_id',string='Bank')
    bank_id = fields.Many2one('res.bank',string='Bank')
    bank_account_id = fields.Many2one('account.journal',"Bank Account")
    user_id = fields.Many2one('hr.employee',related="account_cancellation_id.user_id",string='Responsible User')   

    @api.model
    def create(self, vals):
        res = super(AccountCancellation,self).create(vals)
        seq = self.env['ir.sequence'].next_by_code('request.account.cancellation')
        res.name = seq        
        return res


    def get_sender_recipet3(self):
        trade = self.env['finance.sender.recipient.trades'].search([('template', '=', 'check_acc_cancellation')], limit=1)
        return trade

    @api.onchange('bank_id')
    def onchange_bank_id(self):
        busq = self.env['account.journal'].search([('type', '=', 'bank'), ('bank_id', '=', self.bank_id.id)])
        ids = []
        for dat in busq:
            ids.append(dat.id)
        return {'domain': {'bank_account_id': [('id', 'in', ids)]}}


class OtherProcedure(models.Model):

    _name = 'other.procedure'
    _description = 'Occupation other procedures'
    _rec_name = 'name'

    name = fields.Char("Number")
    account_modification_id = fields.Many2one('request.accounts',domain=[('move_type','=','account_modify')])
    dependancy_id = fields.Many2one('dependency', string='Dependency')
    bank_id = fields.Many2one('res.bank',string='Bank')
    bank_account_id = fields.Many2one('account.journal',"Bank Account")
    user_id = fields.Many2one('res.users','Responsible User')

    @api.model
    def create(self, vals):
        res = super(OtherProcedure,self).create(vals)
        seq = self.env['ir.sequence'].next_by_code('other.procedure')
        res.name = seq        
        return res

    def get_sender_recipet4(self):
        trade = self.env['finance.sender.recipient.trades'].search([('template', '=', 'other_procedures')], limit=1)
        return trade

    @api.onchange('bank_id')
    def onchange_bank_id(self):
        busq = self.env['account.journal'].search([('type', '=', 'bank'), ('bank_id', '=', self.bank_id.id)])
        ids = []
        for dat in busq:
            ids.append(dat.id)
        return {'domain': {'bank_account_id': [('id', 'in', ids)]}}
