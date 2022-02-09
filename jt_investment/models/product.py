from odoo import models, fields, api

class Product(models.Model):

    _inherit = 'product.template'

    type = fields.Selection(selection_add=[('investment', 'Investment')], tracking=True)
    
    investment_income_account_id = fields.Many2one('account.account','Income Account')
    investment_expense_account_id = fields.Many2one('account.account','Expense Account')
    investment_price_diff_account_id = fields.Many2one('account.account','Price Difference Account')