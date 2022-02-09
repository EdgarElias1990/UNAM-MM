from odoo import models, fields, api,_
from datetime import date
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class AgreementType(models.Model):
    
    _inherit = 'agreement.type'    

    base_id = fields.Many2one('bases.collaboration','Type of Agreement')
    name = fields.Char(string='Name', related="base_id.name")
    number = fields.Char(string='Number', related="base_id.convention_no")
 