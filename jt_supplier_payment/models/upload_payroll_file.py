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
from datetime import datetime
from odoo.exceptions import UserError, ValidationError,Warning
from odoo.tools.profiler import profile

class EmployeePayroll(models.Model):

    _inherit = 'employee.payroll.file'

    l10n_mx_edi_payment_method_id = fields.Many2one(
        'l10n_mx_edi.payment.method',
        string='Payment Method',
        help='Indicates the way the payment was/will be received, where the '
        'options could be: Cash, Nominal Check, Credit Card, etc.')
    substate = fields.Selection(related="move_id.payment_state",string="SubState")
    batch_folio = fields.Integer(related="move_id.batch_folio",string="Batch Folio")
    
#     @api.onchange('l10n_mx_edi_payment_method_id')
#     def onchange_l10n_mx_edi_payment_method_id(self):
#         if self.l10n_mx_edi_payment_method_id:
#             cash_payment_method = self.env.ref('l10n_mx_edi.payment_method_efectivo').id
#             if cash_payment_method and cash_payment_method == self.l10n_mx_edi_payment_method_id.id:
#                 self.payment_request_type = 'payment_provider'
#             else: 
#                 self.payment_request_type = False

    @api.model
    def create(self,vals):
        res = super(EmployeePayroll,self).create(vals)
        if res.l10n_mx_edi_payment_method_id:
            cash_payment_method = self.env.ref('l10n_mx_edi.payment_method_efectivo').id
            if cash_payment_method and cash_payment_method == res.l10n_mx_edi_payment_method_id.id:
                res.payment_request_type = 'payment_provider'
        return res
    
    def write(self,vals):
        result = super(EmployeePayroll,self).write(vals)
        if 'l10n_mx_edi_payment_method_id' in vals:
            for res in self:
                if res.l10n_mx_edi_payment_method_id:
                    cash_payment_method = self.env.ref('l10n_mx_edi.payment_method_efectivo').id
                    if cash_payment_method and cash_payment_method == res.l10n_mx_edi_payment_method_id.id:
                        res.payment_request_type = 'payment_provider'
        return result

    def action_draft(self):
        if any(self.filtered(lambda x:x.state != 'revised')):
            raise UserError(_("You can Draft only for those Payroll which are in "
            "'Revised'!"))
        for record in self:
            record.state = 'draft'
    
    def action_reviewed(self):
        if any(self.filtered(lambda x:x.state not in ('draft','revised'))):
            raise UserError(_("You can Reviewed only for those Payroll which are in "
            "'Draft'!"))
        for record in self:
            record.reference= self.env['ir.sequence'].next_by_code('seq.payroll.employee.reference')
            record.state = 'revised'
            if record.casualties_and_cancellations == 'BDEF':
                record.employee_id.active = False
                
    def get_invoice_line_vals(self,line):
        invoice_line_vals = { 'quantity' : 1,
                            'price_unit' : line.amount,
                            }
        if line.account_id:
            invoice_line_vals.update({'account_id':line.account_id and line.account_id.id or False})
            
        return invoice_line_vals
    
    def get_deduction_invoice_line_vals(self,line):
        invoice_line_vals = {}
        amount = -line.amount
#         if line.amount > 0:
#             amount = -line.amount
        
        invoice_line_vals = { 'quantity' : 1,
                            'price_unit' : amount,
                            }
        if line.credit_account_id:
            invoice_line_vals.update({'account_id' : line.credit_account_id.id})
            
        return invoice_line_vals
        
    def get_payroll_payment_vals(self):
        invoice_line_vals = []
        journal = self.env.ref('jt_payroll_payment.payroll_payment_request_jour')
        for line in self.preception_line_ids:
            line_vals = self.get_invoice_line_vals(line)
            if line_vals:
                invoice_line_vals.append((0,0,line_vals))
        
        for line in self.deduction_line_ids:
            line_vals = self.get_deduction_invoice_line_vals(line)
            if line_vals:
                invoice_line_vals.append((0,0,line_vals))
        is_payroll_payment_request = True
        is_pension_payment_request = False
#         if self.is_pension_payment_request:
#             is_payroll_payment_request = False
#             is_pension_payment_request = True
        is_check_payment_method = False
        bank_key_name = ''
        check_payment_method = self.env.ref('l10n_mx_edi.payment_method_cheque')
        if check_payment_method and self.l10n_mx_edi_payment_method_id and check_payment_method.id==self.l10n_mx_edi_payment_method_id.id:
            is_check_payment_method = True
            bank_key_name = self.bank_key_name
        partner_id = self.employee_id and self.employee_id.user_id and self.employee_id.user_id.partner_id and self.employee_id.user_id.partner_id.id or False 
        vals = {'payment_bank_id':self.bank_receiving_payment_id and self.bank_receiving_payment_id.id or False,
                'payment_bank_account_id': self.receiving_bank_acc_pay_id and self.receiving_bank_acc_pay_id.id or False,
                'payment_issuing_bank_id': self.payment_issuing_bank_id and self.payment_issuing_bank_id.id or False,
                'l10n_mx_edi_payment_method_id' : self.l10n_mx_edi_payment_method_id and self.l10n_mx_edi_payment_method_id.id or False,
                'partner_id' : partner_id,
                'is_payroll_payment_request':is_payroll_payment_request,
                'is_pension_payment_request' : is_pension_payment_request,
                'type' : 'in_invoice',
                'journal_id' : journal and journal.id or False,
                'invoice_date' : fields.Date.today(),
                'invoice_line_ids':invoice_line_vals,
                'fornight' : self.fornight,
                'payroll_request_type' : self.request_type,
                'deposite_number' : self.deposite_number,
                'check_number' : self.check_number,
                'bank_key' : self.bank_key,
                'pension_reference': self.reference,
                'period_start' : self.period_start,
                'period_end' : self.period_end,
                'is_check_payment_method':is_check_payment_method,
                'bank_key_name':bank_key_name,
                'payroll_processing_id': self.payroll_processing_id,
                }
        return vals

    def get_pension_payment_request_vals(self,line):
        journal = self.env.ref('jt_payroll_payment.payroll_payment_request_jour')
        is_payroll_payment_request = False
        is_pension_payment_request = True
        
        partner_id = line.partner_id.id
        banco = line.bank_id.id
        no_cuenta = line.bank_acc_number.id
        clave_banco = line.bank_key
        num_depos = line.deposit_number
        account_id = self.env['account.account'].search([('code','=','220.008.001')],limit=1)
        
        
        line_v = {
            'quantity' : 1,
            'price_unit' : line.total_pension,
            }
        if account_id:
            line_v.update({'account_id':account_id.id})
        
        invoice_line_vals=[(0,0,line_v)] 
        vals = {'payment_bank_id': banco,
                'payment_bank_account_id': no_cuenta,
                'payment_issuing_bank_id': self.payment_issuing_bank_id and self.payment_issuing_bank_id.id or False,
                'l10n_mx_edi_payment_method_id' : line.l10n_mx_edi_payment_method_id and line.l10n_mx_edi_payment_method_id.id or False,
                'partner_id' : partner_id,
                'is_payroll_payment_request':is_payroll_payment_request,
                'is_pension_payment_request' : is_pension_payment_request,
                'type' : 'in_invoice',
                'journal_id' : journal and journal.id or False,
                'invoice_date' : fields.Date.today(),
                'invoice_line_ids':invoice_line_vals,
                'fornight' : self.fornight,
                'payroll_request_type' : self.request_type,
                'deposite_number' : num_depos,
                'check_number' : line.check_number,
                'bank_key' : clave_banco,
                'pension_reference': self.reference,
                'period_start' : self.period_start,
                'period_end' : self.period_end,
                }
        return vals
    
    def create_pension_payment_request(self):
        for rec in self:
            if rec.pension_payment_line_ids:
                for line in rec.pension_payment_line_ids:
                    if line.partner_id:
                        vals = self.get_pension_payment_request_vals(line)
                        self.env['account.move'].create(vals)
                            
    def create_payroll_payment(self):
        payroll_payment_vals = self.get_payroll_payment_vals()
        self.create_pension_payment_request()
        return self.env['account.move'].create(payroll_payment_vals)
    
    def action_done(self):
        if any(self.filtered(lambda x:x.casualties_and_cancellations == 'BDEF')):
            raise UserError(_("You can not Request for payment for Casualties And Cancellations which are in BDEF"))
        
        if any(self.filtered(lambda x:x.state != 'revised')):
            raise UserError(_("You can Request for payment only for those Payroll which are in "
            "'Reviewed'!"))
        payment_providers = self.filtered(lambda x:x.payment_request_type == 'payment_provider')
        direct_employee = self.filtered(lambda x:x.payment_request_type == 'direct_employee')
        
        if payment_providers and direct_employee:
            raise UserError(_("You can not Request for payment for both Payment Provider and Direct Employee"))
        
        if payment_providers:
            partner_id = self.env['res.partner'].search([('supplier_of_payment_payroll','=',True)])
            partner = False
            if partner_id:
                partner = partner_id[0].id 
                 
            return {
                'name': _('Payment Provider'),
                'res_model':'payroll.payment.provider.wizard',
                'view_mode': 'form',
                'view_id': self.env.ref('jt_supplier_payment.payroll_payment_provider_form_view').id,
                'context': {'default_partner_id':partner,'default_emp_payroll_ids': [(6, 0, payment_providers.ids)]},
                'target': 'new',
                'type': 'ir.actions.act_window',
            }
            
        elif direct_employee:
            for record in self:
                if record.casualties_and_cancellations and record.casualties_and_cancellations == 'B':
                    record.state = 'done'
                    continue
                elif record.casualties_and_cancellations and record.casualties_and_cancellations == 'BD':
                    record.state = 'done'
                    continue
                
                move_id = record.create_payroll_payment()
                record.write({'move_id':move_id.id})
                #record.state = 'done'
                #record.check_folio_id.date_printing = datetime.today()
                #record.check_folio_id.status = 'Printed'
            all_check_ids = self.mapped('check_folio_id')
            self.write({'state': 'done'})
            all_check_ids = all_check_ids.filtered(lambda x:x.status != 'Cancelled')
            all_check_ids.write({'date_printing':datetime.today(),'status':'Printed'})
            
