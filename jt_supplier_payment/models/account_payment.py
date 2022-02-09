from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError

class AccountPayment(models.Model):

    _inherit = 'account.payment'

    payment_bank_id = fields.Many2one('res.bank', "Bank of receipt of payment")
    payment_bank_account_id = fields.Many2one('res.partner.bank', "Payment Receipt bank account")
    payment_issuing_bank_acc_id = fields.Many2one(related="journal_id.bank_account_id", string="Payment issuing bank Account")
    batch_folio = fields.Integer("Batch Folio")
    folio = fields.Char("Folio against Receipt")
    reason_for_rejection = fields.Text('Reason For Rejection')
    reason_for_cancel = fields.Text('Reason For Cancellation')
    payment_state = fields.Selection([('draft', 'Draft'), 
                              ('for_payment_procedure','For Payment Procedure'),
                               ('posted', 'Validated'), 
                              ('reconciled', 'Reconciled'), 
                              ('rejected','Rejected'),
                              ('cancelled', 'Cancelled')], 
                              readonly=True, default='draft', copy=False, string="Status")
    baneficiary_key = fields.Char('Baneficiary Key', related='partner_id.password_beneficiary', store=True)
         
    banamex_description = fields.Char('Description')
    banamex_concept = fields.Char('Concept',size=34)
    banamex_reference = fields.Char('Reference',size=10)
    
    net_cash_reference = fields.Char('Reference')
    net_cash_availability = fields.Selection([('SPEI','SPEI'),('CECOBAN','CECOBAN')],string='Availability')
    
    sit_file_key = fields.Char('File Key',size=30)
    sit_operation_code = fields.Selection([('payment_on_account_bancomer','Payment on account bancomer'),
                                           ('payment_interbank','Payment interbank account next day')],string="Operation Code")
    sit_reference =fields.Char(size=25,string="SIT Reference")
    sit_reason_for_payment = fields.Char(size=37,string="Reason For Payment")
    sit_additional_data = fields.Char('Additional Data')
    
    santander_payment_concept = fields.Text('Payment Concept')
    
    hsbc_reference = fields.Char('HSBC Reference',size=40)
    
    jp_method = fields.Selection([('WIRES','WIRES'),('BOOKTX','BOOKTX')],string='Method')
    jp_bank_transfer = fields.Selection([('non_financial_institution','Non Financial Institution'),
                                         ('financial_institution','Financial Institutions')
                                         ],string="Bank To Bank Transfer")
    jp_id_type = fields.Selection([('clabe','CLABE'),
                                    ('debit_card','Debit Card'),
                                    ('vostro','Vostro')
                                         ],string="ID Type Beneficiary")
    jp_id_type_beneficiary_bank = fields.Selection([('None','None'),
                                    ('SPEI','SPEI'),
                                    ('SWIFT','SWIFT')
                                         ],string="ID Type Beneficiary Bank")
    jp_charges = fields.Selection([('shared','Shared'),
                                    ('beneficiary','Beneficiary'),
                                    ('remitter','Remitter')
                                         ],string="Charges")
    jp_drawdown_type = fields.Selection([('WIRE','WIRE'),
                                    ('BOOK','BOOK'),('Drawdown','Drawdown')],string="Drawdown Type")
    
    jp_payment_concept = fields.Char('Payment Concept')
    
    payment_request_id = fields.Many2one('account.move','circular')

    employee_partner_type = fields.Selection([('employee','Employee'),('alimony','Alimony')],string='Partner Type',copy=False)
    
    no_validate_payment = fields.Boolean(string="Not Validated",copy=False,default=False)
    transfer_confirmation_date = fields.Date("Confirmation Date",copy=False)
    
#     @api.depends('payment_state')
#     def get_status_of_payment(self):
#         for rec in self:
#             no_validate_payment = False
#             if rec.payment_state and rec.payment_state=='for_payment_procedure':
#                 no_validate_payment = True
#             rec.no_validate_payment = no_validate_payment
            
    @api.depends('journal_id','journal_id.bank_format','journal_id.load_bank_format')
    def check_bank_format_type(self):
        for record in self:
            is_hide_banamex = True
            is_hide_bbva_sit = True
            is_hide_bbva_net = True
            is_hide_hsbc = True
            is_hide_santander = True  
            is_hide_jp_morgan = True
            
            if record.journal_id.bank_format=='banamex' or record.journal_id.load_bank_format == 'banamex':
                is_hide_banamex = False
            if record.journal_id.bank_format=='hsbc' or record.journal_id.load_bank_format == 'hsbc':
                is_hide_hsbc = False
            if record.journal_id.bank_format=='santander' or record.journal_id.load_bank_format == 'santander':
                is_hide_santander = False
            if record.journal_id.bank_format == 'bbva_sit' or record.journal_id.load_bank_format == 'bbva_bancomer':
                is_hide_bbva_sit = False
            if record.journal_id.bank_format in ('bbva_tnn_ptc','bbva_tsc_pcs') or record.journal_id.load_bank_format == 'bbva_bancomer':
                is_hide_bbva_net = False
                
            if record.journal_id.bank_format in ('jpmw','jpmu','jpma') or record.journal_id.load_bank_format == 'jp_morgan':
                is_hide_jp_morgan = False

            record.is_hide_banamex = is_hide_banamex
            record.is_hide_bbva_sit = is_hide_bbva_sit
            record.is_hide_hsbc = is_hide_hsbc
            record.is_hide_santander = is_hide_santander  
            record.is_hide_jp_morgan = is_hide_jp_morgan
            record.is_hide_bbva_net = is_hide_bbva_net
            
    is_hide_banamex = fields.Boolean(compute='check_bank_format_type',default=True)
    is_hide_bbva_sit = fields.Boolean(compute='check_bank_format_type',default=True)
    is_hide_bbva_net = fields.Boolean(compute='check_bank_format_type',default=True)
    is_hide_hsbc = fields.Boolean(compute='check_bank_format_type',default=True)
    is_hide_santander = fields.Boolean(compute='check_bank_format_type',default=True)
    is_hide_jp_morgan = fields.Boolean(compute='check_bank_format_type',default=True)

    @api.constrains('payment_date')
    def check_payment_date(self):
        for rec in self: 
            if rec.payment_request_type and rec.payment_request_type != 'supplier_payment':

                non_business_day = self.env['calendar.payment.regis'].search([('type_pay','=','Non Business Day'),
                                                                              ('date','=',rec.payment_date)])
                if non_business_day:
                    raise UserError(_('Not allow to schedule payment for non-working days.'))
                
    @api.model
    def create(self,vals):
        res = super(AccountPayment,self).create(vals)   
        if res.folio and not res.sit_reason_for_payment:
            sit_res = res.folio.replace("/",'')
            res.sit_reason_for_payment = sit_res
        if res.partner_type and res.payment_request_type and res.payment_request_type == 'payroll_payment':
            res.employee_partner_type = 'employee'
        elif res.partner_type and res.payment_request_type and res.payment_request_type == 'pension_payment':
            res.employee_partner_type = 'alimony'        
        
        return res
    
    @api.constrains('banamex_reference')
    def _check_banamex_reference(self):
        if self.banamex_reference and not str(self.banamex_reference).isnumeric():
            raise ValidationError(_('The Banamex Reference must be numeric value'))

    def cancel(self):
        result = super(AccountPayment,self).cancel()
        if self.env.context and self.env.context.get('call_from_reject',False):
            return result
        self.write({'payment_state': 'cancelled'})
        if self.payment_request_id:
            payment_request = self.env['account.move'].search([('id', '=', self.payment_request_id.id)])
            payment_request.payment_state = 'for_payment_procedure'
        return result
    
    def set_bank_tab_data(self):
        if self.journal_id and self.journal_id.bank_format == 'bbva_sit':
            sit_operation_code = 'payment_interbank'
            sit_reference = '9999'
            if self.partner_id and self.partner_id.bank_ids and self.partner_id.bank_ids[0].l10n_mx_edi_clabe:
                if self.partner_id.bank_ids[0].l10n_mx_edi_clabe.startswith('012'):
                    sit_operation_code = 'payment_on_account_bancomer'
                    sit_reference = '    '
            self.sit_operation_code = sit_operation_code
            self.sit_reference = sit_reference
             
    def action_validate_payment_procedure(self):
        for rec in self:
            if not rec.name:
                if rec.payment_type == 'transfer':
                    sequence_code = 'account.payment.transfer'
                else:
                    if rec.partner_type == 'customer':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.customer.invoice'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.customer.refund'
                    if rec.partner_type == 'supplier':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.supplier.refund'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.supplier.invoice'
                
                    rec.name = self.env['ir.sequence'].next_by_code(sequence_code, sequence_date=rec.payment_date)
                    if not rec.name and rec.payment_type != 'transfer':
                        raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))
            #rec.banamex_concept = rec.name
            rec.payment_state = 'for_payment_procedure'            
            rec.set_bank_tab_data()
            
    def action_reschedule_payment_procedure(self):
        for payment in self:
            payment.action_draft()
            payment.payment_state = 'for_payment_procedure'
        
    def create_journal_for_paid(self,invoice):
        #==== he Bank Journal will be taken, corresponding to the “Paid” accounting moment ===#
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
                                     'account_id': self.journal_id.paid_credit_account_id and self.journal_id.paid_credit_account_id.id or False,
                                     'coa_conac_id': self.journal_id.conac_paid_credit_account_id and self.journal_id.conac_paid_credit_account_id.id or False,
                                     'credit': balance, 
                                     'exclude_from_invoice_tab': True,
                                     'conac_move' : True,
                                     'amount_currency' : -amount_currency,
                                     'currency_id' : currency_id,                                     
                                     'partner_id':invoice.partner_id and invoice.partner_id.id or False,
                                 }), 
                        (0, 0, {
                                     'account_id': self.journal_id.paid_debit_account_id and self.journal_id.paid_debit_account_id.id or False,
                                     'coa_conac_id': self.journal_id.conac_paid_debit_account_id and self.journal_id.conac_paid_debit_account_id.id or False,
                                     'debit': balance,
                                     'exclude_from_invoice_tab': True,
                                     'conac_move' : True,
                                     'amount_currency' : amount_currency,
                                     'currency_id' : currency_id,
                                     'partner_id':invoice.partner_id and invoice.partner_id.id or False,                                     
                                 })]
    
    def post(self):
        result = super(AccountPayment,self).post()
        self.write({'payment_state': 'posted'})
        for payment in self:
            payment.transfer_confirmation_date = fields.Date.today()
            for inv in payment.invoice_ids.filtered(lambda x:x.is_project_payment or x.is_payment_request or x.is_payroll_payment_request or x.is_different_payroll_request or x.is_pension_payment_request):
                if inv.invoice_payment_state == 'paid':
                    inv.payment_state = 'paid'
                    if not inv.is_pension_payment_request and not inv.is_different_payroll_request:
                        payment.create_journal_for_paid(inv)
            is_supplier_payment = payment.invoice_ids.filtered(lambda x:x.is_project_payment or x.is_payment_request or x.is_payroll_payment_request or x.is_different_payroll_request or x.is_pension_payment_request)
            if is_supplier_payment:
                for line in payment.move_line_ids:
                    line.coa_conac_id = line.account_id and line.account_id.coa_conac_id and line.account_id.coa_conac_id.id or False
                    line.conac_move = True  
            payment.banamex_concept = payment.name
            payment.no_validate_payment = False
        return result
 
    def action_draft(self):
        result = super(AccountPayment,self).action_draft()
        self.write({'payment_state': 'draft'})
        if self.payment_request_id:
            payment_request = self.env['account.move'].search([('id', '=', self.payment_request_id.id)])
            payment_request.payment_state = 'for_payment_procedure'
        return result
               
    def action_register_payment(self):
        res =super(AccountPayment,self).action_register_payment()
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return ''
        
        record_ids = self.env['account.move'].browse(active_ids)
        if not record_ids or any(invoice.payment_state != 'approved_payment' and (invoice.is_payroll_payment_request or invoice.is_different_payroll_request or invoice.is_pension_payment_request)  for invoice in record_ids):
            raise UserError(_("You can only register payment for  Approved for payment request"))

        if not record_ids or any(invoice.payment_state not in ('approved_payment','assigned_payment_method') and (invoice.is_project_payment or invoice.is_payment_request)  for invoice in record_ids):
            raise UserError(_("You can only register payment for  Approved for payment request"))
        
#         if not record_ids or any(invoice.state != 'posted' for invoice in record_ids):
#             raise UserError(_("You can only register payments for open invoices"))
        
        record_ids = record_ids.filtered(lambda x:(x.is_project_payment or x.is_payment_request or x.is_payroll_payment_request or x.is_different_payroll_request or x.is_pension_payment_request) and x.is_invoice(include_receipts=True))
        if record_ids:
#             payment_issuing_bank_id = record_ids.mapped('payment_issuing_bank_id')
#             if len(payment_issuing_bank_id) != 1 :
#                 raise UserError(_("You can not register payment for multiple Payment issuing Bank"))
            amount = 0
            for r in record_ids: 
                amount1 = self._compute_payment_amount(r, r.currency_id, r.journal_id,fields.Date.today())
                amount += abs(amount1)
                
            if abs(amount) == 0 :
                raise UserError(_("You can not register payment with 0 amount"))
            
            return {
                'name': _('Schedule Payment'),
                'res_model':'bank.balance.check',
                'view_mode': 'form',
                'view_id': self.env.ref('jt_supplier_payment.view_bank_balance_check').id,
                'context': {'default_total_amount': abs(amount),'default_total_request':len(record_ids),'default_invoice_ids': [(6, 0, record_ids.ids)]},
                'target': 'new',
                'type': 'ir.actions.act_window',
            }
            
        else:
            return res
