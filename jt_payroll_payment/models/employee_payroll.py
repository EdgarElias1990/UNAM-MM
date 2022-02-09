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
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang, format_date, get_lang
from babel.dates import format_datetime, format_date

class Employee(models.Model):
    
    _inherit = 'hr.employee'

    def action_create_portal_users(self):
        group_portal = self.env.ref('base.group_portal')
        company_id = self.env.company.id
        user_obj = self.env['res.users']
        count = 0
        for emp in self.filtered(lambda x: not x.user_id and x.rfc):
            #count += 1
            #print ("calll====",count)
            exist_user = user_obj.search([('login','=',emp.rfc)],limit=1)
            if exist_user:
                self._cr.execute("update hr_employee set user_id = %s,emp_partner_id = %s where id = %s"%(exist_user.id,exist_user.partner_id and exist_user.partner_id.id or False,emp.id,))
                #emp.user_id = exist_user.id
                #emp.emp_partner_id = exist_user.partner_id and exist_user.partner_id.id or False
            else:
                vals = {'name' : emp.name,
                        'login' : emp.rfc,
                        'active': True, 
                        'groups_id': [(4, group_portal.id)],
                        'company_id': company_id,
                        'company_ids': [(6, 0, [company_id])],
                        }
                
                #user_id = user_obj.with_context(no_reset_password=True)._create_user_from_template(vals)
                user_id = user_obj.with_context(no_reset_password=True).create(vals)
                self._cr.execute("update hr_employee set user_id = %s,emp_partner_id = %s where id = %s"%(user_id.id,user_id.partner_id and user_id.partner_id.id or False,emp.id,))
                
                #emp.user_id = user_id.id
                #emp.emp_partner_id = user_id.partner_id and user_id.partner_id.id or False
     
class HRJob(models.Model):
    _inherit = 'hr.job'
    
    def name_get(self):
        result = []
        for rec in self:
            name = rec.name or ''
            if self.env.context:
                if rec.category_key and (self.env.context.get('show_category_name',False)):
                    name = rec.category_key.name
            result.append((rec.id, name))
        return result
    
    
                 
class EmployeePayroll(models.Model):

    _name = 'employee.payroll.file'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Upload Files"

    def get_upload_file_name(self):
        for rec in self:
            name = "Nómina salarial"
            if rec.employee_id:
                name += "-"+rec.employee_id.name
            if rec.period_start:
                datetimemonth = format_datetime(rec.period_start, 'MMMM', locale=get_lang(self.env).code)
                dateyear = rec.period_start.strftime('%Y')
                name += "-"+ datetimemonth +" "+str(dateyear) 
            rec.name = name
    
    @api.depends('bank_key')
    def get_bank_name_from_key(self):
        for rec in self:
            bank_key_name = ''
            if rec.bank_key:
                bank = self.env['res.bank'].search([('l10n_mx_edi_code','=',rec.bank_key)],limit=1)
                if bank:
                    bank_key_name = bank.name
            rec.bank_key_name = bank_key_name
            
    name = fields.Char("Name",compute="get_upload_file_name")
    employee_id = fields.Many2one('hr.employee', "Employee")
    employee_number = fields.Char(related='employee_id.worker_number', string="Employee Number")
    fornight = fields.Selection([('01', '01'), ('02', '02'), ('03', '03'), ('04', '04'), ('05', '05'),
                                      ('06', '06'), ('07', '07'), ('08', '08'), ('09', '09'), ('10', '10'),
                                      ('11', '11'), ('12', '12'), ('13', '13'), ('14', '14'), ('15', '15'),
                                      ('16', '16'), ('17', '17'), ('18', '18'), ('19', '19'), ('20', '20'),
                                      ('21', '21'), ('22', '22'), ('23', '23'), ('24', '24')],
                                string="Fornight")
    period_start = fields.Date("Period")
    period_end = fields.Date("Period End")
    reference = fields.Char("Reference")
    bank_receiving_payment_id = fields.Many2one('res.bank', string="Bank Receiving Payment")
    payment_issuing_bank_id = fields.Many2one("account.journal", string="Payment Issuing Bank")
    receiving_bank_acc_pay_id = fields.Many2one('res.partner.bank', string="Receiving bank account for payment")
    bank_acc_payment_insur_id = fields.Many2one('res.partner.bank', string="Bank account of payment issuance")
    amount_payable = fields.Float("Amount Payable",tracking=True)
    request_type = fields.Selection([('university', 'Payment to University Worker'),
                                     ('add_benifit', 'Additional Benifit'),
                                     ('alimony', 'Payment Special payroll payments Alimony'),
                                     ('payment', 'Payment')], "Type of request for payroll payment")
    payroll_adjustment = fields.Selection([('withdrawal', 'Withdrawal from the university worker'),
                                           ('leave_without_pay', 'Leave without Pay'),
                                           ('judical', 'Judicial Instruction'),
                                           ('add_payment', 'Additional Payments'),
                                           ('salary_mod_inc', 'Salary modification: Increases'),
                                           ('salary_mod_dec', 'Salary modification: Decreases'),
                                           ('salary_mod_don', 'Salary modification: Donation'),
                                           ('inappropriate','Inappropriate')
                                           ],
                                          string="Payroll Adjustment")
    due_to_inappropriate = fields.Selection([('no_check_collected','No Check Collected'),
                                             ('withdrawal','Withdrawal'),
                                             ('leave_without_pay','Leave without pay'),
                                             ('special_cases','Special cases'),
                                             ('due_to_partial','Due to partial or intermediate'),
                                             ('due_to_having_been_processed','Due to having been processed Some payment that corresponds to the worker'),
                                             ('due_to_change_date','Due to change in the date of withdrawal or because it is not applicable'),
                                             ],string="Due to inappropriate")
    
    beneficiary_id = fields.Many2one('res.partner', "Beneficiary")
    state = fields.Selection([('draft', 'Draft'), ('revised', 'Revised'), ('done', 'Done')], string="State",
                             default='draft')
    payment_request_type = fields.Selection([('direct_employee','Direct Employee'),('payment_provider','Payment Provider')],string="Payment Request Type")
    move_id = fields.Many2one('account.move','Payroll Payments')
    payment_place_id = fields.Many2one(related="employee_id.payment_place_id",string="Place of payment",store=True)
    payroll_register_user_id = fields.Many2one('res.users',default=lambda self: self.env.user,copy=False,string="User who registers")

    payroll_processing_id = fields.Many2one('custom.payroll.processing','Payroll Processing')
    preception_line_ids = fields.One2many('preception.line','payroll_id')
    deduction_line_ids = fields.One2many('deduction.line','payroll_id')
    pension_payment_line_ids = fields.One2many('pension.payment.line','payroll_id')
    additional_payments_line_ids = fields.One2many('additional.payments.line','payroll_id')
    additional_pension_payments_line_ids = fields.One2many('additional.pension.payments.line','payroll_id')
    total_deduction = fields.Float(string="Total Deductions",compute="get_total_dedcution",store=True)
    
    rfc = fields.Char(related='employee_id.rfc')
    job_id = fields.Many2one(related='employee_id.job_id',string='Category key')
    deposite_number = fields.Char("Deposit number")
    check_number = fields.Char("Check number")
    bank_key = fields.Char("Bank Key")
    bank_key_name = fields.Char(string='Bank Key Name',compute="get_bank_name_from_key",store=True)
    adjustment_case_id = fields.Many2one('adjustment.cases','Adjustment Cases')
    adjustment_case_description = fields.Text(related="adjustment_case_id.description",string="Case Description")
    net_salary = fields.Float("Net Salary")
    casualties_and_cancellations = fields.Selection([('B','B'),('BD','BD'),('BDEF','BDEF')],string='Casualties And Cancellations',tracking=True)
    
    l10n_mx_edi_payment_method_id = fields.Many2one(
        'l10n_mx_edi.payment.method',
        string='Payment Method',
        help='Indicates the way the payment was/will be received, where the '
        'options could be: Cash, Nominal Check, Credit Card, etc.')

    is_pension_payment_request = fields.Boolean("Pension Payment",default=False,copy=False)

    @api.depends('deduction_line_ids','deduction_line_ids.amount')
    def get_total_dedcution(self):
        for rec in self:
            total_deduction = sum(x.amount for x in rec.deduction_line_ids)
            rec.total_deduction = total_deduction
            
    @api.onchange('employee_id') 
    def onchange_partner_bak_account(self):
        if self.employee_id and self.employee_id.bank_ids:
            #self.receiving_bank_acc_pay_id = self.employee_id.bank_ids[0].id
            self.bank_receiving_payment_id= self.employee_id.bank_ids[0].bank_id and self.employee_id.bank_ids[0].bank_id.id or False
        else:
            self.receiving_bank_acc_pay_id = False
            self.bank_receiving_payment_id = False 
    
    @api.model
    def create(self,vals):
        res  = super(EmployeePayroll,self).create(vals)
        if res.employee_id and res.employee_id.bank_ids:
#             if not res.receiving_bank_acc_pay_id:
#                 res.receiving_bank_acc_pay_id = res.employee_id.bank_ids[0].id
            if not res.bank_receiving_payment_id:
                res.bank_receiving_payment_id= res.employee_id.bank_ids[0].bank_id and res.employee_id.bank_ids[0].bank_id.id or False
        
        return res
    

class PreceptionLine(models.Model):
    
    _name = 'preception.line'
    
    payroll_id = fields.Many2one('employee.payroll.file','Payroll')
    
    preception_id = fields.Many2one('preception','Key To Perception')
    description = fields.Char(related='preception_id.concept',string="Description")
    amount = fields.Float("Matter")
    account_id = fields.Many2one('account.account','Account')
    move_id = fields.Many2one(related='payroll_id.move_id')
    is_adjustment_update = fields.Boolean("Update",copy=False,default=False)
    is_create_from_this = fields.Boolean("Create",copy=False,default=False)
    
    @api.onchange('program_code_id')
    def onchange_program_code(self):
        if self.program_code_id and self.program_code_id.item_id and self.program_code_id.item_id.unam_account_id:
            self.account_id = self.program_code_id.item_id.unam_account_id.id
    @api.model
    def create(self,vals):
        res = super(PreceptionLine,self).create(vals)
        for r in res:
            if r.program_code_id and r.program_code_id.item_id and r.program_code_id.item_id.unam_account_id:
                r.account_id = r.program_code_id.item_id.unam_account_id.id
            
        return res
class deductionLine(models.Model):
    
    _name = 'deduction.line'
    
    payroll_id = fields.Many2one('employee.payroll.file','Payroll')
    
    deduction_id = fields.Many2one('deduction','Key To Perception')
    description = fields.Char(related='deduction_id.concept',string="Description")
    amount = fields.Float("Matter")
    net_salary = fields.Float("Net Salary")
    credit_account_id = fields.Many2one(related='deduction_id.credit_account_id',string='Ledger account')
    move_id = fields.Many2one(related='payroll_id.move_id')
    is_adjustment_update = fields.Boolean("Update",copy=False,default=False)
    is_create_from_this = fields.Boolean("Create",copy=False,default=False)
    
#     @api.constrains('amount')
#     def check_amount(self):
#         if self.amount and self.amount < 0:
#             raise UserError(_('The balance cannot be negative.'))
    
class PensionPaymentLine(models.Model):
    
    _name = 'pension.payment.line'
    
    payroll_id = fields.Many2one('employee.payroll.file','Payroll')
    
    partner_id = fields.Many2one('res.partner','Beneficiary')
    rfc = fields.Char(related='partner_id.vat',string='Beneficiary RFC')
    l10n_mx_edi_payment_method_id = fields.Many2one(
        'l10n_mx_edi.payment.method',
        string='Payment Method',
        help='Indicates the way the payment was/will be received, where the '
        'options could be: Cash, Nominal Check, Credit Card, etc.')
    deposit_number = fields.Char('Deposit Number')
    check_number = fields.Char('Check Number')
    total_pension = fields.Float('Total Pension')
    
    journal_id = fields.Many2one('account.journal','Account number')
    bank_acc_number = fields.Many2one('res.partner.bank',string='Account number')
    bank_id = fields.Many2one('res.bank','Bank')
    bank_key = fields.Char("Bank Key")
    
class AdditionalPaymentsLine(models.Model):
    
    _name = 'additional.payments.line'
    
    payroll_id = fields.Many2one('employee.payroll.file','Payroll')
    
    job_id = fields.Many2one('hr.job','Category Key')
    job_description = fields.Text(related='job_id.description',string='Job Description')
    details = fields.Selection([('N','N'),('U','U')],string='Detail')
    description = fields.Char("Description", compute='_compute_description', store=True)
    amount = fields.Float('Matter')

    @api.depends('details')
    def _compute_description(self):
        for line in self:
            if line.details == 'N':
                line.description = 'Normal'
            else:
                line.description = 'Unique'

class AdditionalPensionPaymentsLine(models.Model):
    
    _name = 'additional.pension.payments.line'
    
    payroll_id = fields.Many2one('employee.payroll.file','Payroll')
    
    partner_id = fields.Many2one('res.partner','Beneficiary')
    amount = fields.Float('Matter')
        
