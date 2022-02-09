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
from odoo import models, fields,api,_
from odoo.exceptions import UserError, ValidationError
import base64
from datetime import datetime, timedelta
from odoo.tools.misc import formatLang, format_date, get_lang
from babel.dates import format_datetime, format_date

class GenerateBankLayout(models.TransientModel):

    _name = 'generate.bank.layout'
    _description = 'Generate Bank Layout'
    
    journal_id = fields.Many2one('account.journal','Select the file to generate')
    payment_ids = fields.Many2many('account.payment','account_payment_bank_layout_rel','bank_layout_id','payment_id','Payments')
    file_name = fields.Char('Filename')
    file_data = fields.Binary('Download')
    sit_file_key = fields.Char('File Key',size=30)
    bank_format = fields.Selection(related='journal_id.bank_format')
    
    @api.onchange('journal_id')
    def onchange_journal_id(self):
        self.sit_file_key = False
        if self.bank_format=='bbva_sit':
            sit_file_key = 'TRANSFERUNAM'
            currect_time = datetime.today()
            
            sit_file_key +=str(currect_time.year)
            sit_file_key +=str(currect_time.month).zfill(2)
            sit_file_key +=str(currect_time.day).zfill(2)

            if self.payment_ids:
                if self.payment_ids[0].currency_id.name=='MXN':
                    sit_file_key += 'MN'
                else:
                    sit_file_key += "ME"
                if self.payment_ids[0].sit_operation_code=='payment_on_account_bancomer':
                    sit_file_key += 'BBVA'
                elif self.payment_ids[0].sit_operation_code=='payment_interbank':
                    sit_file_key += "OTROS"
            
            self.sit_file_key = sit_file_key
            
            
        
    def action_generate_bank_layout(self):
        
        active_ids = self.env.context.get('active_ids')
        for payment in self.env['account.payment'].browse(active_ids):
            if payment.payment_state != 'for_payment_procedure':
                raise UserError(_("You can generate Bank Layout only for those payments which are in "
                "'For Payment Procedure'!"))
        if not active_ids:
            return ''
        active_rec = self.env['account.payment'].browse(active_ids)
        if any(active_rec.filtered(lambda x:x.payment_request_type in ('project_payment','supplier_payment','different_to_payroll'))):
            return {
                'name': _('Generate Bank Layout'),
                'res_model': 'generate.bank.layout',
                'view_mode': 'form',
                'view_id': self.env.ref('jt_supplier_payment.view_generate_bank_layout').id,
                'context': {'default_payment_ids':[(6,0,active_ids)]},
                'target': 'new',
                'type': 'ir.actions.act_window',
            }
        else:
            return {
                'name': _('Generate Bank Layout'),
                'res_model': 'generate.bank.layout',
                'view_mode': 'form',
                'view_id': self.env.ref('jt_supplier_payment.view_generate_payroll_payment_bank_layout').id,
                'context': {'default_payment_ids':[(6,0,active_ids)]},
                'target': 'new',
                'type': 'ir.actions.act_window',
            }
            
    def banamex_file_format(self):
        file_data = ''
        file_name = 'banamex.txt'
        
        for payment in self.payment_ids:
            file_data += '03'
            if payment.journal_id.account_type:
                if payment.journal_id.account_type=='check':
                    file_data += '01'
                    if payment.journal_id.branch_number:
                        file_data += payment.journal_id.branch_number.zfill(4)
                    else: 
                        file_data += '0000'                        
                elif payment.journal_id.account_type=='card':
                    file_data += '03'
                    file_data += '0000'
                elif payment.journal_id.account_type=='master':
                    file_data += '06'
                    file_data += '0000'
                else:
                    file_data += '000000'
            else:
                file_data += '000000'
            if payment.journal_id.bank_account_id:
                file_data += payment.journal_id.bank_account_id.acc_number.zfill(20)
            else:
                temp =''
                file_data +=temp.zfill(20)
           
            #==== Receipt Bank DATA ===========
            if payment.payment_bank_account_id:
                if payment.payment_bank_account_id.account_type=='checks':
                    file_data += '01'
                    if payment.payment_bank_account_id.branch_number:
                        file_data += payment.payment_bank_account_id.branch_number.zfill(4)
                    else: 
                        file_data += '0000'                        
                elif payment.payment_bank_account_id.account_type=='card':
                    file_data += '03'
                    file_data += '0000'
                elif payment.payment_bank_account_id.account_type=='master_acc':
                    file_data += '06'
                    file_data += '0000'
                else:
                    file_data += '00'
                    file_data += '0000'
            else:
                file_data += '000000'
            if payment.payment_bank_account_id:
                file_data += payment.payment_bank_account_id.acc_number.zfill(20)
            else:
                temp =''
                file_data +=temp.zfill(20)
            
            #====== Amount Data =========
            amount = round(payment.amount, 2)
            amount = "%.2f" % payment.amount            
            amount = str(amount).split('.')
            file_data +=str(amount[0]).zfill(12)
            file_data +=str(amount[1])
            #====== Currency Data =========
            if payment.currency_id:
                if payment.currency_id.name=='USD':
                    file_data +='005'
                elif payment.currency_id.name=='MXN':
                    file_data +='001'
            
            #====== Description =========
            temp_desc = ''
#             if payment.banamex_description:
#                 temp_desc = payment.banamex_description
            if payment.dependancy_id and payment.dependancy_id.sort_description:
                temp_desc += payment.dependancy_id.sort_description
            if payment.folio:
                if temp_desc:
                    temp_desc += " "+payment.folio
                else:
                    temp_desc += payment.folio
                    
            file_data += temp_desc.ljust(24, " ")
            #====== banamex_concept =========
            temp_desc = ''
#             if payment.banamex_concept:
#                 temp_desc = payment.banamex_concept
            if payment.dependancy_id and payment.dependancy_id.sort_description:
                temp_desc += payment.dependancy_id.sort_description
            if payment.name:
                if temp_desc:
                    temp_desc += " "+payment.name
                else:
                    temp_desc += payment.name

            file_data += temp_desc.ljust(34, " ")
    
            #====== banamex_reference =========
            temp_desc = ''
            if payment.banamex_reference:
                temp_desc = payment.banamex_reference
            file_data += temp_desc.ljust(10, " ")
            
            #====== Currency constant =========
            file_data += "000"
            #====== Current Dat time=========
            currect_time = datetime.today()
            
            file_data +=str(currect_time.day).zfill(2)
            file_data +=str(currect_time.month).zfill(2)
            file_data +=str(currect_time.year)[2:]
            file_data +=str(currect_time.hour).zfill(2)
            file_data +=str(currect_time.minute).zfill(2)
            file_data +="\r\n"
        gentextfile = base64.b64encode(bytes(file_data,'utf-8'))
        self.file_data = gentextfile
        self.file_name = file_name
        
    def bbva_tnn_ptc_file_format(self):
        file_data = ''
        file_name = 'BBVA BANCOMER NET CASH​ (TNN or PTC).txt'
        
        for payment in self.payment_ids:
            #==== Receipt Bank DATA ===========#            
            if payment.payment_bank_account_id:
                file_data += payment.payment_bank_account_id.acc_number.zfill(18)
            else:
                temp =''
                file_data +=temp.zfill(18)
            #======= Bank Issuance of payment ======#    
            if payment.journal_id.bank_account_id:
                file_data += payment.journal_id.bank_account_id.acc_number.zfill(18)
            else:
                temp =''
                file_data +=temp.zfill(18)
            #====== Currency Data =========#
            if payment.currency_id:
                if payment.currency_id.name=='USD':
                    file_data +='USD'
                elif payment.currency_id.name=='MXN':
                    file_data += 'MXP'
                else:
                    file_data += payment.currency_id.name
            #====== Amount Data =========#
            amount = round(payment.amount, 2)
            amount = "%.2f" % payment.amount            
            amount = str(amount).split('.')
            file_data +=str(amount[0]).zfill(13)
            file_data +='.'
            file_data +=str(amount[1])
            
            #=====reason for payment======#
            reason_payment = 'PAGO'
            if payment.payment_date:
                payment_year = str(payment.payment_date.year)[2:]
                month_name = format_datetime(payment.payment_date, 'MMMM', locale=get_lang(self.env).code)
                if payment.payment_date.month==1:
                    month_name = 'ENERO'
                elif payment.payment_date.month==2:
                    month_name = 'FEBRERO'
                elif payment.payment_date.month==3:
                    month_name = 'MARZO'
                elif payment.payment_date.month==4:
                    month_name = 'ABRIL'
                elif payment.payment_date.month==5:
                    month_name = 'MAYO'
                elif payment.payment_date.month==6:
                    month_name = 'JUNIO'
                elif payment.payment_date.month==7:
                    month_name = 'JULIO'
                elif payment.payment_date.month==8:
                    month_name = 'AGPSTO'
                elif payment.payment_date.month==9:
                    month_name = 'SEPTIEMBRE'
                elif payment.payment_date.month==10:
                    month_name = 'OCTUBRE'
                elif payment.payment_date.month==11:
                    month_name = 'NOVIEMBRE'
                elif payment.payment_date.month==12:
                    month_name = 'DICIEMBRE'
                
                reason_payment += " "+month_name+" "+payment_year
            file_data += reason_payment.ljust(30, " ")     
            file_data +="\r\n"      
        gentextfile = base64.b64encode(bytes(file_data,'utf-8'))
        self.file_data = gentextfile
        self.file_name = file_name

    def bbva_tsc_pcs_file_format(self):
        file_data = ''
        file_name = 'BBVA BANCOMER NET CASH​ ​ (TSC or PSC).txt'
        
        for payment in self.payment_ids:
            #==== Receipt Bank DATA ===========#            
            if payment.payment_bank_account_id:
                file_data += payment.payment_bank_account_id.acc_number.zfill(18)
            else:
                temp =''
                file_data +=temp.zfill(18)
            if payment.journal_id.bank_account_id:
                file_data += payment.journal_id.bank_account_id.acc_number.zfill(18)
            else:
                temp =''
                file_data +=temp.zfill(18)
            #====== Currency Data =========#
            file_data += 'MXP'
#             if payment.currency_id:
#                 file_data += payment.currency_id.name
            #====== Amount Data =========#
            amount = round(payment.amount, 2)
            amount = "%.2f" % payment.amount            
            amount = str(amount).split('.')
            file_data +=str(amount[0]).zfill(13)
            file_data +='.'
            file_data +=str(amount[1])

            #=====“Beneficiary”======#
            beneficiary_name=''
            if payment.partner_id:
                if len(payment.partner_id.name)>30:
                    beneficiary_name = payment.partner_id.name[:30]
                else:
                    beneficiary_name = payment.partner_id.name
            file_data += beneficiary_name.ljust(30, " ")   
            #======= Type of Account ========#
            bank_account_code = '00'
            if payment.partner_id and payment.partner_id.bank_ids:
                if payment.partner_id.bank_ids[0].account_type=='card':
                    bank_account_code = '03'
                elif payment.partner_id.bank_ids[0].account_type=='clabe_acc':
                    bank_account_code = '40'
            file_data +=  bank_account_code
              
#             if payment.payment_bank_account_id:
#                 if payment.payment_bank_account_id.account_type=='card':
#                     file_data += '03'
#                 elif payment.payment_bank_account_id.account_type=='clabe_acc':
#                     file_data += '40'
#                 else:
#                     file_data += '00'
            #======= Bank Code / Key bank ========#
            bank_code = ''
            if payment.payment_bank_id:
                if payment.payment_bank_id.l10n_mx_edi_code:
                    bank_code = payment.payment_bank_id.l10n_mx_edi_code
            file_data += bank_code.zfill(3)
            #=====reason for payment======#
            reason_payment = 'PAGO'
            if payment.payment_date:
                payment_year = str(payment.payment_date.year)[2:]
                month_name = format_datetime(payment.payment_date, 'MMMM', locale=get_lang(self.env).code)
                if payment.payment_date.month==1:
                    month_name = 'ENERO'
                elif payment.payment_date.month==2:
                    month_name = 'FEBRERO'
                elif payment.payment_date.month==3:
                    month_name = 'MARZO'
                elif payment.payment_date.month==4:
                    month_name = 'ABRIL'
                elif payment.payment_date.month==5:
                    month_name = 'MAYO'
                elif payment.payment_date.month==6:
                    month_name = 'JUNIO'
                elif payment.payment_date.month==7:
                    month_name = 'JULIO'
                elif payment.payment_date.month==8:
                    month_name = 'AGPSTO'
                elif payment.payment_date.month==9:
                    month_name = 'SEPTIEMBRE'
                elif payment.payment_date.month==10:
                    month_name = 'OCTUBRE'
                elif payment.payment_date.month==11:
                    month_name = 'NOVIEMBRE'
                elif payment.payment_date.month==12:
                    month_name = 'DICIEMBRE'
                                
                reason_payment += " "+month_name+" "+payment_year
            file_data += reason_payment.ljust(30, " ")     
            #====== net_cash_reference =======#
            net_cash_reference = ''
#             if payment.net_cash_reference:
#                 net_cash_reference = payment.net_cash_reference
            if payment.name:
                net_cash_reference = payment.name
            file_data += net_cash_reference.zfill(7)
            #====== net_cash_availability =======#   
            #file_data += "SPEI"
            availability = 'H'
#             if payment.net_cash_availability:
#                 if payment.net_cash_availability=='SPEI':
#                     availability = 'H'
#                 elif payment.net_cash_availability=='CECOBAN':
#                     file_data += 'M'
            file_data += availability
            file_data +="\r\n"      
                                     
        gentextfile = base64.b64encode(bytes(file_data,'utf-8'))
        self.file_data = gentextfile
        self.file_name = file_name

    def bbva_sit_file_format(self):
        file_data = ''
        file_name = 'BBVA BANCOMER SIT.txt'
        
        #============= Header Data =========#
        file_data += 'H'
        file_data += '000747289'
        
        #========= Current Date =========
        currect_time = datetime.today()
        file_data +=str(currect_time.year)
        file_data +="-"+str(currect_time.month).zfill(2)
        file_data +="-"+str(currect_time.day).zfill(2)
        
        file_data += '01'
        
        #===== sit_file_key ====
#         sit_file_key = ''
#         if self.payment_ids and self.payment_ids[0].sit_file_key:
#             sit_file_key = self.payment_ids[0].sit_file_key
        sit_file_key = 'TRANSFERUNAM'
        sit_file_key +=str(currect_time.year)
        sit_file_key +=str(currect_time.month).zfill(2)
        sit_file_key +=str(currect_time.day).zfill(2)
        if self.payment_ids:
            if self.payment_ids[0].currency_id.name=='MXN':
                sit_file_key += 'MN'
            else:
                sit_file_key += "ME"
            if self.payment_ids[0].sit_operation_code=='payment_on_account_bancomer':
                sit_file_key += 'BBVA'
            elif self.payment_ids[0].sit_operation_code=='payment_interbank':
                sit_file_key += "OTROS"

        file_data +=sit_file_key.ljust(30)
        #======== Response Code =======#
        file_data += '00'
        #======== Response code description =======#
        file_data += ''.ljust(20)
        #======= Channel =======#
        file_data += ''.ljust(3)
        #========= Charge account ==========#
        if self.journal_id.bank_account_id:
            file_data += self.journal_id.bank_account_id.acc_number.zfill(35)
        else:
            temp =''
            file_data +=temp.zfill(35)
        #====== Currency of the agreement =======#
        file_data += ''.ljust(3)
        #======== FILLER =========
        file_data += ''.ljust(1251)
        file_data +="\r\n"
        total_amount = 0
        #============= Payment  Details =========#              
        for payment in self.payment_ids:

            #=======Registration indicato ========            
            file_data +="D"
            #=======Instruction ========            
            file_data +="A"
            #=======Document type ========            
            file_data +="P"
            #=== Reference  =====
            folio = ''
            if payment.folio:
                folio = payment.folio
            folio_splits = folio.split('/')
            rec_data = ''
            for sp_data in folio_splits:
                rec_data+=sp_data
            file_data += rec_data.ljust(20)
            #===== Provider Password / Beneficiary Password =======#
            pass_beneficiary = ''
            if payment.partner_id and payment.partner_id.password_beneficiary:
                pass_beneficiary = payment.partner_id.password_beneficiary
            file_data += pass_beneficiary.ljust(30)
            #======= Type of Service  =======
            file_data +="PDA"
            
            #======= Operation code  ========#
            sit_operation_code = '0'
#             if payment.sit_operation_code:
#                 if payment.sit_operation_code=='payment_on_account_bancomer':
#                     sit_operation_code = '2'
#                 elif payment.sit_operation_code=='payment_interbank':
#                     sit_operation_code = '5'
            
            if payment.partner_id and payment.partner_id.bank_ids and payment.partner_id.bank_ids[0].l10n_mx_edi_clabe:
                if payment.partner_id.bank_ids[0].l10n_mx_edi_clabe.startswith('012'):
                    sit_operation_code = '2'
                else:
                    sit_operation_code = '5'
            file_data +=sit_operation_code
            #======== Charge account  ==========#
            file_data += ''.zfill(20)
            #======== FILLER ========
            file_data += ''.ljust(15)
            #=======Reference numeral ========#
            sit_reference = ''
            if payment.sit_operation_code and payment.sit_operation_code=='payment_interbank' and payment.sit_reference:
                sit_reference = payment.sit_reference
            file_data += sit_reference.ljust(25)
            #=======Reason For Payment ========#
            sit_reason_for_payment = payment.folio or ''
#             if payment.sit_operation_code and payment.sit_operation_code=='payment_interbank' and payment.sit_reason_for_payment:
#                 sit_reason_for_payment = payment.sit_reason_for_payment
            file_data += sit_reason_for_payment.ljust(37)
            #======== FILLER ========
            file_data += ''.ljust(15)
    
            #=======Personalized legend ========#
            sit_reference = ''
            if payment.sit_reference:
                sit_reference = payment.sit_reference
            file_data += sit_reference.ljust(25)
            #======== CIE Concept ========#
            file_data += ''.ljust(37)
            #======Tax receipt =====#
            file_data += "N"
            #======== FILLER ========#
            file_data += ''.ljust(8)
            #======= Account type ======#
            file_data += ''.ljust(2)
            #======= Subscription account ======#
            file_data += ''.ljust(35)
            #======= Name of 1st beneficiary ======#
            file_data += ''.ljust(40)
            #======= Identification code of the 1st beneficiary======#
            file_data += ''.ljust(1)
            #======= Identification number 1st beneficiary======#
            file_data += ''.ljust(30)
            #======= Name of 2nd beneficiary======#
            file_data += ''.ljust(40)
            #======= Identification code of the 2nd beneficiary======#
            file_data += ''.ljust(1)
            #======= Identification number 2nd beneficiary======#
            file_data += ''.ljust(30)
            #====== Currency Data =========#
            if payment.currency_id:
                if payment.currency_id.name=='MXN':
                    file_data += 'MXP'
                else:
                    file_data += payment.currency_id.name
            #====== BIC / SWIFT =========#
            if payment.currency_id:
                if payment.currency_id.name=='MXN':
                    file_data += ''.ljust(11)
                else:
                    if payment.payment_bank_account_id and payment.payment_bank_account_id.bic_swift:
                        file_data += payment.payment_bank_account_id.bic_swift.ljust(11)
                    else:
                        file_data += ''.ljust(11)                         

            #====== ABA =========#
            if payment.currency_id:
                if payment.currency_id.name=='MXN':
                    file_data += ''.ljust(9)
                else:
                    if payment.payment_bank_account_id and payment.payment_bank_account_id.aba:
                        file_data += payment.payment_bank_account_id.aba.zfill(9)
                    else:
                        file_data += ''.zfill(9)                         
        
            #======= Document key ========#
            file_data += 'FA'
            #====== Amount Data =========
            total_amount += payment.amount
            amount = round(payment.amount, 2)
            amount = "%.2f" % payment.amount
            amount = str(amount).split('.')
            file_data +=str(amount[0]).zfill(13)
            file_data +=str(amount[1])
            #========FILLER==========
            file_data +=''.zfill(15)
            #======= Confirmation Type ========#
            file_data += '01'
            #========== Email ==========#
            email = ''
            if payment.partner_id and payment.partner_id.email:
                email =  payment.partner_id.email

            if len(email) > 50:
                file_data += email[:50]
            else:
                file_data += email.ljust(50)
            #===== Periodicity interest of ======#
            file_data += 'N'
            #======= FILLER =======#
            file_data +=''.zfill(8)
            #======= FILLER =======#
            file_data +=''.zfill(4)

            #========= Payment Date =========
            if payment.payment_date:
                file_data +=str(payment.payment_date.year)
                file_data +="-"+str(payment.payment_date.month).zfill(2)
                file_data +="-"+str(payment.payment_date.day).zfill(2)
            #====== Effective date =======#
            file_data += '0001-01-01'
            #====== Grace Date =======#
            file_data += '0001-01-01'
            #====== Expiration date=======#
            file_data += '0001-01-01'
            #=========Document Date =========
            if payment.payment_date:
                file_data +=str(payment.payment_date.year)
                file_data +="-"+str(payment.payment_date.month).zfill(2)
                file_data +="-"+str(payment.payment_date.day).zfill(2)
            #====== Recurring payment indicator =========#
            file_data += 'N'
            #======= FILLER =======#
            file_data += ''.ljust(1) 
            #====== Recurring payment end date=======#
            file_data += '0001-01-01'
            #==== Additional data length or Payment detail =====#
            file_data += '700'
            #======== Additional =======#
#             additional = 'PAGO UNAM'
#             if payment.folio:
#                 split_data = payment.folio.split('/')
#                 if split_data:
#                     additional +=" - "+split_data[0]
#             if payment.sit_additional_data:
#                 additional += payment.sit_additional_data
            additional = ''
            if payment.sit_additional_data:
                additional = payment.sit_additional_data
#             if payment.dependancy_id:
#                 if payment.dependancy_id.description:
#                     additional += payment.dependancy_id.description +" "
#                 if payment.dependancy_id.dependency:
#                     additional += payment.dependancy_id.dependency + "-"
#             if payment.sub_dependancy_id and payment.sub_dependancy_id.sub_dependency:
#                 additional += payment.sub_dependancy_id.sub_dependency + " "
#             if self.env.user.lang == 'es_MX':
#                 additional += "FAVOR DE MANTENER ACTUALIZADA SU INFORMACIÓN BANCARIA"
#             else: 
#                 additional += "PLEASE KEEP YOUR BANKING INFORMATION UPDATED"    
            file_data += additional.ljust(700)
            #======= FILLER =======#
            file_data += ''.ljust(10) 
            #======= FILLER =======#
            file_data += ''.ljust(10)
            #======= Code status of the document =======# 
            file_data += ''.ljust(2)
            #======= Document status code description =======# 
            file_data += ''.ljust(30)
            #====== Date of last document event=======#
            file_data += '0001-01-01'
            file_data +="\r\n"
        
        #============== Trailer or Summary =============#
        if self.payment_ids and self.payment_ids[0].currency_id and self.payment_ids[0].currency_id.name=='MXN':  
            file_data += "T"
            caracts = 1
            total_rec = len(self.payment_ids)
            #==== Number of records high======#
            file_data += str(total_rec).zfill(10)
            caracts += 10
            #==== Import Total MXP Highs======#
            amount = "%.2f" % total_amount
            amount = str(amount).split('.')
            file_data +=str(amount[0]).zfill(13)
            caracts += 13
            file_data +=str(amount[1])
            caracts += len(amount[1])
            #==== Number of records MXP divestitures======#
            #file_data += str(total_rec).zfill(10)
            #==== Total amount Retirements MXP======#
            #file_data +=str(amount[0]).zfill(13)
            #file_data +=str(amount[1])
            #===== Filler ===#
            falt = 251 - caracts
            print('flat', falt)
            file_data += ''.zfill(falt)
            file_data += ''.ljust(1115)
            file_data +="\r\n"
        else:
            file_data += "T"

            total_rec = len(self.payment_ids)
            #=====FILLER=====#
            file_data += ''.zfill(250)
            #============Number of records==============#
            file_data += str(total_rec).zfill(10)
            #============== Total Amount ============#
            amount = "%.2f" % total_amount
            amount = str(amount).split('.')
            file_data +=str(amount[0]).zfill(13)
            file_data +=str(amount[1])
            #============Number of records==============#
            file_data += str(total_rec).zfill(10)
            #============== Total Amount ============#
            amount = "%.2f" % total_amount
            amount = str(amount).split('.')
            file_data +=str(amount[0]).zfill(13)
            file_data +=str(amount[1])
            #=====FILLER=====#
            file_data += ''.zfill(100)
            
            file_data +="\r\n"
        gentextfile = base64.b64encode(bytes(file_data,'utf-8'))
        self.file_data = gentextfile
        self.file_name = file_name
        
    def santander_file_format(self):
        file_name = 'SANTANDER.txt'
        file_data = ''
        for payment in self.payment_ids:
            #========= Charge account ==========#
            if self.journal_id.bank_account_id:
                if len(self.journal_id.bank_account_id.acc_number) > 11:
                    file_data += self.journal_id.bank_account_id.acc_number[:11]
                else:
                    file_data += self.journal_id.bank_account_id.acc_number.zfill(11)
            else:
                temp =''
                file_data +=temp.zfill(11)
            #====== Spaces ====#
            file_data += ''.ljust(5)
            #===== Bank Account Payment Receiving ========#
            if payment.payment_bank_account_id:
                if len(payment.payment_bank_account_id.acc_number) > 11:
                    file_data += payment.payment_bank_account_id.acc_number[:11]
                else:
                    file_data += payment.payment_bank_account_id.acc_number.zfill(11)
            else:
                temp =''
                file_data +=temp.zfill(11)
            #====== Spaces ====#
            file_data += ''.ljust(5)
            #====== Amount Data =========#
            amount = round(payment.amount, 2)
            amount = "%.2f" % payment.amount
            amount = str(amount).split('.')
            file_data +=str(amount[0]).zfill(10)
            file_data +='.'
            file_data +=str(amount[1])
            #======= Payment concept ==========#
            santander_payment_concept = ''
#             if payment.santander_payment_concept:
#                 if len(payment.santander_payment_concept) > 40:
#                     santander_payment_concept = payment.santander_payment_concept[:40]
#                 else:
#                     santander_payment_concept = payment.santander_payment_concept
            if payment.folio:
                santander_payment_concept += payment.folio
            if payment.name:
                santander_payment_concept += " "+payment.name
                
            file_data += santander_payment_concept.ljust(40)
            
            #==== Payment Date ======
            if payment.payment_date:
                file_data +=str(payment.payment_date.day).zfill(2)
                file_data +=str(payment.payment_date.month).zfill(2)
                file_data +=str(payment.payment_date.year)
                file_data += '     '
            else:
                file_data += '           '
            file_data +="\r\n"
        gentextfile = base64.b64encode(bytes(file_data,'utf-8'))
        self.file_data = gentextfile
        self.file_name = file_name
            
    def hsbc_file_format(self):    
        file_name = 'HSBC.csv'
        record_count = 0
        file_data = ''
        for payment in self.payment_ids:
            #==========Sequence ========#
            record_count+=1
            file_data+=str(record_count)

            #==========Bank Account ========#
            if self.journal_id.bank_account_id:
                file_data +=","+self.journal_id.bank_account_id.acc_number.zfill(10)
            else:
                temp =''
                file_data +=","+temp.zfill(10)
            #===== Bank Account Payment Receiving ========#
            if payment.payment_bank_account_id:
                file_data += ","+payment.payment_bank_account_id.acc_number.zfill(10)
            else:
                temp =''
                file_data +=","+temp.zfill(10)            
            #====== Amount Data =========#
            amount = round(payment.amount, 2)
            amount = "%.2f" % payment.amount
            amount = str(amount).split('.')
            #print ('Amount=====',x)
            file_data +=","+str(amount[0])
            file_data +='.'
            file_data +=str(amount[1])
            
            #====== Currency Data =========#
            if payment.currency_id:
                if payment.currency_id.name=='MXN':
                    file_data += ','+'1'
                elif payment.currency_id.name=='USD':
                    file_data += ','+'2'
                else:
                    file_data += ','+''
            #===== hsbc_reference ====#
            hsbc_reference = ''
#             if payment.hsbc_reference:
#                 hsbc_reference = payment.hsbc_reference
            if payment.name:
                hsbc_reference = payment.name
            file_data +="," + hsbc_reference
            #======= Partner Name ========#
            partner_name = ''
            if payment.partner_id:
                partner_name = payment.partner_id.name
            file_data +="," + partner_name   
            #==== Fiscal Proof  ========#
            file_data +="," + '0'
            #==== RFC Of the beneficiary  ========#
            file_data +=",                  " # 18 Space
            #====VAT  ========#
            file_data +=",             "    # 13 Space 
            
            file_data +="\r\n"
        
        file_data +=str(record_count+1) + ","+ str(record_count) + ","+'Transfer terceros' 
        file_data +="\r\n"
        gentextfile = base64.b64encode(bytes(file_data,'utf-8'))
        self.file_data = gentextfile
        self.file_name = file_name

    def jp_morgan_wires_file_format(self):   

        file_name = 'jp_morgan_wires.csv'
        record_count = 0
        total_amount = 0
        file_data = 'HEADER'+","
        #====== Current Dat time=========
        currect_time = datetime.today()
        file_data +=str(currect_time.year)
        file_data +=str(currect_time.month).zfill(2)
        file_data +=str(currect_time.day).zfill(2)
        file_data +=str(currect_time.hour).zfill(2)
        file_data +=str(currect_time.minute).zfill(2)
        file_data +=str(currect_time.second).zfill(2)
        
        file_data += ","+"1"
        file_data +="\r\n"                
        for payment in self.payment_ids:
            record_count += 1
            file_data += "P"
            file_data += ','
            #======== Method ========#
            
#             if payment.jp_method:
#                 if payment.jp_method == 'WIRES':
#                     file_data += 'WIRES'
#                     file_data += ','
#                 if payment.jp_method == 'BOOKTX':
#                     file_data += 'BOOKTX'
#                     file_data += ','
#             else:
#                 file_data += ','
            
            file_data += 'WIRES'
            file_data += ','
            # ======== BIC /SWIFT ======
            if payment.journal_id and payment.journal_id.bank_id and payment.journal_id.bank_id.country:
                if payment.journal_id.bank_id.country.code and payment.journal_id.bank_id.country.code=='MX':
                    file_data += payment.journal_id.bank_id.bic or ''
                else:
                    file_data += payment.journal_id.bank_id.bic or ''
            file_data += ','

            #==========Bank Account ========#
            if payment.journal_id.bank_account_id and payment.journal_id.bank_account_id.acc_number:
                file_data +=payment.journal_id.bank_account_id.acc_number
            file_data += ','
            # ===== Bank to bank transfer ========#
#             if payment.jp_bank_transfer:
#                 if payment.jp_bank_transfer == 'non_financial_institution':
#                     file_data += 'N'
#                 elif payment.jp_bank_transfer == 'financial_institution':
#                     file_data += 'Y'
            file_data += "Non-financial institution (N)"
            file_data += ','

            #====== Currency Data =========#
            if payment.currency_id:
                file_data += payment.currency_id.name
            file_data += ','

            #====== Amount Data =========#
            total_amount += payment.amount
            amount = round(payment.amount, 2)
            amount = "%.2f" % payment.amount
            amount = str(amount).split('.')
            #print ('Amount=====',x)
            file_data +=str(amount[0])
            file_data +='.'
            file_data +=str(amount[1])
            file_data += ','
            #===== Equivalent Amount======#
            file_data += ' ,'
                   
            #===== N / A======#
            file_data += ' , , , ,'
            #======== Payment Date =========
            if payment.payment_date:
                file_data +=str(payment.payment_date.year)
                file_data +=str(payment.payment_date.month).zfill(2)
                file_data +=str(payment.payment_date.day).zfill(2)
            file_data += ','
            
            # ====== ID Type ======#
            if payment.jp_id_type:
                if payment.jp_id_type == 'clabe':
                    file_data += 'CLBE_CODE'
                elif payment.jp_id_type == 'debit_card':
                    file_data += 'DR_CARD'
                elif payment.jp_id_type == 'vostro':
                    file_data += 'VOSTRO_CD'
            file_data += ','

            # ======== CLABE ======
            if payment.partner_id and payment.partner_id.bank_ids:
                bank_clabe = ''
                if payment.partner_id.bank_ids[0].l10n_mx_edi_clabe:
                    bank_clabe = payment.partner_id.bank_ids[0].l10n_mx_edi_clabe
                file_data += bank_clabe
            file_data += ','
            
            #======= Partner Name ========#
            partner_name = ''
            if payment.partner_id:
                partner_name = payment.partner_id.name
            file_data +=partner_name   
            file_data += ','            

            #======= Partner Address1 ========#
            address_1 = ''
            if payment.partner_id and payment.partner_id.street:
                address_1 = payment.partner_id.street
            file_data +=address_1   
            file_data += ','            
            

            #======= Partner Address2 ========#
            address_2 = ''
            if payment.partner_id and payment.partner_id.street2:
                address_2 = payment.partner_id.street2
            file_data +=address_2   
            file_data += ','            

            #======= Partner Address3====#
            address_3 = ''
            if payment.partner_id:
                if payment.partner_id.city:
                    address_3 = payment.partner_id.city
                if payment.partner_id.zip:
                    address_3 += " "+payment.partner_id.zip
            file_data +=address_3   
            file_data += ','            
            # ==== Blank =======
            file_data += ' ,'

            # ==== Country Name =======
            country_code = ''
            if payment.partner_id and payment.partner_id.country_id:
                country_code = payment.partner_id.country_id.code or ''
            file_data +=country_code   
            
            file_data += ','
            #====== Blank Value ======
            file_data += ' , ,'
            #======== ID Type Beneficiary Bank ========#
            if payment.jp_id_type_beneficiary_bank:
                if payment.jp_id_type_beneficiary_bank == 'None':
                    file_data += 'None'
                elif payment.jp_id_type_beneficiary_bank == 'SPEI':
                    file_data += 'SPEI CODE'
                elif payment.jp_id_type_beneficiary_bank == 'SWIFT':
                    file_data += 'SWIFT'
            file_data += ','
            #===== ID Value 25 no =======
            if payment.payment_bank_id:
                bank_code = ''
                if payment.payment_bank_id.l10n_mx_edi_code:
                    bank_code = payment.payment_bank_id.l10n_mx_edi_code[:3]
                print ("Bank Code====",bank_code)
                file_data += bank_code
            file_data += ','
            #==== Bank Name=========#
            if payment.payment_bank_id:
                bank_name = ''
                if payment.payment_bank_id.name:
                    bank_name = payment.payment_bank_id.name
                file_data += bank_name            
            file_data += ','
            
            #======= Bank Address1 ========#
            address_1 = ''
            if payment.payment_bank_id:
                address_1 = payment.payment_bank_id.street or ''
            file_data +=address_1   
            file_data += ','            
            

            #======= Bank Address2 ========#
            address_2 = ''
            if payment.payment_bank_id:
                address_2 = payment.payment_bank_id.street2 or ''
            file_data +=address_2   
            file_data += ','            

            #======= Bank Address3====#
            address_3 = ''
            if payment.payment_bank_id and payment.payment_bank_id.state:
                address_3 = payment.payment_bank_id.state.name
                address_3 += " "+payment.payment_bank_id.zip or ''
            file_data +=address_3   
            file_data += ','            

            # ==== Country Name =======
            country_code = ''
            if payment.partner_id and payment.payment_bank_id.country:
                country_code = payment.payment_bank_id.country.code or ''
            file_data +=country_code   
            file_data += ','
            #=====Supplementary ID======#
            file_data += ' ,'
            #=====Supplementary ID Value======#
            file_data += ' ,'            
            #=====N\A======#
            file_data += ' , , , , , , ,'            
            #=====ID Type======#
            file_data += ' ,'            
            #=====ID Voucher======#
            file_data += ' ,'            
            #=====Bank Name======#
            file_data += ' ,'            
            #=====Address 1======#
            file_data += ' ,'            
            #=====Address 2======#
            file_data += ' ,'
            #=====Address 3======#
            file_data += ' ,'            
            #=====Country======#
            file_data += ' ,'            
            #=====N/A======#
            file_data += ' , ,'            
            #=====ID Type======#
            file_data += ' , ,'            
            #=====By Order Name======#
            file_data += ' ,'            
            #=====Address 1======#
            file_data += ' ,'            
            #=====Address 2======#
            file_data += ' ,'
            #=====Address 3======#
            file_data += ' ,'            
            #=====Country======#
            file_data += ' ,'            
            #=====N/A======#
            file_data += ' , , , , , , , , , , , , , , , , , ,'
            #======== Reference Sent with Payment ======#
            file_data += ' ,'
            #======== Interanal Reference  ======#
            file_data += ' ,'
            #======== N/A  ======#
            file_data += ' ,'
            #======== Detail 1  ======#
#             if payment.jp_payment_concept:
#                 file_data += payment.jp_payment_concept 
            if payment.folio:
                file_data += payment.folio 
            file_data += ','
            #======== Detail 2  ======#
            file_data += ' ,'
            #======== Detail 3  ======#
            file_data += ' ,'
            #======== Detail 4  ======#
            file_data += ' ,'
            #======== N/A  ======#
            file_data += ' , , , , , , , ,'
            #======== Code  ======#
            file_data += ' ,'
            #======== Country  ======#
            file_data += ' ,'
            #======== Instruction 1  ======#
            file_data += ' ,'
            #======== Instruction 2  ======#
            file_data += ' ,'
            #======== Instruction 3  ======#
            file_data += ' ,'
            #======== Instruction Code1  ======#
            file_data += ' ,'
            #======== Instruction  Text 1 ======#
            file_data += ' ,'
            #======== Instruction Code 2 ======#
            file_data += ' ,'
            #======== Instruction  Text 2 ======#
            file_data += ' ,'
            #======== Instruction Code 3  ======#
            file_data += ' ,'
            #======== Instruction  Text 3 ======#
            file_data += ' ,'

            #======== Sender to Receiver Code 1  ======#
            file_data += ' ,'
            #======== Sender to Receiver Line 1======#
            file_data += ' ,'
            #======== Sender to Receiver Code 2  ======#
            file_data += ' ,'
            #======== Sender to Receiver Line 2 ======#
            file_data += ' ,'
            #======== Sender to Receiver Code 3  ======#
            file_data += ' ,'
            #======== Sender to Receiver Line 3 ======#
            file_data += ' ,'
            #======== Sender to Receiver Code 4  ======#
            file_data += ' ,'
            #======== Sender to Receiver Line 4 ======#
            file_data += ' ,'
            #======== Sender to Receiver Code 5  ======#
            file_data += ' ,'
            #======== Sender to Receiver Line 5 ======#
            file_data += ' ,'
            #======== Sender to Receiver Code 6  ======#
            file_data += ' ,'
            #======== Sender to Receiver Line 6 ======#
            file_data += ' ,'
            #======== Priority ======#
            file_data += ' ,'
            #======== N/A ======#
            file_data += ' ,'
            #======== Charges ======#
            if payment.jp_charges:
                if payment.jp_charges == 'shared':
                    file_data += 'SHA'
                elif payment.jp_charges == 'beneficiary':
                    file_data += 'BEN'
                elif payment.jp_charges == 'remitter':
                    file_data += 'OUR'
            file_data += ','
            #======== N/A ======#
            file_data += ' ,'

            #======== Aditional Details ======#
            file_data += ' ,'
            #======== Note ======#
            file_data += ' ,'
            #======== Beneficiary Email ======#
            file_data += ' ,'
            #======== Payroll Indicatorl ======#
            file_data += ' ,'
            #======== Confidential Indicator ======#
            file_data += ' ,'
            #====== Group Name==========#
            file_data += ' ,'
            
            file_data +="\r\n"    
        file_data += "TRAILER" +","+str(record_count)+","
        amount = "%.2f" % total_amount
        amount = str(amount).split('.')
        file_data +=str(amount[0])
        file_data +='.'
        file_data +=str(amount[1])
        file_data +="\r\n"                               
        gentextfile = base64.b64encode(bytes(file_data,'utf-8'))
        self.file_data = gentextfile
        self.file_name = file_name
        
    def jp_morgan_us_drawdowns_file_format(self):
        file_name = 'jp_morgan_us_drawdowns.csv'
        record_count = 0
        total_amount = 0
        file_data = ''

        file_data = 'HEADER'+","
        #====== Current Dat time=========
        currect_time = datetime.today()
        file_data +=str(currect_time.year)
        file_data +=str(currect_time.month).zfill(2)
        file_data +=str(currect_time.day).zfill(2)
        file_data +=str(currect_time.hour).zfill(2)
        file_data +=str(currect_time.minute).zfill(2)
        file_data +=str(currect_time.second).zfill(2)
        
        file_data += ","+"1"
        file_data +="\r\n"                
        
        for payment in self.payment_ids:
            record_count += 1
            #======= Input Type =======
            file_data += "P"
            file_data += ','
            #========= Receipt Method ======
            file_data += "DRWDWN"
            file_data += ','
            # ======== BIC /SWIFT ======
            if payment.journal_id and payment.journal_id.bank_id:
                bank_code = ''
                if payment.journal_id.bank_id.bic:
                    bank_code = payment.journal_id.bank_id.bic
                file_data += bank_code            
            file_data += ','
            #==========Bank Account ========#
            if payment.journal_id.bank_account_id and payment.journal_id.bank_account_id.acc_number:
                file_data +=payment.journal_id.bank_account_id.acc_number
            file_data += ','
            #======= N/A ==========#
            file_data += ' ,'
            #======== Currency =========#
            file_data += "USD"
            file_data += ','
            #====== Amount Data =========#
            total_amount += payment.amount
            amount = round(payment.amount, 2)
            amount = "%.2f" % payment.amount
            amount = str(amount).split('.')
            file_data +=str(amount[0])
            file_data +='.'
            file_data +=str(amount[1])
            file_data += ','
            #======= N/A ==========#
            file_data += ' ,'

            # ===== Drawdown Type ========#
            if payment.jp_drawdown_type:
                if payment.jp_drawdown_type == 'WIRE':
                    file_data += 'WIRE'
                elif payment.jp_drawdown_type == 'BOOK':
                    file_data += 'BOOK'
            file_data += ','
            #======= N/A ==========#
            file_data += ' , , ,'
            #======== Payment Date =========
            if payment.payment_date:
                file_data +=str(payment.payment_date.year)
                file_data +=str(payment.payment_date.month).zfill(2)
                file_data +=str(payment.payment_date.day).zfill(2)
            file_data += ','
            #======= N/A ========== 14 to 60#
            file_data += ' , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , ,'
            #==========Bank Account ========#
            if payment.payment_bank_account_id:
                file_data +=payment.payment_bank_account_id.acc_number
            file_data += ','
            #======= Partner Name ========#
            partner_name = ''
            if payment.partner_id:
                partner_name = payment.partner_id.name
            file_data +=partner_name
            file_data += ','  
            #====== Address 1 ======# 
            file_data += ' ,'
            #======== N/A =======#
            file_data += ' ,'
            #====== City ======#
            file_data += ' ,'
            #===== Country ======#
            file_data += 'MX'
            file_data += ','
            #===== ID Type =======#
            #if payment.jp_drawdown_type and payment.jp_drawdown_type=='Drawdown':
            if payment.payment_bank_id:
                bank_code = ''
                if payment.payment_bank_id.bic:
                    bank_code = payment.payment_bank_id.bic
                file_data += bank_code            
                file_data += ','
            else:
                file_data += ' ,'
#             else:
#                 file_data += ' ,'
            #======== Journal Account =======#
            if payment.jp_drawdown_type and payment.jp_drawdown_type=='Drawdown':
                if payment.journal_id.bank_account_id:
                    file_data +=payment.journal_id.bank_account_id.acc_number
                file_data += ','
            else:
                file_data += ' ,'

            #======== Bank of receipt of payment =======#
            #if payment.jp_drawdown_type and payment.jp_drawdown_type=='Drawdown':
            if payment.payment_bank_id:
                file_data += payment.payment_bank_id.name
            file_data += ','
#             else:
#                 file_data += ' ,'

            #======== Bank Address 1 =======#
            if payment.jp_drawdown_type and payment.jp_drawdown_type=='Drawdown':
                if payment.payment_bank_id and payment.payment_bank_id.street:
                    file_data += payment.payment_bank_id.street
                file_data += ','
            else:
                file_data += ' ,'
            #===== N/A=======#
            file_data += ' ,'
            #===== City=======#
            file_data += ' ,'
            #=====Country=======#
            file_data += ' ,'
            #===== N/A=======#
            file_data += ' ,'
            #===== Internal Reference=======#
            file_data += ' ,'
            #===== N/A=======#
            file_data += ' ,'
            #===== Details1=======#
            file_data += ' ,'
            #===== Details2=======#
            file_data += ' ,'
            #===== Details3=======#
            file_data += ' ,'
            #===== Details4=======#
            file_data += ' ,'
            #===== N/A======= 81 to 116#
            file_data += ' , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , ,'
            #===== Note=======#
            file_data += ' ,'
            #===== N/A=======#
            file_data += ' ,'
            file_data += '\r\n'
        
        #===============TRAILER=================#
        file_data += 'TRAILER'
        file_data += ' ,'
        #------Total Number of Records --------#
        total_rec = len(self.payment_ids)
        file_data +=str(total_rec)
        file_data += ' ,'
        #------Total amount --------#
        amount = "%.2f" % total_amount
        amount = str(amount).split('.')
        file_data +=str(amount[0])
        file_data +='.'
        file_data +=str(amount[1])
        file_data += ','
        file_data += '\r\n'
                 
        gentextfile = base64.b64encode(bytes(file_data,'utf-8'))
        self.file_data = gentextfile
        self.file_name = file_name
        
    def jp_morgan_advice_to_receive_file_format(self):
        file_name = 'jp_morgan_advice_to_receive.csv'
        record_count = 0
        total_amount = 0
        file_data = ''

        file_data = 'HEADER'+","
        #====== Current Dat time=========
        currect_time = datetime.today()
        file_data +=str(currect_time.year)
        file_data +=str(currect_time.month).zfill(2)
        file_data +=str(currect_time.day).zfill(2)
        file_data +=str(currect_time.hour).zfill(2)
        file_data +=str(currect_time.minute).zfill(2)
        file_data +=str(currect_time.second).zfill(2)
        
        file_data += ","+"1"
        file_data +="\r\n"                
        
        for payment in self.payment_ids:
            record_count += 1
            #========Input Type=======#
            file_data += 'P'
            file_data += ','
            #========Receipt Method=======#
            file_data += 'ATR'
            file_data += ','
            # ======== BIC /SWIFT ======
            if payment.journal_id and payment.journal_id.bank_id:
                bank_code = ''
                if payment.journal_id.bank_id.bic:
                    bank_code = payment.journal_id.bank_id.bic
                file_data += bank_code            
            file_data += ','

            #==========Bank Account ========#
            if payment.journal_id.bank_account_id and payment.journal_id.bank_account_id.acc_number:
                file_data +=payment.journal_id.bank_account_id.acc_number
            file_data += ','
            #======= N/A=========#
            file_data += ' ,'
            #====== Currency Data =========
            if payment.currency_id:
                file_data += payment.currency_id.name
                file_data += ','
            else:
                file_data += ' ,'
            #====== Amount Data =========#
            total_amount += payment.amount
            amount = "%.2f" % payment.amount
            amount = str(amount).split('.')
            file_data +=str(amount[0])
            file_data +='.'
            file_data +=str(amount[1])
            file_data += ','
            #====== N/A ========= 8 to 12#
            file_data += ' , , , , ,'
            #======== Payment Date =========
            if payment.payment_date:
                file_data +=str(payment.payment_date.year)
                file_data +=str(payment.payment_date.month).zfill(2)
                file_data +=str(payment.payment_date.day).zfill(2)
            file_data += ','
            #======= N/A========= 14 to 39#
            file_data += ' , , , , , , , , , , , , , , , , , , , , , , , , , ,'
            #===== ID Type =======#
#             if payment.jp_drawdown_type and payment.jp_drawdown_type=='Drawdown':
#                 if payment.journal_id and payment.journal_id.bank_id:
#                     bank_code = ''
#                     if payment.journal_id.bank_id.bic:
#                         bank_code = payment.journal_id.bank_id.bic
#                     file_data += bank_code            
#                 file_data += ','
#             else:
#                 file_data += ' ,'
            if payment.journal_id and payment.journal_id.bank_id and payment.journal_id.bank_id.country:
                if payment.journal_id.bank_id.country.code and payment.journal_id.bank_id.country.code=='MX':
                    file_data += payment.journal_id.bank_id.bic or ''
                else:
                    file_data += payment.journal_id.bank_id.bic or ''
            file_data += ','     
            #====== ID Value =======#
            file_data += ' ,'
            #======== Bank of receipt of payment =======#
            if payment.payment_bank_id:
                file_data += payment.payment_bank_id.name
                file_data += ','
            else:
                file_data += ' ,'
            #===== Address 1 ========#
            file_data += ' ,'
            #===== Address 2 ========#
            file_data += ' ,'
            #===== Address 3 ========#
            file_data += ' ,'
            # ==== Country Name =======
            country_code = ''
            if payment.payment_bank_id and payment.payment_bank_id.country:
                country_code = payment.payment_bank_id.country.code or ''
            file_data +=country_code   
            file_data += ','
            #========== N/A========= 47 to 55 ====#
            file_data += ' , , , , , , , , ,'
            #========= Name========3
            file_data += 'UNIVERSIDAD NACIONAL AUTÓNOMA DE MÉXICO'
            file_data += ','
            #====== Address 1 =======#
            file_data += ' ,'
            #====== Address 2 =======#
            file_data += ' ,'
            #====== City =======#
            file_data += ' ,'
            #====== Country =======#
            file_data += ' ,'
            #====== N/A ======= 61 to 73#
            file_data += ' , , , , , , , , , , , , ,'
            #====== N/A =======#
            file_data += ' ,'
            #======Internal Reference =======#
            file_data += ' ,'
            #======N/A ======= 76 to 116#
            file_data += ' , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , ,'
            #======= Note ========#
            file_data += ' ,'
            #======== N/A =======#
            file_data += ' ,'
            file_data += '\r\n'   

        #===============TRAILER=================#
        file_data += 'TRAILER'
        file_data += ' ,'
        #------Total Number of Records --------#
        total_rec = len(self.payment_ids)
        file_data +=str(total_rec)
        file_data += ' ,'
        #------Total amount --------#
        amount = "%.2f" % total_amount
        amount = str(amount).split('.')
        file_data +=str(amount[0])
        file_data +='.'
        file_data +=str(amount[1])
        file_data += ','
        file_data += '\r\n'
            
        gentextfile = base64.b64encode(bytes(file_data,'utf-8'))
        self.file_data = gentextfile
        self.file_name = file_name
        
    def generate_bank_layout(self):
        for payment in self.payment_ids:
            if self.sit_file_key:
                payment.sit_file_key = self.sit_file_key 
            if payment.journal_id.id != self.journal_id.id:
                raise UserError(_("The selected layout does NOT match the bank of the selected payments"))
        if self.journal_id.bank_format == 'banamex':
            self.banamex_file_format()
        elif self.journal_id.bank_format == 'bbva_tnn_ptc':
            self.bbva_tnn_ptc_file_format()
        elif self.journal_id.bank_format == 'bbva_tsc_pcs':
            self.bbva_tsc_pcs_file_format()
        elif self.journal_id.bank_format == 'bbva_sit':
            self.bbva_sit_file_format()
        elif self.journal_id.bank_format == 'santander':
            self.santander_file_format()
        elif self.journal_id.bank_format == 'hsbc':
            self.hsbc_file_format()
        elif self.journal_id.bank_format == 'jpmw':
            self.jp_morgan_wires_file_format()
        elif self.journal_id.bank_format == 'jpma':
            self.jp_morgan_advice_to_receive_file_format()
        elif self.journal_id.bank_format == 'jpmu':
            self.jp_morgan_us_drawdowns_file_format()
        else:
            self.file_data = False
            self.file_name = False

        for payment in self.payment_ids:
            payment.no_validate_payment = True
        return {
            'name': _('Generate Bank Layout'),
            'res_model': 'generate.bank.layout',
            'res_id' : self.id,
            'view_mode': 'form',
            'target': 'new',
            'view_id': self.env.ref('jt_supplier_payment.view_generate_bank_layout').id,
            'type': 'ir.actions.act_window',
        }    
    #====== Payroll Payment Format ========#

    def payroll_payment_santander_file_format(self):

        file_data = ''
        file_name = 'SANTANDER.txt'
        #===== Type Of Registation ======#
        file_data += '1'
        #===== Sequence Number =======#
        file_data += '00001'
        #====== Sense =========#
        file_data += 'E'
        #====== Generation Date =========#
        currect_time = datetime.today()
        file_data +=str(currect_time.month).zfill(2)
        file_data +=str(currect_time.day).zfill(2)
        file_data +=str(currect_time.year)
        #======= Account ========= #
        if self.journal_id and self.journal_id.bank_account_id:
            file_data += self.journal_id and self.journal_id.bank_account_id.acc_number.ljust(16)
        else:
            file_data += "".ljust(16)
        #===== Application Date ======= #
        currect_time = datetime.today()
        if self.payment_ids and self.payment_ids[0].payment_date:
            currect_time = self.payment_ids[0].payment_date
        
        file_data +=str(currect_time.month).zfill(2)
        file_data +=str(currect_time.day).zfill(2)
        file_data +=str(currect_time.year)
        file_data += "\r\n"
        next_no = 2
        total_record = len(self.payment_ids) 
        total_amount = 0
        for payment in self.payment_ids:
            #===== Type Of Records ======#
            file_data += "2"
            #======= Sequence Number ======#
            file_data += str(next_no).zfill(5)
            next_no += 1
            #===== Employee Number =======#
            file_data += "".ljust(7)
            #===== Patemal Surname =======#
            file_data += "".ljust(30)
            #===== Matemal Surname =======#
            file_data += "".ljust(20)
            #===== Name =======#
            file_data += "".ljust(30)
            #===== Bank account ======= #
            if payment.payment_bank_account_id:
                file_data += payment.payment_bank_account_id.acc_number.ljust(16)
            else:
                file_data += "".ljust(16)
            #========= Amount =======#
            total_amount += payment.amount
            amount = round(payment.amount, 2)
            amount = "%.2f" % payment.amount
            amount = str(amount).split('.')
            file_data +=str(amount[0]).zfill(16)
            file_data +=str(amount[1])
            
            file_data += "\r\n"
        #===== Type Of Reg=========#
        file_data += "3"
        #===== Sequence Number =======#
        #file_data += "00000"
        file_data += str(next_no).zfill(5)
        #====== total_record =======#
        file_data += str(total_record).zfill(5)
        #====== Total Amount ======== #
        amount = round(total_amount, 2)
        amount = "%.2f" % total_amount
        amount = str(amount).split('.')
        file_data +=str(amount[0]).zfill(16)
        file_data +=str(amount[1])
                
        gentextfile = base64.b64encode(bytes(file_data,'utf-8'))
        self.file_data = gentextfile
        self.file_name = file_name

    def payroll_payment_hsbc_file_format(self):
        file_data = ''
        file_name = 'HSBC.txt'
        #======= File Format Indication =======#
        file_data += 'MXPRLF'
        #====== Authorization Level ======#
        file_data += 'F'
        #====== Charge Account ==== ====#
        if self.journal_id and self.journal_id.bank_account_id:
            file_data += self.journal_id and self.journal_id.bank_account_id.acc_number.ljust(10)
        else:
            file_data += "".ljust(10)
        #===== Total Amount ===== TODO#
        total_amount = sum(x.amount for x in self.payment_ids)
        amount = "%.2f" % total_amount
        amount = str(amount).split('.')
        file_data +=str(amount[0]).zfill(12)
        file_data +=str(amount[1])
        #===== Total Operation =====#
        total_record = len(self.payment_ids)
        file_data += str(total_record).zfill(7)
        #===== Value Date ===== #
        currect_time = datetime.today()
        if self.payment_ids and self.payment_ids[0].payment_date:
            currect_time = self.payment_ids[0].payment_date
        
        file_data +=str(currect_time.day).zfill(2)
        file_data +=str(currect_time.month).zfill(2)
        file_data +=str(currect_time.year)
        #===== Application Time =======#
        file_data += '17:00'
        #===== Batch Reference =====#
        file_data += ''.ljust(34)
        file_data += "\r\n"
        for payment in self.payment_ids:
            #===== Beneficiary Account =======#
            if payment.payment_bank_account_id:
                file_data += payment.payment_bank_account_id.acc_number.zfill(10)
            else:
                file_data += "".zfill(10)
 
            #===== Amount ====== #
            amount = round(payment.amount, 2)
            amount = "%.2f" % payment.amount
            amount = str(amount).split('.')
            file_data +=str(amount[0]).zfill(12)
            file_data +=str(amount[1])
            
            #===== Reference for the account ref ===#
            payment_ref = 'PAGO DE NOMINA QNA '
            fornight = '00 '
            if payment.fornight:
                fornight = payment.fornight+" "
            payment_ref += fornight
            currect_time = datetime.today()
            payment_ref += str(currect_time.year)
            
            file_data += payment_ref.ljust(34)
            #===== Name of the Benefiaciry =====#
            file_data += payment.partner_id.name[:35].ljust(35)
            file_data += "\r\n"
            
        gentextfile = base64.b64encode(bytes(file_data,'utf-8'))
        self.file_data = gentextfile
        self.file_name = file_name


    def payroll_paymentbbva_bancomer_bbva_nomina_file_format(self):
        file_data = ''
        file_name = 'BBVA_BANCOMER_PAYROLL.txt'
        #====== Identifier ========#
        file_data += '1'
        #====== Total Line ==== #
        total_record = len(self.payment_ids)
        file_data += str(total_record).zfill(7)
        #===== Total Amount =====  #
        total_amount = sum(x.amount for x in self.payment_ids)
        amount = "%.2f" % total_amount
        amount = str(amount).split('.')
        file_data +=str(amount[0]).zfill(13)
        file_data +=str(amount[1])
        
        #===== Constant Records ======#
        file_data += ''.zfill(7)
        #===== Constant Amount ======#
        file_data += ''.zfill(15)
        #===== Contract ======#
        file_data += '001800001316'
        #===== Contract ======#
        file_data += '4200106119R23'
        #===== Type Of Service ======#
        file_data += '101'
        #===== Constant ======#
        file_data += '0'
        #==== Issue Date ======#
        currect_time = datetime.today()
        file_data +=str(currect_time.year)[2:]
        file_data +=str(currect_time.month).zfill(2)
        file_data +=str(currect_time.day).zfill(2)
        file_data += "\r\n"
        next_number = 1
        nombre = ''
        lista = []
        for payment in self.payment_ids:
            lista.append(payment.partner_id.name)
            #====== Record identifier ======#
            file_data += "3"
            #====== Sequential =========#
            if nombre == '':
                file_data += str(next_number).zfill(2)
            elif nombre == lista[0]:
                next_number += 1
                file_data += str(next_number).zfill(2)
            else:
                next_number = 1
                file_data += str(next_number).zfill(2)
            lista.clear()
            nombre = payment.partner_id.name
            #=== Main reference / Employee Beneficiary ====  #
            file_data += payment.partner_id.name[:20].ljust(20)
            #==== Movement Amount ==========#
            amount = round(payment.amount, 2)
            amount = "%.2f" % payment.amount
            amount = str(amount).split('.')
            file_data +=str(amount[0]).zfill(13)
            file_data +=str(amount[1])
            
            #==== PaymentDate Date ==========#
            if payment.payment_date:
                file_data +=str(payment.payment_date.year)[2:]
                file_data +=str(payment.payment_date.month).zfill(2)
                file_data +=str(payment.payment_date.day).zfill(2)
            else:
                file_data += '      '
            #==== Ban account payment receiving  ===#
            if payment.payment_bank_account_id:
                file_data += payment.payment_bank_account_id.acc_number.zfill(16)
            else:
                file_data += "".zfill(16)
            
            #===== Payroll payment request type / Fortnight TODO====#
            request_type = ''
            if payment.payroll_request_type == 'university':
                request_type = 'SUELDO QN'
            elif payment.payroll_request_type == 'add_benifit':
                request_type = 'PRESTA QN'
            elif payment.payroll_request_type == 'alimony':
                request_type = 'PENSION Q'
            fornight = '00 '
            if payment.fornight:
                fornight = payment.fornight+" "
            request_type += fornight
            currect_time = datetime.today()
            request_type += str(currect_time.year)[2:]
             
            file_data += request_type.ljust(14)
            #==== Status ======#
            file_data += '00'
            #==== Filler =====#
            file_data += ''.ljust(4)
            
            file_data += "\r\n"
            
        gentextfile = base64.b64encode(bytes(file_data,'utf-8'))
        self.file_data = gentextfile
        self.file_name = file_name

    def bbva_bancomer_payroll_232_file_format(self):
        file_data = ''
        file_name = 'BBVA_BANCOMER_DISPERSION_PAYROLL_232.txt'
        #====== Identification No =======#
        file_data += '1'
        #====== Total Line ==== #
        total_record = len(self.payment_ids)
        file_data += str(total_record).zfill(7)
        #===== Total Amount =====  #
        total_amount = sum(x.amount for x in self.payment_ids)
        amount = "%.2f" % total_amount
        amount = str(amount).split('.')
        file_data +=str(amount[0]).zfill(13)
        file_data +=str(amount[1])
        #==== Number of NOK Records ====#
        file_data += ''.zfill(7)
        #==== Total amount NOK Records ====#
        file_data += ''.zfill(15)
        #========= Contract Page ===========#
        file_data += ''.zfill(12)
        #========= Number ===========#
        file_data += '4200106119'
        #========= Legend Code ===========#
        file_data += 'R23'
        #========= Type Of Service ===========#
        file_data += '101'
        #========= Entry Key ===========#
        file_data += 'H'
        #========= File Creation Date ===========#
        currect_time = datetime.today()
        file_data +=str(currect_time.year)
        file_data +=str(currect_time.strftime('%m')).zfill(2)
        file_data +=str(currect_time.strftime('%d'))
        #==== Date OF Payment TODO =======#
        currect_time = datetime.today()
        if self.payment_ids and self.payment_ids[0].payment_date:
            currect_time = self.payment_ids[0].payment_date
        file_data +=str(currect_time.year)
        file_data +=str(currect_time.month).zfill(2)
        file_data +=str(currect_time.day).zfill(2)
        
        #===== Filler ========#
        file_data += ''.ljust(142)
        file_data += '\r\n'
        
        for payment in self.payment_ids:
            #======== Identifier ====#
            file_data += '3'
            #=== Type Of Request for payment of payroll TODO =====#
            req_payroll = '0000000' 
            if payment.payroll_request_type == 'university':
                req_payroll = '0000001'
            if payment.payroll_request_type == 'add_benifit':
                req_payroll = '0000002'
                 
            file_data += req_payroll
             
            #==== CURP / RFC TODO ======#
            vat = ''
            emp_id = self.env['hr.employee'].search([('emp_partner_id','=',payment.partner_id.id)],limit=1)
            if emp_id:
                vat = emp_id.rfc
            elif payment.partner_id.vat:
                vat = payment.partner_id.vat
                
            file_data += vat.ljust(18)
            #==== Type Of account TODO=======#
            bank_account_code = '00'
            if payment.partner_id and payment.partner_id.bank_ids:
                if payment.partner_id.bank_ids[0].account_type=='card':
                    bank_account_code = '03'
                elif payment.partner_id.bank_ids[0].account_type=='clabe_acc':
                    bank_account_code = '40'
                elif payment.partner_id.bank_ids[0].account_type=='checks':
                    bank_account_code = '01'
                elif payment.partner_id.bank_ids[0].account_type=='payment_card':
                    bank_account_code = '98'
                    
            file_data +=  bank_account_code
            
            #===== Target Bank ========#
            file_data += '012'
            #==== Destination Sequence ======#
            file_data += '000'
            #===== Beneficiary Account =======#
            if payment.payment_bank_account_id:
                file_data += payment.payment_bank_account_id.acc_number.zfill(16)
            else:
                file_data += "".zfill(16)
 
            #===== Amount ====== #
            amount = round(payment.amount, 2)
            amount = "%.2f" % payment.amount
            amount = str(amount).split('.')
            file_data +=str(amount[0]).zfill(13)
            file_data +=str(amount[1])
            #======= Payment Status Code =====#
            file_data += ''.zfill(7)
            #====== Payment status Description =====#
            file_data += ''.ljust(80)
            #====== Deposite account holder TODO=====#
            if len(payment.partner_id.name) > 40:
                file_data += payment.partner_id.name[:40]
            else:
                file_data += payment.partner_id.name.ljust(40)
            #==== Reason for payment ======= #
            file_data += ''.ljust(40)
            
            file_data += '\r\n'
        gentextfile = base64.b64encode(bytes(file_data,'utf-8'))
        self.file_data = gentextfile
        self.file_name = file_name

    def payroll_payment_banamex_file_format(self):

        file_data = ''
        file_name = 'BANAMEX.txt'
        #===== Type Of Records =======#
        file_data += '1'
        #===== Customer Identification Number =======#
        file_data += '000008505585'
        #===== Payment Date =======#
        currect_time = datetime.today()
        if self.payment_ids and self.payment_ids[0].payment_date:
            currect_time = self.payment_ids[0].payment_date
        
        file_data +=str(currect_time.day).zfill(2)
        file_data +=str(currect_time.month).zfill(2)
        file_data +=str(currect_time.year)[2:]
        
        #====== Sequence of the file TODO =====#
        file_data += '0001'
        #===== Company Name ======#
        file_data += 'UNIVERSIDAD NACIONAL AUTONOMA MEXICO'
        #====Description the file of   ====#
        file_data += 'DEPOSITO NOMINA '
        currect_time = datetime.today()
        file_data += str(currect_time.year)
        #===== Nature of the file =======#
        file_data += '05'
        #===== Instructions for payment orders ===#
        file_data += ''.ljust(40)
        #===== Layout Version =======#
        file_data += 'C'
        #===== Volume =======#
        file_data += '0'
        #===== File characteristics =======#
        file_data += '1'
        #===== File Status =======#
        file_data += '  '
        #===== File authorization number =======#
        file_data += ''.ljust(12)
        
        file_data += '\r\n'
        #======== Second  Heading ========#
        #==== Records Type ====#
        file_data += "2"
        #==== Operation Type ====#
        file_data += "1"
        #==== Currency Key ====#
        file_data += "001"
        #==== Total amount  TODO====#
        total_amount = sum(x.amount for x in self.payment_ids)
        amount = "%.2f" % total_amount
        amount = str(amount).split('.')
        file_data +=str(amount[0]).zfill(16)
        file_data +=str(amount[1])
        
        #==== Account Type ====#
        file_data += "01"
        
        #==== Branch Number TODO====#
        branch_no = ''
        if self.journal_id.branch_number:
            branch_no = self.journal_id.branch_number
        file_data += branch_no.zfill(4)
        #==== Account Number ====#
        bank_account_no = ''
        if self.journal_id.bank_account_id:
            bank_account_no = self.journal_id.bank_account_id.acc_number
            
        file_data += bank_account_no.zfill(20)
        #==== Blank Space====#
        file_data += "".ljust(20)
        #==== Return Amount====#
        file_data += "".ljust(18)
        
        file_data += "\r\n"
        row_count = 1
        for payment in self.payment_ids:
            #==== Record Type ======#
            file_data += '3'
            #==== Operation Key ======#
            file_data += '0'
            #==== Currency Key ======#
            file_data += '001'
            #===== Amount ========#
            amount = round(payment.amount, 2)
            amount = "%.2f" % payment.amount
            amount = str(amount).split('.')
            file_data +=str(amount[0]).zfill(16)
            file_data +=str(amount[1])
            
            #===== Account Type ======#
            bank_account_code = '00'
            if payment.partner_id and payment.partner_id.bank_ids:
                if payment.partner_id.bank_ids[0].account_type=='card':
                    bank_account_code = '03'
                elif payment.partner_id.bank_ids[0].account_type=='clabe_acc':
                    bank_account_code = '40'
                elif payment.partner_id.bank_ids[0].account_type=='checks':
                    bank_account_code = '01'
                elif payment.partner_id.bank_ids[0].account_type=='payment_order':
                    bank_account_code = '04'
                elif payment.partner_id.bank_ids[0].account_type=='con_acc':
                    bank_account_code = '15'
            
            file_data += bank_account_code
            #======== Account Number =====#
            account_no = ''
            if payment.partner_id and payment.partner_id.bank_ids:
                if payment.partner_id.bank_ids[0].branch_number:
                    account_no += payment.partner_id.bank_ids[0].branch_number

                if payment.partner_id.bank_ids[0].acc_number:
                    account_no += payment.partner_id.bank_ids[0].acc_number
                    
            file_data += account_no.zfill(20)
            #======= Operation Reference ======#
            file_data += '0000000010'
            file_data += ''.ljust(30)
            #====== Beneficiary  ====#
            file_data += payment.partner_id.name.ljust(55)
            #====== Instructions ====#
            file_data += ''.ljust(40)
            #====== Description TODO====#
            request_type = ''
            if payment.payroll_request_type:
                if payment.payroll_request_type == 'university':
                    request_type = 'PAGO DE NOMINA QNA'
                elif payment.payroll_request_type == 'add_benifit':
                    request_type = 'PRESTA QN'
                elif payment.payroll_request_type == 'alimony':
                    request_type = 'PAGO PENSION A QNA'
                fornight = '00'
                if payment.fornight:
                    fornight = payment.fornight
                request_type += fornight
                currect_time = datetime.today()
                request_type += str(currect_time.year)
                 
                file_data += request_type.ljust(14)
            else:
                if payment.payment_request_type=='pension_payment' and payment.payment_request_id:
                    request_type = 'PAGO PENSION A QNA'
                    fornight = '00'
                    if payment.payment_request_id.fornight:
                        fornight = str(payment.payment_request_id.fornight)
                    request_type += fornight
                    
                    if payment.payment_request_id.invoice_date:
                        request_type += str(payment.payment_request_id.invoice_date.year)
                    file_data += request_type.ljust(24)    
                else:
                    file_data += ''.ljust(24)
            #====== Bank code ====#
            file_data += '0000'
            #====== Reference Low Value ====#
            file_data += str(row_count).zfill(7)
            row_count += 1
            
            #======= Term =======#
            file_data += '00'
            file_data += "\r\n"
        
        #====== Total Records Data========#
        #===== Record Type =======#
        file_data += '4'
        #===== Currency Key =======#
        file_data += '001'
        #===== Number of subscriptions=======#
        total_rec= len(self.payment_ids)
        file_data += str(total_rec).zfill(6)
        #===== Total Amount TODO=======#
        total_amount = sum(x.amount for x in self.payment_ids)
        amount = "%.2f" % total_amount
        amount = str(amount).split('.')
        file_data +=str(amount[0]).zfill(16)
        file_data +=str(amount[1])
        
        #===== Number of charges=======#
        file_data += '000001'
        #===== Total Amount of charges TODO=======#
        total_amount = sum(x.amount for x in self.payment_ids)
        amount = "%.2f" % total_amount
        amount = str(amount).split('.')
        file_data +=str(amount[0]).zfill(16)
        file_data +=str(amount[1])
        file_data += "\r\n"
        
        gentextfile = base64.b64encode(bytes(file_data,'utf-8'))
        self.file_data = gentextfile
        self.file_name = file_name

    def scotiabank_file_format(self):
        file_data = ''
        file_name = 'SCOTIABANK.txt'
        #====== Header First Line =====#
        #==== File Type ======#
        file_data += 'EE'
        #==== Type Of Registration ======#
        file_data += 'HA'
        #==== Contract Number ======#
        file_data += '06852'
        #==== Sequence ======#
        file_data += '01'
        #==== File Generation Date ======#
        file_data += ''.zfill(8)
        #==== Initial Date ======#
        file_data += ''.zfill(8)
        #==== End Date ======#
        file_data += ''.zfill(8)
        #==== Code-status-registration ======#
        file_data += ''.zfill(3)
        #==== Filler ======#
        file_data += ''.ljust(332)
        
        file_data += '\r\n'
        #======= Block ​ header (second header, second row of the file) ====#
        #=== File Type =======#
        file_data += 'EE'
        #=== File Type =======#
        file_data += 'HB'
        #=== Charge Currency =======#
        file_data += '00'
        #=== Fature Type =======#
        file_data += '0000'
        #=== Charge Account =======#
        if self.journal_id and self.journal_id.bank_account_id:
            file_data += self.journal_id and self.journal_id.bank_account_id.acc_number.zfill(11)
        else:
            file_data += "".zfill(11)
        
        #=== Company Reference =======#
        file_data += '0000000000'
        #=== Code status registration =======#
        file_data += '000'
        #==== Filler =======#
        file_data += ''.ljust(336)
        
        file_data += '\r\n'
        sequence_no = 1
        for payment in self.payment_ids:
            #===== File Type ========#
            file_data += 'EE'
            #===== Record Type ========#
            file_data += 'DA'
            #===== Movement Type ========#
            file_data += '04'
            #===== Cve currency payment ========#
            file_data += '00'
            #===== Amount TODO ========#
            amount = round(payment.amount, 2)
            amount = "%.2f" % payment.amount
            amount = str(amount).split('.')
            file_data +=str(amount[0]).zfill(13)
            file_data +=str(amount[1])
            
            #===== Application Date========#
            if payment.payment_date:
                file_data +=str(payment.payment_date.year)
                file_data +=str(payment.payment_date.month).zfill(2)
                file_data +=str(payment.payment_date.day).zfill(2)
            else:
                file_data += '00000000'
            
            #===== Service Concept========#
            file_data += '01'
            #===== Cve-beneficiary ========#
            file_data += str(sequence_no).zfill(20)
            sequence_no += 1
            #===== RFC TODO========#
            vat = ''
            emp_id = self.env['hr.employee'].search([('emp_partner_id','=',payment.partner_id.id)],limit=1)
            if emp_id:
                vat = emp_id.rfc
            elif payment.partner_id.vat:
                vat = payment.partner_id.vat
            file_data += vat.ljust(13)
            #===== Employee/Beneficiary========#
            file_data += payment.partner_id.name.ljust(40)
            #===== Payment Date ========#
            file_data += ''.zfill(8)
            if payment.payment_date:
                file_data +=str(payment.payment_date.month).zfill(2)
                file_data +=str(payment.payment_date.day).zfill(2)
                file_data +=str(payment.payment_date.year)
                
            else:
                file_data += '00000000'

            #===== SBI Payment Place========#
            file_data += '00000'
            #===== Payment Branch========#
            file_data += '00000'
            #===== Bank account receiving payment========#
            if payment.payment_bank_account_id:
                file_data += payment.payment_bank_account_id.acc_number.zfill(20)
            else:
                temp =''
                file_data +=temp.zfill(20)
            
            #===== Country========#
            file_data += '00000'
            #===== City / State========#
            file_data += ''.ljust(40)
            #===== Account Type========#
            file_data += '1'
            #===== Digit Exchange========#
            file_data += ' '
            #===== Plaza-cuenta-banco========#
            file_data += ''.zfill(5)
            #===== Issuer-bank-number========#
            file_data += '044'
            #===== Num-banktransceiver========#
            file_data += '044'
            #===== Days-Valid========#
            file_data += '001'
            #===== Concept-Payment========#
            file_data += 'SUELDO QUINCENAL'.ljust(50)
            #===== Field-use-company-1========#
            file_data += ''.ljust(20)
            #===== Field-use-company-2========#
            file_data += ''.ljust(20)
            #===== Field-use-company-3========#
            file_data += ''.ljust(20)
            #===== Code-status-registration========#
            file_data += ''.zfill(3)
            #===== Cve-change-inst========#
            file_data += ''.zfill(1)
            #===== Code-status-change-inst========#
            file_data += ''.zfill(3)
            #===== Payment date========#
            file_data += ''.zfill(8)
            #===== Payment place========#
            file_data += ''.zfill(5)
            #===== Branch OF Payment========#
            file_data += ''.zfill(5)
            #===== Filler ========#
            file_data += ''.ljust(22)
            file_data += '\r\n'
            
        #====== Block trailer does ​ (penultimate row of the file) =====#
        
        #==== File Type =====#
        file_data += 'EE' 
        #==== Record type =====#
        file_data += 'TB' 
        #===== Amount of high movements TODO =====#
        total_rec = len(self.payment_ids)
        file_data += str(total_rec).zfill(7)
        #==== Total Amount TODO =====#
        total_amount = sum(x.amount for x in self.payment_ids)
        amount = "%.2f" % total_amount
        amount = str(amount).split('.')
        file_data +=str(amount[0]).zfill(15)
        file_data +=str(amount[1])
        #==== Number of low movements=====#
        file_data += ''.zfill(7)
        #==== Amount of low movements=====#
        file_data += ''.zfill(17)
        #==== Data filled in by the bank=====#
        file_data += ''.zfill(195)
        #==== Filler=====#
        file_data += ''.ljust(123)
        file_data += "\r\n"
        #======= Trailer file does ​ (last row of the file) =======#
        
        #==== File Type =====#
        file_data += 'EE' 
        #==== Record type =====#
        file_data += 'TA' 
        #===== Amount of high movements TODO =====#
        total_rec = len(self.payment_ids)
        file_data += str(total_rec).zfill(7)
        #==== Total Amount TODO =====#
        total_amount = sum(x.amount for x in self.payment_ids)
        amount = "%.2f" % total_amount
        amount = str(amount).split('.')
        file_data +=str(amount[0]).zfill(15)
        file_data +=str(amount[1])
        #==== Number of low movements=====#
        file_data += ''.zfill(7)
        #==== Amount of low movements=====#
        file_data += ''.zfill(17)
        #==== Data filled in by the bank=====#
        file_data += ''.zfill(198)
        #==== Filler=====#
        file_data += ''.ljust(120)
        file_data += '\r\n' 
        gentextfile = base64.b64encode(bytes(file_data,'utf-8'))
        self.file_data = gentextfile
        self.file_name = file_name

    def banorte_file_format(self):
        file_data = ''
        file_name = 'NI2005201.txt'  # TODO for file name base on Type of request for payment of payroll

        #==== Record type =====#
        file_data += 'H'
        #====== Service code ========#
        file_data += 'NE'
        #====== Issuer ========#
        file_data += '20052'
        #====== Process Date TODO========#
        currect_time = datetime.today()
        if self.payment_ids and self.payment_ids[0].payment_date:
            currect_time = self.payment_ids[0].payment_date
        
        file_data +=str(currect_time.year)
        file_data +=str(currect_time.month).zfill(2)
        file_data +=str(currect_time.day).zfill(2)
        
        #====== Consecutive Number TODO========#
        file_data += '01'
        #====== Total No of records ========#
        total_rec = len(self.payment_ids)
        file_data += str(total_rec).zfill(6)
        #====== Total Amount of Records ========#
        total_amount = sum(x.amount for x in self.payment_ids)
        amount = "%.2f" % total_amount
        amount = str(amount).split('.')
        file_data +=str(amount[0]).zfill(13)
        file_data +=str(amount[1])
        
        #====== Total Number of HIGH Sent ========#
        file_data += ''.zfill(6)
        #====== Total Amount of HIGH Sent========#
        file_data += ''.rjust(15)
        #====== Total number of DEPARTURES Sent========#
        file_data += ''.zfill(6)
        #====== Total Amount of DEPARTURES Sent========#
        file_data += ''.zfill(15)
        #====== Total number of account verify Sent========#
        file_data += ''.zfill(6)
        #====== Action========#
        file_data += ''.zfill(1)
        #====== Filler========#
        file_data += ''.rjust(77)
        file_data += "\r\n"

        for payment in self.payment_ids:
            #====== Type of record ========#
            file_data += 'D'
            #====== Application date=======#
            if payment.payment_date:
                file_data +=str(payment.payment_date.year)
                file_data +=str(payment.payment_date.month).zfill(2)
                file_data +=str(payment.payment_date.day).zfill(2)
                
            else:
                file_data += '00000000'
            #========= Partner Bank Account==============#
#             bank_account = ''
#             if payment.payment_bank_account_id and payment.payment_bank_account_id.acc_number:
#                 bank_account = payment.payment_bank_account_id.acc_number
#             file_data += bank_account
            #====== Employee number ========#
            benific = ''
            emp_id = self.env['hr.employee'].search([('emp_partner_id','=',payment.partner_id.id)],limit=1)
            if emp_id:
                benific = emp_id.worker_number
#             if payment.partner_id.password_beneficiary:
#                 benific = payment.partner_id.password_beneficiary
            file_data += benific.zfill(10)
            
            #====== Service reference========#
            file_data += ''.ljust(40)
            #====== Fortnight ========#
            fortnight_msg = 'PAGO NOMINA QNA '
            fornight = '00'
            if payment.fornight:
                fornight = payment.fornight
            fortnight_msg += fornight
            currect_time = datetime.today()
            fortnight_msg += str(currect_time.year)[2:]
            fortnight_msg += " DE LA EMISORA 20052"
            
            file_data += fortnight_msg.ljust(40)
            #====== Amount========#
            amount = round(payment.amount, 2)
            amount = "%.2f" % payment.amount
            amount = str(amount).split('.')
            file_data +=str(amount[0]).zfill(13)
            file_data +=str(amount[1])
            
            #====== Receiving bank number========#
            file_data += '072'
            #====== Type of account ========#
            bank_account_code = '00'
            if payment.partner_id and payment.partner_id.bank_ids:
                if payment.partner_id.bank_ids[0].account_type=='card':
                    bank_account_code = '03'
                elif payment.partner_id.bank_ids[0].account_type=='clabe_acc':
                    bank_account_code = '40'
                elif payment.partner_id.bank_ids[0].account_type=='checks':
                    bank_account_code = '01'
                    
            file_data +=  bank_account_code
            
            #====== Payment receipt bank account   TODO========#
            if payment.payment_bank_account_id:
                file_data += payment.payment_bank_account_id.acc_number.zfill(18)
            else:
                temp =''
                file_data +=temp.zfill(18)
            
            #====== Movement type========#
            file_data += ''.zfill(1)
            #====== Action========#
            file_data += ''.ljust(1)
            #====== VAT amount of the transaction========#
            file_data += ''.zfill(8)
            #===== Filler =====#
            file_data += ''.ljust(18)
            file_data += '\r\n'
    
        gentextfile = base64.b64encode(bytes(file_data,'utf-8'))
        self.file_data = gentextfile
        self.file_name = file_name

    def generate_payroll_payment_bank_layout(self):
        for payment in self.payment_ids:
            if payment.journal_id.id != self.journal_id.id:
                raise UserError(_("The selected layout does NOT match the bank of the selected payments"))

        if self.journal_id.payroll_bank_format == 'santander':
            self.payroll_payment_santander_file_format()
        elif self.journal_id.payroll_bank_format == 'hsbc':
            self.payroll_payment_hsbc_file_format()
        elif self.journal_id.payroll_bank_format == 'bbva_nomina':
            self.payroll_paymentbbva_bancomer_bbva_nomina_file_format()
        elif self.journal_id.payroll_bank_format == 'bbva_232':
            self.bbva_bancomer_payroll_232_file_format()
        elif self.journal_id.payroll_bank_format == 'banamex':
            self.payroll_payment_banamex_file_format()
        elif self.journal_id.payroll_bank_format == 'scotiabank':
            self.scotiabank_file_format()
        elif self.journal_id.payroll_bank_format == 'banorte':
            self.banorte_file_format()

        for payment in self.payment_ids:
            payment.no_validate_payment = True
        
            
        return {
            'name': _('Generate Bank Layout'),
            'res_model': 'generate.bank.layout',
            'res_id' : self.id,
            'view_mode': 'form',
            'target': 'new',
            'view_id': self.env.ref('jt_supplier_payment.view_generate_payroll_payment_bank_layout').id,
            'type': 'ir.actions.act_window',
        }    
    
