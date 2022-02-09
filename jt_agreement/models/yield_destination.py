from odoo import models, fields, api , _ 
from datetime import datetime
from odoo.exceptions import UserError


class YieldDestination(models.Model):

    _name = 'yield.destination'
    _description = "Yield Destination"

    name = fields.Char(string="Yield Destination",required=1)
