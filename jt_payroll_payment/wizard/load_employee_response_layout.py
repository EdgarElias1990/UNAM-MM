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
from odoo import models, fields,_
from odoo.exceptions import UserError, ValidationError
import base64
from datetime import datetime, timedelta
from odoo.tools.misc import formatLang, format_date, get_lang
from babel.dates import format_datetime, format_date
import io

class LoadBankLayoutEmployee(models.TransientModel):

    _name = 'load.bank.layout.employee'
    _description = 'Load Bank Layout Employee'

    bank_layout = fields.Selection([('BANORTE','BANORTE')],string="Layout")
    employee_ids = fields.Many2many('hr.employee','hr_employee_load_bank_layout_rel','bank_layout_id','emp_id','Employee')
    file_name = fields.Char('Filename')
    file_data = fields.Binary('Upload')

    failed_file_name = fields.Char('Failed Filename', default=lambda self: _("Failed_Rows.txt"))
    failed_file_data = fields.Binary('Failed File')
    success_file_name = fields.Char('Success Filename',default="Success_Rows.txt")
    success_file_data = fields.Binary('Success File')
    is_hide_failed = fields.Boolean('Hide Failed',default=True)
    is_hide_success = fields.Boolean('Hide Success',default=True)
    is_hide_file_upload = fields.Boolean('Hide Success',default=False)


    def action_load_bank_layout(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return ''
        
        return {
            'name': _('Load Bank Layout'),
            'res_model': 'load.bank.layout.employee',
            'view_mode': 'form',
            'view_id': self.env.ref('jt_payroll_payment.view_load_bank_layout_employee_form').id,
            'context': {'default_employee_ids':[(6,0,active_ids)]},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }    


    def get_banorte_file(self):
        try:
            failed_content = ''
            success_content = ''
            
            file_data = base64.b64decode(self.file_data)
            data = io.StringIO(file_data.decode("utf-8")).readlines()
            count = 0
            for line in data:
                count+=1
                emp_number = line[1:11]
                state = line[139:149]
                if emp_number and state:
                    
                    emp_number = emp_number.lstrip('0')
                    state = state.strip() 
                    match_emp =  self.employee_ids.filtered(lambda x:x.worker_number==emp_number)
                    if match_emp:
                        if state=='Confirmed' or state=='Rejected': 
                            success_content += str(count)+' : '+ str(line) + "\n"    
                            registration = False
                            if state=='Confirmed':
                                registration = 'confirmed'
                            if state=='Rejected':
                                registration = 'rejected'
                            match_emp[0].registration = registration
                    else:
                        failed_content += str(count)+' : '+ str(line) + "\n"
                else:
                    failed_content += str(count)+' : '+ str(line) + "\n"

            if failed_content:
                failed_data = base64.b64encode(failed_content.encode('utf-8'))
                self.failed_file_data = failed_data
                self.is_hide_failed = False
                
            if success_content:
                success_data = base64.b64encode(success_content.encode('utf-8'))
                self.success_file_data = success_data
                self.is_hide_success = False
                                                                
        except:
            raise Warning(_("File Format not Valid!"))        

    def load_bank_layout(self):

        if self.bank_layout == 'BANORTE':
            self.get_banorte_file()
            
        self.is_hide_file_upload = True        
        return {
            'name': _('Load Bank Layout'),
            'res_model': 'load.bank.layout.employee',
            'res_id' : self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('jt_payroll_payment.view_load_bank_layout_employee_form').id,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

