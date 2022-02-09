from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class NumeroDeposito(models.Model):
    _inherit = 'account.move'

    deposite_number = fields.Char(string="Número de depósito")