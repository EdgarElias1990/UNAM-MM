from odoo import models, fields,api,_
from odoo.exceptions import ValidationError

class ActivityCatalog(models.Model):

    _name = 'activity.catalog'
    _description = "Activity Catalog"
    _rec_name = 'activity_id'

    activity_id = fields.Char("ID")
    description = fields.Text("Description")

    @api.constrains('activity_id')
    def _check_code(self):
        for rec in self:
            if rec.activity_id:
                activity_id = self.env['activity.catalog'].search([('activity_id','=',rec.activity_id),('id','!=',rec.id)],limit=1)
                if activity_id:
                    raise ValidationError(_("There is already a record with the same Activity ID"))
            
    def name_get(self):
        result = []
        for rec in self:
            name = rec.activity_id or ''
            if rec.description: 
                name += ' ' + rec.description
            result.append((rec.id, name))
        return result