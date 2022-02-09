from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError

class ResPartnerBank(models.Model):

    _inherit = 'res.partner.bank'
    
    minimum_balance = fields.Float('Minimum Balance')
