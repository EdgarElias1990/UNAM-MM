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
from datetime import datetime, timedelta
from odoo.modules.module import get_resource_path
from xlrd import open_workbook
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import ustr
import io

class GeneratePayrollWizard(models.TransientModel):

    _name = 'generate.payroll.wizard'
    _description = "Generate Payroll Wizard"

    type_of_movement = fields.Selection([('payroll_perceptions','Payroll Perceptions'),
                                         ('payroll_deductions','Payroll Deductions'),
                                         ('pension_payment','Pension Payment'),
                                         ('additional_payments','Additional Payments'),
                                         ('additional_pension_payments','Additional Pension Payments')
                                         ],string='Type of Movement')
    
    file = fields.Binary('File to import')
    filename = fields.Char('FileName')
    
    employee_ids = fields.Many2many('hr.employee','employee_generate_payroll_wizard_rel','employee_id','wizard_id','Employees')
    payroll_process_id = fields.Many2one('custom.payroll.processing','Payroll Process')
    file_row = fields.Integer(default=0)
    cron_id = fields.Many2one('ir.cron',"Active Cron")
    
    def check_employee_data(self,failed_row,rfc,import_type,counter):
        failed_row += "Row " +str(counter)+" : " + str(rfc) + "------>> Invalid Employee RFC In "+str(import_type)+" Import\n"
        return failed_row
    
    def check_category_data(self,failed_row,cat,import_type,counter):
        failed_row +="Row " +str(counter)+" : " + str(cat) + "------>> Invalid Category Key In "+str(import_type)+" Import\n"
        return failed_row

    def check_program_code_data(self,failed_row,program,import_type,counter):
        failed_row +="Row " +str(counter)+" : " + str(program) + "------>> Invalid Program Code In "+str(import_type)+" Import\n"
        return failed_row

    def check_payment_method_data(self,failed_row,method,import_type,counter):
        failed_row +="Row " +str(counter)+" : " + str(method) + "------>> Invalid Payment Method In "+str(import_type)+" Import\n"
        return failed_row

    def check_bank_key_data(self,failed_row,key,import_type,counter):
        failed_row +="Row " +str(counter)+" : " + str(key) + "------>> Invalid Bank Key In "+str(import_type)+" Import\n"
        return failed_row

    def check_checklog_data(self,failed_row,number,import_type,counter):
        failed_row +="Row " +str(counter)+" : " + str(number) + "------>> Invalid Check Number In "+str(import_type)+" Import\n"
        return failed_row

    def check_bank_accunt_data(self,failed_row,acount,import_type,counter):
        failed_row +="Row " +str(counter)+" : " + str(acount) + "------>> Invalid Bank Account In "+str(import_type)+" Import\n"
        return failed_row

    def check_perception_data(self,failed_row,perception,import_type,counter):
        failed_row +="Row " +str(counter)+" : " + str(perception) + "------>> Invalid Payment key In "+str(import_type)+" Import\n"
        return failed_row

    def check_deduction_data(self,failed_row,deduction,import_type,counter):
        failed_row +="Row " +str(counter)+" : " + str(deduction) + "------>> Invalid Deduction key In "+str(import_type)+" Import\n"
        return failed_row
    def check_parter_data(self,failed_row,partner,import_type,counter):
        failed_row +="Row " +str(counter)+" : " + str(partner) + "------>> Invalid Beneficiaries In "+str(import_type)+" Import\n"
        return failed_row
    
    def create_new_cron(self):
        nextcall = datetime.now()
        nextcall = nextcall + timedelta(seconds=5)
        
        cron_vals = {
            'name': "Payroll_"+str(self.payroll_process_id.name)+"_"+str(self.id)+"_"+str(self.file_row),
            'state': 'code',
            'nextcall': nextcall,
            'nextcall_copy': nextcall,
            'numbercall': -1,
            'code': "model.generate(%s)"%(self.id),
            'model_id': self.env.ref('jt_payroll_payment.model_generate_payroll_wizard').id,
            'user_id': self.env.user.id,
            'doall':True,
        }

                    # Final process
        cron = self.env['ir.cron'].sudo().create(cron_vals)
                     
    def generate(self,record_id=False):
        if record_id:
            self = self.env['generate.payroll.wizard'].browse(int(record_id))
        
        if self.file:
            failed_row = ""
            
            data = base64.decodestring(self.file)
            book = open_workbook(file_contents=data or b'')
            sheet = book.sheet_by_index(0)

            result_dict = {
                }
            line_data = []
            exit_payroll_id = False
            employee_records = self.env['hr.employee'].search_read([], fields=['id', 'rfc'])
            program_code_records = self.env['program.code'].search_read([], fields=['id', 'program_code'])
            preception_records = self.env['preception'].search_read([], fields=['id', 'key'])
            #======================== payroll_perceptions ================# 
            if self.type_of_movement == 'payroll_perceptions':
                self.payroll_process_id.perception_file = self.file
                self.payroll_process_id.perception_filename = self.filename
                self.payroll_process_id.perception_file_index = 1
                self.payroll_process_id.perception_file_load = True
                self.payroll_process_id.perception_hide = False
                return
                counter = 0                
                for rowx, row in enumerate(map(sheet.row, range(self.file_row, sheet.nrows)), 1):
                    counter += 1
                    rfc = row[0].value
                    program_code = row[2].value
                    payment_method = row[4].value
                    bank_key = row[5].value
                    check_number = row[6].value
                    deposite_number = row[7].value
                    bank_account = row[8].value
                    pre_key = row[9].value
                    amount = row[10].value

                    if rfc and str(rfc).isalnum():
                        if exit_payroll_id and line_data:
                            exit_payroll_id.write({'preception_line_ids':line_data})
                            line_data = []
                            exit_payroll_id = False
                            result_dict = {}
                            
                        if result_dict:
                            result_dict.update({'preception_line_ids':line_data})
                            self.env['employee.payroll.file'].create(result_dict)
                            result_dict = {}
                            line_data = []
                            exit_payroll_id = False
                            
                        payment_method_id = False    
                        
                        if payment_method and str(payment_method).isalnum():     
                            if  type(payment_method) is int or type(payment_method) is float:
                                payment_method = int(payment_method)
                            payment_method_rec = self.env['l10n_mx_edi.payment.method'].search([('name','=',str(payment_method))],limit=1)
                            if payment_method_rec:
                                payment_method_id = payment_method_rec.id
                            else:
                                failed_row = self.check_payment_method_data(failed_row,payment_method,'Payroll Perceptions',counter)
                                continue    
                        #employee_id =self.env['hr.employee'].search([('rfc','=',rfc)],limit=1)
                        
                        
                        employee_id = list(filter(lambda emp: emp['rfc'] == rfc, employee_records))
                        employee_id = employee_id[0]['id'] if employee_id else False
                        
                        if not employee_id:
                            failed_row = self.check_employee_data(failed_row, rfc, 'Payroll Perceptions',counter)
                        if employee_id:
                            employee_id = self.env['hr.employee'].browse(employee_id)
                            rec_check_number = check_number
                            rec_deposite_number = deposite_number
                            rec_bank_key = bank_key
                            bank_account_id = False
                            
                            if check_number:
                                if  type(check_number) is int or type(check_number) is float:
                                    rec_check_number = int(check_number)

                            if deposite_number:
                                if  type(deposite_number) is int or type(deposite_number) is float:
                                    rec_deposite_number = int(deposite_number)

                            if bank_key:
                                if type(bank_key) is int or type(bank_key) is float:
                                    rec_bank_key = int(bank_key)
                                bank_id_1 = self.env['res.bank'].search([('l10n_mx_edi_code', '=', rec_bank_key)])
                                if not bank_id_1:
                                    failed_row = self.check_bank_key_data(failed_row,bank_key,'Payroll Perceptions',counter)
                                    continue

                            if rec_check_number and rec_bank_key:
                                log = self.env['check.log'].search([('folio', '=', rec_check_number),
                                    ('status', 'in', ('Checkbook registration', 'Assigned for shipping',
                                    'Available for printing')), ('general_status', '=', 'available'),
                                                ('bank_id.bank_id.l10n_mx_edi_code', '=', rec_bank_key)], limit=1)
                                if not log:
                                    failed_row = self.check_checklog_data(failed_row,rec_check_number,'Payroll Perceptions',counter)
                                    continue
                                
                            if bank_account and str(bank_account).isalnum():
                                if  type(bank_account) is int or type(bank_account) is float:
                                    bank_account = int(bank_account)
                                bank_account_rec = self.env['res.partner.bank'].search([('acc_number','=',str(bank_account))],limit=1)
                                if bank_account_rec:
                                    bank_account_id = bank_account_rec.id
                                else:
                                    failed_row = self.check_bank_accunt_data(failed_row,bank_account,'Payroll Perceptions',counter)
                                    continue
                                    
                            exit_payroll_id = self.env['employee.payroll.file'].search([('employee_id','=',employee_id.id),
                                                        ('id','in',self.payroll_process_id.payroll_ids.ids)],limit=1)
                            if exit_payroll_id:
                                exit_payroll_id.l10n_mx_edi_payment_method_id = payment_method_id
                                exit_payroll_id.deposite_number = rec_deposite_number
                                exit_payroll_id.check_number = rec_check_number
                                exit_payroll_id.bank_key = rec_bank_key
                                exit_payroll_id.receiving_bank_acc_pay_id = bank_account_id
                                if check_number and rec_bank_key:
                                    log = self.env['check.log'].search([('folio', '=', check_number),
                                    ('status', 'in', ('Checkbook registration','Assigned for shipping',
                                           'Available for printing')),('general_status', '=', 'available'),
                                                    ('bank_id.bank_id.l10n_mx_edi_code', '=', rec_bank_key)], limit=1)
                                    if log:
                                        exit_payroll_id.check_folio_id = log.id
                                
                            if not exit_payroll_id:
                                log = False
                                if check_number:
                                    log = self.env['check.log'].search([('folio', '=', check_number),
                                    ('status', 'in', ('Checkbook registration','Assigned for shipping',
                                    'Available for printing')),('general_status', '=', 'available'),
                                                    ('bank_id.bank_id.l10n_mx_edi_code', '=', rec_bank_key)], limit=1)
                                result_dict.update({'payroll_processing_id':self.payroll_process_id.id,
                                                    'period_start' : self.payroll_process_id.period_start,
                                                    'period_end' : self.payroll_process_id.period_end,
                                                    'fornight' : self.payroll_process_id.fornight,
                                                    'employee_id':employee_id.id,
                                                    'bank_key' : rec_bank_key,
                                                    'deposite_number' : rec_deposite_number,
                                                    'check_number' : rec_check_number,
                                                    'l10n_mx_edi_payment_method_id':payment_method_id,
                                                    'is_pension_payment_request' : True,
                                                    'receiving_bank_acc_pay_id' : bank_account_id,
                                                    'payment_request_type':'direct_employee'})
                                if log:
                                    result_dict.update({'check_folio_id': log.id if log else False})
                                    
                        else:
                            continue

                    program_id = False
                    if program_code:
                        program_id = list(filter(lambda pc: pc['program_code'] == program_code, program_code_records))
                        program_id = program_id[0]['id'] if program_id else False
                        if not program_id:
                            failed_row = self.check_program_code_data(failed_row,program_code,'Payroll Perceptions',counter)
                            continue
                    if pre_key and str(pre_key).isalnum():
                        
                        if  type(pre_key) is int or type(pre_key) is float:
                            pre_key = int(pre_key)
                        
                        pre_id = list(filter(lambda per: per['key'] == pre_key, preception_records))
                        pre_id = pre_id[0]['id'] if pre_id else False
                        
                        #pre_id = self.env['preception'].search([('key','=',pre_key)],limit=1)
                        if pre_id:
                            line_data.append((0,0,{'program_code_id':program_id,'preception_id':pre_id,'amount':amount}))
                        else:
                            failed_row = self.check_perception_data(failed_row,pre_key,'Payroll Perceptions',counter)
                            continue
                         
                    if exit_payroll_id and line_data:
                        exit_payroll_id.write({'preception_line_ids':line_data})
                        line_data = []
                        # exit_payroll_id = False

                    if result_dict:
                        result_dict.update({'preception_line_ids':line_data})
                        exit_payroll_id = self.env['employee.payroll.file'].create(result_dict)
                        line_data = []
                        result_dict = {}
            #======================== payroll_deductions ================#
            if self.type_of_movement == 'payroll_deductions':

                self.payroll_process_id.deductions_file = self.file
                self.payroll_process_id.deductions_filename = self.filename
                self.payroll_process_id.deductions_file_index = 1
                self.payroll_process_id.deductions_file_load = True
                self.payroll_process_id.deductions_hide = False
                return
                
                counter = 0
                for rowx, row in enumerate(map(sheet.row, range(1, sheet.nrows)), 1):
                    
                    counter += 1
                    print ("Con====",counter)
                    rfc = row[0].value
                    ded_key = row[2].value
                    amount = row[3].value
                    net_salary = row[4].value
                    
                    if rfc:
                        if exit_payroll_id and line_data:
                            exit_payroll_id.write({'deduction_line_ids':line_data})
                            line_data = []
                            exit_payroll_id = False
                            result_dict = {}
                            
                        if result_dict:
                            result_dict.update({'deduction_line_ids':line_data})
                            self.env['employee.payroll.file'].create(result_dict)
                            result_dict = {}
                            line_data = []
                            exit_payroll_id = False
                             
                        employee_id =self.env['hr.employee'].search([('rfc','=',rfc)],limit=1)
                        if not employee_id:
                            failed_row = self.check_employee_data(failed_row,rfc,'Payroll Deductions',counter)                            
                        if employee_id:

                            exit_payroll_id = self.env['employee.payroll.file'].search([('employee_id','=',employee_id.id),('id','in',self.payroll_process_id.payroll_ids.ids)],limit=1)
                            if exit_payroll_id:
                                exit_payroll_id.net_salary = net_salary
                                
                            if not exit_payroll_id:                             
                                result_dict.update({'payroll_processing_id':self.payroll_process_id.id,
                                                    'period_start' : self.payroll_process_id.period_start,
                                                    'period_end' : self.payroll_process_id.period_end,
                                                    'fornight' : self.payroll_process_id.fornight,
                                                    'employee_id':employee_id.id,
                                                    'net_salary':net_salary,
                                                    'is_pension_payment_request' : True,
                                                    'payment_request_type':'direct_employee'})
                        else:
                            continue

                    if ded_key:
                        if  type(ded_key) is int or type(ded_key) is float:
                            ded_key = int(ded_key)
                        
                        ded_id = self.env['deduction'].search([('key','=',ded_key)],limit=1)
                        if ded_id:
                            line_data.append((0,0,{'deduction_id':ded_id.id,'amount':amount})) 
                        else:
                            failed_row = self.check_deduction_data(failed_row,ded_key,'Payroll Deductions',counter)
                            continue
                    if exit_payroll_id and line_data:
                        exit_payroll_id.write({'deduction_line_ids':line_data})
                        line_data = []
                        # exit_payroll_id = False

                    if result_dict:
                        result_dict.update({'deduction_line_ids':line_data})
                        exit_payroll_id = self.env['employee.payroll.file'].create(result_dict)
                        line_data = []
                        # exit_payroll_id = False
                        result_dict = {}

            #======================== pension_payment ================# 
            if self.type_of_movement == 'pension_payment':
                self.env.user.notify_success(message='Pension Payment Process Is Start',
                                    title="Pension Payment", sticky=True)
                
                counter = 0
                for rowx, row in enumerate(map(sheet.row, range(1, sheet.nrows)), 1):
                    counter += 1
                    rfc = row[0].value
                    ben_name = row[2].value
                    payment_method = row[3].value
                    bank_key = row[4].value
                    check_no = row[5].value
                    deposite = row[6].value
                    bank_account = row[7].value
                    total_pension = row[8].value

                    if rfc:
                        employee_id =self.env['hr.employee'].search([('rfc','=',rfc)],limit=1)
                        if not employee_id:
                            failed_row = self.check_employee_data(failed_row,rfc,'Pension Payment',counter)                            
                        
                        if employee_id:
                            exit_payroll_id = self.env['employee.payroll.file'].search([('employee_id','=',employee_id.id),('id','in',self.payroll_process_id.payroll_ids.ids)],limit=1)
                            if not exit_payroll_id:                             
                                result_dict.update({'payroll_processing_id':self.payroll_process_id.id,
                                                    'period_start' : self.payroll_process_id.period_start,
                                                    'period_end' : self.payroll_process_id.period_end,
                                                    'fornight' : self.payroll_process_id.fornight,
                                                    'employee_id':employee_id.id,
                                                    'is_pension_payment_request' : True,
                                                    'payment_request_type':'direct_employee'})
                        else:
                            continue

                    partner_id = False
                    deposite_data = deposite
                    check_no_data = check_no
                    payment_method_id = False
                    bank_account_id = False
                    bank_id = False
                    check_folio_id = False
                    if ben_name:
                        per_rec = self.env['res.partner'].search([('name','=',ben_name)],limit=1)
                        if per_rec:
                            partner_id = per_rec.id
                        else:
                            failed_row = self.check_parter_data(failed_row,ben_name,'Pension Payment',counter)
                            continue
                            
                    if deposite:         
                        if  type(deposite) is int or type(deposite) is float:
                            deposite_data = int(deposite)
                    
                    if check_no:         
                        if  type(check_no) is int or type(check_no) is float:
                            check_no_data = int(check_no)
                            
                    if payment_method:         
                        if  type(payment_method) is int or type(payment_method) is float:
                            payment_method = int(payment_method)
                        payment_method_rec = self.env['l10n_mx_edi.payment.method'].search([('name','=',str(payment_method))],limit=1)
                        if payment_method_rec:
                            payment_method_id = payment_method_rec.id
                        else:
                            failed_row = self.check_payment_method_data(failed_row,payment_method,'Pension Payment',counter)
                            continue
                        
                    if bank_account:
                        if  type(bank_account) is int or type(bank_account) is float:
                            bank_account = int(bank_account)
                        bank_account_rec = self.env['res.partner.bank'].search([('acc_number','=',str(bank_account))],limit=1)
                        if bank_account_rec:
                            bank_account_id = bank_account_rec.id
                        else:
                            failed_row = self.check_bank_accunt_data(failed_row,bank_account,'Pension Payment',counter)
                            continue
                        
                    if bank_key:
                        if  type(bank_key) is int or type(bank_key) is float:
                            bank_key = int(bank_key)
                        bank_rec = self.env['res.bank'].search([('l10n_mx_edi_code','=',str(bank_key))],limit=1)
                        if bank_rec:
                            bank_id = bank_rec.id
                        else:
                            failed_row = self.check_bank_key_data(failed_row,bank_key,'Pension Payment',counter)
                            continue

                    if check_no_data and bank_key:
                        log = self.env['check.log'].search([('folio', '=', check_no_data),
                            ('status', 'in',('Checkbook registration', 'Assigned for shipping','Available for printing')),
                            ('general_status', '=', 'available'),('bank_id.bank_id.l10n_mx_edi_code', '=', bank_key)],
                            limit=1)
                        if not log:
                            failed_row = self.check_checklog_data(failed_row,check_no_data,'Pension Payment',counter)
                            continue
                        else:
                            check_folio_id = log
                            
                    line_data.append((0,0,{'bank_key':bank_key,
                                           'bank_id':bank_id,'bank_acc_number':bank_account_id,
                                           'l10n_mx_edi_payment_method_id':payment_method_id,
                                           'partner_id':partner_id,'deposit_number':deposite_data,
                                           'check_number':check_no_data,'total_pension':total_pension,
                                           'check_folio_id': check_folio_id.id if check_folio_id else False}))

                    if exit_payroll_id and line_data:
                        exit_payroll_id.write({'pension_payment_line_ids':line_data})
                        line_data = []
                        # exit_payroll_id = False

                    if result_dict:
                        result_dict.update({'pension_payment_line_ids':line_data})
                        exit_payroll_id = self.env['employee.payroll.file'].create(result_dict)
                        line_data = []
                        result_dict = {}
                        # exit_payroll_id = False
                self.env.user.notify_success(message='Pension Payment Process Is End',
                                    title="Pension Payment", sticky=True)

            #======================== Additional payments ================# 
            if self.type_of_movement == 'additional_payments':
                self.env.user.notify_success(message='Additional Payments Process Is Start',
                                    title="Additional Payments", sticky=True)
                
                counter = 0
                for rowx, row in enumerate(map(sheet.row, range(1, sheet.nrows)), 1):
                    
                    counter += 1
                    rfc = row[0].value
                    job_id = row[1].value
                    amount = row[2].value
                    program_code = row[3].value
                    details = row[4].value
                    
                    if rfc:

                        if exit_payroll_id and line_data:
                            exit_payroll_id.write({'additional_payments_line_ids':line_data})
                            line_data = []
                            exit_payroll_id = False
                            result_dict = {}
                        
                        if result_dict:
                            result_dict.update({'additional_payments_line_ids':line_data})
                            self.env['employee.payroll.file'].create(result_dict)
                            result_dict = {}
                            line_data = []
                            exit_payroll_id = False
                             
                        employee_id =self.env['hr.employee'].search([('rfc','=',rfc)],limit=1)
                        if not employee_id:
                            failed_row = self.check_employee_data(failed_row,rfc,'Additional Payments',counter)                            
                        
                        if employee_id:
                            exit_payroll_id = self.env['employee.payroll.file'].search([('employee_id','=',employee_id.id),('id','in',self.payroll_process_id.payroll_ids.ids)],limit=1)
                            if not exit_payroll_id:                             
                                result_dict.update({'payroll_processing_id':self.payroll_process_id.id,
                                                    'period_start' : self.payroll_process_id.period_start,
                                                    'period_end' : self.payroll_process_id.period_end,
                                                    'fornight' : self.payroll_process_id.fornight,
                                                    'employee_id':employee_id.id,
                                                    'is_pension_payment_request' : True,
                                                    'payment_request_type':'direct_employee'})
                        else:
                            continue

                    job_data = False
                    program_code_id = False
                    details_data = False
                    
                    if details:
                        if details=='N':
                            details_data = 'N'
                        if details=='U':
                            details_data = 'U'
                    if job_id:
                        job_rec = self.env['hr.job'].search([('category_key.name','=',job_id)],limit=1)
                        if job_rec:
                            job_data = job_rec.id
                        else:
                            failed_row = self.check_category_data(failed_row, job_id,'Additional Payments',counter)
                    if program_code:
                        p_id = self.env['program.code'].search([('program_code','=',program_code)],limit=1)
                        if p_id:
                            program_code_id = p_id.id
                        else:
                            failed_row = self.check_program_code_data(failed_row,program_code,'Additional Payments',counter)
                            continue
                    line_data.append((0,0,{'job_id':job_data,'program_code_id':program_code_id,'details':details_data,'amount':amount})) 

                    if exit_payroll_id and line_data:
                        exit_payroll_id.write({'additional_payments_line_ids':line_data})
                        line_data = []
                        # exit_payroll_id = False
                        result_dict = {}

                    if result_dict:
                        result_dict.update({'additional_payments_line_ids':line_data})
                        exit_payroll_id = self.env['employee.payroll.file'].create(result_dict)
                        result_dict = {}
                        line_data = []
                        # exit_payroll_id = False
                self.env.user.notify_success(message='Additional Payments Process Is End',
                                    title="Additional Payments", sticky=True)

            #======================== additional_pension_payments ================# 
            if self.type_of_movement == 'additional_pension_payments':
                self.env.user.notify_success(message='Additional Pension Payments Process Is Start',
                                    title="Additional Pension Payments", sticky=True)
                
                counter = 0
                for rowx, row in enumerate(map(sheet.row, range(1, sheet.nrows)), 1):
                    
                    counter += 1
                    rfc = row[0].value
                    ben_name = row[1].value
                    amount = row[2].value
                    
                    if rfc:
                        if exit_payroll_id and line_data:
                            exit_payroll_id.write({'additional_pension_payments_line_ids':line_data})
                            line_data = []
                            exit_payroll_id = False
                            result_dict = {}

                        if result_dict:
                            result_dict.update({'additional_pension_payments_line_ids':line_data})
                            self.env['employee.payroll.file'].create(result_dict)
                            result_dict = {}
                            line_data = []
                            exit_payroll_id = False

                        employee_id =self.env['hr.employee'].search([('rfc','=',rfc)],limit=1)
                        if not employee_id:
                            failed_row = self.check_employee_data(failed_row,rfc,'Additional Pension Payments',counter)                            
                        
                        if employee_id:
                            exit_payroll_id = self.env['employee.payroll.file'].search([('employee_id','=',employee_id.id),
                                                        ('id','in',self.payroll_process_id.payroll_ids.ids)],limit=1)
                            if not exit_payroll_id:
                                result_dict.update({'payroll_processing_id':self.payroll_process_id.id,
                                                    'period_start' : self.payroll_process_id.period_start,
                                                    'period_end' : self.payroll_process_id.period_end,
                                                    'fornight' : self.payroll_process_id.fornight,
                                                    'employee_id':employee_id.id,
                                                    'is_pension_payment_request' : True,
                                                    'payment_request_type':'direct_employee'})
                        else:
                            continue
                    partner_id = False
                    
                    if ben_name:
                        per_rec = self.env['res.partner'].search([('name','=',ben_name)],limit=1)
                        if per_rec:
                            partner_id = per_rec.id
                        else:
                            failed_row = self.check_parter_data(failed_row,ben_name,'Additional Pension Payments',counter)
                            continue
                    line_data.append((0,0,{'partner_id':partner_id,'amount':amount})) 

                    if exit_payroll_id and line_data:
                        exit_payroll_id.write({'additional_pension_payments_line_ids':line_data})
                        line_data = []
                        # exit_payroll_id = False
                        result_dict = {}

                    if result_dict:
                        result_dict.update({'additional_pension_payments_line_ids':line_data})
                        exit_payroll_id = self.env['employee.payroll.file'].create(result_dict)
                        line_data = []
                        # exit_payroll_id = False
                        result_dict = {}

                self.env.user.notify_success(message='Additional Pension Payments Process Is Start',
                                    title="Additional Pension Payments", sticky=True)

            if failed_row != "":
                self.payroll_process_id.update_failed_file(failed_row,self.type_of_movement,'completed',self.env.user,self.filename)
                
#                 content = ""
#                 if self.payroll_process_id.failed_row_file:
#                     file_data = base64.b64decode(self.payroll_process_id.failed_row_file)
#                     content += io.StringIO(file_data.decode("utf-8")).read()
#                 # if cron:
#                 #     content = ''
#                 content += "\n"
#                 content += "...................Failed Rows " + \
#                            str(datetime.today()) + "...............\n"
#                 content += str(failed_row)
#                 failed_data = base64.b64encode(content.encode('utf-8'))
#                 self.payroll_process_id.failed_row_file = failed_data
