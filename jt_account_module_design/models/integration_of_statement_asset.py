from odoo import models, fields, api,_

class ProjectCustomStage(models.Model):

    _name = 'integration.statement.asset'
    _description = "Integration Of some items of the Statement of Assets"
    _rec_name = "concept"

    concept = fields.Char(string='Concept')
    account_ids = fields.Many2many('account.account', string='Account')