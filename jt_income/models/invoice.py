from odoo import models, fields, api,_
from babel.dates import format_datetime, format_date

from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date, get_lang

from datetime import date, timedelta
from itertools import groupby
from itertools import zip_longest
from hashlib import sha256
from json import dumps

import json
import re

class Invoice(models.Model):

    _inherit = 'account.move'

    @api.depends('registry')
    def get_charge_data(self):
        for rec in self:
            if rec.registry:
                emp = self.env['hr.employee'].search([('user_id','=',rec.registry.id)],limit=1)
                if emp.job_id:
                    rec.charge_id = emp.job_id.id
                else:
                    rec.charge_id = False
            else:
                rec.charge_id = False
                
    income_type = fields.Selection([('extra', 'Extraordinary'),
                                    ('own', 'Own')], string="Income Type")
    sub_origin_resource_id = fields.Many2one('sub.origin.resource', "Extraordinary / Own income")
    sub_origin_resource_name = fields.Char(related='sub_origin_resource_id.name',string="sub origin resource name",store=True,copy=False)
    type_of_revenue_collection = fields.Selection([('billing', 'Billing'),
                                                   ('deposit_cer', 'Certificates of deposit'),
                                                   ('dgae_ref', 'Reference of DGAE'),
                                                   ('dgoae_trades', 'Trades DGOAE')], string="Type of Revenue Collection",copy=False)
    income_bank_journal_id = fields.Many2one('account.journal', "Bank")
    income_bank_account = fields.Many2one(related="income_bank_journal_id.bank_account_id", string="Bank Account")
    reception_date = fields.Date("Reception Date")
    deposit_date = fields.Date("Deposit Date")
    cfdi_folio = fields.Char("Folio CFDI")
    range_sheet_used = fields.Char("Range of sheets used")
    income_activity = fields.Selection([('procosion_service', 'Provision of service'),
                                        ('disposal_property', 'Disposal of property'),
                                        ('leasing_real_estate', 'Leasing of real estate'),
                                        ('donations', 'Donations'),
                                        ('conacyt', 'Conacyt')], "Activity")
    voucher_type = fields.Selection([('income', 'Income'),
                                     ('expenditure', 'Expenditure'),
                                     ('payment_supplement', 'Payment Supplement'),
                                     ('transfer', 'Transfer'),
                                     ('credit_note','Credit Note'),
                                     ], "Voucher Type")
    currency_type = fields.Selection([('national', 'National Currency'), ('foreign', 'Foreign Currency')])
    exchange_rate = fields.Monetary("Exchange Rate")
    income_payment_type = fields.Selection([('single_pue', 'Payment in a singlePUE'),
                                            ('ppd_installments', 'Payment in PPD installments')], "Payment Type")
    related_cfdi = fields.Char("Related CFDI")
    income_payment_ref = fields.Char("Payment reference or approval number")
    ieps = fields.Char('IEPS')
    ieps_amount = fields.Monetary("IEPS Amount")
    record_type = fields.Selection([('manual', 'Manual'),
                                    ('automatic', 'Automatic')], 'Record Type')
    exercise = fields.Char("Exercise")
    operation_key_id = fields.Many2one('deposit.certificate.type', "Operation Key")
    concept = fields.Char("Concept")
    folio_upa = fields.Char("Folio UPA")
    exercise_upa = fields.Char("Exercise UPA")
    observations = fields.Char("Observations")
    status_certificate = fields.Selection([('approved', 'Approved'),
                                           ('cancelled', 'Cancelled')], 'Status Certificate')
    cancellation_date = fields.Date("Cancellation Date")
    date_reference = fields.Date('Date of Reference')
    exercise_reference = fields.Char("Exercise of the reference")
    email = fields.Char("Mail")
    certificate_seal = fields.Char("Certificate Seal")
    base_salary = fields.Monetary("Base Salary")
    emitter = fields.Char("Emitter")
    registry = fields.Many2one("res.users",string="Registry",default=lambda self: self.env.user)
    charge_id = fields.Many2one('hr.job',string="Charge",compute="get_charge_data",store=True)
    issuer_dependency_id = fields.Many2one('dependency', "Issuer Dependency")
    cfdi_conacyt_enter = fields.Char("CFDI CONACYT Enter")
    cfdi_conacyt_exercise = fields.Char("CFDI Exercise CONACYT entry")
    amount_cfdi_conacyt_income = fields.Monetary("Amount CFDI CONACYT Income")
    conacyt_project_key = fields.Many2one('project.project', "CONACYT project key")
    cfdi_conacyt_date = fields.Date('CFDI CONACYT Date')
    conacyt_project_name = fields.Char('CONACYT Project Name')
    uuid_cfdi_ps = fields.Char('UUID CFDI PS')
    income_vat = fields.Monetary("VAT")
    income_isr = fields.Monetary("ISR")
    surcharges_ps = fields.Monetary("Surcharges PS")
    legal_number = fields.Char("Legal Number")
    legal_compensation = fields.Char("Legal Compensation")
    number_of_returned_check = fields.Integer('Number of returned check') 
    circular_number = fields.Char('Circular number')
    addressee = fields.Char('Addressee')
    bank_status_account = fields.Char('Bank status account')
    bank_account_statement = fields.Char('Bank account statement')
    number_receipts = fields.Char('Number receipts')
    movement_date = fields.Date('Movement date')
    description_of_the_movement = fields.Char('Description of the movement')
    settlement_date = fields.Date('Settlement date')
    income_id = fields.Char('ID')
    income_branch = fields.Char('Branch')
    reference_plugin = fields.Char('Reference Plugin')
    income_status = fields.Selection([('approved','Approved'),('rejected','Rejected')],string="Income Status")
    adequacies_ids = fields.One2many("adequacies",'invoice_move_id')
    hide_base_on_account = fields.Boolean('Hide Base Accounts',compute='get_hide_base_on_account')
    payment_method_name = fields.Char(related='l10n_mx_edi_payment_method_id.name')
    sub_origin_ids = fields.Many2many('sub.origin.resource',compute="get_sub_origin_ids",store=True)
    customer_ref = fields.Char("Customer Reference")
    returned_check = fields.Boolean("Returned check",default=False)
    manual_rfc = fields.Char("RFC")
    full_name = fields.Char("Full Name")
    type_of_changes = fields.Float("Type Of Changes")
    trade_no = fields.Char("Trade No")
    payment_of_id = fields.Many2one('payment.of.income','Payment of')
    #===== Notice of compensation Tab fields=========#

    template1 = fields.Selection([('application_form_20','Application form 20%')],string="Template")
    template1_recipient_emp_id = fields.Many2one('hr.employee','Application form Recipient Employee')
    template1_recipient_title = fields.Char(related="template1_recipient_emp_id.emp_title",string='Title')
    template1_recipient_professional_title = fields.Char(related="template1_recipient_emp_id.emp_job_title",string='Professional Title')
    template1_sender_emp_id = fields.Many2one('hr.employee','Application form Sender Employee')
    template1_sender_title = fields.Char(related="template1_sender_emp_id.emp_title",string='Title')
    template1_sender_professional_title = fields.Char(related="template1_sender_emp_id.emp_job_title",string='Professional Title')
    template1_employee_ids = fields.Many2many('hr.employee','rel_template1_employee_income_invoice','sender_id','emp_id','Application Form EMPLOYEES COPIED')

    template2 = fields.Selection([('format_forgiveness','Format Forgiveness')],string="Template")
    template2_recipient_emp_id = fields.Many2one('hr.employee','Format Forgiveness Recipient Employee')
    template2_recipient_title = fields.Char(related="template2_recipient_emp_id.emp_title",string='Title')
    template2_recipient_professional_title = fields.Char(related="template2_recipient_emp_id.emp_job_title",string='Professional Title')
    template2_sender_emp_id = fields.Many2one('hr.employee','Format Forgiveness Sender Employee')
    template2_sender_title = fields.Char(related="template2_sender_emp_id.emp_title",string='Title')
    template2_sender_professional_title = fields.Char(related="template2_sender_emp_id.emp_job_title",string='Professional Title')
    template2_employee_ids = fields.Many2many('hr.employee','rel_template2_employee_income_invoice','sender_id','emp_id','Format Forgiveness EMPLOYEES COPIED')

    template3 = fields.Selection([('format_notice_change','Format notice change form of payment to transfer')],string="Template")
    template3_recipient_emp_id = fields.Many2one('hr.employee','Format notice Recipient Employee')
    template3_recipient_title = fields.Char(related="template3_recipient_emp_id.emp_title",string='Title')
    template3_recipient_professional_title = fields.Char(related="template3_recipient_emp_id.emp_job_title",string='Professional Title')
    template3_sender_emp_id = fields.Many2one('hr.employee','Format notice Sender Employee')
    template3_sender_title = fields.Char(related="template3_sender_emp_id.emp_title",string='Title')
    template3_sender_professional_title = fields.Char(related="template3_sender_emp_id.emp_job_title",string='Professional Title')
    template3_employee_ids = fields.Many2many('hr.employee','rel_template3_employee_income_invoice','sender_id','emp_id','Format Notice EMPLOYEES COPIED')

    template4 = fields.Selection([('2nd application_form_20','2nd Application form 20%')],string="Template")
    template4_recipient_emp_id = fields.Many2one('hr.employee','2nd Application form Recipient Employee')
    template4_recipient_title = fields.Char(related="template4_recipient_emp_id.emp_title",string='Title')
    template4_recipient_professional_title = fields.Char(related="template4_recipient_emp_id.emp_job_title",string='Professional Title')
    template4_sender_emp_id = fields.Many2one('hr.employee','2nd Application form Sender Employee')
    template4_sender_title = fields.Char(related="template4_sender_emp_id.emp_title",string='Title')
    template4_sender_professional_title = fields.Char(related="template4_sender_emp_id.emp_job_title",string='Professional Title')
    template4_employee_ids = fields.Many2many('hr.employee','rel_template4_employee_income_invoice','sender_id','emp_id','2nd Application EMPLOYEES COPIED')

    template5 = fields.Selection([('format_remission_20','Format remission 20%')],string="Template")
    template5_recipient_emp_id = fields.Many2one('hr.employee','Format remission Recipient Employee')
    template5_recipient_title = fields.Char(related="template5_recipient_emp_id.emp_title",string='Title')
    template5_recipient_professional_title = fields.Char(related="template5_recipient_emp_id.emp_job_title",string='Professional Title')
    template5_sender_emp_id = fields.Many2one('hr.employee','Format remission Sender Employee')
    template5_sender_title = fields.Char(related="template5_sender_emp_id.emp_title",string='Title')
    template5_sender_professional_title = fields.Char(related="template5_sender_emp_id.emp_job_title",string='Professional Title')
    template5_employee_ids = fields.Many2many('hr.employee','rel_template5_employee_income_invoice','sender_id','emp_id','Format remission EMPLOYEES COPIED')

    template6 = fields.Selection([('reporting_format_returned_check','Reporting format returned check')],string="Template")
    template6_recipient_emp_id = fields.Many2one('hr.employee','Reporting format Recipient Employee')
    template6_recipient_title = fields.Char(related="template6_recipient_emp_id.emp_title",string='Title')
    template6_recipient_professional_title = fields.Char(related="template6_recipient_emp_id.emp_job_title",string='Professional Title')
    template6_sender_emp_id = fields.Many2one('hr.employee','Reporting format Sender Employee')
    template6_sender_title = fields.Char(related="template6_sender_emp_id.emp_title",string='Title')
    template6_sender_professional_title = fields.Char(related="template6_sender_emp_id.emp_job_title",string='Professional Title')
    template6_employee_ids = fields.Many2many('hr.employee','rel_template6_employee_income_invoice','sender_id','emp_id','Reporting format EMPLOYEES COPIED')
    
    #===================================================#
    
    income_invoice_line_ids = fields.One2many('income.invoice.move.line','move_id',string="Income Invoice Lines")
    income_invoice_trades_dgoae = fields.One2many('income.invoice.move.line','move_id',string="Income Type Reference")
    income_invoice_billing = fields.One2many('income.invoice.move.line','move_id',string="Income Billing")
    income_invoice_billing_return_checked = fields.One2many('income.invoice.move.line','move_id',string="Income Billing Return Checked")
    income_invoice_deposit_manual = fields.One2many('income.invoice.move.line','move_id',string="Income Billing Return Checked")
    income_invoice_deposit_automatic = fields.One2many('income.invoice.move.line','move_id',string="Income Billing Return Checked")
    

    @api.onchange('type_of_revenue_collection')
    def _onchange_type_of_revenue_collection_set(self):
        self.returned_check = False
        self.record_type = False
    
    @api.onchange('type_of_revenue_collection','returned_check','record_type')
    def _onchange_type_of_revenue_collection(self):
        self.income_invoice_billing = False
        self.income_invoice_trades_dgoae = False
        self.income_invoice_line_ids = False
        self.income_invoice_billing_return_checked = False
        self.income_invoice_deposit_manual = False
        self.income_invoice_deposit_automatic = False
        self.invoice_line_ids = False
        self.line_ids = False

    
    @api.onchange('income_invoice_deposit_manual')
    def _onchange_income_invoice_deposit_manual(self):
        self.create_income_invoice_line_ids(self.income_invoice_deposit_manual)

    @api.onchange('income_invoice_deposit_automatic')
    def _onchange_income_invoice_deposit_automatic(self):
        self.create_income_invoice_line_ids(self.income_invoice_deposit_automatic)
        
    @api.onchange('income_invoice_billing_return_checked')
    def _onchange_income_invoice_billing_return_checked(self):
        self.create_income_invoice_line_ids(self.income_invoice_billing_return_checked)
        
    @api.onchange('income_invoice_billing')
    def _onchange_income_invoice_billing(self):
        self.create_income_invoice_line_ids(self.income_invoice_billing)
        
    @api.onchange('income_invoice_trades_dgoae')
    def _onchange_income_invoice_trades_dgoae(self):
        self.create_income_invoice_line_ids(self.income_invoice_trades_dgoae)
        
    @api.onchange('income_invoice_line_ids')
    def _onchange_income_invoice_line_ids(self):
        self.create_income_invoice_line_ids(self.income_invoice_line_ids)
        
    def create_income_invoice_line_ids(self,lines):
        invoice_line = []
        for line in lines:
            if line.account_ie_id and line.account_ie_id.ie_account_line_ids:
                total_line_pr = sum(x.percentage for x in line.account_ie_id.ie_account_line_ids)
                if total_line_pr != 100:
                    raise ValidationError(_('Please configure IE Accounts 100% Percentage'))
                for account_line in line.account_ie_id.ie_account_line_ids.filtered(lambda x:x.percentage > 0):
                    price_per = (line.price_unit*account_line.percentage)/100 
                    line_vals = {
                                    'product_id':line.product_id and line.product_id.id or False,
                                    'name' : line.name,
                                    'account_id' : account_line.account_id and account_line.account_id.id or False,
                                    'price_unit' : price_per,   
                                    'exclude_from_invoice_tab' : False,
                                    'quantity' : line.quantity,
                                    'income_line_id' : line.id,
                                    'account_ie_id' : line.account_ie_id,
                                    'discount' : line.discount,
                                    'currency_id' : line.currency_id and line.currency_id.id or False,
                                    'partner_id' : line.partner_id and line.partner_id.id or False,
                                    'product_uom_id' : line.product_uom_id and line.product_uom_id.id or False,
                                    'tax_ids' : line.tax_ids and line.tax_ids.ids or False,
                                    'unidentified_product' : line.unidentified_product,
                                    'income_sub_account' : line.income_sub_account,
                                    'income_sub_subaccount' : line.income_sub_subaccount,
                                    'ddi_office_accounting' : line.ddi_office_accounting,
                                    'amount_of_check' : line.amount_of_check,
                                    'deposit_for_check_recovery' : line.deposit_for_check_recovery,
                                    'cfdi_20' : line.cfdi_20,
                                    'program_code_id' : line.program_code_id and line.program_code_id.id or False,
                                    'fixed_discount' : line.fixed_discount,
                                } 
                    invoice_line.append((0,0,line_vals))
                                        
            else:
                line_vals = {
                                'product_id':line.product_id and line.product_id.id or False,
                                'name' : line.name,
                                'account_id' : line.account_id and line.account_id.id or False,
                                'price_unit' : line.price_unit,   
                                'exclude_from_invoice_tab' : False,
                                'quantity' : line.quantity,
                                'income_line_id' : line.id,
                                'account_ie_id' : line.account_ie_id and line.account_ie_id.id or False,
                                'discount' : line.discount,
                                'currency_id' : line.currency_id and line.currency_id.id or False,
                                'partner_id' : line.partner_id and line.partner_id.id or False,
                                'product_uom_id' : line.product_uom_id and line.product_uom_id.id or False,
                                'tax_ids' : line.tax_ids and line.tax_ids.ids or False,
                                'unidentified_product' : line.unidentified_product,
                                'income_sub_account' : line.income_sub_account,
                                'income_sub_subaccount' : line.income_sub_subaccount,
                                'ddi_office_accounting' : line.ddi_office_accounting,
                                'amount_of_check' : line.amount_of_check,
                                'deposit_for_check_recovery' : line.deposit_for_check_recovery,
                                'cfdi_20' : line.cfdi_20,
                                'program_code_id' : line.program_code_id and line.program_code_id.id or False,
                                'fixed_discount' : line.fixed_discount,
                            } 
                
                invoice_line.append((0,0,line_vals))
            
        self.invoice_line_ids = False
        self.invoice_line_ids = invoice_line
        self.invoice_line_ids._onchange_price_subtotal()
        self._onchange_invoice_line_ids()
        
        
    @api.depends('type_of_revenue_collection','returned_check')
    def show_trade_no(self):
        for rec in self:
            is_show_trade_no = False
            if rec.returned_check:
                is_show_trade_no = True
            elif rec.type_of_revenue_collection and rec.type_of_revenue_collection == 'dgoae_trades':
                is_show_trade_no = True
            rec.is_show_trade_no = is_show_trade_no 
            
    is_show_trade_no = fields.Boolean(string="Show Trade NO",compute="show_trade_no",store=True)
    
    @api.depends('income_type','state')
    def get_sub_origin_ids(self):
        for rec in self:
            if rec.income_type and rec.income_type == 'own':
                rec.sub_origin_ids = [(6,0,self.env['sub.origin.resource'].search([('resource_id.desc','=','income')]).ids)]
            else:
                rec.sub_origin_ids = [(6,0,self.env['sub.origin.resource'].search([('resource_id.desc','!=','income')]).ids)]
    
    @api.depends('income_bank_journal_id','income_bank_account')
    def get_hide_base_on_account(self):
        for rec in self:
            hide_base_on_account = True
            if rec.income_bank_account and rec.income_bank_account.acc_number == '444101001':
                hide_base_on_account = False
            rec.hide_base_on_account = hide_base_on_account
                
    @api.depends('adequacies_ids','record_type','type_of_revenue_collection','state')
    def get_hide_budget_refund(self):
        for record in self:
            is_hide_budget_refund = False
            if record.adequacies_ids:
                is_hide_budget_refund = True
            elif record.state != 'posted':
                is_hide_budget_refund = True
            elif record.record_type != 'manual' or record.type_of_revenue_collection != 'deposit_cer':
                is_hide_budget_refund = True
            record.is_hide_budget_refund = is_hide_budget_refund
            
    is_hide_budget_refund = fields.Boolean('Hide Budget Refund',compute='get_hide_budget_refund',store=True)
    
    @api.constrains('income_id')
    def _check_income_id(self):
        if self.income_id and not str(self.income_id).isnumeric():
            raise ValidationError(_('The ID must be numeric value'))

    @api.constrains('income_branch')
    def _check_income_branch(self):
        if self.income_branch and not str(self.income_branch).isnumeric():
            raise ValidationError(_('The Branch must be numeric value'))
    
 
    def action_budget_refund(self):
        liq_adequacy_jour = self.env.ref('jt_conac.liq_adequacy_jour')
        journal_id = False
        if liq_adequacy_jour:
            journal_id = liq_adequacy_jour.id

        seq_ids = self.env['ir.sequence'].search([('code', '=', 'adequacies.folio')], order='company_id')
        number_next = 0
        if seq_ids:
            number_next = seq_ids[0].number_next_actual 

        return {
            'name': _('Liquid Adjustments'),
            'res_model': 'liquid.adjustments.manual.deposite',
            'view_mode': 'form',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context' : {'default_journal_id' : journal_id,'default_folio':number_next,'default_move_id':self.id}
        }
    def get_related_journal(self,journal_id,type_of_revenue_collection):
        if type_of_revenue_collection == 'billing':
            journal_id = self.env.ref('jt_income.income_billing')
        elif type_of_revenue_collection == 'deposit_cer':
            journal_id = self.env.ref('jt_income.income_certificate_of_deposit') 
        elif type_of_revenue_collection == 'dgae_ref':
            journal_id = self.env.ref('jt_income.income_reference_DGAE') 
        elif type_of_revenue_collection == 'dgoae_trades':
            journal_id = self.env.ref('jt_income.income_trades_DGOAE') 
        
        journal_id = journal_id and journal_id.id or False
        return journal_id
    
    @api.onchange('type_of_revenue_collection')
    def onchange_type_of_revenue_collection(self):
        if self.type_of_revenue_collection:
            self.journal_id = self.get_related_journal(self.journal_id, self.type_of_revenue_collection)

    def get_line_accounts_for_report(self):
        accout_name = False
        account_ids = self.invoice_line_ids.mapped('account_id')
        for account in account_ids:
            if accout_name:
                accout_name += ","+account.code
            else:
                accout_name =account.code
                
        if accout_name:
            return accout_name
        else:
            return ''
        
    def get_all_employee(self,template):
        sender_template = self.env['sender.recipient.trades'].search([('template','=',template)],limit=1)
        return sender_template

    def number_of_return_check_char(self):
        if self.number_of_returned_check:
            return str(self.number_of_returned_check)
        else:
            return ''
        
    def get_my_amount_to_text(self,amount):
        split_num = str(amount).split('.')
        int_part = int(split_num[0])         
        amount_to_words = self.currency_id.amount_to_text(int_part)
        return amount_to_words.upper()

    def get_my_amount_to_text_decimal(self,amount):
        split_num = str(amount).split('.')
        print ("Decimal===",split_num[1])
        decimal_part = split_num[1]
        if len(decimal_part)==1:
            decimal_part +="0"
        decimal_part = decimal_part+"/100 M.N" 
        return decimal_part
        
    def get_invoice_date_in_pdf(self):
        invoice_date = ''
        if self.invoice_date:
            month_name = format_datetime(self.invoice_date, 'MMMM', locale=get_lang(self.env).code)
            dateyear = self.invoice_date.strftime('%Y')
            dateday = self.invoice_date.strftime('%d')
            if self.env.user.lang == 'es_MX':
                if self.invoice_date.month==1:
                    month_name = 'Enero'
                elif self.invoice_date.month==2:
                    month_name = 'Febrero'
                elif self.invoice_date.month==3:
                    month_name = 'Marzo'
                elif self.invoice_date.month==4:
                    month_name = 'Abril'
                elif self.invoice_date.month==5:
                    month_name = 'Mayo'
                elif self.invoice_date.month==6:
                    month_name = 'Junio'
                elif self.invoice_date.month==7:
                    month_name = 'Julio'
                elif self.invoice_date.month==8:
                    month_name = 'Agosto'
                elif self.invoice_date.month==9:
                    month_name = 'Septiembre'
                elif self.invoice_date.month==10:
                    month_name = 'Octubre'
                elif self.invoice_date.month==11:
                    month_name = 'Noviembre'
                elif self.invoice_date.month==12:
                    month_name = 'Diciembre'
            
            invoice_date = str(dateday) + " de " + month_name + " de " + str(dateyear)
            
        return invoice_date

    def set_pdf_remplate_data(self,records):
        for res in records:
            if res.type_of_revenue_collection == 'billing' and res.returned_check:
                sender_template_1 = self.env['sender.recipient.trades'].search([('template','=','application_form_20')],limit=1)
                if sender_template_1:
                        res.template1 = 'application_form_20'
                        res.template1_recipient_emp_id = sender_template_1.recipient_emp_id and sender_template_1.recipient_emp_id.id or False
                        res.template1_sender_emp_id = sender_template_1.sender_emp_id and sender_template_1.sender_emp_id.id or False,
                        res.template1_employee_ids = [(6,0,sender_template_1.employee_ids.ids)]

                sender_template_1 = self.env['sender.recipient.trades'].search([('template','=','format_forgiveness')],limit=1)
                if sender_template_1:
                        res.template2 = 'format_forgiveness'
                        res.template2_recipient_emp_id = sender_template_1.recipient_emp_id and sender_template_1.recipient_emp_id.id or False
                        res.template2_sender_emp_id = sender_template_1.sender_emp_id and sender_template_1.sender_emp_id.id or False,
                        res.template2_employee_ids = [(6,0,sender_template_1.employee_ids.ids)]

                sender_template_1 = self.env['sender.recipient.trades'].search([('template','=','format_notice_change')],limit=1)
                if sender_template_1:
                        res.template3 = 'format_notice_change'
                        res.template3_recipient_emp_id = sender_template_1.recipient_emp_id and sender_template_1.recipient_emp_id.id or False
                        res.template3_sender_emp_id = sender_template_1.sender_emp_id and sender_template_1.sender_emp_id.id or False,
                        res.template3_employee_ids = [(6,0,sender_template_1.employee_ids.ids)]

                sender_template_1 = self.env['sender.recipient.trades'].search([('template','=','2nd application_form_20')],limit=1)
                if sender_template_1:
                        res.template4 = '2nd application_form_20'
                        res.template4_recipient_emp_id = sender_template_1.recipient_emp_id and sender_template_1.recipient_emp_id.id or False
                        res.template4_sender_emp_id = sender_template_1.sender_emp_id and sender_template_1.sender_emp_id.id or False,
                        res.template4_employee_ids = [(6,0,sender_template_1.employee_ids.ids)]

                sender_template_1 = self.env['sender.recipient.trades'].search([('template','=','format_remission_20')],limit=1)
                if sender_template_1:
                        res.template5 = 'format_remission_20'
                        res.template5_recipient_emp_id = sender_template_1.recipient_emp_id and sender_template_1.recipient_emp_id.id or False
                        res.template5_sender_emp_id = sender_template_1.sender_emp_id and sender_template_1.sender_emp_id.id or False,
                        res.template5_employee_ids = [(6,0,sender_template_1.employee_ids.ids)]

                sender_template_1 = self.env['sender.recipient.trades'].search([('template','=','reporting_format_returned_check')],limit=1)
                if sender_template_1:
                        res.template6 = 'reporting_format_returned_check'
                        res.template6_recipient_emp_id = sender_template_1.recipient_emp_id and sender_template_1.recipient_emp_id.id or False
                        res.template6_sender_emp_id = sender_template_1.sender_emp_id and sender_template_1.sender_emp_id.id or False,
                        res.template6_employee_ids = [(6,0,sender_template_1.employee_ids.ids)]
                        
    @api.model_create_multi
    def create(self, vals_list):
        result = super(Invoice, self).create(vals_list)
        self.set_pdf_remplate_data(result)
        for rec in result:
            if rec.type_of_revenue_collection and rec.type=='out_invoice':
                rec._onchange_income_invoice_line_ids()
                rec._onchange_income_invoice_deposit_manual()
                rec._onchange_income_invoice_deposit_automatic()
                rec._onchange_income_invoice_billing_return_checked()
                rec._onchange_income_invoice_billing()
                rec._onchange_income_invoice_trades_dgoae()
            
            
            if rec.type_of_revenue_collection=='deposit_cer' and rec.record_type=='manual' and rec.income_bank_journal_id:
                if not rec.income_bank_journal_id.default_debit_account_id:
                    if self.env.user.lang == 'es_MX':
                        raise ValidationError(_("Configure la cuenta de débito predeterminada del Banco %s")%(rec.income_bank_journal_id.name))
                    else:
                        raise ValidationError(_("Please Configure Default Debit Account of Bank %s")%(rec.income_bank_journal_id.name))                
                else:
                    if any(rec.invoice_line_ids.filtered(lambda x:not x.program_code_id and x.account_ie_id)):
                        for line in rec.line_ids.filtered(lambda x:x.account_id and x.debit != 0):
                            if line.account_id.user_type_id.type == 'receivable' and line.debit != 0:
                                line.account_id = False
                                line.account_id = rec.income_bank_journal_id.default_debit_account_id.id
        return result
    
    def write(self,vals):
        result = super(Invoice, self).write(vals)
        if vals.get('returned_check'):
            self.set_pdf_remplate_data(self)
        if vals.get('type_of_revenue_collection',False) or vals.get('record_type',False) or vals.get('income_bank_journal_id',False) or vals.get('line_ids',False):
            for rec in self:
                if rec.type_of_revenue_collection=='deposit_cer' and rec.record_type=='manual' and rec.income_bank_journal_id:
                    if not rec.income_bank_journal_id.default_debit_account_id:
                        if self.env.user.lang == 'es_MX':
                            raise ValidationError(_("Configure la cuenta de débito predeterminada del Banco %s")%(rec.income_bank_journal_id.name))
                        else:
                            raise ValidationError(_("Please Configure Default Debit Account of Bank %s")%(rec.income_bank_journal_id.name))                
                    else:
                        if any(rec.invoice_line_ids.filtered(lambda x:not x.program_code_id and x.account_ie_id)):                                            
                            for line in rec.line_ids.filtered(lambda x:x.account_id and x.debit != 0):
                                if line.debit != 0:
                                    line.account_id = False
                                    line.account_id = rec.income_bank_journal_id.default_debit_account_id.id
            
        return result

    def _recompute_tax_lines(self, recompute_tax_base_amount=False):
        ''' Compute the dynamic tax lines of the journal entry.

        :param lines_map: The line_ids dispatched by type containing:
            * base_lines: The lines having a tax_ids set.
            * tax_lines: The lines having a tax_line_id set.
            * terms_lines: The lines generated by the payment terms of the invoice.
            * rounding_lines: The cash rounding lines of the invoice.
        '''
        self.ensure_one()
        in_draft_mode = self != self._origin

        def _serialize_tax_grouping_key(grouping_dict):
            ''' Serialize the dictionary values to be used in the taxes_map.
            :param grouping_dict: The values returned by '_get_tax_grouping_key_from_tax_line' or '_get_tax_grouping_key_from_base_line'.
            :return: A string representing the values.
            '''
            return '-'.join(str(v) for v in grouping_dict.values())

        def _compute_base_line_taxes(base_line):
            ''' Compute taxes amounts both in company currency / foreign currency as the ratio between
            amount_currency & balance could not be the same as the expected currency rate.
            The 'amount_currency' value will be set on compute_all(...)['taxes'] in multi-currency.
            :param base_line:   The account.move.line owning the taxes.
            :return:            The result of the compute_all method.
            '''
            move = base_line.move_id

            if move.is_invoice(include_receipts=True):
                sign = -1 if move.is_inbound() else 1
                quantity = base_line.quantity
                if base_line.currency_id:
                    price_unit_foreign_curr = sign * base_line.price_unit * (1 - (base_line.discount / 100.0))
                    price_unit_foreign_curr = price_unit_foreign_curr - base_line.fixed_discount + base_line.other_amounts
                    price_unit_comp_curr = base_line.currency_id._convert(price_unit_foreign_curr, move.company_id.currency_id, move.company_id, move.date)
                else:
                    price_unit_foreign_curr = 0.0
                    price_unit_comp_curr = sign * base_line.price_unit * (1 - (base_line.discount / 100.0))
                    price_unit_comp_curr = price_unit_comp_curr - base_line.fixed_discount + base_line.other_amounts
            else:
                quantity = 1.0
                price_unit_foreign_curr = base_line.amount_currency
                price_unit_comp_curr = base_line.balance

            if move.is_invoice(include_receipts=True):
                handle_price_include = True
            else:
                handle_price_include = False

            balance_taxes_res = base_line.tax_ids._origin.compute_all(
                price_unit_comp_curr,
                currency=base_line.company_currency_id,
                quantity=quantity,
                product=base_line.product_id,
                partner=base_line.partner_id,
                is_refund=self.type in ('out_refund', 'in_refund'),
                handle_price_include=handle_price_include,
            )

            if base_line.currency_id:
                # Multi-currencies mode: Taxes are computed both in company's currency / foreign currency.
                amount_currency_taxes_res = base_line.tax_ids._origin.compute_all(
                    price_unit_foreign_curr,
                    currency=base_line.currency_id,
                    quantity=quantity,
                    product=base_line.product_id,
                    partner=base_line.partner_id,
                    is_refund=self.type in ('out_refund', 'in_refund'),
                )
                for b_tax_res, ac_tax_res in zip(balance_taxes_res['taxes'], amount_currency_taxes_res['taxes']):
                    tax = self.env['account.tax'].browse(b_tax_res['id'])
                    b_tax_res['amount_currency'] = ac_tax_res['amount']

                    # A tax having a fixed amount must be converted into the company currency when dealing with a
                    # foreign currency.
                    if tax.amount_type == 'fixed':
                        b_tax_res['amount'] = base_line.currency_id._convert(b_tax_res['amount'], move.company_id.currency_id, move.company_id, move.date)

            return balance_taxes_res

        taxes_map = {}

        # ==== Add tax lines ====
        to_remove = self.env['account.move.line']
        for line in self.line_ids.filtered('tax_repartition_line_id'):
            grouping_dict = self._get_tax_grouping_key_from_tax_line(line)
            grouping_key = _serialize_tax_grouping_key(grouping_dict)
            if grouping_key in taxes_map:
                # A line with the same key does already exist, we only need one
                # to modify it; we have to drop this one.
                to_remove += line
            else:
                taxes_map[grouping_key] = {
                    'tax_line': line,
                    'balance': 0.0,
                    'amount_currency': 0.0,
                    'tax_base_amount': 0.0,
                    'grouping_dict': False,
                }
        self.line_ids -= to_remove

        # ==== Mount base lines ====
        for line in self.line_ids.filtered(lambda line: not line.tax_repartition_line_id):
            # Don't call compute_all if there is no tax.
            if not line.tax_ids:
                line.tag_ids = [(5, 0, 0)]
                continue

            compute_all_vals = _compute_base_line_taxes(line)

            # Assign tags on base line
            line.tag_ids = compute_all_vals['base_tags']

            tax_exigible = True
            for tax_vals in compute_all_vals['taxes']:
                grouping_dict = self._get_tax_grouping_key_from_base_line(line, tax_vals)
                grouping_key = _serialize_tax_grouping_key(grouping_dict)

                tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_vals['tax_repartition_line_id'])
                tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id

                if tax.tax_exigibility == 'on_payment':
                    tax_exigible = False

                taxes_map_entry = taxes_map.setdefault(grouping_key, {
                    'tax_line': None,
                    'balance': 0.0,
                    'amount_currency': 0.0,
                    'tax_base_amount': 0.0,
                    'grouping_dict': False,
                })
                taxes_map_entry['balance'] += tax_vals['amount']
                taxes_map_entry['amount_currency'] += tax_vals.get('amount_currency', 0.0)
                taxes_map_entry['tax_base_amount'] += tax_vals['base']
                taxes_map_entry['grouping_dict'] = grouping_dict
            line.tax_exigible = tax_exigible

        # ==== Process taxes_map ====
        for taxes_map_entry in taxes_map.values():
            # Don't create tax lines with zero balance.
            if self.currency_id.is_zero(taxes_map_entry['balance']) and self.currency_id.is_zero(taxes_map_entry['amount_currency']):
                taxes_map_entry['grouping_dict'] = False

            tax_line = taxes_map_entry['tax_line']
            tax_base_amount = -taxes_map_entry['tax_base_amount'] if self.is_inbound() else taxes_map_entry['tax_base_amount']

            if not tax_line and not taxes_map_entry['grouping_dict']:
                continue
            elif tax_line and recompute_tax_base_amount:
                tax_line.tax_base_amount = tax_base_amount
            elif tax_line and not taxes_map_entry['grouping_dict']:
                # The tax line is no longer used, drop it.
                self.line_ids -= tax_line
            elif tax_line:
                tax_line.update({
                    'amount_currency': taxes_map_entry['amount_currency'],
                    'debit': taxes_map_entry['balance'] > 0.0 and taxes_map_entry['balance'] or 0.0,
                    'credit': taxes_map_entry['balance'] < 0.0 and -taxes_map_entry['balance'] or 0.0,
                    'tax_base_amount': tax_base_amount,
                })
            else:
                create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
                tax_repartition_line_id = taxes_map_entry['grouping_dict']['tax_repartition_line_id']
                tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_repartition_line_id)
                tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id
                tax_line = create_method({
                    'name': tax.name,
                    'move_id': self.id,
                    'partner_id': line.partner_id.id,
                    'company_id': line.company_id.id,
                    'company_currency_id': line.company_currency_id.id,
                    'quantity': 1.0,
                    'date_maturity': False,
                    'amount_currency': taxes_map_entry['amount_currency'],
                    'debit': taxes_map_entry['balance'] > 0.0 and taxes_map_entry['balance'] or 0.0,
                    'credit': taxes_map_entry['balance'] < 0.0 and -taxes_map_entry['balance'] or 0.0,
                    'tax_base_amount': tax_base_amount,
                    'exclude_from_invoice_tab': True,
                    'tax_exigible': tax.tax_exigibility == 'on_invoice',
                    **taxes_map_entry['grouping_dict'],
                })

            if in_draft_mode:
                tax_line._onchange_amount_currency()
                tax_line._onchange_balance()
        
class AccountMoveLine(models.Model):
    
    _inherit = 'account.move.line'
    
    @api.depends('product_id')
    def count_sub_produts(self):
        for record in self:
            if record.product_id and record.product_id.sub_product:
                record.subproduct_count = record.product_id.default_code
            else:
                record.subproduct_count = ''
        
    subproduct_count = fields.Char('Subproduct',compute="count_sub_produts",store=True)
    unidentified_product = fields.Integer('Unidentified product')
    income_sub_account = fields.Char("Income Sub-account")
    income_sub_subaccount = fields.Char("Income Sub-subaccount")
    ddi_office_accounting = fields.Char("Official DDI to the General Accounting Office")
    amount_of_check = fields.Float("Amount of the check")
    deposit_for_check_recovery = fields.Char("Deposit for check recovery")
    cfdi_20 = fields.Char("CFDI 20%")
    account_ie_id = fields.Many2one('association.distribution.ie.accounts','Account I.E.')
    income_line_id = fields.Many2one("income.invoice.move.line",'Income Line')
    l10n_mx_edi_product_code_sat_id = fields.Many2one(related="product_id.l10n_mx_edi_code_sat_id",
                                                      string="Key Product SAT")
    l10n_mx_edi_uom_code_sat_id = fields.Many2one(related="product_uom_id.l10n_mx_edi_code_sat_id",
                                                  string="SAT Key Unit")
    fixed_discount = fields.Float('Discount')

    @api.model_create_multi
    def create(self, vals_list):
        lines = super(AccountMoveLine, self).create(vals_list)
        for line in lines:
            if line.other_amounts:
                line.price_unit -= line.other_amounts 
        return lines
    
    def get_account_list(self):
        for rec in self:
            if rec.product_id:
                rec.account_ie_ids = [(6,0,rec.product_id.ie_account_id.ids)]
            else:
                ie_acount_ids = self.env['association.distribution.ie.accounts'].search([])
                rec.account_ie_ids = [(6,0,ie_acount_ids.ids)]
    account_ie_ids = fields.Many2many('association.distribution.ie.accounts','ie_account_move_line','line_id','ie_id',compute="get_account_list")
    
    @api.onchange('product_id')
    def get_ie_accounts_ids(self):
        self.get_account_list()

    @api.onchange('quantity','fixed_discount' ,'discount', 'price_unit', 'tax_ids','other_amounts')
    def _onchange_price_subtotal(self):
        for line in self:
            if not line.move_id.is_invoice(include_receipts=True):
                continue

            line.update(line._get_price_total_and_subtotal())
            line.update(line._get_fields_onchange_subtotal())



    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes, move_type):
        ''' This method is used to compute 'price_total' & 'price_subtotal'.

        :param price_unit:  The current price unit.
        :param quantity:    The current quantity.
        :param discount:    The current discount.
        :param currency:    The line's currency.
        :param product:     The line's product.
        :param partner:     The line's partner.
        :param taxes:       The applied taxes.
        :param move_type:   The type of the move.
        :return:            A dictionary containing 'price_subtotal' & 'price_total'.
        '''
        res = {}
        
        # Compute 'price_subtotal'.
        
        price_unit_wo_discount = price_unit * (1 - (discount / 100.0))
        if self and self[0].fixed_discount:
            price_unit_wo_discount = price_unit - self[0].fixed_discount 

        if self and self[0].other_amounts and quantity:
            price_unit_wo_discount  += self[0].other_amounts/quantity
        
        subtotal = quantity * price_unit_wo_discount
        # Compute 'price_total'.
        if taxes:
            taxes_res = taxes._origin.compute_all(price_unit_wo_discount,
                quantity=quantity, currency=currency, product=product, partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))
            res['price_subtotal'] = taxes_res['total_excluded']
            res['price_total'] = taxes_res['total_included']
        else:
            res['price_total'] = res['price_subtotal'] = subtotal
        #In case of multi currency, round before it's use for computing debit credit
        if currency:
            res = {k: currency.round(v) for k, v in res.items()}
        return res
        
class IncomeIncomeMoveLine(models.Model):
    
    _name = 'income.invoice.move.line'

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------

    @api.depends('currency_id')
    def _compute_always_set_currency_id(self):
        for line in self:
            line.always_set_currency_id = line.currency_id or line.company_currency_id

    @api.depends('debit', 'credit')
    def _compute_balance(self):
        for line in self:
            line.balance = line.debit - line.credit

    @api.depends('debit', 'credit', 'account_id', 'amount_currency', 'currency_id', 'matched_debit_ids', 'matched_credit_ids', 'matched_debit_ids.amount', 'matched_credit_ids.amount', 'move_id.state', 'company_id')
    def _amount_residual(self):
        """ Computes the residual amount of a move line from a reconcilable account in the company currency and the line's currency.
            This amount will be 0 for fully reconciled lines or lines from a non-reconcilable account, the original line amount
            for unreconciled lines, and something in-between for partially reconciled lines.
        """
        for line in self:
            if not line.account_id.reconcile and line.account_id.internal_type != 'liquidity':
                line.reconciled = False
                line.amount_residual = 0
                line.amount_residual_currency = 0
                continue
            #amounts in the partial reconcile table aren't signed, so we need to use abs()
            amount = abs(line.debit - line.credit)
            amount_residual_currency = abs(line.amount_currency) or 0.0
            sign = 1 if (line.debit - line.credit) > 0 else -1
            if not line.debit and not line.credit and line.amount_currency and line.currency_id:
                #residual for exchange rate entries
                sign = 1 if float_compare(line.amount_currency, 0, precision_rounding=line.currency_id.rounding) == 1 else -1

            for partial_line in (line.matched_debit_ids + line.matched_credit_ids):
                # If line is a credit (sign = -1) we:
                #  - subtract matched_debit_ids (partial_line.credit_move_id == line)
                #  - add matched_credit_ids (partial_line.credit_move_id != line)
                # If line is a debit (sign = 1), do the opposite.
                sign_partial_line = sign if partial_line.credit_move_id == line else (-1 * sign)

                amount += sign_partial_line * partial_line.amount
                #getting the date of the matched item to compute the amount_residual in currency
                if line.currency_id and line.amount_currency:
                    if partial_line.currency_id and partial_line.currency_id == line.currency_id:
                        amount_residual_currency += sign_partial_line * partial_line.amount_currency
                    else:
                        if line.balance and line.amount_currency:
                            rate = line.amount_currency / line.balance
                        else:
                            date = partial_line.credit_move_id.date if partial_line.debit_move_id == line else partial_line.debit_move_id.date
                            rate = line.currency_id.with_context(date=date).rate
                        amount_residual_currency += sign_partial_line * line.currency_id.round(partial_line.amount * rate)

            #computing the `reconciled` field.
            reconciled = False
            digits_rounding_precision = line.move_id.company_id.currency_id.rounding
            if float_is_zero(amount, precision_rounding=digits_rounding_precision):
                if line.currency_id and line.amount_currency:
                    if float_is_zero(amount_residual_currency, precision_rounding=line.currency_id.rounding):
                        reconciled = True
                else:
                    reconciled = True
            line.reconciled = reconciled

            line.amount_residual = line.move_id.company_id.currency_id.round(amount * sign) if line.move_id.company_id else amount * sign
            line.amount_residual_currency = line.currency_id and line.currency_id.round(amount_residual_currency * sign) or 0.0

    @api.depends('tax_repartition_line_id.invoice_tax_id', 'tax_repartition_line_id.refund_tax_id')
    def _compute_tax_line_id(self):
        """ tax_line_id is computed as the tax linked to the repartition line creating
        the move.
        """
        for record in self:
            rep_line = record.tax_repartition_line_id
            # A constraint on account.tax.repartition.line ensures both those fields are mutually exclusive
            record.tax_line_id = rep_line.invoice_tax_id or rep_line.refund_tax_id

    @api.depends('tag_ids', 'debit', 'credit')
    def _compute_tax_audit(self):
        separator = '        '

        for record in self:
            currency = record.company_id.currency_id
            audit_str = ''
            for tag in record.tag_ids:

                caba_origin_inv_type = record.move_id.type
                caba_origin_inv_journal_type = record.journal_id.type

                if record.move_id.tax_cash_basis_rec_id:
                    # Cash basis entries are always treated as misc operations, applying the tag sign directly to the balance
                    type_multiplicator = 1
                else:
                    type_multiplicator = (record.journal_id.type == 'sale' and -1 or 1) * (record.move_id.type in ('in_refund', 'out_refund') and -1 or 1)

                tag_amount = type_multiplicator * (tag.tax_negate and -1 or 1) * record.balance

                if tag.tax_report_line_ids:
                    #Then, the tag comes from a report line, and hence has a + or - sign (also in its name)
                    for report_line in tag.tax_report_line_ids:
                        audit_str += separator if audit_str else ''
                        audit_str += report_line.tag_name + ': ' + formatLang(self.env, tag_amount, currency_obj=currency)
                else:
                    # Then, it's a financial tag (sign is always +, and never shown in tag name)
                    audit_str += separator if audit_str else ''
                    audit_str += tag.name + ': ' + formatLang(self.env, tag_amount, currency_obj=currency)

            record.tax_audit = audit_str

    
    @api.model
    def _get_default_account(self):
        account_id = self.env['account.account'].sudo().search([('code','=','120.001.001'),('internal_type','=','receivable'),('deprecated','=',False)],limit=1)
        if account_id:
            return account_id
        else:
            return False
        
    move_id = fields.Many2one('account.move', string='Journal Entry',
        index=True, required=True, readonly=True, auto_join=True, ondelete="cascade",
        help="The move of this entry line.")

    move_name = fields.Char(string='Number', related='move_id.name', store=True, index=True)
    date = fields.Date(related='move_id.date', store=True, readonly=True, index=True, copy=False, group_operator='min')
    ref = fields.Char(related='move_id.ref', store=True, copy=False, index=True, readonly=False)
    parent_state = fields.Selection(related='move_id.state', store=True, readonly=True)
    journal_id = fields.Many2one(related='move_id.journal_id', store=True, index=True, copy=False)
    company_id = fields.Many2one(related='move_id.company_id', store=True, readonly=True)
    company_currency_id = fields.Many2one(related='company_id.currency_id', string='Company Currency',
        readonly=True, store=True,
        help='Utility field to express amount currency')
    country_id = fields.Many2one(comodel_name='res.country', related='move_id.company_id.country_id')
    account_id = fields.Many2one('account.account', string='Account',
        index=True, ondelete="restrict", check_company=True,
        domain=[('deprecated', '=', False)],default=_get_default_account)
    account_internal_type = fields.Selection(related='account_id.user_type_id.type', string="Internal Type", store=True, readonly=True)
    account_root_id = fields.Many2one(related='account_id.root_id', string="Account Root", store=True, readonly=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Label')
    quantity = fields.Float(string='Quantity',
        default=1.0, digits='Product Unit of Measure',
        help="The optional quantity expressed by this line, eg: number of product sold. "
             "The quantity is not a legal requirement but is very useful for some reports.")
    price_unit = fields.Float(string='Unit Price', digits='Product Price')
    discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
    debit = fields.Monetary(string='Debit', default=0.0, currency_field='company_currency_id')
    credit = fields.Monetary(string='Credit', default=0.0, currency_field='company_currency_id')
    balance = fields.Monetary(string='Balance', store=True,
        currency_field='company_currency_id',
        compute='_compute_balance',
        help="Technical field holding the debit - credit in order to open meaningful graph views from reports")
    amount_currency = fields.Monetary(string='Amount in Currency', store=True, copy=True,
        help="The amount expressed in an optional other currency if it is a multi-currency entry.")
    price_subtotal = fields.Monetary(string='Subtotal', store=True, readonly=True,
        currency_field='always_set_currency_id')
    price_total = fields.Monetary(string='Total', store=True, readonly=True,
        currency_field='always_set_currency_id')
    reconciled = fields.Boolean(compute='_amount_residual', store=True)
    blocked = fields.Boolean(string='No Follow-up', default=False,
        help="You can check this box to mark this journal item as a litigation with the associated partner")
    date_maturity = fields.Date(string='Due Date', index=True,
        help="This field is used for payable and receivable journal entries. You can put the limit date for the payment of this line.")
    currency_id = fields.Many2one('res.currency', string='Currency')
    partner_id = fields.Many2one('res.partner', string='Partner', ondelete='restrict')
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    product_id = fields.Many2one('product.product', string='Product')

    # ==== Origin fields ====
    reconcile_model_id = fields.Many2one('account.reconcile.model', string="Reconciliation Model", copy=False, readonly=True)
    payment_id = fields.Many2one('account.payment', string="Originator Payment", copy=False,
        help="Payment that created this entry")
    statement_line_id = fields.Many2one('account.bank.statement.line',
        string='Bank statement line reconciled with this entry',
        index=True, copy=False, readonly=True)
    statement_id = fields.Many2one(related='statement_line_id.statement_id', store=True, index=True, copy=False,
        help="The bank statement used for bank reconciliation")

    # ==== Tax fields ====
    tax_ids = fields.Many2many('account.tax', string='Taxes', help="Taxes that apply on the base amount")
    tax_line_id = fields.Many2one('account.tax', string='Originator Tax', ondelete='restrict', store=True,
        compute='_compute_tax_line_id', help="Indicates that this journal item is a tax line")
    tax_group_id = fields.Many2one(related='tax_line_id.tax_group_id', string='Originator tax group',
        readonly=True, store=True,
        help='technical field for widget tax-group-custom-field')
    tax_base_amount = fields.Monetary(string="Base Amount", store=True, readonly=True,
        currency_field='company_currency_id')
    tax_exigible = fields.Boolean(string='Appears in VAT report', default=True, readonly=True,
        help="Technical field used to mark a tax line as exigible in the vat report or not (only exigible journal items"
             " are displayed). By default all new journal items are directly exigible, but with the feature cash_basis"
             " on taxes, some will become exigible only when the payment is recorded.")
    tax_repartition_line_id = fields.Many2one(comodel_name='account.tax.repartition.line',
        string="Originator Tax Repartition Line", ondelete='restrict', readonly=True,
        help="Tax repartition line that caused the creation of this move line, if any")
    tag_ids = fields.Many2many(string="Tags", comodel_name='account.account.tag', ondelete='restrict',
        help="Tags assigned to this line by the tax creating it, if any. It determines its impact on financial reports.")
    tax_audit = fields.Char(string="Tax Audit String", compute="_compute_tax_audit", store=True,
        help="Computed field, listing the tax grids impacted by this line, and the amount it applies to each of them.")

    # ==== Reconciliation fields ====
    amount_residual = fields.Monetary(string='Residual Amount', store=True,
        currency_field='company_currency_id',
        compute='_amount_residual',
        help="The residual amount on a journal item expressed in the company currency.")
    amount_residual_currency = fields.Monetary(string='Residual Amount in Currency', store=True,
        compute='_amount_residual',
        help="The residual amount on a journal item expressed in its currency (possibly not the company currency).")
    full_reconcile_id = fields.Many2one('account.full.reconcile', string="Matching #", copy=False, index=True, readonly=True)
    matched_debit_ids = fields.One2many('account.partial.reconcile', 'credit_move_id', string='Matched Debits',
        help='Debit journal items that are matched with this journal item.', readonly=True)
    matched_credit_ids = fields.One2many('account.partial.reconcile', 'debit_move_id', string='Matched Credits',
        help='Credit journal items that are matched with this journal item.', readonly=True)

    # ==== Analytic fields ====
    analytic_line_ids = fields.One2many('account.analytic.line', 'move_id', string='Analytic lines')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', index=True)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')

    # ==== Onchange / display purpose fields ====
    recompute_tax_line = fields.Boolean(store=False, readonly=True,
        help="Technical field used to know on which lines the taxes must be recomputed.")
    display_type = fields.Selection([
        ('line_section', 'Section'),
        ('line_note', 'Note'),
    ], default=False, help="Technical field for UX purpose.")
    is_rounding_line = fields.Boolean(help="Technical field used to retrieve the cash rounding line.")
    exclude_from_invoice_tab = fields.Boolean(help="Technical field used to exclude some lines from the invoice_line_ids tab in the form view.")
    always_set_currency_id = fields.Many2one('res.currency', string='Foreign Currency',
        compute='_compute_always_set_currency_id',
        help="Technical field used to compute the monetary field. As currency_id is not a required field, we need to use either the foreign currency, either the company one.")
    
    
    @api.depends('product_id')
    def count_sub_produts(self):
        for record in self:
            if record.product_id and record.product_id.sub_product:
                record.subproduct_count = record.product_id.default_code
            else:
                record.subproduct_count = ''
        
    subproduct_count = fields.Char('Subproduct',compute="count_sub_produts",store=True)
    unidentified_product = fields.Integer('Unidentified product')
    income_sub_account = fields.Char("Income Sub-account")
    income_sub_subaccount = fields.Char("Income Sub-subaccount")
    ddi_office_accounting = fields.Char("DDI Office to general accounting the")
    amount_of_check = fields.Float("Amount of the check")
    deposit_for_check_recovery = fields.Char("Deposit for check recovery")
    cfdi_20 = fields.Char("CFDI 20%")
    account_ie_id = fields.Many2one('association.distribution.ie.accounts','Account I.E.')
    program_code_id = fields.Many2one('program.code')
    move_line_ids = fields.One2many("account.move.line","income_line_id")
    l10n_mx_edi_product_code_sat_id = fields.Many2one("l10n_mx_edi.product.sat.code", string="SAT Code")
    l10n_mx_edi_uom_code_sat_id = fields.Many2one(related="product_uom_id.l10n_mx_edi_code_sat_id",string="SAT Key Unit")
    fixed_discount = fields.Float('Discount')
    
    @api.onchange('account_ie_id')
    def onchange_account_ie_id_name_set(self):
        if self.account_ie_id and self.move_id.record_type == 'manual':
            self.name = self.account_ie_id.desc
        
    def get_account_list(self):
        for rec in self:
            if rec.product_id:
                rec.account_ie_ids = [(6,0,rec.product_id.ie_account_id.ids)]
            else:
                ie_acount_ids = self.env['association.distribution.ie.accounts'].search([])
                rec.account_ie_ids = [(6,0,ie_acount_ids.ids)]
                
    account_ie_ids = fields.Many2many('association.distribution.ie.accounts','ie_account_income_move_line','line_id','ie_id',compute="get_account_list")

    def write(self,vals):
        res = super(IncomeIncomeMoveLine,self).write(vals)        
        for line in self:
            #print ("====",vals)
            #if not vals.get('price_subtotal'):
            price_subtotal = line._get_price_total_and_subtotal().get('price_subtotal', 0.0)
            to_write = {'price_subtotal':price_subtotal}
            res |= super(IncomeIncomeMoveLine, line).write(to_write)
        return res
    
    @api.model
    def create(self,vals):
        move = self.env['account.move'].browse(vals['move_id'])
        vals.setdefault('company_currency_id', move.company_id.currency_id.id) # important to bypass the ORM limitation where monetary fields are not rounded; more info in the commit message

        if move.is_invoice(include_receipts=True):
            currency = move.currency_id
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            taxes = self.resolve_2many_commands('tax_ids', vals.get('tax_ids', []), fields=['id'])
            tax_ids = set(tax['id'] for tax in taxes)
            taxes = self.env['account.tax'].browse(tax_ids)
            vals.update(self._get_price_total_and_subtotal_model(
                vals.get('price_unit', 0.0),
                vals.get('quantity', 0.0),
                vals.get('discount', 0.0),
                currency,
                self.env['product.product'].browse(vals.get('product_id')),
                partner,
                taxes,
                move.type,
            ))
            vals.update(self._get_fields_onchange_subtotal_model(
                vals['price_subtotal'],
                move.type,
                currency,
                move.company_id,
                move.date,
            ))
        
        res = super(IncomeIncomeMoveLine,self).create(vals)
        res._onchange_price_subtotal()
        res._get_fields_onchange_balance()
#         for line in self:
#             line.price_subtotal = line._get_price_total_and_subtotal().get('price_subtotal', 0.0)
        return res
    
    @api.model
    def default_get(self, default_fields):
        # OVERRIDE
        values = super(IncomeIncomeMoveLine, self).default_get(default_fields)

        if 'account_id' in default_fields \
            and (self._context.get('journal_id') or self._context.get('default_journal_id')) \
            and not values.get('account_id') \
            and self._context.get('default_type') in self.move_id.get_inbound_types():
            # Fill missing 'account_id'.
            journal = self.env['account.journal'].browse(self._context.get('default_journal_id') or self._context['journal_id'])
            values['account_id'] = journal.default_credit_account_id.id
        elif 'account_id' in default_fields \
            and (self._context.get('journal_id') or self._context.get('default_journal_id')) \
            and not values.get('account_id') \
            and self._context.get('default_type') in self.move_id.get_outbound_types():
            # Fill missing 'account_id'.
            journal = self.env['account.journal'].browse(self._context.get('default_journal_id') or self._context['journal_id'])
            values['account_id'] = journal.default_debit_account_id.id
        elif self._context.get('line_ids') and any(field_name in default_fields for field_name in ('debit', 'credit', 'account_id', 'partner_id')):
            move = self.env['account.move'].new({'line_ids': self._context['line_ids']})

            # Suggest default value for debit / credit to balance the journal entry.
            balance = sum(line['debit'] - line['credit'] for line in move.line_ids)
            # if we are here, line_ids is in context, so journal_id should also be.
            journal = self.env['account.journal'].browse(self._context.get('default_journal_id') or self._context['journal_id'])
            currency = journal.exists() and journal.company_id.currency_id
            if currency:
                balance = currency.round(balance)
            if balance < 0.0:
                values.update({'debit': -balance})
            if balance > 0.0:
                values.update({'credit': balance})

            # Suggest default value for 'partner_id'.
            if 'partner_id' in default_fields and not values.get('partner_id'):
                if len(move.line_ids[-2:]) == 2 and  move.line_ids[-1].partner_id == move.line_ids[-2].partner_id != False:
                    values['partner_id'] = move.line_ids[-2:].mapped('partner_id').id

            # Suggest default value for 'account_id'.
            if 'account_id' in default_fields and not values.get('account_id'):
                if len(move.line_ids[-2:]) == 2 and  move.line_ids[-1].account_id == move.line_ids[-2].account_id != False:
                    values['account_id'] = move.line_ids[-2:].mapped('account_id').id
        if values.get('display_type'):
            values.pop('account_id', None)
        return values

    @api.constrains('currency_id', 'account_id')
    def _check_account_currency(self):
        for line in self:
            account_currency = line.account_id.currency_id
            if account_currency and account_currency != line.company_currency_id and account_currency != line.currency_id:
                raise UserError(_('The account selected on your journal entry forces to provide a secondary currency. You should remove the secondary currency on the account.'))

    @api.constrains('account_id')
    def _check_constrains_account_id(self):
        for line in self.filtered(lambda x: x.display_type not in ('line_section', 'line_note')):
            account = line.account_id
            journal = line.journal_id

            if account.deprecated:
                raise UserError(_('The account %s (%s) is deprecated.') % (account.name, account.code))

            control_type_failed = journal.type_control_ids and account.user_type_id not in journal.type_control_ids
            control_account_failed = journal.account_control_ids and account not in journal.account_control_ids
            if control_type_failed or control_account_failed:
                raise UserError(_('You cannot use this general account in this journal, check the tab \'Entry Controls\' on the related journal.'))

    @api.constrains('account_id', 'tax_ids', 'tax_line_id', 'reconciled')
    def _check_off_balance(self):
        for line in self:
            if line.account_id.internal_group == 'off_balance':
                if any(a.internal_group != line.account_id.internal_group for a in line.move_id.line_ids.account_id):
                    raise UserError(_('If you want to use "Off-Balance Sheet" accounts, all the accounts of the journal entry must be of this type'))
                if line.tax_ids or line.tax_line_id:
                    raise UserError(_('You cannot use taxes on lines with an Off-Balance account'))
                if line.reconciled:
                    raise UserError(_('Lines from "Off-Balance Sheet" accounts cannot be reconciled'))
    
    @api.onchange('product_id')
    def get_ie_accounts_ids(self):
        self.get_account_list()
        if self.product_id and self.product_id.l10n_mx_edi_code_sat_id:
            self.l10n_mx_edi_product_code_sat_id = self.product_id.l10n_mx_edi_code_sat_id
        if self.product_id and self.product_id.ie_account_id and len(self.product_id.ie_account_id)==1:
            self.account_ie_id = self.product_id.ie_account_id[0].id
        else:
            self.account_ie_id = False


    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if not line.product_id or line.display_type in ('line_section', 'line_note'):
                continue

            line.name = line._get_computed_name()
            line.account_id = line._get_computed_account()
            line.tax_ids = line._get_computed_taxes()
            line.product_uom_id = line._get_computed_uom()
            line.price_unit = line._get_computed_price_unit()

            # Manage the fiscal position after that and adapt the price_unit.
            # E.g. mapping a price-included-tax to a price-excluded-tax must
            # remove the tax amount from the price_unit.
            # However, mapping a price-included tax to another price-included tax must preserve the balance but
            # adapt the price_unit to the new tax.
            # E.g. mapping a 10% price-included tax to a 20% price-included tax for a price_unit of 110 should preserve
            # 100 as balance but set 120 as price_unit.
            if line.tax_ids and line.move_id.fiscal_position_id:
                line.price_unit = line._get_price_total_and_subtotal()['price_subtotal']
                line.tax_ids = line.move_id.fiscal_position_id.map_tax(line.tax_ids._origin, partner=line.move_id.partner_id)
                accounting_vals = line._get_fields_onchange_subtotal(price_subtotal=line.price_unit, currency=line.move_id.company_currency_id)
                balance = accounting_vals['debit'] - accounting_vals['credit']
                line.price_unit = line._get_fields_onchange_balance(balance=balance).get('price_unit', line.price_unit)

            # Convert the unit price to the invoice's currency.
            company = line.move_id.company_id
            line.price_unit = company.currency_id._convert(line.price_unit, line.move_id.currency_id, company, line.move_id.date)

        if len(self) == 1:
            return {'domain': {'product_uom_id': [('category_id', '=', self.product_uom_id.category_id.id)]}}

    @api.onchange('product_uom_id')
    def _onchange_uom_id(self):
        ''' Recompute the 'price_unit' depending of the unit of measure. '''
        price_unit = self._get_computed_price_unit()

        # See '_onchange_product_id' for details.
        taxes = self._get_computed_taxes()
        if taxes and self.move_id.fiscal_position_id:
            price_subtotal = self._get_price_total_and_subtotal(price_unit=price_unit, taxes=taxes)['price_subtotal']
            accounting_vals = self._get_fields_onchange_subtotal(price_subtotal=price_subtotal, currency=self.move_id.company_currency_id)
            balance = accounting_vals['debit'] - accounting_vals['credit']
            price_unit = self._get_fields_onchange_balance(balance=balance).get('price_unit', price_unit)

        # Convert the unit price to the invoice's currency.
        company = self.move_id.company_id
        self.price_unit = company.currency_id._convert(price_unit, self.move_id.currency_id, company, self.move_id.date)

    @api.onchange('account_id')
    def _onchange_account_id(self):
        ''' Recompute 'tax_ids' based on 'account_id'.
        /!\ Don't remove existing taxes if there is no explicit taxes set on the account.
        '''
        if not self.display_type and (self.account_id.tax_ids or not self.tax_ids):
            taxes = self._get_computed_taxes()

            if taxes and self.move_id.fiscal_position_id:
                taxes = self.move_id.fiscal_position_id.map_tax(taxes, partner=self.partner_id)

            self.tax_ids = taxes

    def _get_computed_name(self):
        self.ensure_one()

        if not self.product_id:
            return ''

        if self.partner_id.lang:
            product = self.product_id.with_context(lang=self.partner_id.lang)
        else:
            product = self.product_id

        values = []
        if product.partner_ref:
            values.append(product.partner_ref)
        if self.journal_id.type == 'sale':
            if product.description_sale:
                values.append(product.description_sale)
        elif self.journal_id.type == 'purchase':
            if product.description_purchase:
                values.append(product.description_purchase)
        return '\n'.join(values)

    def _get_computed_price_unit(self):
        self.ensure_one()

        if not self.product_id:
            return self.price_unit
        elif self.move_id.is_sale_document(include_receipts=True):
            # Out invoice.
            price_unit = self.product_id.lst_price
        elif self.move_id.is_purchase_document(include_receipts=True):
            # In invoice.
            price_unit = self.product_id.standard_price
        else:
            return self.price_unit

        if self.product_uom_id != self.product_id.uom_id:
            price_unit = self.product_id.uom_id._compute_price(price_unit, self.product_uom_id)

        return price_unit

    def _get_computed_account(self):
        self.ensure_one()
        self = self.with_context(force_company=self.move_id.journal_id.company_id.id)

        if not self.product_id:
            return

        fiscal_position = self.move_id.fiscal_position_id
        accounts = self.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)
        if self.move_id.is_sale_document(include_receipts=True):
            # Out invoice.
            return accounts['income']
        elif self.move_id.is_purchase_document(include_receipts=True):
            # In invoice.
            return accounts['expense']

    def _get_computed_taxes(self):
        self.ensure_one()

        if self.move_id.is_sale_document(include_receipts=True):
            # Out invoice.
            if self.product_id.taxes_id:
                tax_ids = self.product_id.taxes_id.filtered(lambda tax: tax.company_id == self.move_id.company_id)
            elif self.account_id.tax_ids:
                tax_ids = self.account_id.tax_ids
            else:
                tax_ids = self.env['account.tax']
            if not tax_ids and not self.exclude_from_invoice_tab:
                tax_ids = self.move_id.company_id.account_sale_tax_id
        elif self.move_id.is_purchase_document(include_receipts=True):
            # In invoice.
            if self.product_id.supplier_taxes_id:
                tax_ids = self.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == self.move_id.company_id)
            elif self.account_id.tax_ids:
                tax_ids = self.account_id.tax_ids
            else:
                tax_ids = self.env['account.tax']
            if not tax_ids and not self.exclude_from_invoice_tab:
                tax_ids = self.move_id.company_id.account_purchase_tax_id
        else:
            # Miscellaneous operation.
            tax_ids = self.account_id.tax_ids

        if self.company_id and tax_ids:
            tax_ids = tax_ids.filtered(lambda tax: tax.company_id == self.company_id)

        return tax_ids

    def _get_computed_uom(self):
        self.ensure_one()
        if self.product_id:
            return self.product_id.uom_id
        return False

    @api.onchange('quantity','fixed_discount' ,'discount', 'price_unit', 'tax_ids')
    def _onchange_price_subtotal(self):
        for line in self:
            if not line.move_id.is_invoice(include_receipts=True):
                continue

            line.update(line._get_price_total_and_subtotal())
            line.update(line._get_fields_onchange_subtotal())


    def _get_price_total_and_subtotal(self, price_unit=None, quantity=None, discount=None, currency=None, product=None, partner=None, taxes=None, move_type=None):
        self.ensure_one()
        return self._get_price_total_and_subtotal_model(
            price_unit=price_unit or self.price_unit,
            quantity=quantity or self.quantity,
            discount=discount or self.discount,
            currency=currency or self.currency_id,
            product=product or self.product_id,
            partner=partner or self.partner_id,
            taxes=taxes or self.tax_ids,
            move_type=move_type or self.move_id.type,
        )

    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes, move_type):
        ''' This method is used to compute 'price_total' & 'price_subtotal'.

        :param price_unit:  The current price unit.
        :param quantity:    The current quantity.
        :param discount:    The current discount.
        :param currency:    The line's currency.
        :param product:     The line's product.
        :param partner:     The line's partner.
        :param taxes:       The applied taxes.
        :param move_type:   The type of the move.
        :return:            A dictionary containing 'price_subtotal' & 'price_total'.
        '''
        res = {}
        
        # Compute 'price_subtotal'.
        price_unit_wo_discount = price_unit * (1 - (discount / 100.0))
        if self.fixed_discount:
            price_unit_wo_discount = price_unit - self.fixed_discount 
            
        subtotal = quantity * price_unit_wo_discount

        # Compute 'price_total'.
        if taxes:
            taxes_res = taxes._origin.compute_all(price_unit_wo_discount,
                quantity=quantity, currency=currency, product=product, partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))
            res['price_subtotal'] = taxes_res['total_excluded']
            res['price_total'] = taxes_res['total_included']
        else:
            res['price_total'] = res['price_subtotal'] = subtotal
        #In case of multi currency, round before it's use for computing debit credit
        if currency:
            res = {k: currency.round(v) for k, v in res.items()}
        return res

    def _get_fields_onchange_subtotal(self, price_subtotal=None, move_type=None, currency=None, company=None, date=None):
        self.ensure_one()
        return self._get_fields_onchange_subtotal_model(
            price_subtotal=price_subtotal or self.price_subtotal,
            move_type=move_type or self.move_id.type,
            currency=currency or self.currency_id,
            company=company or self.move_id.company_id,
            date=date or self.move_id.date,
        )

    @api.model
    def _get_fields_onchange_subtotal_model(self, price_subtotal, move_type, currency, company, date):
        ''' This method is used to recompute the values of 'amount_currency', 'debit', 'credit' due to a change made
        in some business fields (affecting the 'price_subtotal' field).

        :param price_subtotal:  The untaxed amount.
        :param move_type:       The type of the move.
        :param currency:        The line's currency.
        :param company:         The move's company.
        :param date:            The move's date.
        :return:                A dictionary containing 'debit', 'credit', 'amount_currency'.
        '''
        if move_type in self.move_id.get_outbound_types():
            sign = 1
        elif move_type in self.move_id.get_inbound_types():
            sign = -1
        else:
            sign = 1
        price_subtotal *= sign

        if currency and currency != company.currency_id:
            # Multi-currencies.
            balance = currency._convert(price_subtotal, company.currency_id, company, date)
            return {
                'amount_currency': price_subtotal,
                'debit': balance > 0.0 and balance or 0.0,
                'credit': balance < 0.0 and -balance or 0.0,
            }
        else:
            # Single-currency.
            return {
                'amount_currency': 0.0,
                'debit': price_subtotal > 0.0 and price_subtotal or 0.0,
                'credit': price_subtotal < 0.0 and -price_subtotal or 0.0,
            }

    def _get_fields_onchange_balance(self, quantity=None, discount=None, balance=None, move_type=None, currency=None, taxes=None, price_subtotal=None):
        self.ensure_one()
        return self._get_fields_onchange_balance_model(
            quantity=quantity or self.quantity,
            discount=discount or self.discount,
            balance=balance or self.balance,
            move_type=move_type or self.move_id.type,
            currency=currency or self.currency_id or self.move_id.currency_id,
            taxes=taxes or self.tax_ids,
            price_subtotal=price_subtotal or self.price_subtotal,
        )

    @api.model
    def _get_fields_onchange_balance_model(self, quantity, discount, balance, move_type, currency, taxes, price_subtotal):
        ''' This method is used to recompute the values of 'quantity', 'discount', 'price_unit' due to a change made
        in some accounting fields such as 'balance'.

        This method is a bit complex as we need to handle some special cases.
        For example, setting a positive balance with a 100% discount.

        :param quantity:        The current quantity.
        :param discount:        The current discount.
        :param balance:         The new balance.
        :param move_type:       The type of the move.
        :param currency:        The currency.
        :param taxes:           The applied taxes.
        :param price_subtotal:  The price_subtotal.
        :return:                A dictionary containing 'quantity', 'discount', 'price_unit'.
        '''
        if move_type in self.move_id.get_outbound_types():
            sign = 1
        elif move_type in self.move_id.get_inbound_types():
            sign = -1
        else:
            sign = 1
        balance *= sign

        # Avoid rounding issue when dealing with price included taxes. For example, when the price_unit is 2300.0 and
        # a 5.5% price included tax is applied on it, a balance of 2300.0 / 1.055 = 2180.094 ~ 2180.09 is computed.
        # However, when triggering the inverse, 2180.09 + (2180.09 * 0.055) = 2180.09 + 119.90 = 2299.99 is computed.
        # To avoid that, set the price_subtotal at the balance if the difference between them looks like a rounding
        # issue.
        if currency.is_zero(balance - price_subtotal):
            return {}

        taxes = taxes.flatten_taxes_hierarchy()
        if taxes and any(tax.price_include for tax in taxes):
            # Inverse taxes. E.g:
            #
            # Price Unit    | Taxes         | Originator Tax    |Price Subtotal     | Price Total
            # -----------------------------------------------------------------------------------
            # 110           | 10% incl, 5%  |                   | 100               | 115
            # 10            |               | 10% incl          | 10                | 10
            # 5             |               | 5%                | 5                 | 5
            #
            # When setting the balance to -200, the expected result is:
            #
            # Price Unit    | Taxes         | Originator Tax    |Price Subtotal     | Price Total
            # -----------------------------------------------------------------------------------
            # 220           | 10% incl, 5%  |                   | 200               | 230
            # 20            |               | 10% incl          | 20                | 20
            # 10            |               | 5%                | 10                | 10
            taxes_res = taxes._origin.compute_all(balance, currency=currency, handle_price_include=False)
            for tax_res in taxes_res['taxes']:
                tax = self.env['account.tax'].browse(tax_res['id'])
                if tax.price_include:
                    balance += tax_res['amount']

        discount_factor = 1 - (discount / 100.0)
        if balance and discount_factor:
            # discount != 100%
            vals = {
                'quantity': quantity or 1.0,
                'price_unit': balance / discount_factor / (quantity or 1.0),
            }
        elif balance and not discount_factor:
            # discount == 100%
            vals = {
                'quantity': quantity or 1.0,
                'discount': 0.0,
                'price_unit': balance / (quantity or 1.0),
            }
        elif not discount_factor:
            # balance of line is 0, but discount  == 100% so we display the normal unit_price
            vals = {}
        else:
            # balance is 0, so unit price is 0 as well
            vals = {'price_unit': 0.0}
        return vals

    # -------------------------------------------------------------------------
    # ONCHANGE METHODS
    # -------------------------------------------------------------------------

    @api.onchange('amount_currency', 'currency_id', 'debit', 'credit', 'tax_ids', 'account_id')
    def _onchange_mark_recompute_taxes(self):
        ''' Recompute the dynamic onchange based on taxes.
        If the edited line is a tax line, don't recompute anything as the user must be able to
        set a custom value.
        '''
        for line in self:
            if not line.tax_repartition_line_id:
                line.recompute_tax_line = True

    @api.onchange('analytic_account_id', 'analytic_tag_ids')
    def _onchange_mark_recompute_taxes_analytic(self):
        ''' Trigger tax recomputation only when some taxes with analytics
        '''
        for line in self:
            if not line.tax_repartition_line_id and any(tax.analytic for tax in line.tax_ids):
                line.recompute_tax_line = True
