from odoo import models, fields, api, _


class AccountJournal(models.Model):
    
    _inherit = "account.journal"

    estimate_income_credit_account_id = fields.Many2one('account.account', "Default Credit Account")
    conac_estimate_income_credit_account_id = fields.Many2one(related='estimate_income_credit_account_id.coa_conac_id', string="CONAC Credit Account")
    estimate_income_debit_account_id = fields.Many2one('account.account', "Default Debit Account")
    conac_estimate_income_debit_account_id = fields.Many2one(related='estimate_income_debit_account_id.coa_conac_id', string="CONAC Debit Account")

    income_run_credit_account_id = fields.Many2one('account.account', "Default Credit Account")
    conac_income_run_credit_account_id = fields.Many2one(related='income_run_credit_account_id.coa_conac_id', string="CONAC Credit Account")
    income_run_debit_account_id = fields.Many2one('account.account', "Default Debit Account")
    conac_income_run_debit_account_id = fields.Many2one(related='income_run_debit_account_id.coa_conac_id', string="CONAC Debit Account")

    accrued_income_credit_account_id = fields.Many2one('account.account', "Default Credit Account")
    conac_accrued_income_credit_account_id = fields.Many2one(related='accrued_income_credit_account_id.coa_conac_id', string="CONAC Credit Account")
    accrued_income_debit_account_id = fields.Many2one('account.account', "Default Debit Account")
    conac_accrued_income_debit_account_id = fields.Many2one(related='accrued_income_debit_account_id.coa_conac_id', string="CONAC Debit Account")

    recover_income_credit_account_id = fields.Many2one('account.account', "Default Credit Account")
    conac_recover_income_credit_account_id = fields.Many2one(related='recover_income_credit_account_id.coa_conac_id', string="CONAC Credit Account")
    recover_income_debit_account_id = fields.Many2one('account.account', "Default Debit Account")
    conac_recover_income_debit_account_id = fields.Many2one(related='recover_income_debit_account_id.coa_conac_id', string="CONAC Debit Account")

    for_income = fields.Boolean(related="bank_account_id.for_income",string="Income")
    