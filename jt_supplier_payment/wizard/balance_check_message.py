from odoo import models, fields,_
from odoo.exceptions import UserError, ValidationError
import io
import xlwt
import base64

from xlwt import Workbook, easyxf


class BalanceCheckWizard(models.TransientModel):
    
    _name = 'balance.check.wizard'
    
    is_balance = fields.Boolean('Is Check',default=False)
    wizard_id = fields.Many2one('bank.balance.check','Wizard')
    excel_file = fields.Binary('Report')
    file_name = fields.Char('File', size=64)
    account_balance = fields.Float('Account Balance')
    minimum_balance = fields.Float("Minimum Balance")
    required_balance = fields.Float("Account balance required")
    different_balance = fields.Float("Difference Between current and required balance")
    
    def accept(self):
        return {
            'name': _('Schedule Payment'),
            'res_model':'bank.balance.check',
            'view_mode': 'form',
            'view_id': self.env.ref('jt_supplier_payment.view_bank_balance_check').id,
            'target': 'new',
            'type': 'ir.actions.act_window',
            'res_id' : self.wizard_id.id,
        }

    def generate_report(self):
        filename = 'bank_balance_report.xls'
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Bank Report', cell_overwrite_ok=True)
        style_header_right = easyxf(
            'font: name Arial;'
            'alignment: horizontal left, vertical center,wrap yes ;'
            'font:bold True,height 180;'
            'borders:left thin, right thin, top thin, bottom thin;'
        )
        style_header_data =  easyxf(
            'font: name Arial;'
            'alignment: horizontal right, vertical center,wrap yes ;'
         
            'borders:left thin, right thin, top thin, bottom thin;',
            num_format_str='#,##0.00'
        )
        col = 0
        row = 0
        worksheet.row(0).height = 200 * 2
        if self.env.user.lang == 'es_MX':
            worksheet.write(row, col, 'Folio de lote',style_header_right)
        else:
            worksheet.write(row, col, 'Batch Sheet',style_header_right)
        col += 1
        if self.env.user.lang == 'es_MX':
            worksheet.write(row, col, 'Banco de emisión de pago',style_header_right)
        else:
            worksheet.write(row, col, 'Bank',style_header_right)
        col += 1
        worksheet.col(col).width = 256 * 15
        if self.env.user.lang == 'es_MX':
            worksheet.write(row, col, 'Cuenta bancaria de emisión de pago',style_header_right)
        else:
            worksheet.write(row, col, 'Bank Account',style_header_right)
        col += 1
        worksheet.col(col).width = 256 * 15
        if self.env.user.lang == 'es_MX':
            worksheet.write(row, col, 'Saido de la cuenta',style_header_right)
        else:
            worksheet.write(row, col, 'Account Balance',style_header_right)
        col += 1
        worksheet.col(col).width = 256 * 15
        if self.env.user.lang == 'es_MX':
            worksheet.write(row, col, 'Saido minimo',style_header_right)
        else:
            worksheet.write(row, col, 'Minimum Balance',style_header_right)
        col += 1
        worksheet.col(col).width = 256 * 23
        if self.env.user.lang == 'es_MX':
            worksheet.write(row, col, 'Saido requerido en la cuenta',style_header_right)
        else:
            worksheet.write(row, col, 'Account balance required',style_header_right)
        col += 1
        worksheet.col(col).width = 256 * 43
        if self.env.user.lang == 'es_MX':
            worksheet.write(row, col, 'Diferencia entre el saido actual y el requerido',style_header_right)
        else:
            worksheet.write(row, col, 'Difference Between current and required balance',style_header_right)
        col += 1
        row += 1
        col = 0
        #====== Data =====
        worksheet.write(row, col, self.wizard_id.total_request)
        col += 1
        bank = self.wizard_id.journal_id and self.wizard_id.journal_id.bank_id and self.wizard_id.journal_id.bank_id.name or ''
        worksheet.write(row, col, bank)
        col += 1
        worksheet.col(col).width = 256 * 15
        bank_account_name = self.wizard_id.journal_id and self.wizard_id.journal_id.bank_account_id and self.wizard_id.journal_id.bank_account_id.acc_number or '' 
        worksheet.write(row, col, bank_account_name)
        col += 1
        worksheet.col(col).width = 256 * 15
        worksheet.write(row, col, self.account_balance,style_header_data)
        col += 1
        worksheet.col(col).width = 256 * 15
        minimum_balance = self.wizard_id.journal_id and self.wizard_id.journal_id.min_balance or 0
        worksheet.write(row, col,minimum_balance,style_header_data)
        col += 1
        worksheet.col(col).width = 256 * 23
        worksheet.write(row, col, self.wizard_id.total_amount,style_header_data)
        col += 1
        worksheet.col(col).width = 256 * 43
        worksheet.write(row, col,self.account_balance - self.wizard_id.total_amount,style_header_data)
        
        fp = io.BytesIO()
        workbook.save(fp)
        self.excel_file = base64.encodestring(fp.getvalue())
        self.file_name = filename
        fp.close()
        
        return {
            'name': _('Schedule Payment'),
            'res_model':'balance.check.wizard',
            'view_mode': 'form',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'res_id' : self.id,
        }
        
