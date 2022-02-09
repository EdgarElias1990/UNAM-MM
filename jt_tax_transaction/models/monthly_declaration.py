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
from odoo import models, fields, api
from datetime import datetime

class MonthlyDeclaration(models.Model):

    _name = 'declaration.month'
    _description = 'Monthly declaration'
    _rec_name = 'folio'

    partner_id = fields.Many2one('res.partner','Beneficiary of the payment')
    move_id = fields.Many2one('account.move','Payment Request')
    egress_key_id = fields.Many2one("egress.keys", string="Egress Key")
    
    folio = fields.Integer(string='Folio')
    year = fields.Selection([(str(num), str(num)) for num in range(
        2000, (datetime.now().year) + 80)], string='Year')
    year_id = fields.Many2one('year.configuration',compute="get_year",store=True)
    month = fields.Selection([
        ('january', 'January'),
        ('february', 'February'),
        ('march', 'March'),
        ('april', 'April'),
        ('may', 'May'),
        ('june', 'June'),
        ('july', 'July'),
        ('august', 'August'),
        ('september', 'September'),
        ('october', 'October'),
        ('november', 'November'),
        ('december', 'December')], string='Month', default='january')
    filling_date = fields.Date(string='Filling date')
    programatic_code_id = fields.Many2one('program.code', string='Programmatic code')
    observations = fields.Char(string='Observations')
    amount_payable = fields.Integer(string='Amount payable')
    capture_line = fields.Char(string='Capture line')
    tax_report = fields.Binary("Tax Payable Report")
    vat_card = fields.Binary("VAT card")
    tax_comparison = fields.Binary("Withholding Tax Comparison")
    declaration_proof = fields.Binary("Proof of Declaration")
    payment_ref = fields.Binary("Payment references")
    payment_proof = fields.Binary("Proof of payment")
    sat_receipt = fields.Binary("SAT acknowledgement of receipt")
    state = fields.Selection([('draft', 'Draft'), ('declared', 'Declared'),
                              ('requested', 'Requested'), ('paid', 'Paid'),
                              ('rejected', 'Rejected')
                             ], string="Status", default='draft')

    _sql_constraints = [
        ('folio_uniq', 'unique(folio)', 'The folio must be unique.')]

    @api.depends('year')
    def get_year(self):
        for rec in self:
            if rec.year:
                y = self.env['year.configuration'].search([('name','=',rec.year)],limit=1)
                if y:
                    rec.year_id = y.id
                else:
                    rec.year_id = False
            else:
                rec.year_id = False
    @api.model 
    def create(self, values):            
#         if values.get('state'):    
#             values['state'] = 'declared'
        values.update({'state':'declared'})         
        return super(MonthlyDeclaration, self ).create (values)

    def get_invoice_line_vals(self):
        invoice_line_vals = { 'quantity' : 1,
                            'price_unit' : self.amount_payable,
                            'program_code_id' : self.programatic_code_id.id,
                            'egress_key_id' : self.egress_key_id.id
                            }
        return invoice_line_vals
    
    def get_payment_request_vals(self):
        invoice_line_vals = []
        journal = self.env.ref('jt_supplier_payment.payment_request_jour')
        if self.programatic_code_id:
            line_vals = self.get_invoice_line_vals()
            if line_vals:
                invoice_line_vals.append((0,0,line_vals))
        
                
        partner_id = self.partner_id.id 
        vals = {
                #'payment_bank_id':self.bank_receiving_payment_id and self.bank_receiving_payment_id.id or False,
                #'payment_bank_account_id': self.receiving_bank_acc_pay_id and self.receiving_bank_acc_pay_id.id or False,
                #'payment_issuing_bank_id': self.payment_issuing_bank_id and self.payment_issuing_bank_id.id or False,
                #'l10n_mx_edi_payment_method_id' : self.l10n_mx_edi_payment_method_id and self.l10n_mx_edi_payment_method_id.id or False,
                'partner_id' : partner_id,
                'type' : 'in_invoice',
                'journal_id' : journal and journal.id or False,
                'invoice_date' : self.filling_date,
                'invoice_line_ids':invoice_line_vals,
                'is_payment_request' : True,
                'declaration_month_id' : self.id,
                }
        return vals

    def create_payment_request(self):
        payroll_payment_vals = self.get_payment_request_vals()
        move_id = self.env['account.move'].create(payroll_payment_vals)
        self.move_id = self.move_id.id
        
    def action_requested(self):
        self.state = 'requested'
        self.create_payment_request()
        
class AccountMove(models.Model):

    _inherit = 'account.move'
    
    declaration_month_id = fields.Many2one('declaration.month','Declaration Month')
    