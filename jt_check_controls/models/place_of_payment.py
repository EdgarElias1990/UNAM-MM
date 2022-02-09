from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError

class PlaceOfPayments(models.Model):
    _inherit = 'payment.place'

    module = fields.Selection([('ACATLAN', 'ACATLAN'),
                               ('ARAGON', 'ARAGON'), ('CUAUTITLAN', 'CUAUTITLAN'),
                               ('CUERNAVACA', 'CUERNAVACA'),
                               ('COVE', 'COVE'), ('IZTACALA', 'IZTACALA'),
                               ('JURIQUILLA', 'JURIQUILLA'), ('LION', 'LION'),
                               ('MORELIA', 'MORELIA'), ('YUCATAN', 'YUCATAN')], string="Module")
