from odoo import models, fields, api,_

class ProjectCustomStage(models.Model):

    _name = 'miles.revenue'
    _description = "Miles Revenue"
    _rec_name = "concept"

    concept = fields.Char(string='Concept')
    account_ids = fields.Many2many('account.account', string='Account')
