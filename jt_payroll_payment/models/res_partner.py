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

class Contacts(models.Model):

    _inherit = 'res.partner'

    supplier_of_payment_payroll = fields.Boolean("Supplier of payment of payroll")
    workstation_id = fields.Many2one('hr.job', "Appointment")
    category_key = fields.Many2one(string="Category Key", related='workstation_id.category_key', store=True)
    
    @api.model
    def default_get(self, fields):
        res = super(Contacts, self).default_get(fields)
        account_id = self.env['account.account'].sudo().search([('code','=','120.001.001'),('internal_type','=','receivable'),('deprecated','=',False)],limit=1)
        if account_id:
            res.update({'property_account_receivable_id': account_id.id})
        return res

    @api.model
    def create(self, vals):
        res = super(Contacts, self).create(vals)
        if vals.get('supplier_of_payment_payroll'):
            is_sup = self.search([('supplier_of_payment_payroll', '=', True)])
            if is_sup:
                raise UserError(_("There must be only one Supplier of payment of payroll!"))
        if not res.property_account_receivable_id:
            account_id = self.env['account.account'].sudo().search([('code','=','120.001.001'),('internal_type','=','receivable'),('deprecated','=',False)],limit=1)
            if account_id:
                res.property_account_receivable_id = account_id.id
            
        return res


    def write(self, vals):
        if vals.get('supplier_of_payment_payroll'):
            is_sup = self.search([('supplier_of_payment_payroll', '=', True)])
            if is_sup:
                raise UserError(_("There must be only one Supplier of payment of payroll!"))
        res = super(Contacts, self).write(vals)
        return res
    
    @api.constrains('name')
    def check_min_balance(self):
        for rec in self:
            if rec.name:
                if rec.name=="ISSSTE":
                    if self.env['res.partner'].search([('name','=','ISSSTE'),('id','!=',rec.id)]):
                        raise UserError(_('Contact ISSSTE already exists.'))
                if rec.name=="FOVISSSTE":
                    if self.env['res.partner'].search([('name','=','FOVISSSTE'),('id','!=',rec.id)]):
                        raise UserError(_('Contact FOVISSSTE already exists.'))
