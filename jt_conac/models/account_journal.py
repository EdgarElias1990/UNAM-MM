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

    conac_debit_account_id = fields.Many2one(
        'coa.conac', string='CONAC Debit Account')
    conac_credit_account_id = fields.Many2one(
        'coa.conac', string='CONAC Credit Account')
    execercise_credit_account_id = fields.Many2one('account.account', "Default Credit Account")
    conac_exe_credit_account_id = fields.Many2one('coa.conac', "CONAC Credit Account")
    execercise_debit_account_id = fields.Many2one('account.account', "Default Debit Account")
    conac_exe_debit_account_id = fields.Many2one('coa.conac', "CONAC Debit Account")
    paid_credit_account_id = fields.Many2one('account.account', "Default Credit Account")
    conac_paid_credit_account_id = fields.Many2one('coa.conac', "CONAC Credit Account")
    paid_debit_account_id = fields.Many2one('account.account', "Default Debit Account")
    conac_paid_debit_account_id = fields.Many2one('coa.conac', "CONAC Debit Account")

    def write(self, vals):
        res = super(AccountJournal, self).write(vals)
        acc_obj = self.env['account.account']
        for record in self:
            if vals.get('default_credit_account_id'):
                default_credit_account_id = acc_obj.browse(vals.get('default_credit_account_id'))
                if default_credit_account_id.coa_conac_id:
                    record.conac_credit_account_id = default_credit_account_id.coa_conac_id
            if vals.get('default_debit_account_id'):
                default_debit_account_id = acc_obj.browse(vals.get('default_debit_account_id'))
                if default_debit_account_id.coa_conac_id:
                    record.conac_debit_account_id = default_debit_account_id.coa_conac_id
            if vals.get('execercise_credit_account_id'):
                execercise_credit_account_id = acc_obj.browse(vals.get('execercise_credit_account_id'))
                if execercise_credit_account_id.coa_conac_id:
                    record.conac_exe_credit_account_id = execercise_credit_account_id.coa_conac_id
            if vals.get('execercise_debit_account_id'):
                execercise_debit_account_id = acc_obj.browse(vals.get('execercise_debit_account_id'))
                if execercise_debit_account_id.coa_conac_id:
                    record.conac_exe_debit_account_id = execercise_debit_account_id.coa_conac_id
            if vals.get('paid_credit_account_id'):
                paid_credit_account_id = acc_obj.browse(vals.get('paid_credit_account_id'))
                if paid_credit_account_id.coa_conac_id:
                    record.conac_paid_credit_account_id = paid_credit_account_id.coa_conac_id
            if vals.get('paid_debit_account_id'):
                paid_debit_account_id = acc_obj.browse(vals.get('paid_debit_account_id'))
                if paid_debit_account_id.coa_conac_id:
                    record.conac_paid_debit_account_id = paid_debit_account_id.coa_conac_id
        return res

    @api.onchange('default_credit_account_id', 'default_debit_account_id')
    def onchange_account(self):
        if self.default_credit_account_id and self.default_credit_account_id.coa_conac_id:
            self.conac_credit_account_id = self.default_credit_account_id.coa_conac_id
        else:
            self.conac_credit_account_id = False
        if self.default_debit_account_id and self.default_debit_account_id.coa_conac_id:
            self.conac_debit_account_id = self.default_debit_account_id.coa_conac_id
        else:
            self.conac_debit_account_id = False

    @api.onchange('execercise_credit_account_id', 'execercise_debit_account_id')
    def onchange_exe_account(self):
        if self.execercise_credit_account_id and self.execercise_credit_account_id.coa_conac_id:
            self.conac_exe_credit_account_id = self.execercise_credit_account_id.coa_conac_id
        else:
            self.conac_exe_credit_account_id = False
        if self.execercise_debit_account_id and self.execercise_debit_account_id.coa_conac_id:
            self.conac_exe_debit_account_id = self.execercise_debit_account_id.coa_conac_id
        else:
            self.conac_exe_debit_account_id = False

    @api.onchange('paid_credit_account_id', 'paid_debit_account_id')
    def onchange_paid_account(self):
        if self.paid_credit_account_id and self.paid_credit_account_id.coa_conac_id:
            self.conac_paid_credit_account_id = self.paid_credit_account_id.coa_conac_id
        else:
            self.conac_paid_credit_account_id = False
        if self.paid_debit_account_id and self.paid_debit_account_id.coa_conac_id:
            self.conac_paid_debit_account_id = self.paid_debit_account_id.coa_conac_id
        else:
            self.conac_paid_debit_account_id = False