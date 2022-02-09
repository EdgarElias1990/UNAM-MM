from odoo import models, fields, api,_

class DetailedIncomeStatement(models.Model):

    _name = 'detailed.statement.income'
    _description = "Detailed Statement of income"
    _rec_name = "concept"

    concept = fields.Char(string='Concept')
    account_ids = fields.Many2many('account.account', string='Account')
    inc_exp_type = fields.Selection([('income', 'Income'), ('expenses', 'Expenses'),('investments','INVESTMENTS'),('other expenses','OTHER EXPENSES')],string='Type')
    major_id = fields.Many2one("income.major.details","Major")
    item_ids = fields.Many2many("expenditure.item","rel_item_details_statement_income",'item_id','income_id',"Item")

class IncomeMajorDetails(models.Model):
    
    _name = "income.major.details"
    
    name = fields.Char("Major")    