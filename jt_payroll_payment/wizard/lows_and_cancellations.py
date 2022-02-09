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
import base64
import xlrd
from datetime import datetime
from odoo.modules.module import get_resource_path
from xlrd import open_workbook
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import ustr

class LowsAndCancellationWizard(models.TransientModel):

    _name = 'lows.cancellation.wizard'
    _description = "Lows And Cancellation Wizard"

    type_of_movement = fields.Selection([('casualties_cancellations','Casualties and cancellations'),
                                         ('BDEF','BDEF'),
                                         ],string='Casualties and cancellations')
    
    file = fields.Binary('File to import')
    filename = fields.Char('FileName')
    
    employee_ids = fields.Many2many('hr.employee','employee_lows_payroll_wizard_rel','employee_id','wizard_id','Employees')
    payroll_process_id = fields.Many2one('custom.payroll.processing','Payroll Process')
    
    def generate(self):
        if self.file:
            data = base64.decodestring(self.file)
            book = open_workbook(file_contents=data or b'')
            sheet = book.sheet_by_index(0)

            if self.type_of_movement == 'casualties_cancellations' or self.type_of_movement=='BDEF':
                for rowx, row in enumerate(map(sheet.row, range(1, sheet.nrows)), 1):
                    
                    rfc = row[0].value
                    lows = row[1].value
                    
                    #bank_no = row[2].value
                    #pension = row[3].value
                    
                    employee_id = False
                    emp_payroll_ids = []
                    if rfc:
                        employee_id =self.env['hr.employee'].search([('rfc','=',rfc)],limit=1)
                        if employee_id:
                            employee_id = employee_id.id
                        
                    if employee_id:
                        emp_payroll_ids = self.payroll_process_id.payroll_ids.filtered(lambda x:x.employee_id.id==employee_id)
                    
                    print ("===EMp===",emp_payroll_ids)    
                    for rec in emp_payroll_ids:
                        print ("===lllllll===",lows)
                        if lows:
                            print ("===lows===",lows)
                            lows_selection = False
                            
                            if lows=='B':
                                lows_selection = 'B'
                            elif lows=='BD':
                                lows_selection = 'BD'
                            elif lows=='BDEF':
                                lows_selection = 'BDEF'
                            
                            rec.casualties_and_cancellations = lows_selection