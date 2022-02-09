from odoo import models, fields,api,_
from odoo.exceptions import ValidationError

class DepositCertificateType(models.Model):

    _name = 'deposit.certificate.type'
    _description = "Type of Deposit Certificate"

    name = fields.Char("Name")
    description = fields.Text("General Description")
    
    @api.constrains('name')
    def _check_code(self):
        for rec in self:
            if rec.name:
                deposit_id = self.env['deposit.certificate.type'].search([('name','=',rec.name),('id','!=',rec.id)],limit=1)
                if deposit_id:
                    raise ValidationError(_("There is already a record with the same Certificate of Deposit Name"))    