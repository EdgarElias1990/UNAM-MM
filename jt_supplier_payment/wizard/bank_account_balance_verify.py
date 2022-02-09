from odoo import models, fields,_,api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from odoo.tools.profiler import profile

class payment_register(models.TransientModel):
    _inherit = 'account.payment.register'

    def _prepare_payment_vals(self, invoices):
        values = super(payment_register,self)._prepare_payment_vals(invoices)
        if not values.get('partner_id',False):
            values.update({'partner_id':invoices[0].partner_id.id})
        return values
    
class BankBalanceCheck(models.TransientModel):

    _name = 'bank.balance.check'    
    _description = 'Bank Balance Check'
    
    journal_id = fields.Many2one('account.journal','Bank Of Payment Issue')
    account_id = fields.Many2one('account.account','Bank Account')
    bank_account_id = fields.Many2one(related="journal_id.bank_account_id",string="Bank Account")
    total_amount = fields.Float('Total Amount')
    total_request = fields.Float('Total Request')
    is_balance = fields.Boolean('Balance')
    invoice_ids = fields.Many2many('account.move', 'account_invoice_payment_rel_bank_balance', 'payment_id', 'invoice_id', string="Invoices", copy=False, readonly=True)
    
    account_balance = fields.Float("Account Balance")
    minimum_balance = fields.Float("Minimum Balance")
    required_balance = fields.Float("Account balance required")
    different_balance = fields.Float("Difference Between current and required balance")
    
    @api.onchange('journal_id')
    def onchange_jounal(self):
        if self.journal_id:
            self.account_id = self.journal_id.default_debit_account_id and self.journal_id.default_debit_account_id.id or False
        else:
            self.account_id = False
    
    def verify_balance(self):
        account_balance = 0
        if not self.account_id:
            raise ValidationError("Please Configure default debit account into Bank Journal")
        
        if self.account_id:
            values= self.env['account.move.line'].search([('account_id', '=', self.account_id.id),('move_id.state', '=', 'posted')])
            account_balance = sum(x.debit-x.credit for x in values)
            if account_balance >= self.total_amount:
                self.is_balance = True
                self.account_balance = account_balance 
                self.minimum_balance = self.journal_id and self.journal_id.min_balance or 0
                self.required_balance = self.total_amount + self.minimum_balance
                self.different_balance = account_balance - self.total_amount - self.minimum_balance
                 
                return {
                'name': 'Balance',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': False,
                'res_model': 'balance.check.wizard',
                'domain': [],
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context':{'default_different_balance':self.different_balance,'default_required_balance':self.required_balance,'default_minimum_balance':self.minimum_balance,'default_account_balance':account_balance,'default_is_balance':True,'default_wizard_id':self.id},
            } 
            else:
                self.is_balance = False
                return {
                'name': 'Balance',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': False,
                'res_model': 'balance.check.wizard',
                'domain': [],
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context':{'default_different_balance':self.different_balance,'default_required_balance':self.required_balance,'default_minimum_balance':self.minimum_balance,'default_account_balance':account_balance,'default_is_balance':False,'default_wizard_id':self.id},
                }
    def get_payroll_payment_date(self,rec,payment_date):
        if rec.is_payroll_payment_request and rec.employee_paryoll_ids:
            payroll_process_ids = rec.employee_paryoll_ids.mapped('payroll_processing_id')
            if payroll_process_ids and payroll_process_ids[0].period_start and payroll_process_ids[0].period_end and payroll_process_ids[0].fornight:
                #cal_id = self.env['calendar.payment.regis'].search([('type_of_payment','=','payroll'),('fornight_does','=',payroll_process_ids[0].fornight),('type_pay', '=', 'Payment schedule'), ('date', '>=', payroll_process_ids[0].period_start), ('date', '<=', payroll_process_ids[0].period_end)],limit=1)
                cal_id = self.env['calendar.payment.regis'].search([('type_of_payment','=','payroll'),('fornight_does','=',payroll_process_ids[0].fornight),('type_pay', '=', 'Payment schedule')],limit=1)
                if cal_id and cal_id.date:
                    payment_date = cal_id.date
        return payment_date
    
    def get_payment_data(self,rec,data):
        payment_date = False
        if rec.invoice_payment_term_id:
            result = rec.invoice_payment_term_id.compute(rec.amount_total, rec.invoice_date, rec.currency_id)
            if result:
                payment_date = result[0][0]
                if rec.is_different_payroll_request or rec.is_pension_payment_request:
                    if rec.invoice_date and payment_date and isinstance(payment_date,str):
                        payment_date = datetime.strptime(payment_date, '%Y-%m-%d')
                        payment_date = payment_date + timedelta(days=-1)

                        non_business_day_ids = rec.get_non_business_day(
                            rec.invoice_date, payment_date)
                        if non_business_day_ids:
                            payment_date = payment_date + timedelta(days=1)
                            payment_date = rec.get_patment_date(len(non_business_day_ids) - 1, payment_date)
                        
        elif not rec.invoice_payment_term_id and rec.invoice_date_due:
            
            payment_date = rec.invoice_date_due
            if rec.is_different_payroll_request or rec.is_pension_payment_request:
                payment_date = rec.get_patment_date(0, payment_date)
            
        elif rec.invoice_date and not rec.invoice_payment_term_id:
            payment_date = rec.get_patment_date(30, rec.invoice_date)
        payment_request_type = False
        if rec.is_payroll_payment_request:
            payment_request_type = 'payroll_payment'
            payment_date = self.get_payroll_payment_date(rec,payment_date)
        elif rec.is_payment_request:
            payment_request_type = 'supplier_payment'
        elif rec.is_different_payroll_request:
            payment_request_type = 'different_to_payroll'
        elif rec.is_project_payment:
            payment_request_type = 'project_payment'
        elif rec.is_pension_payment_request:
            payment_request_type = 'pension_payment'  
        data.update({'payment_bank_id':rec.payment_bank_id and rec.payment_bank_id.id or False,
                     'payment_bank_account_id' : rec.payment_bank_account_id and rec.payment_bank_account_id.id or False,
                     'payment_issuing_bank_acc_id' : rec.payment_issuing_bank_acc_id and rec.payment_issuing_bank_acc_id.id or False,
                     'batch_folio' : rec.batch_folio,
                     'folio' : rec.folio,
                     'payment_state': 'for_payment_procedure',
                     'payment_request_id':rec.id,
                     'l10n_mx_edi_payment_method_id':rec.l10n_mx_edi_payment_method_id and rec.l10n_mx_edi_payment_method_id.id or False,
                     'payment_request_type' : payment_request_type,
                     'fornight' : rec.fornight,
                      'payroll_request_type' : rec.payroll_request_type,

                     }) 
        if payment_date:
            data.update({'payment_date':payment_date})
        return data

    def create_journal_line_for_payment_procedure(self,invoice):
        #===== for the accounting impact of the "Accrued" Budget====#
        if invoice.journal_id and not invoice.journal_id.accured_credit_account_id \
            or not invoice.journal_id.conac_accured_credit_account_id \
            or not invoice.journal_id.accured_debit_account_id \
            or not invoice.journal_id.conac_accured_debit_account_id :
            raise ValidationError("Please configure UNAM and CONAC Accrued account in payment request journal!")
        amount_total = sum(x.price_total for x in invoice.invoice_line_ids.filtered(lambda x:x.program_code_id))
        if invoice.currency_id != invoice.company_id.currency_id:
            amount_currency = abs(amount_total)
            balance = invoice.currency_id._convert(amount_currency, invoice.company_currency_id, invoice.company_id, invoice.date)
            currency_id = invoice.currency_id and invoice.currency_id.id or False 
        else:
            balance = abs(amount_total)
            amount_currency = 0.0
            currency_id = False
        
        invoice.line_ids = [(0, 0, {
                                     'account_id': invoice.journal_id.accured_credit_account_id and invoice.journal_id.accured_credit_account_id.id or False,
                                     'coa_conac_id': invoice.journal_id.conac_accured_credit_account_id and invoice.journal_id.conac_accured_credit_account_id.id or False,
                                     'credit': balance, 
                                     'exclude_from_invoice_tab': True,
                                     'conac_move' : True,
                                     'amount_currency' : -amount_currency,
                                     'currency_id' : currency_id,
                                     'partner_id':invoice.partner_id and invoice.partner_id.id or False,
                                 }), 
                        (0, 0, {
                                     'account_id': invoice.journal_id.accured_debit_account_id and  invoice.journal_id.accured_debit_account_id.id or False,
                                     'coa_conac_id': invoice.journal_id.conac_accured_debit_account_id and invoice.journal_id.conac_accured_debit_account_id.id or False,
                                     'debit': balance,
                                     'exclude_from_invoice_tab': True,
                                     'conac_move' : True,
                                     'amount_currency' : amount_currency,
                                     'currency_id' : currency_id,
                                     'partner_id':invoice.partner_id and invoice.partner_id.id or False,
                                 })]
        #====== the Bank Journal, for the accounting impact of the "Exercised" Budget ======#
        if not self.journal_id.execercise_credit_account_id or not self.journal_id.conac_exe_credit_account_id \
            or not self.journal_id.execercise_debit_account_id or not self.journal_id.conac_exe_debit_account_id :
            raise ValidationError("Please configure UNAM and CONAC Exercised account in %s journal!" %
                                  self.journal_id.name)
        
        invoice.line_ids = [(0, 0, {
                                     'account_id': self.journal_id.execercise_credit_account_id and self.journal_id.execercise_credit_account_id.id or False,
                                     'coa_conac_id': self.journal_id.conac_exe_credit_account_id and self.journal_id.conac_exe_credit_account_id.id or False,
                                     'credit': balance, 
                                     'exclude_from_invoice_tab': True,
                                     'conac_move' : True,
                                     'amount_currency' : -amount_currency,
                                     'currency_id' : currency_id,
                                     'partner_id':invoice.partner_id and invoice.partner_id.id or False,
                                 }), 
                        (0, 0, {
                                     'account_id': self.journal_id.execercise_debit_account_id and self.journal_id.execercise_debit_account_id.id or False,
                                     'coa_conac_id': self.journal_id.conac_exe_debit_account_id and self.journal_id.conac_exe_debit_account_id.id or False,
                                     'debit': balance,
                                     'exclude_from_invoice_tab': True,
                                     'conac_move' : True,
                                     'amount_currency' : amount_currency,
                                     'currency_id' : currency_id,      
                                     'partner_id':invoice.partner_id and invoice.partner_id.id or False,                               
                                 })]
        
    
        
    def schedule_payment(self):
        all_payments = self.env['account.payment']
        #self.invoice_ids.write({'payment_state': 'for_payment_procedure','payment_issuing_bank_id':self.journal_id.id})
        qq = "UPDATE account_move set payment_state='for_payment_procedure',payment_issuing_bank_id=%s where id in %s" 
        self.env.cr.execute(qq,(self.journal_id.id,tuple(self.invoice_ids.ids)))
        self.invoice_ids.action_post()
        for rec in self.invoice_ids:
            #rec.action_post()
            #rec.payment_issuing_bank_id = self.journal_id.id
            if not rec.is_pension_payment_request and not rec.is_different_payroll_request:
                self.create_journal_line_for_payment_procedure(rec)
            payment_record = self.env['account.payment.register'].with_context(active_ids=rec.ids).\
                create({'journal_id':self.journal_id.id,'invoice_ids':[(6, 0, rec.ids)]})
            Payment = self.env['account.payment']
            datas = payment_record.get_payments_vals()
            for data in datas:
                new_dict = self.get_payment_data(rec, data)
                payments = Payment.create(new_dict)
                all_payments += payments 
            #rec.write({'payment_state': 'for_payment_procedure'})
            for line in rec.line_ids.filtered(lambda x:not x.coa_conac_id):
                line.coa_conac_id = line.account_id and line.account_id.coa_conac_id and line.account_id.coa_conac_id.id or False 
            
        for payment in all_payments:
            payment.action_validate_payment_procedure()
