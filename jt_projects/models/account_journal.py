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
########################
######################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import re
from datetime import datetime

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_conacyt_project = fields.Boolean(string='CONACYT Project',default=False,copy=False)
    is_purchase_of_foreign_curr = fields.Boolean(string='Purchase of Foreign Currency',default=False,copy=False)


    receivable_CFDIS_credit_account_id = fields.Many2one('account.account', "Default Credit Account")
    conac_receivable_CFDIS_credit_account_id = fields.Many2one(related='receivable_CFDIS_credit_account_id.coa_conac_id', string="CONAC Credit Account")
    receivable_CFDIS_debit_account_id = fields.Many2one('account.account', "Default Debit Account")
    conac_receivable_CFDIS_debit_account_id = fields.Many2one(related='receivable_CFDIS_debit_account_id.coa_conac_id', string="CONAC Debit Account")

    income_CFDIS_credit_account_id = fields.Many2one('account.account', "Default Credit Account")
    conac_income_CFDIS_credit_account_id = fields.Many2one(related='income_CFDIS_credit_account_id.coa_conac_id', string="CONAC Credit Account")
    income_CFDIS_debit_account_id = fields.Many2one('account.account', "Default Debit Account")
    conac_income_CFDIS_debit_account_id = fields.Many2one(related='income_CFDIS_debit_account_id.coa_conac_id', string="CONAC Debit Account")

    ministrations_credit_account_id = fields.Many2one('account.account', "Default Credit Account")
    conac_ministrations_credit_account_id = fields.Many2one(related='ministrations_credit_account_id.coa_conac_id', string="CONAC Credit Account")
    ministrations_debit_account_id = fields.Many2one('account.account', "Default Debit Account")
    conac_ministrations_debit_account_id = fields.Many2one(related='ministrations_debit_account_id.coa_conac_id', string="CONAC Debit Account")

    ei_credit_account_id = fields.Many2one('account.account', "Default Credit Account")
    conac_ei_credit_account_id = fields.Many2one(related='ei_credit_account_id.coa_conac_id', string="CONAC Credit Account")
    ei_debit_account_id = fields.Many2one('account.account', "Default Debit Account")
    conac_ei_debit_account_id = fields.Many2one(related='ei_debit_account_id.coa_conac_id', string="CONAC Debit Account")

    ai_credit_account_id = fields.Many2one('account.account', "Default Credit Account")
    conac_ai_credit_account_id = fields.Many2one(related='ai_credit_account_id.coa_conac_id', string="CONAC Credit Account")
    ai_debit_account_id = fields.Many2one('account.account', "Default Debit Account")
    conac_ai_debit_account_id = fields.Many2one(related='ai_debit_account_id.coa_conac_id', string="CONAC Debit Account")

    capitalizable_credit_account_id = fields.Many2one('account.account', "Default Credit Account")
    conac_capitalizable_credit_account_id = fields.Many2one(related='capitalizable_credit_account_id.coa_conac_id', string="CONAC Credit Account")
    capitalizable_debit_account_id = fields.Many2one('account.account', "Default Debit Account")
    conac_capitalizable_debit_account_id = fields.Many2one(related='capitalizable_debit_account_id.coa_conac_id', string="CONAC Debit Account")
    
    
    
