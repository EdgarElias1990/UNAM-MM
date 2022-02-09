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

class AdjustedPayrollWizard(models.TransientModel):

    _name = 'adjusted.payroll.wizard'
    _description = "Adjusted Payroll Wizard"

    type_of_movement = fields.Selection([('adjustment','Adjustment'),
                                         ('perception_adjustment_detail','Perception Adjustment Detail'),
                                         ('deduction_adjustment_detail','Deduction Adjustment Detail'),
                                         ('detail_alimony_adjustments','Detail of Alimony Adjustments'),
                                         ],string='Adjustment Type')
    
    file = fields.Binary('File to import')
    filename = fields.Char('FileName')
    
    employee_ids = fields.Many2many('hr.employee','employee_adjusted_payroll_wizard_rel','employee_id','wizard_id','Employees')
    payroll_process_id = fields.Many2one('custom.payroll.processing','Payroll Process')
    
    def update_employee_payroll_pension(self,rec,payment_method_id,deposit_number,check_number,bank_account_id,bank_key,bank_id):

        log = False
        bank_records = self.env['res.bank'].search_read([], fields=['id', 'l10n_mx_edi_code'])
        if bank_key and check_number:
            if type(bank_key) is int or type(bank_key) is float:
                bank_key = int(bank_key)

            log,from_check= self.env['custom.payroll.processing'].get_perception_check_log(check_number,bank_key)
        
        exit_vals = {'l10n_mx_edi_payment_method_id' : payment_method_id,
                     'deposite_number' : deposit_number,
                     'check_number' : check_number,
                     'bank_key' : bank_key,
                     'receiving_bank_acc_pay_id' : bank_account_id,
        
                    }
        if log:
            exit_vals.update({'check_folio_id':log.id})
        rec.write(exit_vals)
    
    def update_employee_payroll_perception(self,emp_payroll_ids,payment_method,bank_key,check_number,deposite_number,ben):

        bank_records = self.env['res.bank'].search_read([], fields=['id', 'l10n_mx_edi_code'])
        bank_account_records = self.env['res.partner.bank'].search_read([], fields=['id', 'acc_number'])
        payment_method_records = self.env['l10n_mx_edi.payment.method'].search_read([], fields=['id', 'name'])

        rec_check_number = check_number
        rec_deposite_number = deposite_number
        rec_bank_key = bank_key
        bank_account = ben
        bank_account_id = False
        log = False
        payment_method_id = False
            
        if payment_method and str(payment_method).isalnum():    
            if  type(payment_method) is int or type(payment_method) is float:
                payment_method = int(payment_method)
        else:
            payment_method = str(payment_method)
              
        payment_method_id = list(filter(lambda pm: pm['name'] == str(payment_method), payment_method_records))
        payment_method_id = payment_method_id[0]['id'] if payment_method_id else False
        
        if check_number:
            if  type(check_number) is int or type(check_number) is float:
                rec_check_number = int(check_number)

        if deposite_number:
            if  type(deposite_number) is int or type(deposite_number) is float:
                rec_deposite_number = int(deposite_number)

        if bank_key and rec_check_number:
            if type(bank_key) is int or type(bank_key) is float:
                rec_bank_key = int(bank_key)

            bank_id_1 = list(filter(lambda b: b['l10n_mx_edi_code'] == rec_bank_key, bank_records))
            bank_id_1 = bank_id_1[0]['id'] if bank_id_1 else False

            log,from_check= self.env['custom.payroll.processing'].get_perception_check_log(rec_check_number,rec_bank_key)
            
        if bank_account and str(bank_account).isalnum():
            if  type(bank_account) is int or type(bank_account) is float:
                bank_account = int(bank_account)
        elif bank_account and str(bank_account).isnumeric():
            if  type(bank_account) is int or type(bank_account) is float:
                bank_account = int(bank_account)
        if  type(bank_account) is int or type(bank_account) is float:
            bank_account = int(bank_account)
                
        bank_account_id = list(filter(lambda b: b['acc_number'] == str(bank_account), bank_account_records))
        bank_account_id = bank_account_id[0]['id'] if bank_account_id else False
        
        exit_vals = {'l10n_mx_edi_payment_method_id' : payment_method_id,
                     'bank_key' : rec_bank_key,
                     'receiving_bank_acc_pay_id' : bank_account_id
                    }
        check_payment_method = self.env.ref('l10n_mx_edi.payment_method_cheque')
        if not payment_method_id:
            exit_vals.update({'deposite_number' : rec_deposite_number,'check_number' : rec_check_number})
            if log:
                exit_vals.update({'check_folio_id':log.id})
            
        elif check_payment_method and payment_method_id and check_payment_method.id!=payment_method_id:
            exit_vals.update({'deposite_number' : rec_deposite_number,'check_number' : rec_check_number,})
            if log:
                exit_vals.update({'check_folio_id':log.id})
            
        emp_payroll_ids.write(exit_vals)
        
    def generate(self):
        if self.file:
            data = base64.decodestring(self.file)
            book = open_workbook(file_contents=data or b'')
            sheet = book.sheet_by_index(0)

            if self.type_of_movement == 'adjustment':
                for rowx, row in enumerate(map(sheet.row, range(1, sheet.nrows)), 1):
                    
                    counter = 0
                    case = row[0].value
                    check_no = row[1].value
                    bank_no = row[2].value
                    deposite_no = row[3].value
                    new_bank_no = row[4].value
                    emp_no = row[5].value
                    q_digit = row[6].value
                    q_new_digit = row[7].value
                    rfc = row[8].value
                    old_amount = row[9].value
                    new_amount = row[10].value
                    
                    employee_id = False
                    emp_payroll_ids = []
                    if rfc:
                        employee_id =self.env['hr.employee'].search([('rfc','=',rfc)],limit=1)
                        if employee_id:
                            employee_id = employee_id.id
                    
                    case_id = self.env['adjustment.cases'].search([('case','=',case)],limit=1)
                        
                    if employee_id:
                        emp_payroll_ids = self.payroll_process_id.payroll_ids.filtered(lambda x:x.employee_id.id==employee_id)
                    
                    for rec in emp_payroll_ids:
                        check_payment_method = self.env.ref('l10n_mx_edi.payment_method_cheque').id
                        if check_payment_method:
                            rec.l10n_mx_edi_payment_method_id = check_payment_method

                        if deposite_no and new_bank_no:
                            log = self.env['check.log'].search([('folio', '=', deposite_no),
                            ('status', 'in', ('Checkbook registration', 'Assigned for shipping',
                            'Available for printing')), ('general_status', '=', 'available'),
                            ('bank_id.bank_id.l10n_mx_edi_code', '=', new_bank_no)], limit=1)
                            if log:
                                rec.check_final_folio_id = log.id
                            
                        rec.adjustment_case_id = case_id and case_id.id or False
                        if case=='P' or case=='A' or case=='R' or case=='F' or case=='Z' or case=='H' or case=='E' or case=='S' or case=='V' or case=='C':
                            if check_no:
                                if  type(check_no) is int or type(check_no) is float:
                                    check_no = int(check_no)
                                rec.check_number = check_no

#                             if deposite_no and new_bank_no:
#                                 log = self.env['check.log'].search([('folio', '=', deposite_no),
#                                 ('status', 'in', ('Checkbook registration', 'Assigned for shipping',
#                                 'Available for printing')), ('general_status', '=', 'available'),
#                                 ('bank_id.bank_id.l10n_mx_edi_code', '=', new_bank_no)], limit=1)
#                                 if log:
#                                     rec.check_final_folio_id = log.id
                                    
                            check_payment_method = self.env.ref('l10n_mx_edi.payment_method_cheque').id
                            if deposite_no and rec.l10n_mx_edi_payment_method_id and \
                                rec.l10n_mx_edi_payment_method_id.id == check_payment_method:
                                if case == 'P' or case == 'A' or case == 'R' or case == 'F' or case == 'H' or case == 'E' or case == 'V' or case == 'C':
                                    if deposite_no and new_bank_no:
                                        log = self.env['check.log'].search([('folio', '=', deposite_no),
                                        ('status', 'in', ('Checkbook registration', 'Assigned for shipping',
                                        'Available for printing')), ('general_status', '=', 'available'),
                                        ('bank_id.bank_id.l10n_mx_edi_code', '=', new_bank_no)], limit=1)
                                        if log:
                                            rec.check_final_folio_id = log.id

#                                 elif deposite_no:
#                                     if  type(deposite_no) is int or type(deposite_no) is float:
#                                         deposite_no = int(deposite_no)
#                                     
#                                     rec.deposite_number = deposite_no
                                            
#                             elif deposite_no:
#                                 if  type(deposite_no) is int or type(deposite_no) is float:
#                                     deposite_no = int(deposite_no)
#                                 
#                                 rec.deposite_number = deposite_no
    
                        if case=='D' or case=='A' or case=='C' or case=='P':
                            if rec.net_salary==old_amount:
                                rec.net_salary = new_amount
                        
                        if case=='B' or case=='V':
                            rec.net_salary = new_amount 

            employee_id = False
            if self.type_of_movement == 'perception_adjustment_detail':
                exist_lines = self.env['preception.line']
                update_lines = self.env['preception.line']
                all_payroll_ids = self.env['employee.payroll.file']
                for rowx, row in enumerate(map(sheet.row, range(1, sheet.nrows)), 1):
                    counter = 0
                    rfc = row[0].value
                    clave_categ = row[1].value
                    program_code = row[2].value
                    payment_place = row[3].value
                    payment_method = row[4].value
                    bank = row[5].value
                    check_no = row[6].value
                    deposite_no = row[7].value
                    ben = row[8].value
                    perception = row[9].value
                    amount = row[10].value
                    
                    program_id = False
                    if program_code:
                        p_id = self.env['program.code'].search([('program_code','=',program_code)],limit=1)
                        if p_id:
                            program_id = p_id.id
                    emp_payroll_ids = []
                    if rfc:
                        employee_id =self.env['hr.employee'].search([('rfc','=',rfc)],limit=1)
                        if employee_id:
                            emp_payroll_ids = self.payroll_process_id.payroll_ids.filtered(lambda x:x.employee_id.id==employee_id.id)
                            if emp_payroll_ids:
                                self.update_employee_payroll_perception(emp_payroll_ids,payment_method,bank,check_no,deposite_no,ben)
                            employee_id = employee_id.id

                    if employee_id:
                        emp_payroll_ids = self.payroll_process_id.payroll_ids.filtered(lambda x:x.employee_id.id==employee_id)
                        all_payroll_ids += emp_payroll_ids
                    for rec in emp_payroll_ids:
                        exist_lines += rec.preception_line_ids
                        
                        if perception:
                            if  type(perception) is int or type(perception) is float:
                                perception = int(perception)
                            
                            pre_id = self.env['preception'].search([('key','=',perception)],limit=1)
                            if pre_id:
                                lines = rec.preception_line_ids.filtered(lambda x:x.preception_id.id==pre_id.id and not x.is_adjustment_update)
                                
                                for line in lines:
                                    update_lines += line
                                    line.program_code_id = program_id
                                    line.amount = amount
                                    line.is_adjustment_update = True
                                    break
                                
                                if not lines:
                                    rec.write({'preception_line_ids':[(0,0,{'program_code_id':program_id,'preception_id':pre_id.id,'amount':amount,'is_create_from_this':True,'is_adjustment_update':True,})]})
                delete_lines = exist_lines - update_lines
                if delete_lines:
                    delete_lines = delete_lines.filtered(lambda x:not x.is_create_from_this)
                    delete_lines.unlink()
                if all_payroll_ids:
                    all_payroll_ids = list(set(all_payroll_ids))
                    for payroll in all_payroll_ids:
                        payroll.preception_line_ids.write({'is_adjustment_update':False,'is_create_from_this':False})
                    
            employee_id = False
            if self.type_of_movement == 'deduction_adjustment_detail':
                exist_lines = self.env['deduction.line']
                update_lines = self.env['deduction.line']
                all_payroll_ids = self.env['employee.payroll.file']
                for rowx, row in enumerate(map(sheet.row, range(1, sheet.nrows)), 1):
                    
                    rfc = row[0].value
                    account_code = row[1].value
                    deduction_key = row[2].value
                    amount = row[3].value
                    net_salary = row[4].value
                    
                    
                    emp_payroll_ids = []
                    if rfc:
                        employee_id =self.env['hr.employee'].search([('rfc','=',rfc)],limit=1)
                        if employee_id:
                            employee_id = employee_id.id
                            emp_payroll_ids = self.payroll_process_id.payroll_ids.filtered(lambda x:x.employee_id.id==employee_id)
                            emp_payroll_ids.write({'net_salary':net_salary})
                    if employee_id:
                        emp_payroll_ids = self.payroll_process_id.payroll_ids.filtered(lambda x:x.employee_id.id==employee_id)
                        all_payroll_ids += emp_payroll_ids 
                    for rec in emp_payroll_ids:
                        exist_lines += rec.deduction_line_ids
                        if deduction_key:
                            if  type(deduction_key) is int or type(deduction_key) is float:
                                deduction_key = int(deduction_key)
                            
                            pre_id = self.env['deduction'].search([('key','=',deduction_key)],limit=1)
                            if pre_id:
                                lines = rec.deduction_line_ids.filtered(lambda x:x.deduction_id.id==pre_id.id and not x.is_adjustment_update)
                                 
                                for line in lines:
                                    update_lines += line
                                    line.amount = amount
                                    line.is_adjustment_update = True
                                    break
                                if not lines:
                                    rec.write({'deduction_line_ids':[(0,0,{'is_create_from_this':True,'is_adjustment_update':True,'deduction_id':pre_id.id,'amount':amount})]})                                    

                delete_lines = exist_lines - update_lines
                if delete_lines:
                    delete_lines = delete_lines.filtered(lambda x:not x.is_create_from_this)
                    delete_lines.unlink()
                if all_payroll_ids:
                    all_payroll_ids = list(set(all_payroll_ids))
                    for payroll in all_payroll_ids:
                        payroll.deduction_line_ids.write({'is_adjustment_update':False,'is_create_from_this':False})
                        
            if self.type_of_movement == 'detail_alimony_adjustments':
                exist_lines = self.env['pension.payment.line']
                update_lines = self.env['pension.payment.line']
                
                for rowx, row in enumerate(map(sheet.row, range(1, sheet.nrows)), 1):
                    
                    rfc = row[0].value
                    ben_name = row[2].value
                    payment_method = row[3].value
                    bank_key = row[4].value
                    check_no = row[5].value
                    deposite = row[6].value
                    bank_account = row[7].value
                    total_pension = row[8].value
                    
                    partner_id = False
                    deposite_data = deposite
                    check_no_data = check_no
                    
                    if ben_name:
                        per_rec = self.env['res.partner'].search([('name','=',ben_name)],limit=1)
                        if per_rec:
                            partner_id = per_rec.id
                    if deposite:         
                        if  type(deposite) is int or type(deposite) is float:
                            deposite_data = int(deposite)
                    
                    if check_no:         
                        if  type(check_no) is int or type(check_no) is float:
                            check_no_data = int(check_no)
                    
                    emp_payroll_ids = []
                    if rfc:
                        employee_id =self.env['hr.employee'].search([('rfc','=',rfc)],limit=1)
                        if employee_id:
                            employee_id = employee_id.id
                        
                    if employee_id:
                        emp_payroll_ids = self.payroll_process_id.payroll_ids.filtered(lambda x:x.employee_id.id==employee_id)
                    
                    for rec in emp_payroll_ids:
                        exist_lines += rec.pension_payment_line_ids
                        if payment_method:
                            payment_method_id = False
                            journal_id = False
                            bank_id = False
                            bank_account_id = False
                            
                            if  type(payment_method) is int or type(payment_method) is float:
                                payment_method = int(payment_method)

                            if  type(bank_account) is int or type(bank_account) is float:
                                bank_account = int(bank_account)

                            if payment_method:         
                                if  type(payment_method) is int or type(payment_method) is float:
                                    payment_method = int(payment_method)
                                payment_method_rec = self.env['l10n_mx_edi.payment.method'].search([('name','=',str(payment_method))],limit=1)
                                if payment_method_rec:
                                    payment_method_id = payment_method_rec.id
        
                            if bank_account:
                                if  type(bank_account) is int or type(bank_account) is float:
                                    bank_account = int(bank_account)
                                bank_account_rec = self.env['res.partner.bank'].search([('acc_number','=',str(bank_account))],limit=1)
                                if bank_account_rec:
                                    bank_account_id = bank_account_rec.id
        
                            if bank_key:
                                if  type(bank_key) is int or type(bank_key) is float:
                                    bank_key = int(bank_key)
                                bank_rec = self.env['res.bank'].search([('l10n_mx_edi_code','=',str(bank_key))],limit=1)
                                if bank_rec:
                                    bank_id = bank_rec.id
                            
                            self.update_employee_payroll_pension(rec,payment_method_id,deposite_data,check_no_data,bank_account_id,bank_key,bank_id)
                            if payment_method_id:
                                lines = rec.pension_payment_line_ids.filtered(lambda x:
                                        x.l10n_mx_edi_payment_method_id.id==payment_method_id and
                                        x.bank_key == str(bank_key))
                                update_lines += lines
                                for line in lines:
                                    line.total_pension = total_pension
                                    line.partner_id = partner_id 
                                    line.deposit_number = deposite_data
                                    line.check_number = check_no_data
                                    line.bank_acc_number = bank_account_id
                                    line.bank_key = bank_key
                                
                                if not lines:
                                    rec.write({'pension_payment_line_ids':[(0,0,{'partner_id':partner_id,
                                                                                 'l10n_mx_edi_payment_method_id':payment_method_id,
                                                                                 'bank_id':bank_id,
                                                                                 'bank_acc_number' : bank_account_id,
                                                                                 'total_pension':total_pension,
                                                                                 'deposit_number':deposite_data,
                                                                                 'check_number' : check_no_data,
                                                                                 'bank_key':bank_key,
                                                                                 })]})
                                    
                                    
                                                                        
                delete_lines = exist_lines - update_lines
                if delete_lines:
                    delete_lines.unlink()
                                    