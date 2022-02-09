from odoo import models, fields,_
from odoo.exceptions import UserError, ValidationError
import base64
from datetime import datetime, timedelta
from odoo.tools.misc import formatLang, format_date, get_lang
from babel.dates import format_datetime, format_date

class GenerateBankPayrollPayment(models.TransientModel):

    _name = 'generate.bank.layout.payroll.payment'
    _description = 'Generate Bank Layout Payroll Payment'

    bank_layout = fields.Selection([('SANTANDER','SANTANDER'),
                                    ('HSBC','HSBC'),
                                    ('BBVA BANCOMER PAYROLL','BBVA BANCOMER PAYROLL'),
                                    ('BBVA BANCOMER DISPERSION 232','BBVA BANCOMER DISPERSION 232'),
                                    ('BANAMEX','BANAMEX'),
                                    ('SCOTIABANK','SCOTIABANK'),
                                    ('BANORTE','BANORTE'),
                                    ],string="Layout")
    payment_ids = fields.Many2many('account.payment','account_payment_payroll_bank_layout_rel','bank_layout_id','payment_id','Payments')
    file_name = fields.Char('Filename')
    file_data = fields.Binary('Download')

    def action_generate_bank_layout(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return ''
        
        return {
            'name': _('Generate Bank Layout'),
            'res_model': 'generate.bank.layout.payroll.payment',
            'view_mode': 'form',
            'view_id': self.env.ref('jt_payroll_payment.view_generate_bank_layout_payroll_payment').id,
            'context': {'default_payment_ids':[(6,0,active_ids)]},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }    
    def santander_file_format(self):

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
        #======= Account ========= TODO#
        file_data += "".ljust(16)
        #===== Application Date ======= TODO#
        currect_time = datetime.today()
        file_data +=str(currect_time.month).zfill(2)
        file_data +=str(currect_time.day).zfill(2)
        file_data +=str(currect_time.year)
        file_data += "\n"
        next_no = 2
        total_record = len(self.payment_ids) 
        
        for payment in self.payment_ids:
            #===== Type Of Records ======#
            file_data += "2"
            #======= Sequence Number ======#
            file_data += "0000"
            file_data += str(next_no)
            next_no += 1
            #===== Employee Number =======#
            file_data += "".ljust(7)
            #===== Patemal Surname =======#
            file_data += "".ljust(30)
            #===== Matemal Surname =======#
            file_data += "".ljust(20)
            #===== Name =======#
            file_data += "".ljust(30)
            #===== Bank account ======= TODO#
            if payment.payment_bank_account_id:
                file_data += payment.payment_bank_account_id.acc_number.ljust(16)
            else:
                file_data += "".ljust(16)
            #========= Amount =======TODO#
            file_data += "".ljust(18)
            
            file_data += "\n"
        #===== Type Of Reg=========#
        file_data += "3"
        #===== Sequence Number =======#
        file_data += "0000"
        file_data += str(next_no)
        #====== total_record =======#
        file_data += str(total_record).zfill(5)
        #====== Total Amount ======== TODO#
        file_data += "".ljust(18)
        
        gentextfile = base64.b64encode(bytes(file_data,'utf-8'))
        self.file_data = gentextfile
        self.file_name = file_name
        
    def hsbc_file_format(self):
        file_data = ''
        file_name = 'HSBC.txt'
        #======= File Format Indication =======#
        file_data += 'MXPRLF'
        #====== Authorization Level ======#
        file_data += 'F'
        #====== Charge Account ==== TODO ====#
        file_data += ''.zfill(10)
        #===== Total Amount ===== TODO#
        file_data += ''.zfill(14) 
        #===== Total Operation ===== TODO#
        file_data += ''.zfill(7) 
        #===== Value Date ===== TODO#
        file_data += '        '
        #===== Application Time =======#
        file_data += '17:00'
        #===== Batch Reference =====#
        file_data += ''.ljust(34)
        file_data += "\n"
        for emp in self.payment_ids:
            #===== Beneficiary Account TODO=======#
            file_data += ''.ljust(10) 
            #===== Amount ====== TODO#
            file_data += ''.ljust(14)
            #===== Reference for the account Beneficiary TODO===#
            file_data += ''.ljust(34)
            #===== Name of the Benefiaciry TODO =====#
            file_data += ''.ljust(35)
            file_data += "\n"
            
        gentextfile = base64.b64encode(bytes(file_data,'utf-8'))
        self.file_data = gentextfile
        self.file_name = file_name
        
    def bbva_bancomer_payroll_file_format(self):
        file_data = ''
        file_name = 'BBVA_BANCOMER_PAYROLL.txt'
        #====== Identifier ========#
        file_data += '1'
        #====== Total Line ==== TODO#
        file_data += ''.zfill(7)
        #===== Total Amount ===== TODO #
        file_data += ''.zfill(15)
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
        file_data +=str(currect_time.year)[:2]
        file_data +=str(currect_time.month).zfill(2)
        file_data +=str(currect_time.day)
        file_data += "\n"
        
        for emp in self.payment_ids:
            #====== Record identifier ======#
            file_data += "3"
            #====== Sequential ===== TODO ====#
            file_data += "01"
            #=== Main reference / Employee Beneficiary ==== TODO  #
            file_data += "".ljust(20)
            #==== Movement Amount ======= TODO ===#
            file_data += ''.zfill(15)
            #==== PaymentDate Date ==== TODO ======#
            file_data += 'YYMMDD'
            #==== Ban account payment receiving TODO ===#
            file_data += ''.zfill(16)
            #===== Payroll payment request type / Fortnight TODO====#
            file_data += ''.ljust(14)
            #==== Status ======#
            file_data += '00'
            #==== Filler =====#
            file_data += ''.ljust(4)
            
            file_data += "\n"
            
        gentextfile = base64.b64encode(bytes(file_data,'utf-8'))
        self.file_data = gentextfile
        self.file_name = file_name

    def bbva_bancomer_payroll_232_file_format(self):
        file_data = ''
        file_name = 'BBVA_BANCOMER_DISPERSION_PAYROLL_232.txt'
        #====== Identification No =======#
        file_data += '1'
        #==== No Of Records  TODO =====#
        file_data += ''.zfill(7)
        #==== Total Amount  TODO =====#
        file_data += ''.zfill(15)
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
        file_data +=str(currect_time.month).zfill(2)
        file_data +=str(currect_time.day)
        #==== Date OF Payment TODO =======#
        file_data += 'YYYYMMDD'
        #===== Filler ========#
        file_data += ''.ljust(142)
        file_data += '\n'
        
        for emp in self.payment_ids:
            #======== Identifier ====#
            file_data += '3'
            #=== Type Of Request for payment of payroll TODO =====#
            file_data += '0000000'
            #==== CURP / RFC TODO ======#
            file_data += ''.ljust(18)
            #==== Type Of account TODO=======#
            file_data += ''.ljust(2)
            #===== Target Bank ========#
            file_data += '012'
            #==== Destination Sequence ======#
            file_data += '000'
            #====== Bank Account TODO=====#
            file_data += ''.zfill(16)
            #====== Amount TO Payt TODO=====#
            file_data += ''.zfill(15)
            #======= Payment Status Code =====#
            file_data += ''.zfill(7)
            #====== Payment status Description =====#
            file_data += ''.ljust(80)
            #====== Deposite account holder TODO=====#
            file_data += ''.ljust(40)
            #==== Reason for payment ======= #
            file_data += ''.ljust(40)
            
            file_data += '\n'
        gentextfile = base64.b64encode(bytes(file_data,'utf-8'))
        self.file_data = gentextfile
        self.file_name = file_name
            
    def banamex_file_format(self):

        file_data = ''
        file_name = 'BANAMEX.txt'
        #===== Type Of Records =======#
        file_data += '1'
        #===== Customer Identification Number =======#
        file_data += '000008505585'
        #===== Payment Date TODO =======#
        file_data += 'DDMMAA'
        #====== Sequence of the file TODO =====#
        file_data += '0000'
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
        
        file_data += '\n'
        #======== Second  Heading ========#
        #==== Records Type ====#
        file_data += "2"
        #==== Operation Type ====#
        file_data += "1"
        #==== Currency Key ====#
        file_data += "001"
        #==== Total amount  TODO====#
        file_data += "".zfill(18)
        #==== Account Type ====#
        file_data += "01"
        
        #==== Branch Number TODO====#
        file_data += "".zfill(4)
        #==== Account Number TODO====#
        file_data += "".zfill(20)
        #==== Blank Space====#
        file_data += "".ljust(20)
        #==== Return Amount====#
        file_data += "".ljust(18)
        
        file_data += "\n"
        row_count = 1
        for emp in self.payment_ids:
            #==== Record Type ======#
            file_data += '3'
            #==== Operation Key ======#
            file_data += '0'
            #==== Currency Key ======#
            file_data += '001'
            #===== Amount TODO ========#
            file_data += ''.zfill(18)
            #===== Account Type TODO======#
            file_data += '00'
            #======== Account Number TODO=====#
            file_data += ''.zfill(20)
            #======= Operation Reference ======#
            file_data += '0000000010'
            file_data += ''.zfill(30)
            #====== Beneficiary TODO ====#
            file_data += ''.ljust(55)
            #====== Instructions ====#
            file_data += ''.ljust(40)
            #====== Description TODO====#
            file_data += ''.ljust(24)
            #====== Bank code ====#
            file_data += '0000'
            #====== Reference Low Value ====#
            file_data += str(row_count).zfill(7)
            row_count += 1
            
            #======= Term =======#
            file_data += '00'
            file_data += "\n"
        
        #====== Total Records Data========#
        #===== Record Type =======#
        file_data += '4'
        #===== Currency Key =======#
        file_data += '001'
        #===== Number of subscriptions TODO=======#
        file_data += ''.zfill(6)
        #===== Total Amount TODO=======#
        file_data += ''.zfill(18)
        #===== Number of charges=======#
        file_data += '000001'
        #===== Total Amount of charges TODO=======#
        file_data += ''.zfill(18)
        
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
        
        file_data += '\n'
        #======= Block ​ header (second header, second row of the file) ====#
        #=== File Type =======#
        file_data += 'EE'
        #=== File Type =======#
        file_data += 'HB'
        #=== Charge Currency =======#
        file_data += '00'
        #=== Fature Type =======#
        file_data += '0000'
        #=== Charge Account TODO =======#
        file_data += ''.ljust(11)
        #=== Company Reference =======#
        file_data += '0000000000'
        #=== Code status registration =======#
        file_data += '000'
        #==== Filler =======#
        file_data += ''.ljust(336)
        
        file_data += '\n'
        sequence_no = 1
        for emp in self.payment_ids:
            #===== File Type ========#
            file_data += 'EE'
            #===== Record Type ========#
            file_data += 'DA'
            #===== Movement Type ========#
            file_data += '04'
            #===== Cve currency payment ========#
            file_data += '00'
            #===== Amount TODO ========#
            file_data += ''.zfill(15)
            #===== Payment Date TODO========#
            file_data += 'YYYYMMDD'
            #===== Service Concept========#
            file_data += '01'
            #===== Cve-beneficiary ========#
            file_data += str(sequence_no).zfill(20)
            sequence_no += sequence_no
            #===== RFC TODO========#
            file_data += ''.ljust(13)
            #===== Employee/Beneficiary TODO========#
            file_data += ''.ljust(40)
            #===== Payment Date TODO========#
            file_data += 'MMDDAAAA'
            file_data += ''.zfill(8)
            #===== SBI Payment Place========#
            file_data += '00000'
            #===== Payment Branch========#
            file_data += '00000'
            #===== Bank account receiving payment TODO========#
            file_data += ''.zfill(20)
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
            file_data += 'QUARTERLY SALARY'.ljust(50)
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
            file_data += '\n'
            
        #====== Block trailer does ​ (penultimate row of the file) =====#
        
        #==== File Type =====#
        file_data += 'EE' 
        #==== Record type =====#
        file_data += 'TB' 
        #===== Amount of high movements TODO =====#
        file_data += ''.zfill(7)
        #==== Total Amount TODO =====#
        file_data += ''.zfill(17)
        #==== Number of low movements=====#
        file_data += ''.zfill(7)
        #==== Amount of low movements=====#
        file_data += ''.zfill(17)
        #==== Data filled in by the bank=====#
        file_data += ''.zfill(195)
        #==== Filler=====#
        file_data += ''.ljust(123)
        file_data += "\n"
        #======= Trailer file does ​ (last row of the file) =======#
        
        #==== File Type =====#
        file_data += 'EE' 
        #==== Record type =====#
        file_data += 'TA' 
        #====Amount of high movements TODO=====#
        file_data += ''.zfill(7)
        #====Amount of high movements(Total Amount) TODO=====#
        file_data += ''.zfill(17)
        #==== Number of low movements=====#
        file_data += ''.zfill(7)
        #==== Amount of low movements=====#
        file_data += ''.zfill(17)
        #==== Data filled in by the bank=====#
        file_data += ''.zfill(198)
        #==== Filler=====#
        file_data += ''.ljust(120)
         
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
        file_data += 'YYYYMMDD'
        #====== Consecutive Number TODO========#
        file_data += '01'
        #====== Total No of records TODO========#
        file_data += ''.zfill(6)
        #====== Total Amount of Records TODO========#
        file_data += ''.zfill(15)
        #====== Total Number of HIGH Sent ========#
        file_data += ''.zfill(6)
        #====== Total Amount of HIGH Sent========#
        file_data += ''.zfill(15)
        #====== Total number of DEPARTURES Sent========#
        file_data += ''.zfill(6)
        #====== Total Amount of DEPARTURES Sent========#
        file_data += ''.zfill(15)
        #====== Total number of account verify Sent========#
        file_data += ''.zfill(6)
        #====== Action========#
        file_data += ''.zfill(1)
        #====== Filler========#
        file_data += ''.ljust(77)
        file_data += "\n"

        for emp in self.payment_ids:
            #====== Type of record ========#
            file_data += 'D'
            #====== Application date  TODO========#
            file_data += 'YYYYMMDD'
            #====== Employee number  TODO========#
            file_data += ''.zfill(10)
            #====== Service reference========#
            file_data += ''.ljust(40)
            #====== Fortnight TODO========#
            file_data += ''.ljust(40)
            #====== Amount TODO========#
            file_data += ''.zfill(15)
            #====== Receiving bank number========#
            file_data += '072'
            #====== Type of account   TODO========#
            file_data += '00'
            #====== Payment receipt bank account   TODO========#
            file_data += ''.zfill(18)
            #====== Movement type========#
            file_data += ''.zfill(1)
            #====== Action========#
            file_data += ''.ljust(1)
            #====== VAT amount of the transaction========#
            file_data += ''.zfill(8)
            #===== Filler =====#
            file_data += ''.ljust(18)
            file_data += '\n'




        
        gentextfile = base64.b64encode(bytes(file_data,'utf-8'))
        self.file_data = gentextfile
        self.file_name = file_name
        
    def generate_bank_layout(self):
        if self.bank_layout == 'SANTANDER':
            self.santander_file_format()
        elif self.bank_layout == "HSBC":
            self.hsbc_file_format()
        elif self.bank_layout == "BBVA BANCOMER PAYROLL":
            self.bbva_bancomer_payroll_file_format()
        elif self.bank_layout == "BBVA BANCOMER DISPERSION 232":
            self.bbva_bancomer_payroll_232_file_format()
        elif self.bank_layout == "BANAMEX":
            self.banamex_file_format()
        elif self.bank_layout == "SCOTIABANK":
            self.scotiabank_file_format()
        elif self.bank_layout == "BANORTE":
            self.banorte_file_format()
        
        
        
            
        return {
            'name': _('Generate Bank Layout'),
            'res_model': 'generate.bank.layout.payroll.payment',
            'res_id' : self.id,
            'view_mode': 'form',
            'target': 'new',
            'type': 'ir.actions.act_window',
        }    
