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
from odoo.tools.profiler import profile

class CustomPayrollProcessing(models.Model):

    _name = 'custom.payroll.processing'
    _description = "Custom Payroll Processing"
    

    name = fields.Char("Name")

    period_start = fields.Date("Period")
    period_end = fields.Date("Period End")
    fornight = fields.Selection([('01', '01'), ('02', '02'), ('03', '03'), ('04', '04'), ('05', '05'),
                                      ('06', '06'), ('07', '07'), ('08', '08'), ('09', '09'), ('10', '10'),
                                      ('11', '11'), ('12', '12'), ('13', '13'), ('14', '14'), ('15', '15'),
                                      ('16', '16'), ('17', '17'), ('18', '18'), ('19', '19'), ('20', '20'),
                                      ('21', '21'), ('22', '22'), ('23', '23'), ('24', '24')],
                                string="Fornight")
    
    payroll_ids = fields.One2many('employee.payroll.file','payroll_processing_id')
    total_record = fields.Integer(compute='get_total_record',string='Payment Receipt')

    failed_row_file = fields.Binary(string='Failed Rows File')
    fialed_row_filename = fields.Char(
        string='File name', default=lambda self: _("Failed_Rows.txt"))
    

    perception_file = fields.Binary('File to import')
    perception_filename = fields.Char('FileName')
    perception_file_index = fields.Integer(default=0)
    perception_file_load = fields.Boolean(default=False)
    perception_hide = fields.Boolean(default=True)
    perception_user = fields.Many2one('res.users')
    
    deductions_file = fields.Binary('File to import')
    deductions_filename = fields.Char('FileName')
    deductions_file_index = fields.Integer(default=0)
    deductions_file_load = fields.Boolean(default=False)
    deductions_user = fields.Many2one('res.users')
    deductions_hide = fields.Boolean(default=True)
    
    failed_log_ids = fields.One2many("payroll.processing.failed.log",'payroll_processing_id','Failed Logs')
    cron_id = fields.Many2one("ir.cron")
    
    def get_total_record(self):
        for rec in self:
            rec.total_record = len(rec.payroll_ids)
            
    def generate_payroll(self):
        return {
                'name': _('Generate Payroll'),
                'res_model':'generate.payroll.wizard',
                'view_mode': 'form',
                'view_id': self.env.ref('jt_payroll_payment.generate_payroll_wizard_view1').id,
                'context': {'default_payroll_process_id': self.id},
                'target': 'new',
                'type': 'ir.actions.act_window',
            }

    def generate_adjustment(self):
        return {
                'name': _('Generate Adjustment'),
                'res_model':'adjusted.payroll.wizard',
                'view_mode': 'form',
                'view_id': self.env.ref('jt_payroll_payment.adjusted_payroll_wizard_view1').id,
                'context': {'default_payroll_process_id': self.id},
                'target': 'new',
                'type': 'ir.actions.act_window',
            }

    def lows_and_cancellations(self):
        return {
                'name': _('Lows And Cancellations'),
                'res_model':'lows.cancellation.wizard',
                'view_mode': 'form',
                'view_id': self.env.ref('jt_payroll_payment.lows_cancellation_wizard_view1').id,
                'context': {'default_payroll_process_id': self.id},
                'target': 'new',
                'type': 'ir.actions.act_window',
            }

        
    def view_payment_receipt(self):
        return {
                'name': _('Payroll'),
                'res_model':'employee.payroll.file',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'views': [(self.env.ref('jt_payroll_payment.employee_payroll_file_tree_process').id, 'tree'), (self.env.ref("jt_payroll_payment.employee_payroll_file_form_processing").id, 'form')],
                'context': {'show_category_name': True},
                'target': 'current',
                'type': 'ir.actions.act_window',
                'domain':[('id','in',self.payroll_ids.ids)]
            }

    def update_failed_file(self,failed_row,type_of_movement,state,user_id,import_file_name):
        
        failed_line_id = False
        failed_line_ids = self.failed_log_ids.filtered(lambda x:x.type_of_movement == type_of_movement and x.state == 'in_progress')
        if failed_line_ids:
            failed_line_id = failed_line_ids[0]
            
        if failed_row != "":
            content = ""
            
            if not failed_line_id:
                vals = {'payroll_processing_id':self.id,
                        'import_file_name' : import_file_name,
                        'user_id' : user_id.id,
                        'type_of_movement' : type_of_movement,
                        'state' : state,
                    }
                failed_line_id = self.env['payroll.processing.failed.log'].create(vals)
                
            if failed_line_id.failed_row_file:
                file_data = base64.b64decode(failed_line_id.failed_row_file)
                content += io.StringIO(file_data.decode("utf-8")).read()
                
            content += "\n"
            content += "...................Failed Rows " + \
                       str(datetime.today()) + "...............\n"
            content += str(failed_row)
            failed_data = base64.b64encode(content.encode('utf-8'))
            failed_line_id.failed_row_file = failed_data

        if failed_line_id and state=='completed':
            failed_line_id.state = 'completed'
            
        
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
    
    def get_perception_check_log(self,rec_check_number,rec_bank_key):
        log = False
        from_check = False
        
        return log,from_check     
    
    def send_perception_notification(self):
        if self.perception_user:
            self.perception_user.notify_success(message='Active batch process is completed, new batch process will auto activate in few seconds if any data pending to validate.',
                                title="Perception Process", sticky=True)

    def send_deductions_notification(self):
        if self.deductions_user:
            self.deductions_user.notify_success(message='Active batch process is completed, new batch process will auto activate in few seconds if any data pending to validate.',
                                title="Deductions Process", sticky=True)

    def create_perception_cron(self):
        cron_name = str(self.name).replace(' ', '') + "_Perception_" + str(datetime.now()).replace(' ', '')
        nextcall = datetime.now()
        nextcall = nextcall + timedelta(seconds=10)

        cron_vals = {
            'name': cron_name,
            'state': 'code',
            'nextcall': nextcall,
            'nextcall_copy': nextcall,
            'numbercall': -1,
            'code': "model.process_perception_file()",
            'model_id': self.env.ref('jt_payroll_payment.model_custom_payroll_processing').id,
            'user_id': self.env.user.id,
            'payroll_processing_id': self.id,
            'doall':True,
        }

        cron = self.env['ir.cron'].sudo().create(cron_vals)
        self.cron_id = cron.id
        cron.write(
            {'code': "model.process_perception_file(" + str(self.id) + ")"})
        
    def process_perception_cron(self):
        self.perception_user = self.env.user.id
        self.perception_hide = True
        self.create_perception_cron()
        self.perception_user.notify_success(message='Batch process will auto activate in few seconds.',
                            title="Perception Process", sticky=True)
    
    
    def process_perception_file(self,record_id=False):
        if record_id:
            self = self.env['custom.payroll.processing'].browse(record_id)
        failed_row = ""
        
        counter = 0
        if self.perception_file and self.perception_file_load:
            
            data = base64.decodestring(self.perception_file)
            book = open_workbook(file_contents=data or b'')
            sheet = book.sheet_by_index(0)

            result_dict = {
                }
            line_data = []
            exit_payroll_id = False
            exist_per_lines = False
            employee_records = self.env['hr.employee'].search_read([], fields=['id', 'rfc'])
            program_code_records = self.env['program.code'].search_read([], fields=['id', 'program_code'])
            program_code_dict = {}
            for p_rec in program_code_records:
                program_code_dict[p_rec['program_code']] = p_rec['id']
            
            preception_records = self.env['preception'].search_read([], fields=['id', 'key'])
            bank_records = self.env['res.bank'].search_read([], fields=['id', 'l10n_mx_edi_code'])
            bank_account_records = self.env['res.partner.bank'].search_read([], fields=['id', 'acc_number'])
            payment_method_records = self.env['l10n_mx_edi.payment.method'].search_read([], fields=['id', 'name'])
            payroll_process_records = self.env['employee.payroll.file'].search_read([('payroll_processing_id','=',self.id)], fields=['id','employee_id'])
            
            counter = 0
            for rowx, row in enumerate(map(sheet.row, range(self.perception_file_index, sheet.nrows)), 1):
                counter += 1
                #print ("Con====",counter)
                rfc = row[0].value
                program_code = row[2].value
                payment_method = row[4].value
                bank_key = row[5].value
                check_number = row[6].value
                deposite_number = row[7].value
                bank_account = row[8].value
                pre_key = row[9].value
                amount = row[10].value

                log = False
                from_check = False

                if rfc and str(rfc).isalnum():
                    if counter > 40000:
                        self.update_failed_file(failed_row,'payroll_perceptions','in_progress',self.perception_user,self.perception_filename)
                        self.perception_file_index += counter - 1
                        self.send_perception_notification()
                        self.create_perception_cron()
                        return
                    
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
                    else:
                        payment_method = str(payment_method)
                    
                          
                    payment_method_id = list(filter(lambda pm: pm['name'] == str(payment_method), payment_method_records))
                    payment_method_id = payment_method_id[0]['id'] if payment_method_id else False
                    
                    if not payment_method_id:
                        failed_row = self.check_payment_method_data(failed_row,payment_method,'Payroll Perceptions',counter)
                        continue    
                
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

                        if bank_key and rec_check_number:
                            if type(bank_key) is int or type(bank_key) is float:
                                rec_bank_key = int(bank_key)

                            bank_id_1 = list(filter(lambda b: b['l10n_mx_edi_code'] == rec_bank_key, bank_records))
                            bank_id_1 = bank_id_1[0]['id'] if bank_id_1 else False
                                
                            if not bank_id_1:
                                failed_row = self.check_bank_key_data(failed_row,bank_key,'Payroll Perceptions',counter)
                                continue

                            log,from_check= self.get_perception_check_log(rec_check_number,rec_bank_key)
                            
                            if not log and from_check:
                                failed_row = self.check_checklog_data(failed_row,rec_check_number,'Payroll Perceptions',counter)
                                continue
                            
                        if bank_account and str(bank_account).isalnum():
                            if  type(bank_account) is int or type(bank_account) is float:
                                bank_account = int(bank_account)
                        elif bank_account and str(bank_account).isnumeric():
                            if  type(bank_account) is int or type(bank_account) is float:
                                bank_account = int(bank_account)
                        if  type(bank_account) is int or type(bank_account) is float:
                            bank_account = int(bank_account)
                        
                        if len(str(bank_account)) > 0:
                            bank_account_id = list(filter(lambda b: b['acc_number'] == str(bank_account), bank_account_records))
                            bank_account_id = bank_account_id[0]['id'] if bank_account_id else False
                             
                            if not bank_account_id:
                                failed_row = self.check_bank_accunt_data(failed_row,bank_account,'Payroll Perceptions',counter)
                                continue
                        
                        
                        exit_payroll_id = list(filter(lambda b: b['employee_id'][0] == employee_id.id, payroll_process_records))
                        exit_payroll_id = exit_payroll_id[0]['id'] if exit_payroll_id else False
                        
                        if exit_payroll_id:
                             
                            exit_payroll_id = self.env['employee.payroll.file'].browse(exit_payroll_id)
                            exist_per_lines = exit_payroll_id.preception_line_ids
                            exit_vals = {'l10n_mx_edi_payment_method_id' : payment_method_id,
                                         'deposite_number' : rec_deposite_number,
                                         'check_number' : rec_check_number,
                                         'bank_key' : rec_bank_key,
                                         'receiving_bank_acc_pay_id' : bank_account_id
                                        }
                            if log:
                                exit_vals.update({'check_folio_id':log.id})
                            exit_payroll_id.write(exit_vals)
                            
                        if not exit_payroll_id:
                            result_dict.update({'payroll_processing_id':self.id,
                                                'period_start' : self.period_start,
                                                'period_end' : self.period_end,
                                                'fornight' : self.fornight,
                                                'employee_id':employee_id.id,
                                                'bank_key' : rec_bank_key,
                                                'deposite_number' : rec_deposite_number,
                                                'check_number' : rec_check_number,
                                                'l10n_mx_edi_payment_method_id':payment_method_id,
                                                'is_pension_payment_request' : True,
                                                'receiving_bank_acc_pay_id' : bank_account_id,
                                                'payment_request_type':'direct_employee'})
                            if from_check:
                                result_dict.update({'check_folio_id': log.id if log else False})
                                
                    else:
                        continue

                program_id = False
                if program_code in program_code_dict.keys():
                    program_id = program_code_dict[program_code]
                if not program_id:
                    failed_row = self.check_program_code_data(failed_row,program_code,'Payroll Perceptions',counter)
                    continue

                                    
                if pre_key:
                    if  type(pre_key) is int or type(pre_key) is float:
                        pre_key = int(pre_key)
                    
                    pre_id = list(filter(lambda per: per['key'] == str(pre_key), preception_records))
                    pre_id = pre_id[0]['id'] if pre_id else False
                    if pre_id:
                        preception_lines = False
                        if exit_payroll_id:
                            if exist_per_lines:
                                preception_lines = exit_payroll_id.preception_line_ids.filtered(lambda x:x.preception_id.id==pre_id)
                                for line in preception_lines:
                                    line.program_code_id = program_id
                                    line.amount = amount
                        if not preception_lines:    
                            line_data.append((0,0,{'program_code_id':program_id,'preception_id':pre_id,'amount':amount}))
                    else:
                        failed_row = self.check_perception_data(failed_row,pre_key,'Payroll Perceptions',counter)
                        continue
                     
                if exit_payroll_id and line_data:
                    exit_payroll_id.write({'preception_line_ids':line_data})
                    line_data = []

                if result_dict:
                    result_dict.update({'preception_line_ids':line_data})
                    exit_payroll_id = self.env['employee.payroll.file'].create(result_dict)
                    line_data = []
                    result_dict = {}
                    
        self.update_failed_file(failed_row,'payroll_perceptions','completed',self.perception_user,self.perception_filename)
        self.perception_file_index += counter
        self.perception_file_load = False
        #self.perception_hide = False
        self.send_perception_notification()
        

    def create_deductions_cron(self):
        cron_name = str(self.name).replace(' ', '') + "_deductions_" + str(datetime.now()).replace(' ', '')
        nextcall = datetime.now()
        nextcall = nextcall + timedelta(seconds=10)

        cron_vals = {
            'name': cron_name,
            'state': 'code',
            'nextcall': nextcall,
            'nextcall_copy': nextcall,
            'numbercall': -1,
            'code': "model.process_deductions_file()",
            'model_id': self.env.ref('jt_payroll_payment.model_custom_payroll_processing').id,
            'user_id': self.env.user.id,
            'payroll_processing_id': self.id,
            'doall':True,
        }

        cron = self.env['ir.cron'].sudo().create(cron_vals)
        self.cron_id = cron.id
        cron.write(
            {'code': "model.process_deductions_file(" + str(self.id) + ")"})
        
    def process_deductions_cron(self):
        self.deductions_user = self.env.user.id
        self.deductions_hide = True
        self.create_deductions_cron()
        self.deductions_user.notify_success(message='Batch process will auto activate in few seconds',
                            title="Deductions Process", sticky=True)

    def process_deductions_file(self,record_id=False):
        if record_id:
            self = self.env['custom.payroll.processing'].browse(record_id)
        
        failed_row = ""
        #self.deductions_user = self.env.user.id
        if self.deductions_file and self.deductions_file_load:
            
            data = base64.decodestring(self.deductions_file)
            book = open_workbook(file_contents=data or b'')
            sheet = book.sheet_by_index(0)

            result_dict = {
                }
            line_data = []
            exit_payroll_id = False
            exist_ded_lines = False
            employee_records = self.env['hr.employee'].search_read([], fields=['id', 'rfc'])
            deduction_records = self.env['deduction'].search_read([], fields=['id', 'key'])
            payroll_process_records = self.env['employee.payroll.file'].search_read([('payroll_processing_id','=',self.id)], fields=['id','employee_id'])
            
            counter = 0

            for rowx, row in enumerate(map(sheet.row, range(self.deductions_file_index, sheet.nrows)), 1):
                
                counter += 1
                #print ("Con====",counter)
                rfc = row[0].value
                ded_key = row[2].value
                amount = row[3].value
                net_salary = row[4].value
                
                if rfc and str(rfc).isalnum():
                    if counter > 40000:
                        self.update_failed_file(failed_row,'payroll_deductions','in_progress',self.deductions_user,self.deductions_filename)
                        self.deductions_file_index += counter - 1
                        self.send_deductions_notification()
                        self.process_deductions_cron()
                        return
                    
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
                         
#                    employee_id =self.env['hr.employee'].search([('rfc','=',rfc)],limit=1)

                    employee_id = list(filter(lambda emp: emp['rfc'] == rfc, employee_records))
                    employee_id = employee_id[0]['id'] if employee_id else False
                    
                    if not employee_id:
                        failed_row = self.check_employee_data(failed_row,rfc,'Payroll Deductions',counter)                            
                    if employee_id:
                        employee_id = self.env['hr.employee'].browse(employee_id)

                        exit_payroll_id = list(filter(lambda b: b['employee_id'][0] == employee_id.id, payroll_process_records))
                        exit_payroll_id = exit_payroll_id[0]['id'] if exit_payroll_id else False
                        exit_payroll_id = self.env['employee.payroll.file'].browse(exit_payroll_id)
                        
                        if exit_payroll_id:
                            exist_ded_lines = exit_payroll_id.deduction_line_ids 
                            exit_payroll_id.net_salary = net_salary
                            
                        if not exit_payroll_id:                             
                            result_dict.update({'payroll_processing_id':self.id,
                                                'period_start' : self.period_start,
                                                'period_end' : self.period_end,
                                                'fornight' : self.fornight,
                                                'employee_id':employee_id.id,
                                                'net_salary':net_salary,
                                                'is_pension_payment_request' : True,
                                                'payment_request_type':'direct_employee'})
                    else:
                        continue

                if ded_key:
                    if  type(ded_key) is int or type(ded_key) is float:
                        ded_key = int(ded_key)

                    ded_id = list(filter(lambda per: per['key'] == str(ded_key), deduction_records))
                    ded_id = ded_id[0]['id'] if ded_id else False
                    
                    if ded_id:
                        deduction_line = False
                        if exit_payroll_id:
                            if exist_ded_lines:
                                deduction_line = exit_payroll_id.deduction_line_ids.filtered(lambda x:x.deduction_id.id==ded_id)
                                for line in deduction_line:
                                    line.amount = amount
                        if not deduction_line:     
                            line_data.append((0,0,{'deduction_id':ded_id,'amount':amount})) 
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

        self.update_failed_file(failed_row,'payroll_deductions','completed',self.deductions_user,self.deductions_filename)
        self.deductions_file_index += counter
        self.deductions_file_load = False
        #self.deductions_hide = False
        self.send_deductions_notification()
    
    def remove_cron_records(self):
        crons = self.env['ir.cron'].sudo().search(
            [('payroll_processing_id', '!=', False)])
        for cron in crons:
            self.cron_id = cron.id
            if cron.payroll_processing_id and cron.payroll_processing_id.cron_id and cron.payroll_processing_id.cron_id.id== cron.id:
                 if cron.payroll_processing_id.deductions_file_load or cron.payroll_processing_id.perception_file_load:
                    continue
            if cron.payroll_processing_id:
                try:
                    cron.sudo().unlink()
                except:
                    pass
        
class PayrollProcessingFailedLog(models.Model):
    
    _name = 'payroll.processing.failed.log'
    _order = 'id desc'
    
    payroll_processing_id = fields.Many2one('custom.payroll.processing','Payroll processing')
    import_file_name = fields.Char("Import File Name")
    user_id = fields.Many2one('res.users','Imported by')
    failed_row_file = fields.Binary(string='Failed Rows File')
    fialed_row_filename = fields.Char(
        string='Log File', default=lambda self: _("Failed_Rows.txt"))
        
    type_of_movement = fields.Selection([('payroll_perceptions','Payroll Perceptions'),
                                         ('payroll_deductions','Payroll Deductions'),
                                         ('pension_payment','Pension Payment'),
                                         ('additional_payments','Additional Payments'),
                                         ('additional_pension_payments','Additional Pension Payments')
                                         ],string='Type of Movement')
    
    state = fields.Selection([('in_progress','In Progress'),
                                         ('completed','Completed'),
                                         ],string='Status')
    
    process_date_time = fields.Datetime('Process Date',default=lambda self: fields.Datetime.now())
    

    def download_file(self):
        self.ensure_one()
        return {
                'type': 'ir.actions.act_url',
                'target':'download',
                 'url': "web/content/?model=payroll.processing.failed.log&id=" + str(self.id) + "&filename_field=fialed_row_filename&field=failed_row_file&download=true&filename=" + self.fialed_row_filename,
            }    

class Cron(models.Model):

    _inherit = 'ir.cron'

    payroll_processing_id = fields.Many2one('custom.payroll.processing','Payroll Process') 
    
    
