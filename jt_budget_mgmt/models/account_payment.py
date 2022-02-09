from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class AccountPayment(models.Model):

    _inherit = 'account.payment'
    
    dependancy_id = fields.Many2one('dependency', string='Dependency')
    sub_dependancy_id = fields.Many2one('sub.dependency', 'Sub Dependency')
    transfer_made_origin = fields.Boolean('Transfer Made (origin account)', default=True)
    confirmed_transfer = fields.Boolean('Confirmed Transfer (destination account)', default=True)
    circular_acc_destination = fields.Text(string='Circular Account Destination')

    def post(self):
        record = super(AccountPayment,self).post()
        for rec in self:
            move_ids = rec.move_line_ids.mapped('move_id')
            for move in move_ids:
                if rec.dependancy_id:
                    move.dependancy_id = rec.dependancy_id.id
                if rec.sub_dependancy_id:
                    move.sub_dependancy_id = rec.sub_dependancy_id.id 
        return record

    def set_bank_tab_data(self):
        res = super(AccountPayment,self).set_bank_tab_data()
        if self.payment_request_type=='supplier_payment':
            if self.journal_id.bank_format=='banamex' or self.journal_id.load_bank_format == 'banamex':
                banamex_description = ''
                banamex_concept = ''
                if self.dependancy_id and self.dependancy_id.sort_description:
                    banamex_description = self.dependancy_id.sort_description + " "
                    banamex_concept = self.dependancy_id.sort_description + " "
                if self.folio:
                    banamex_description += self.folio
                if self.name:
                    banamex_concept += self.name
                    
                self.banamex_description = banamex_description
                self.banamex_concept = banamex_concept
                
            if self.journal_id.bank_format=='hsbc' or self.journal_id.load_bank_format == 'hsbc':
                hsbc_reference = ''
                if self.folio:
                    hsbc_reference = self.folio
                self.hsbc_reference = hsbc_reference
            if self.journal_id.bank_format=='santander' or self.journal_id.load_bank_format == 'santander':
                santander_payment_concept = ''
                if self.folio:
                    santander_payment_concept = self.folio + " "
                if self.name:
                    santander_payment_concept += self.name
                self.santander_payment_concept = santander_payment_concept
            if self.journal_id.bank_format == 'bbva_sit' or self.journal_id.load_bank_format == 'bbva_bancomer':
                sit_additional_data = 'PAGOUNAM - '
                if self.dependancy_id and self.dependancy_id.description:
                    sit_additional_data += self.dependancy_id.description +" "
                if self.dependancy_id and self.dependancy_id.dependency:
                    sit_additional_data += self.dependancy_id.dependency +"-"
                if self.sub_dependancy_id and self.sub_dependancy_id.sub_dependency:
                    sit_additional_data += self.sub_dependancy_id.sub_dependency
                if self.env.user.lang == 'es_MX':
                    sit_additional_data += "FAVOR DE MANTENER ACTUALIZADA SU INFORMACIÓN BANCARIA"
                else: 
                    sit_additional_data += "PLEASE KEEP YOUR BANKING INFORMATION UPDATED"    
                
                self.sit_additional_data = sit_additional_data
            if self.journal_id.bank_format in ('bbva_tnn_ptc','bbva_tsc_pcs') or self.journal_id.load_bank_format == 'bbva_bancomer':
                today_date = datetime.today().date()
                if self.payment_date and self.payment_date == today_date:
                    self.net_cash_availability = 'SPEI'
                self.net_cash_reference = self.name
            if self.journal_id.bank_format in ('jpmw','jpmu','jpma') or self.journal_id.load_bank_format == 'jp_morgan':
                self.jp_method = 'WIRES'
                self.jp_bank_transfer = 'non_financial_institution'
                jp_payment_concept = ''
                if self.folio:
                    jp_payment_concept = self.folio
                self.jp_payment_concept = jp_payment_concept
                 
        return res
    