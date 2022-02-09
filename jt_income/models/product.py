from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class Product(models.Model):

    _inherit = 'product.template'

    unit_id = fields.Many2one('dependency', string="Dependency")
    sub_dependency_id = fields.Many2one('sub.dependency', string="Subdependency")
    activity_id = fields.Many2one('activity.catalog', string="ID Activity")
    parent_product_id = fields.Many2one('product.product', string="Parent Product")
    sub_product = fields.Boolean("Subproduct")
    do_you_require_password = fields.Boolean("Do you require password?")
    ie_account_id = fields.Many2many('association.distribution.ie.accounts','ie_accounts_product','product_id','ie_account','IE Account')

    _sql_constraints = [('unique_default_code', 'unique(default_code)', (_('Internal Reference must be unique.'))),
                        ]
    
    @api.onchange('parent_product_id')
    def onchange_parent_product(self):
        if self.parent_product_id:
            self.sub_product = True
        else:
            self.sub_product = False

    @api.model
    def create(self,vals):
        res = super(Product,self).create(vals)
        if res.sub_dependency_id and res.unit_id:
            new_sub_dep_id = self.env['sub.dependency'].search([('dependency_id','=',res.unit_id.id),('sub_dependency','=',res.sub_dependency_id.sub_dependency)],limit=1)
            if new_sub_dep_id:
                res.sub_dependency_id = new_sub_dep_id.id
                
        if not res.default_code:
            raise ValidationError(_('Internal Reference NULL Not Allowed!'))
        return res
    
#     @api.constrains('default_code')
#     def _project_number_unique(self):
#         for record in self:
#             print ("Record===",record)
#             print ("default_code===",record.default_code)
#             if not record.default_code:
#                 raise ValidationError(_('Internal Reference NULL Not Allowed!'))            