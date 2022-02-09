# -*- coding: utf-8 -*-
##############################################################################
#
#    Jupical Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Jupical Technologies(<http://www.jupical.com>).
#    Author: Jupical Technologies Pvt. Ltd.(<http://www.jupical.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AgreementType(models.Model):

    _name = 'agreement.agreement.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Agreement Type"
    
    code = fields.Char("Agreement Type Code")
    group = fields.Char("Group",size=1,required=True)
    name = fields.Char("Name of Agreement Type")
    fund_type_id = fields.Many2one('fund.type', "Fund Type")
    fund_id = fields.Many2one('agreement.fund',string="Fund")



    @api.constrains('code')
    def _check_code(self):
        code = self.code
        code_id = self.env['agreement.agreement.type'].search([('code','=',code),('id','!=',self.id)],limit=1)
        if code_id:
            raise ValidationError(_("Code Value Must Be Unique"))
        if self.code and len(self.code) != 2:
            raise ValidationError(_('Agreement Type Code must be 2 characters.'))

    @api.constrains('group')
    def _check_group(self):
        group = self.group
#         group_id = self.env['agreement.agreement.type'].search([('group','=',group),('id','!=',self.id)],limit=1)
#         if group_id:
#             raise ValidationError(_("Group Value Must Be Unique"))
        
        if group.isdigit():
            return True
        else:
            raise ValidationError(_("Group Value Must Be numeric"))


