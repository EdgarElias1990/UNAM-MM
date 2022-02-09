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


class PreceptionLine(models.Model):
    _inherit = 'preception.line'

    program_code_id = fields.Many2one("program.code", string="Program Code")

class EmployeePayroll(models.Model):

    _inherit = 'employee.payroll.file'

    dependancy_id = fields.Many2one(related="employee_id.dependancy_id", string='Dependency')
    sub_dependancy_id = fields.Many2one(related="employee_id.sub_dependancy_id", string='Sub Dependency')
    program_code_id = fields.Many2one("program.code", string="Program Code")
    total_preception = fields.Float("Total Preception", compute="_compute_preception", store=True)

    @api.depends('preception_line_ids')
    def _compute_preception(self):
        for file in self:
            file.total_preception = sum(line.amount if line.program_code_id else 0 for line in file.preception_line_ids)

    def get_invoice_line_vals(self,line):
        invoice_line_vals = super(EmployeePayroll,self).get_invoice_line_vals(line)
        if line.program_code_id:
            account_id = line.program_code_id and line.program_code_id.item_id and line.program_code_id.item_id.unam_account_id and line.program_code_id.item_id.unam_account_id.id or False
            invoice_line_vals.update({'program_code_id':line.program_code_id and line.program_code_id.id or False})
            if account_id:
                invoice_line_vals.update({'account_id':account_id})
#             else:
#                 invoice_line_vals = {}
#         else:
#             invoice_line_vals = {}
            
        return invoice_line_vals
    
    def get_payroll_payment_vals(self):
        vals = super(EmployeePayroll,self).get_payroll_payment_vals()
        # invoice_line_vals = self.get_invoice_line_vals() 
        vals.update({'dependancy_id':self.dependancy_id and self.dependancy_id.id or False,
                     'sub_dependancy_id' : self.sub_dependancy_id and self.sub_dependancy_id.id or False,
                     'payment_place_id' : self.payment_place_id and self.payment_place_id.id or False,
                     #'invoice_line_ids':[(0,0,invoice_line_vals)]
                     })
        
        return vals
    
class PaymentRequest(models.Model):

    _inherit = 'payment.request'

    dependancy_id = fields.Many2one('dependency', string='Dependency')
    sub_dependancy_id = fields.Many2one('sub.dependency', 'Sub Dependency')
    program_code_id = fields.Many2one("program.code", string="Program Code")

class AdditionalPaymentsLine(models.Model):
    
    _inherit = 'additional.payments.line'
    
    program_code_id = fields.Many2one("program.code", string="Program Code")
    