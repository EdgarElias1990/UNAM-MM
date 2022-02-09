from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class TypeOfReissue(models.Model):

    _name = 'type.of.reissue'
    _description = "Type Of Reissue"

    name = fields.Char('Description of the reissue')