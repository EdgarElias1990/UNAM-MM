from odoo import models, fields


class RemainingResource(models.Model):
    _name = 'remaining.resource'
    _description = "Integration of remaining resources"
    _rec_name = 'concept'

    concept = fields.Char('Concept')
    stage_id = fields.Many2one("project.custom.stage","Stage")
    stage_name = fields.Char(related='stage_id.name')
    year = fields.Char("Year",size=4)
    project_type = fields.Selection(
        [('papit', 'PAPIIT'), ('papime', 'PAPIME'), ('infocab', 'INFOCAB')], string='Project Type')
    account_id = fields.Many2one('account.account')
