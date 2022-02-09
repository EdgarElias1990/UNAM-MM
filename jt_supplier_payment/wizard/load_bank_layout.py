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
from odoo.exceptions import UserError, ValidationError,Warning
import base64
from datetime import datetime, timedelta
from odoo.tools.misc import formatLang, format_date, get_lang
from babel.dates import format_datetime, format_date
import csv
import io
from odoo.tools.misc import ustr
from xlrd import open_workbook

class loadBankLayoutSupplierPayment(models.TransientModel):

    _name = 'load.bank.layout.supplier.payment'
    _description = 'Load Bank Layout Supplier Payment'
    
    journal_id = fields.Many2one('account.journal','Select the file to generate')
    payment_ids = fields.Many2many('account.payment','account_payment_load_bank_layout_rel','load_bank_layout_id','payment_id','Payments')
    file_name = fields.Char('Filename')
    file_data = fields.Binary('Upload File')
    failed_file_name = fields.Char('Failed Filename', default=lambda self: _("Failed_Rows.txt"))
    failed_file_data = fields.Binary('Failed File')
    success_file_name = fields.Char('Success Filename',default="Success_Rows.txt")
    success_file_data = fields.Binary('Success File')
    is_hide_failed = fields.Boolean('Hide Failed',default=True)
    is_hide_success = fields.Boolean('Hide Success',default=True)
    is_hide_file_upload = fields.Boolean('Hide Success',default=False)
         
    def action_load_bank_layout(self):
        active_ids = self.env.context.get('active_ids')
        for payment in self.env['account.payment'].browse(active_ids):
            if payment.payment_state != 'for_payment_procedure':
                raise UserError(_("You can load Bank Layout only for those payments which are in "
                "'For Payment Procedure'!"))
        if not active_ids:
            return ''
        active_rec = self.env['account.payment'].browse(active_ids)
        active_rec.no_validate_payment = True
        if any(active_rec.filtered(lambda x:x.payment_request_type in ('project_payment','supplier_payment','different_to_payroll'))):
            return {
                'name': _('Load Bank Layout'),
                'res_model': 'load.bank.layout.supplier.payment',
                'view_mode': 'form',
                'view_id': self.env.ref('jt_supplier_payment.view_load_bank_layout_supplier_payment_form').id,
                'context': {'default_payment_ids':[(6,0,active_ids)]},
                'target': 'new',
                'type': 'ir.actions.act_window',
            }
        else:
            return {
                'name': _('Load Bank Layout'),
                'res_model': 'load.bank.layout.supplier.payment',
                'view_mode': 'form',
                'view_id': self.env.ref('jt_supplier_payment.view_load_bank_layout_payroll_payment_form').id,
                'context': {'default_payment_ids':[(6,0,active_ids)]},
                'target': 'new',
                'type': 'ir.actions.act_window',
            }

    def convert_string_to_float(self,values):
        amount = 0
        values = str(values)
        amount = values.replace('$','')
        amount = amount.replace(',','')
        amount = float(amount)
        return amount
                
    def get_banamex_file(self):
        try:
            failed_content = ''
            success_content = ''

#             data = base64.decodestring(self.file_data)
#             book = open_workbook(file_contents=data or b'')
#             sheet = book.sheet_by_index(0)
            
            file_data = base64.b64decode(self.file_data)
            data = io.StringIO(file_data.decode("utf-8"))
            data.seek(0)
            file_reader = []
            csv_reader = csv.reader(data, delimiter=',')
            file_reader.extend(csv_reader)
            
            count = 0
            result_vals = []
#             for rowx, row in enumerate(map(sheet.row, range(1, sheet.nrows)), 1):
#                 count+=1
#                 result_dict = {}
#                 for colx, cell in enumerate(row, 1):
#                     
#                     if colx==3:
#                         value = str(cell.value)
#                         result_dict.update({'first':value})
# #                     else:
# #                         continue
#                     if colx==7:
#                         if isinstance(cell.value, float):
#                             value = cell.value
#                             value = str(value).split('.')[0]
#                         else:
#                             value = str(cell.value)
#                         result_dict.update({'bank_account':value})
#                     if colx==9:
#                         value = cell.value
#                         result_dict.update({'amount':value})
#                         
#                 if result_dict and result_dict.get('first','')=='C':
#                     
#                     match_payment =  self.payment_ids.filtered(lambda x:x.state=='draft' and x.amount==result_dict.get('amount',0.0) and x.payment_issuing_bank_acc_id.acc_number==result_dict.get('bank_account',''))
#                     if match_payment:
#                         success_content += str(count)+' : Fecha del corte = '+ str(result_dict.get('bank_account',''))+" and Cuenta = "+str(result_dict.get('amount',0.0)) + "\n"
#                         match_payment[0].post()
#                     else:
#                         failed_content += str(count)+': Payment Not Found For ----> Fecha del corte = '+ str(result_dict.get('bank_account',''))+" and Cuenta = "+str(result_dict.get('amount',0.0)) + "\n"
            previous_account =  False       
            for line in file_reader:
#                 if count==0:
#                     count += 2
#                     continue
                #continue
                amount = 0
                account_no = False
                if line[2]=='C':
                    amount = line[8]
                    account_no = line[6]
                else:
                    previous_account = line[8]
                    continue
                if amount and account_no and previous_account:
                    act_amount = self.convert_string_to_float(amount)
                    #first_amount = amount[:-2]
                    #last_amount = amount[-2:]
 
                    #act_amount = first_amount+"."+last_amount
                    #act_amount = float(act_amount)
                    match_payment =  self.payment_ids.filtered(lambda x:x.state=='draft' and x.amount==act_amount and x.payment_bank_account_id.acc_number==str(account_no) and x.payment_issuing_bank_acc_id.acc_number==str(previous_account))
                    if match_payment:
                        success_content += str(count)+' : '+ str(line) + "\n"
                        match_payment[0].post()
                    else:
                        failed_content += str(count)+' : Payment Not Found For Amount,Bank Account Payment Receipt And Payment Issuing Bank ---> '+ str(act_amount) +","+str(account_no)+","+str(previous_account)+"\n"
                else:
                    failed_content += str(count)+' :PLease Set Amount,Bank Account Payment Receipt And Payment Issuing Bank ---> '+ str(line) + "\n"
                count += 1
                 
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

    def get_hsbc_file(self):
        try:
            failed_content = ''
            success_content = ''
            
            file_data = base64.b64decode(self.file_data)
            data = io.StringIO(file_data.decode("utf-8"))
            data.seek(0)
            file_reader = []
            csv_reader = csv.reader(data, delimiter=',')
            file_reader.extend(csv_reader)
            count = 0
            for line in file_reader:
                if count==0:
                    count += 2
                    continue
                # account_no = line[1]
                cutomer_ref = line[3]
                amount = line[6]
                if amount and cutomer_ref:
                    act_amount = float(amount)
                    match_payment =  self.payment_ids.filtered(lambda x:x.state=='draft' and x.amount==act_amount and x.hsbc_reference==cutomer_ref)
                    if match_payment:
                        success_content += str(count)+' : '+ str(line) + "\n"                        
                        match_payment[0].post()
                    else:
                        failed_content += str(count)+' : Payment Not Found For Amount and HSBC Reference---> '+ str(line) + "\n"
                else:
                    failed_content += str(count)+' :Please set Amount and HSBC Reference---> '+ str(line) + "\n"
                count += 1
                                                            
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
                
                
    def get_santander_file(self):
        try:
            failed_content = ''
            success_content = ''
            
            file_data = base64.b64decode(self.file_data)
            data = io.StringIO(file_data.decode("utf-8")).readlines()
            count = 0
            for line in data:
                count+=1
                sing = line[76]
                amount = line[77:91]
                concept = line[113:152]
                if sing and amount and concept and sing=='-':
                    first_amount = amount[:-2]
                    last_amount = amount[-2:]
                    concept = concept.rstrip()    
                    act_amount = first_amount+"."+last_amount
                    act_amount = float(act_amount)
                    
                    match_payment =  self.payment_ids.filtered(lambda x:x.state=='draft' and x.amount==act_amount and x.santander_payment_concept==concept)
                    if match_payment:
                        success_content += str(count)+' : '+ str(line) + "\n"    
                        match_payment[0].post()
                    else:
                        failed_content += str(count)+' : Payment Not Found For Amount and Santander Payment Concept--->  '+ str(line) + "\n"
                else:
                    failed_content += str(count)+' :Please Set amount and concept---->'+ str(line) + "\n"

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

    def get_jp_morgan_file(self):
        try:

            failed_content = ''
            success_content = ''
            
            file_data = base64.b64decode(self.file_data)
            data = io.StringIO(file_data.decode("utf-8"))
            data.seek(0)
            file_reader = []
            csv_reader = csv.reader(data, delimiter=',')
            file_reader.extend(csv_reader)
            count = 0
            for line in file_reader:
                if count==0:
                    count += 2
                    continue
                jp_payment_concept = line[8]
                amount = line[10]
                if amount and jp_payment_concept:
                    act_amount = float(amount)
                    match_payment =  self.payment_ids.filtered(lambda x:x.state=='draft' and x.amount==act_amount and x.jp_payment_concept==jp_payment_concept)
                    if match_payment:
                        success_content += str(count)+' : '+ str(line) + "\n"                        
                        match_payment[0].post()
                    else:
                        failed_content += str(count)+' : Payment Not Found For Amount and JP Payment Concept---> '+ str(line) + "\n"
                else:
                    failed_content += str(count)+' : Please Set The Amount Or JP Payment Concept----> '+ str(line) + "\n"
                count += 1
                
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

    def get_bbva_file(self):
        try:
            failed_content = ''
            success_content = ''
            file_data = base64.b64decode(self.file_data)
            data = io.StringIO(file_data.decode("utf-8"))
            data.seek(0)
            file_reader = []
            csv_reader = csv.reader(data, delimiter=',')
            file_reader.extend(csv_reader)
            #account_no = ''
            count = 0
            len_file = len(file_reader)
         
            for line in file_reader:
                count += 1
                #if line[0]=='11':
                    #account_no = line[3]
                #    continue
                if count==1:
                    continue
                if count==len_file:
                    continue
                if line[0]!='22':
                    failed_content += str(count)+' : First Column Data Will "22" only For Payment Match---> '+ str(line) + "\n"
                    continue
                payment_charge = line[7]
                amount = line[8]
                data_line = line[0]
                if data_line and data_line=='22' and amount and payment_charge and payment_charge=='1':
                    act_amount = float(amount)
                    
                    match_payment =  self.payment_ids.filtered(lambda x:x.state=='draft' and x.amount==act_amount)
                    if match_payment:
                        success_content += str(count)+' : '+ str(line) + "\n"                        
                        match_payment[0].post()
                    else:
                        failed_content += str(count)+' :Payment Not Found For Amount---> '+ str(line) + "\n"
                else:
                    failed_content += str(count)+' :Please set data line 22 and payment charge 1---> '+ str(line) + "\n"
                
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
        diff_payment = self.payment_ids.filtered(lambda x:x.journal_id.load_bank_format != self.journal_id.load_bank_format)
        if diff_payment: 
            raise UserError(_("The selected layout does NOT match the bank of the selected payments"))

        if self.journal_id.load_bank_format == 'banamex':         
            self.get_banamex_file()
        if self.journal_id.load_bank_format == 'hsbc':         
            self.get_hsbc_file()
        if self.journal_id.load_bank_format == 'santander':         
            self.get_santander_file()
        if self.journal_id.load_bank_format == 'jp_morgan':
            self.get_jp_morgan_file()
        if self.journal_id.load_bank_format == 'bbva_bancomer':
            self.get_bbva_file()
        self.is_hide_file_upload = True
        
        return {
            'name': _('Load Bank Layout'),
            'res_model': 'load.bank.layout.supplier.payment',
            'res_id' : self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('jt_supplier_payment.view_load_bank_layout_supplier_payment_form').id,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
    #========= Payroll Payment verification ========#

    def payroll_payment_get_santander_file(self):
        try:
            failed_content = ''
            success_content = ''
            
            file_data = base64.b64decode(self.file_data)
            data = io.StringIO(file_data.decode("utf-8"))
            data.seek(0)
            file_reader = []
            csv_reader = csv.reader(data, delimiter=',')
            file_reader.extend(csv_reader)
            count = 0
            for line in file_reader:
                if count==0:
                    count += 1
                    continue
                account_no = line[3]
                amount = line[5]
                result_file = line[6]
                if account_no and amount and result_file and result_file=='Procesado':
                    amount = amount.replace(',','')
                    act_amount = float(amount)
                    match_payment =  self.payment_ids.filtered(lambda x:x.state=='draft' and x.amount==act_amount and x.payment_bank_account_id.acc_number==account_no)
                    if match_payment:
                        success_content += str(count)+' : '+ str(line) + "\n"                        
                        match_payment[0].post()
                    else:
                        failed_content += str(count)+' : Payment Not Found For Amount and Account Number---> '+ str(line) + "\n"
                else:
                    failed_content += str(count)+' : Please set account,amount or result Procesado---> '+ str(line) + "\n"
                count += 1
                                                            
            if failed_content:
                failed_data = base64.b64encode(failed_content.encode('utf-8'))
                self.failed_file_data = failed_data
                self.is_hide_failed = False
                
            if success_content:
                success_data = base64.b64encode(success_content.encode('utf-8'))
                self.success_file_data = success_data
                self.is_hide_success = False
                
        except:
            raise Warning(_("The selected layout does NOT match the bank of the selected payments"))        
    
    def payroll_payment_get_hsbc_file(self):
        try:
            failed_content = ''
            success_content = ''
            
            file_data = base64.b64decode(self.file_data)
            data = io.StringIO(file_data.decode("utf-8"))
            data.seek(0)
            file_reader = []
            csv_reader = csv.reader(data, delimiter=',')
            file_reader.extend(csv_reader)
            count = 0
            for line in file_reader:
                if not line:
                    continue
                count += 1
                if count <= 12:
                    continue
                account_no = line[1]
                amount = line[4]
                result_file = line[6]
                
                if account_no and amount and result_file and result_file=='Processed':
                    amount = amount.replace(',','')
                    act_amount = float(amount)
                    match_payment =  self.payment_ids.filtered(lambda x:x.state=='draft' and x.amount==act_amount and x.payment_bank_account_id.acc_number==account_no)
                    if match_payment:
                        success_content += str(count)+' : '+ str(line) + "\n"                        
                        match_payment[0].post()
                    else:
                        failed_content += str(count)+' : Payment Not Found For Amount and Account Number---> '+ str(line) + "\n"
                else:
                    failed_content += str(count)+' : Please set account,amount or result Processed---->'+ str(line) + "\n"
                count += 1
                                                            
            if failed_content:
                failed_data = base64.b64encode(failed_content.encode('utf-8'))
                self.failed_file_data = failed_data
                self.is_hide_failed = False
                
            if success_content:
                success_data = base64.b64encode(success_content.encode('utf-8'))
                self.success_file_data = success_data
                self.is_hide_success = False
                
        except:
            raise Warning(_("The selected layout does NOT match the bank of the selected payments"))        
        
    def payroll_payment_get_bbva_nomina_file(self):
        try:
            failed_content = ''
            success_content = ''
            
            file_data = base64.b64decode(self.file_data)
            data = io.StringIO(file_data.decode("utf-8")).readlines()
            count = 0
            for line in data:
                count+=1
                if count <= 2:
                    continue
                account_no = line[44:60]
                amount = line[23:38]
                status = line[74:76]
                if account_no and amount and status and status=='00':
                    first_amount = amount[:-2]
                    last_amount = amount[-2:]
                        
                    act_amount = first_amount+"."+last_amount
                    act_amount = float(act_amount)
                    #account_no= account_no.lstrip('0')
                    
                    match_payment =  self.payment_ids.filtered(lambda x:x.state=='draft' and x.amount==act_amount and x.payment_bank_account_id.acc_number in account_no)
                    
                    if match_payment:
                        success_content += str(count)+' : '+ str(line) + "\n"                        
                        match_payment[0].post()
                    else:
                        failed_content += str(count)+' : Payment Not Found For Amount and Account Number--->'+ str(line) + "\n"
                else:
                    failed_content += str(count)+' :Please set account,amount or status 00--> '+ str(line) + "\n"
            if failed_content:
                failed_data = base64.b64encode(failed_content.encode('utf-8'))
                self.failed_file_data = failed_data
                self.is_hide_failed = False
                
            if success_content:
                success_data = base64.b64encode(success_content.encode('utf-8'))
                self.success_file_data = success_data
                self.is_hide_success = False

        except:
            raise Warning(_("The selected layout does NOT match the bank of the selected payments"))        
                                                                
#         except ValueError as e:
#             raise ValidationError(_("Column  contains incorrect values. Error: %s")% (ustr(e)))
#         except ValidationError as e:
#             raise ValidationError(_("Column  contains incorrect values. Error: %s")% (ustr(e)))
#         except UserError as e:
#             raise ValidationError(_("Column  contains incorrect values. Error: %s")% (ustr(e)))            

    def payroll_payment_get_bbva_232_file(self):
        try:
            failed_content = ''
            success_content = ''
            
            file_data = base64.b64decode(self.file_data)
            data = io.StringIO(file_data.decode("utf-8")).readlines()
            count = 0
            for line in data:
                count+=1
                if count <= 3:
                    continue
                account_no = line[34:50]
                amount = line[50:65]
                status = line[65:72]
                
                if account_no and amount and status and status=='0000000':
                    first_amount = amount[:-2]
                    last_amount = amount[-2:]
                        
                    act_amount = first_amount+"."+last_amount
                    act_amount = float(act_amount)
                    #account_no= account_no.lstrip('0') 
                    match_payment =  self.payment_ids.filtered(lambda x:x.state=='draft' and x.amount==act_amount and x.payment_bank_account_id.acc_number in account_no)
                    if match_payment:
                        success_content += str(count)+' : '+ str(line) + "\n"                        
                        match_payment[0].post()
                    else:
                        failed_content += str(count)+' : Payment Not Found For Amount and Account Number---> '+ str(line) + "\n"
                else:
                    failed_content += str(count)+' : Please set amount,account or status 0000000---->'+ str(line) + "\n"
            if failed_content:
                failed_data = base64.b64encode(failed_content.encode('utf-8'))
                self.failed_file_data = failed_data
                self.is_hide_failed = False
                
            if success_content:
                success_data = base64.b64encode(success_content.encode('utf-8'))
                self.success_file_data = success_data
                self.is_hide_success = False
                                                                
        except:
            raise Warning(_("The selected layout does NOT match the bank of the selected payments"))        

    def payroll_payment_get_banamex_file(self):
        try:
            failed_content = ''
            success_content = ''
            
            file_data = base64.b64decode(self.file_data)
            data = io.StringIO(file_data.decode("utf-8")).readlines()
            count = 0
            for line in data:
                if not line:
                    continue
                count+=1
                if count <= 2:
                    continue
                if line and line[0]=='4':
                    continue
                
                amount = line[5:23]
                account_no = line[25:45]
                status = line[229]
                
                if account_no and amount and status and status=='3':
                    first_amount = amount[:-2]
                    last_amount = amount[-2:]
                    act_amount = first_amount+"."+last_amount
                    act_amount = float(act_amount)
                    #account_no= account_no[-7:]
                    #account_no = account_no.lstrip("0")
                    match_payment =  self.payment_ids.filtered(lambda x:x.state=='draft' and x.amount==act_amount and x.payment_bank_account_id.acc_number in account_no)
                    
                    if match_payment:
                        success_content += str(count)+' : '+ str(line) + "\n"                        
                        match_payment[0].post()
                    else:
                        failed_content += str(count)+' : Payment Not Found For Amount and Account Number--->'+ str(line) + "\n"
                else:
                    failed_content += str(count)+' : Please set account,amount or status 3'+ str(line) + "\n"
            if failed_content:
                failed_data = base64.b64encode(failed_content.encode('utf-8'))
                self.failed_file_data = failed_data
                self.is_hide_failed = False
                
            if success_content:
                success_data = base64.b64encode(success_content.encode('utf-8'))
                self.success_file_data = success_data
                self.is_hide_success = False
                                                                
        except:
            raise Warning(_("The selected layout does NOT match the bank of the selected payments"))        

    def payroll_payment_get_scotiabank_file(self):
        try:
            failed_content = ''
            success_content = ''
            
            file_data = base64.b64decode(self.file_data)
            data = io.StringIO(file_data.decode("utf-8")).readlines()
            count = 0
            process_len = len(data) - 2 
            for line in data:
                count+=1
                if count <= 2:
                    continue
                if process_len < count:
                    continue
                account_no = line[132:152]
                amount = line[8:23]
                status = line[323:326]
                
                if account_no and amount and status and status=='000':
                    first_amount = amount[:-2]
                    last_amount = amount[-2:]
                    act_amount = first_amount+"."+last_amount
                    act_amount = float(act_amount)
                    #account_no= account_no.lstrip('0')
                    match_payment =  self.payment_ids.filtered(lambda x:x.state=='draft' and x.amount==act_amount and x.payment_bank_account_id.acc_number in account_no)
                    
                    if match_payment:
                        success_content += str(count)+' : '+ str(line) + "\n"                        
                        match_payment[0].post()
                    else:
                        failed_content += str(count)+' : Payment Not Found For Amount and Account Number--->'+ str(line) + "\n"
                else:
                    failed_content += str(count)+' : Please set account,amount or status 000---->'+ str(line) + "\n"
            if failed_content:
                failed_data = base64.b64encode(failed_content.encode('utf-8'))
                self.failed_file_data = failed_data
                self.is_hide_failed = False
                
            if success_content:
                success_data = base64.b64encode(success_content.encode('utf-8'))
                self.success_file_data = success_data
                self.is_hide_success = False
                                                                
        except:
            raise Warning(_("The selected layout does NOT match the bank of the selected payments"))        

    #====== TODO FILE ========#              
    def payroll_payment_get_banorte_file(self):
        try:
            failed_content = ''
            success_content = ''
            
            file_data = base64.b64decode(self.file_data)
            data = io.StringIO(file_data.decode("utf-8")).readlines()
            count = 0
            for line in data:
                count+=1
                if count <= 1:
                    continue
                account_no = line[132:150]
                amount = line[99:114]
                status = line[165:167]
                if account_no and amount and status and status=='00':
                    first_amount = amount[:-2]
                    last_amount = amount[-2:]
                    act_amount = first_amount+"."+last_amount
                    act_amount = float(act_amount)
                    #account_no= account_no.lstrip('0')
                    match_payment =  self.payment_ids.filtered(lambda x:x.state=='draft' and x.amount==act_amount and x.payment_bank_account_id.acc_number in account_no)
                    
                    if match_payment:
                        success_content += str(count)+' : '+ str(line) + "\n"                        
                        match_payment[0].post()
                    else:
                        failed_content += str(count)+' : Payment Not Found For Amount and Account Number--->'+ str(line) + "\n"
                else:
                    failed_content += str(count)+' : Please set account,amount or status 00'+ str(line) + "\n"
            if failed_content:
                failed_data = base64.b64encode(failed_content.encode('utf-8'))
                self.failed_file_data = failed_data
                self.is_hide_failed = False
                
            if success_content:
                success_data = base64.b64encode(success_content.encode('utf-8'))
                self.success_file_data = success_data
                self.is_hide_success = False
                                                                
        except:
            raise Warning(_("The selected layout does NOT match the bank of the selected payments"))        
        
    def load_payroll_payment_bank_layout(self):
        diff_payment = self.payment_ids.filtered(lambda x:x.journal_id.payroll_load_bank_format != self.journal_id.payroll_load_bank_format)
        if diff_payment: 
            raise UserError(_("The selected layout does NOT match the bank of the selected payments"))

        if self.journal_id.payroll_load_bank_format == 'santander':         
            self.payroll_payment_get_santander_file()
        elif self.journal_id.payroll_load_bank_format == 'hsbc':         
            self.payroll_payment_get_hsbc_file()
        elif self.journal_id.payroll_load_bank_format == 'bbva_nomina':
            self.payroll_payment_get_bbva_nomina_file()
        elif self.journal_id.payroll_load_bank_format == 'bbva_232':
            self.payroll_payment_get_bbva_232_file()
        elif self.journal_id.payroll_load_bank_format == 'banamex':         
            self.payroll_payment_get_banamex_file()
        elif self.journal_id.payroll_load_bank_format == 'scotiabank':
            self.payroll_payment_get_scotiabank_file()
        elif self.journal_id.payroll_load_bank_format == 'banorte':
            self.payroll_payment_get_banorte_file()
            
        self.is_hide_file_upload = True
        
        return {
            'name': _('Load Bank Layout'),
            'res_model': 'load.bank.layout.supplier.payment',
            'res_id' : self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('jt_supplier_payment.view_load_bank_layout_payroll_payment_form').id,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
