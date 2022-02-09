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
from odoo.exceptions import ValidationError

class MassApproveTransfer(models.TransientModel):
    _name = 'mass.approve.transfer'
    _description = "Mass Approve Transfer"

    bank_account_id = fields.Many2one(
        'account.journal', "Origin Bank")
    origin_account = fields.Many2one(related="bank_account_id.bank_account_id" , string="Account Origin")
    
    def approve(self):
        context = self.env.context
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        recs = self.env[active_model].browse(active_ids)
        for rec in recs:
            rec.bank_account_id = self.bank_account_id and self.bank_account_id.id or False
            rec.approve_finance()
        