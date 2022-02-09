from odoo import models, fields,_
from odoo.exceptions import UserError, ValidationError
import base64
from datetime import datetime, timedelta
from odoo.tools.misc import formatLang, format_date, get_lang
from babel.dates import format_datetime, format_date

class GenerateCancelCheckLayout(models.TransientModel):
    _name = 'generate.cancel.check.layout'
    _description = 'Generate Cancel Check Layout'

    layout = fields.Selection([('Banamex', 'Banamex'), ('BBVA Bancomer', 'BBVA Bancomer'),
                                ('Scotiabank', 'Scotiabank')], string="Layout")
    file_name = fields.Char('Filename')
    file_data = fields.Binary('Download')
    reissue_ids = fields.Many2many('reissue.checks','reissue_checks_bank_layout_rel','check_layout_id','reissue_id','Reissue')

    def banamex_cancel_check_file_format(self):
        file_data = ''
        file_name = 'Banamex.txt'
        
        #===Transaction Type ====#
        file_data += '01'
        branch_no = '0000'
        if self.reissue_ids:
            check = self.reissue_ids[0]
            
        if check.bank_id and check.bank_id.branch_number:
            branch_no = check.bank_id.branch_number.zfill(4)
        file_data += branch_no
        #===Destination Account ====#
        bank_account = '00000000000000000000'
        if check.bank_account_id and check.bank_account_id.acc_number:
            bank_account = check.bank_account_id.acc_number.zfill(20)
             
        file_data += bank_account
        #===Client ====#
        file_data += '000008505585'
        #===File Format ====#
        file_data += '0001'
        #===Sequential ====#
        file_data += '000001'
        #===Future use ====#
        file_data += '000000000000'
        file_data +="\r\n"
        
        total_rec = len(self.reissue_ids)
        total_amount = 0
        
        for check in self.reissue_ids:
            #===Transaction Type ====#
            file_data += '02'
            #===Branch Account Number ====#
            branch_no = '0000'
            if check.bank_id and check.bank_id.branch_number:
                branch_no = check.bank_id.branch_number.zfill(4)
            file_data += branch_no
            #===Destination Account ====#
            bank_account = '00000000000000000000'
            if check.bank_account_id and check.bank_account_id.acc_number:
                bank_account = check.bank_account_id.acc_number.zfill(20)
                 
            file_data += bank_account
            
            temp_log = ''
            if check.check_log_id and check.check_log_id.folio:
                temp_log =  check.check_log_id.folio
                file_data += str(temp_log).zfill(7)
            else:
                file_data += temp_log.zfill(7)

            #=== Check Status=======#
            file_data += '08'

            #====== Amount Data =========
            amount = round(check.check_amount, 2)
            amount = "%.2f" % check.check_amount            
            amount = str(amount).split('.')
            file_data +=str(amount[0]).zfill(12)
            file_data +=str(amount[1])
            
            total_amount += check.check_amount
            #=====Future use=========#
            file_data += '00000000000'
            file_data +="\r\n"
        
        #=======TRAILER =======#
        
        #=======Transaction Type =======#
        file_data += '03'
        
        #====== Total Movement ======#
        file_data +=str(total_rec).zfill(6)

        #======Total Amount Data =========
        amount = round(total_amount, 2)
        amount = "%.2f" % total_amount            
        amount = str(amount).split('.')
        file_data +=str(amount[0]).zfill(14)
        file_data +=str(amount[1])

        gentextfile = base64.b64encode(bytes(file_data, 'utf-8'))
        self.file_data = gentextfile
        self.file_name = file_name

    def BBVA_cancel_check_file_format(self):
        file_data = ''
        file_name = 'BBVA Bancomer.txt'
        
        #====== Number of account ==#
        file_data += '1/'
        # ==== bank account ===#
        bank_account = ''
        if self.reissue_ids and self.reissue_ids[0].bank_account_id:
            bank_account = self.reissue_ids[0].bank_account_id.acc_number
            
        file_data += bank_account.zfill(18)
        file_data += '/'
        total_rec = len(self.reissue_ids)
        total_amount = sum(x.check_amount for x in self.reissue_ids) 
        
        #====== Total Movement ======#
        file_data +=str(total_rec).zfill(6)
        file_data += '/'
        #======Total Amount Data =========
        amount = round(total_amount, 2)
        amount = "%.2f" % total_amount            
        amount = str(amount).split('.')
        file_data +=str(amount[0]).zfill(13)
        file_data +=str(amount[1])
        file_data += '/'

        #====== Current Dat time=========
        currect_time = datetime.today()
        
        file_data +=str(currect_time.year) + "-" 
        file_data +=str(currect_time.month).zfill(2) + "-"
        file_data +=str(currect_time.day).zfill(2)
        file_data += '/'
        file_data += '\r\n'        
               
        for check in self.reissue_ids:
            temp_log = ''
            if check.check_log_id and check.check_log_id.folio:
                temp_log =  check.check_log_id.folio
                file_data += str(temp_log).zfill(7)
            else:
                file_data += temp_log.zfill(7)
            file_data += '/'
                        
            #===== action ======#
            file_data += 'B/'

            #====== Amount Data =========
            amount = round(check.check_amount, 2)
            amount = "%.2f" % check.check_amount            
            amount = str(amount).split('.')
            file_data +=str(amount[0]).zfill(13)
            file_data +=str(amount[1])
            file_data += '/'
            file_data += '\r\n'
            
        gentextfile = base64.b64encode(bytes(file_data, 'utf-8'))
        self.file_data = gentextfile
        self.file_name = file_name
            

    def scotiabank_cancel_check_file_format(self):
        file_data = ''
        file_name = 'Scotiabank.txt'

        #===== Type of Registration =====#
        file_data += 'H'

        #====== Current Dat time=========
        currect_time = datetime.today()
        
        file_data +=str(currect_time.year) 
        file_data +=str(currect_time.month).zfill(2)
        file_data +=str(currect_time.day).zfill(2)
        
        #===== Filler ======#
        filler = ''
        file_data += filler.ljust(140, " ")

        #===== Key movement =====#
        file_data += '1'

        file_data += '\r\n'
        
        total_amount = 0
        total_check_folio = 0
        for check in self.reissue_ids:
            #===== Registration =====#
            file_data += 'B'
            
            branch_number = '001'

#             if check.bank_id and check.bank_id.branch_number and len(check.bank_id.branch_number) > 3:
#                 branch_number = check.bank_id.branch_number[-3:]
#             elif check.bank_id and check.bank_id.branch_number:
#                 branch_number = check.bank_id.branch_number if check.bank_id.branch_number else ''
            
            file_data += branch_number

            #===== Account Currency=====#
            file_data += '1'
            
            #===== Bank Account ====#
            bank_account = ''
            if check.bank_account_id and check.bank_account_id.acc_number:
                bank_account = check.bank_account_id.acc_number[-10:]
            
            file_data +=bank_account.zfill(-10)
            
            #====== Check Folio ======#
            temp_log = ''
            if check.check_log_id and check.check_log_id.folio:
                total_check_folio += check.check_log_id.folio
                temp_log =  check.check_log_id.folio
                file_data += str(temp_log).zfill(10)
            else:
                file_data += temp_log.zfill(10)
            
            total_amount += check.check_amount
            
            #====== Amount Data =========#
            amount = round(check.check_amount, 2)
            amount = "%.2f" % check.check_amount            
            amount = str(amount).split('.')
            file_data +=str(amount[0]).zfill(13)
            file_data +=str(amount[1])
            
            #===== Beneficiary's =====#
            partner_name = ''
            if check.partner_id:
                partner_name = check.partner_id.name
            file_data += partner_name.ljust(60)
            
            #======= Fillrer=====
            file_data += ''.ljust(49)

            #======= Key Movement=====
            file_data += '3'
            
            file_data += '\r\n'
        
        #====Trailer========#
        
        #=========== Type Of Registration ====#
        file_data += 'P'

        #======= Total highs =====
        file_data += ''.zfill(9)

        #======= Checksum of Check Numbers =====
        file_data += ''.zfill(15)

        #======= Sum Of amounts =====
        file_data += ''.zfill(18)
        
        #======= Total Records =====
        total_rec= len(self.reissue_ids)
        file_data +=str(total_rec).zfill(9)
        
        #===== Checksum (Low) ===#
        amount = "%.2f" % total_check_folio            
        amount = str(amount).split('.')
        file_data +=str(amount[0]).zfill(15)

        #===== Sum of amounts (Low) ===#    
        amount = round(total_amount, 2)
        amount = "%.2f" % total_amount       
        amount = str(amount).split('.')
        file_data +=str(amount[0]).zfill(16)
        file_data +=str(amount[1])
        
        #===== Total high and lows===#
        file_data +=str(total_rec).zfill(10)

        #===== Checksum (Low) ===#
        amount = "%.2f" % total_check_folio            
        amount = str(amount).split('.')
        file_data +=str(amount[0]).zfill(15)

        #===== Sum of amounts (Low) ===#    
        amount = round(total_amount, 2)
        amount = "%.2f" % total_amount       
        amount = str(amount).split('.')
        file_data +=str(amount[0]).zfill(16)
        file_data +=str(amount[1])
        
        #======= Fillrer=====
        file_data += ''.ljust(21)

        #======= Key Movement=====
        file_data += '5'

                
        gentextfile = base64.b64encode(bytes(file_data, 'utf-8'))
        self.file_data = gentextfile
        self.file_name = file_name
            
    def action_generate(self):
        for check in self.reissue_ids:            
            if check.state != 'approved':
                raise ValidationError(_('Confirm that the status of all selected checks is "Approved", therefore no '
                                        'layout can be generated until the status is not Approved'))

            if check.type_of_batch in ('supplier', 'project'):
                if check.type_of_request != 'check_cancellation':
                    raise ValidationError(_('Confirm that the all selected checks Type of Request is "Check Cancellation", therefore no '
                                        'layout can be generated until the Type of Request is not Check Cancellation'))
            else:
                if check.type_of_request_payroll != 'check_cancellation':
                    raise ValidationError(_('Confirm that the all selected checks Type of Request is "Check Cancellation", therefore no '
                                        'layout can be generated until the Type of Request is not Check Cancellation'))
            if check.status != 'Cancelled':
                raise ValidationError(_('Confirm that all selected checks Status is "Cancelled", therefore no '
                                        'layout can be generated until the Check Status is not Cancelled'))

            if not check.bank_id:
                raise ValidationError(_('Please select Payment Issuing Bank into records'))

            if check.bank_id and not check.bank_id.bank_id:
                raise ValidationError(_('Please select Bank into Payment Issuing Bank'))

            if check.bank_id.bank_id.name.upper() != self.layout.upper():
                raise ValidationError(_('The selected layout does NOT match the bank of the selected records" and no '
                                        'layout can be generated until the correct bank is selected.'))
            check.layout_generated = True
            
        if self.layout == 'Banamex':
            self.banamex_cancel_check_file_format()
        elif self.layout == 'BBVA Bancomer':
            self.BBVA_cancel_check_file_format()
        elif self.layout == 'Scotiabank':
            self.scotiabank_cancel_check_file_format()
                    
        return {
            'name': _('Generate Bank Layout'),
            'res_model': 'generate.cancel.check.layout',
            'res_id' : self.id,
            'view_mode': 'form',
            'target': 'new',
            #'view_id': self.env.ref('jt_supplier_payment.view_generate_payroll_payment_bank_layout').id,
            'type': 'ir.actions.act_window',
        }