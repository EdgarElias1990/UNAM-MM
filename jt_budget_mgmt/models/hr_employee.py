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
from odoo.exceptions import UserError

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    dependancy_id = fields.Many2one('dependency', string='Dependency')
    dependancy_description = fields.Text(related="dependancy_id.description",string="Dependency Description")
    sub_dependancy_id = fields.Many2one('sub.dependency', 'Sub Dependency')
    sub_dependancy_id_description = fields.Text(related="sub_dependancy_id.description",string="Sub dependency     Description")

    @api.onchange('payment_place_id')
    def onchange_payment_place_id_dep(self):
        if self.payment_place_id:
            self.dependancy_id = self.payment_place_id.dependancy_id and self.payment_place_id.dependancy_id.id or False
            self.sub_dependancy_id = self.payment_place_id.sub_dependancy_id and self.payment_place_id.sub_dependancy_id.id or False 
    
    @api.model
    def create(self,vals):
        res = super(HrEmployee,self).create(vals)
        if res.payment_place_id and not res.dependancy_id:
            res.dependancy_id = res.payment_place_id.dependancy_id and res.payment_place_id.dependancy_id.id or False
        if res.payment_place_id and not res.sub_dependancy_id:
            sub_dependancy_id = False
            if res.payment_place_id.sub_dependancy_id:
                sub_dependancy_id = res.payment_place_id.sub_dependancy_id.id
                if res.dependancy_id and res.payment_place_id.sub_dependancy_id.dependency_id and res.dependancy_id.id != res.payment_place_id.sub_dependancy_id.dependency_id.id:
                    sub_dependancy_id = self.env['sub.dependency'].get_sub_dep_records(res.payment_place_id.sub_dependancy_id.sub_dependency,res.dependancy_id.id)
            res.sub_dependancy_id = sub_dependancy_id
            
        return res
    
    def write(self,vals):
        result = super(HrEmployee,self).write(vals)
        if vals.get('payment_place_id',False):
            for res in self:
                if res.payment_place_id and not res.dependancy_id:
                    res.dependancy_id = res.payment_place_id.dependancy_id and res.payment_place_id.dependancy_id.id or False
                if res.payment_place_id and not res.sub_dependancy_id:
                    res.sub_dependancy_id = res.payment_place_id.sub_dependancy_id and res.payment_place_id.sub_dependancy_id.id or False
        return result
