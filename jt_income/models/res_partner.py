from odoo import models, fields, api

class ResPartner(models.Model):

    _inherit = 'res.partner'

    contact_type = fields.Selection([('client', 'Client'),
                                     ('provider', 'Provider')], string="Contact Type")
    
    income_control = fields.Char('Control')