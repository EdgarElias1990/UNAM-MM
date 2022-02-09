from odoo import models, fields,api,_
from odoo.exceptions import ValidationError

class PaymentOfIncome(models.Model):

    _name = 'payment.of.income'
    _description = "Payment Of Income"
    
    name = fields.Char("Payment of")
    description = fields.Text("Description")
    
    def name_get(self):
        result = []
        for rec in self:
            name = ''
            if rec.name:
                name = rec.name
            if rec.description: 
                name += ' ' + rec.description
                
            result.append((rec.id, name))
        return result

    @api.constrains('name')
    def _check_code(self):
        for rec in self:
            if rec.name:
                deposit_id = self.env['payment.of.income'].search([('name','=',rec.name),('id','!=',rec.id)],limit=1)
                if deposit_id:
                    raise ValidationError(_("There is already a record with the same Collection of"))        
