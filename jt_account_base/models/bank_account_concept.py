from odoo import models, fields, api, _
from odoo.exceptions import UserError
import re

class BankAccountConcept(models.Model):
    _name = 'bank.account.concept'
    
    name = fields.Char('Concept')
    bank_account_id = fields.Many2one('res.partner.bank','Bank Accounts')

class ResBank(models.Model):

    _inherit = 'res.partner.bank'

    for_finance = fields.Boolean("Finance")
    for_payment = fields.Boolean("Payment")
    for_payroll = fields.Boolean("Payroll")
    for_budget = fields.Boolean("Budget")
