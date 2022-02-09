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
from odoo import models, fields,_


class RequestConfirm(models.TransientModel):
    _name = 'request.confirm'

    bank_account_id = fields.Many2one(
        'account.journal', string='Bank', domain=[('type', '=', 'bank')])
    bank_acc_number_id = fields.Many2one(
        related='bank_account_id.bank_account_id', string="Bank Account")
    no_contract = fields.Char(
        related='bank_account_id.contract_number', string='No. contract')

    def apply(self):

        active_id = self._context.get('active_id', False)
        if active_id:
            request_account_id = self.env['request.accounts'].browse(active_id)
            request_account_id.bank_account_id = self.bank_account_id
            request_account_id.bank_acc_number_id = self.bank_acc_number_id.acc_number
            request_account_id.no_contract = self.no_contract
            request_account_id.customer_number = self.bank_account_id.customer_number
            request_account_id.confirm_account()
            
