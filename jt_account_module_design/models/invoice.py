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
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from datetime import datetime, timedelta
from datetime import date


class Provision(models.Model):

    _name = 'provision'
    _description = 'Provision'
    _rec_name = 'number'

    @api.model
    def _get_default_journal(self):
        ''' Get the default journal.
        It could either be passed through the context using the 'default_journal_id' key containing its id,
        either be determined by the default type.
        '''
        journal = None
        if 'default_is_payment_request' in self._context:
            journal = self.env.ref('jt_supplier_payment.payment_request_jour')

        return journal


    number = fields.Char("Number")
    baneficiary_id = fields.Many2one(
        'hr.employee', string="Beneficiary of the payment")
    partner_id = fields.Many2one('res.partner', readonly=True, tracking=True,
        states={'draft': [('readonly', False)]},
        check_company=True,
        string='Partner', change_default=True)
    state = fields.Selection(selection=[
            ('draft', 'Draft'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
        ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')

    @api.model
    def _get_default_currency(self):
        ''' Get the default currency from either the journal, either the default journal's company. '''
        journal = self.journal_id
        return journal.currency_id or journal.company_id.currency_id

    currency_id = fields.Many2one('res.currency', store=True, readonly=True, tracking=True, required=True,
        states={'draft': [('readonly', False)]},
        string='Currency',
        default=_get_default_currency)

    req_registeration_date = fields.Date('Request Registeration Date')
    payment_state = fields.Selection([('draft', 'Draft'), ('registered', 'Registered'),
                                    ('provision', 'Provisions'),
                                    ('rejected', 'Rejected'),
                                    ('cancel', 'Cancel')], default='draft', copy=False)
    is_from_reschedule_payment = fields.Boolean(
        string="From Reschedule", default=False)
    leaves = fields.Integer('Leaves')
    project_code = fields.Char('Project Code')
    dependancy_id = fields.Many2one('dependency', string='Dependency')
    sub_dependancy_id = fields.Many2one('sub.dependency', 'Sub Dependency')
    exchange_rate = fields.Char('Exchange Rate')
    foreign_currency_amount = fields.Monetary('Foreign currency amount')
    project_number_id = fields.Many2one(
        'project.project', string='Project Number')
    is_papiit_project = fields.Boolean(
        related='project_number_id.is_papiit_project', string='Is Papiit Project')
    agreement_number = fields.Char(
        related='project_number_id.number_agreement', string='Agreement Number')
    stage = fields.Many2one(
        related='project_number_id.stage_identifier_id', string='Stage',readonly=False)
    invoice_vault_folio = fields.Char('Invoice vault folio')
    line = fields.Integer("Header")
    req_registration_date = fields.Date('Request Registration Date')
    baneficiary_key = fields.Char(
        'Baneficiary Key', related='partner_id.password_beneficiary', store=True)
    rfc = fields.Char("RFC", related='partner_id.vat', store=True)
    student_account = fields.Char("Student Account")
    transfer_key = fields.Char("Transfer Key")
    category_key = fields.Many2one(
        string="Category Key", related='partner_id.category_key', store=True)
    workstation_id = fields.Many2one(
        'hr.job', "Appointment", related='partner_id.workstation_id',readonly=False)
    folio = fields.Char("Folio against Receipt")
    folio_dependency = fields.Char("Folio Dependency")
    operation_type_id = fields.Many2one('operation.type', "Operation Type")
    date_receipt = fields.Datetime("Date of Receipt")
    date_approval_request = fields.Date("Date Approval Request")
    administrative_forms = fields.Integer("Number of Administrative Forms")
    no_of_document = fields.Integer("Number of Documents")
    sheets = fields.Integer("Sheets")
    payment_method = fields.Selection(
        [('check', 'Check'), ('electronic_transfer', 'Electronic Transfer'), ('cash', 'Cash')])
    l10n_mx_edi_payment_method_id = fields.Many2one(
        'l10n_mx_edi.payment.method',
        string='Payment Method',
        help='Indicates the way the payment was/will be received, where the '
        'options could be: Cash, Nominal Check, _compute_rejection_messageedit Card, etc.')

    document_type = fields.Selection(
        [('national', 'National Currency'), ('foreign', 'Foreign Currency')])
    upa_key = fields.Many2one('policy.keys', 'UPA Key')
    upa_document_type = fields.Many2one(
        'upa.document.type', string="Document Type UPA")
    provenance = fields.Text("Provenance")
    batch_folio = fields.Integer("Batch Folio")
    vault_folio = fields.Char("Vault folio")
    payment_bank_id = fields.Many2one('res.bank', "Bank of receipt of payment")
    payment_bank_account_id = fields.Many2one(
        'res.partner.bank', "Payment Receipt bank account")
    payment_issuing_bank_id = fields.Many2one(
        'account.journal', "Payment issuing Bank")
    payment_issuing_bank_acc_id = fields.Many2one(
        related="payment_issuing_bank_id.bank_account_id", string="Payment issuing bank Account")
    responsible_id = fields.Many2one(
        'hr.employee', 'Responsible/Irresponsible')
    administrative_secretary_id = fields.Many2one(
        'hr.employee', 'Administrative Secretary')
    holder_of_dependency_id = fields.Many2one(
        'hr.employee', "Holder of the Dependency")
    invoice_uuid = fields.Char("Invoice UUID")
    invoice_series = fields.Char("Invoice Series")
    folio_invoice = fields.Char("Folio Invoice")
    user_registering_id = fields.Many2one('res.users')
    commitment_date = fields.Date("Commitment Date")
    
    # @api.depends('payment_state')
    # def _compute_rejection_message(self):

    #     for record in self:
    #         if record.payment_state == 'rejected':
    #             record.reason_rejection_req = 'Budget Insufficiency'

    reason_rejection_req = fields.Text(string="Reason for Rejecting Request")
    reason_rejection = fields.Text("Reason for Rejection")
    reason_cancellation = fields.Text("Reason for Cancellation")
    is_payment_request = fields.Boolean("Payment Request")
    # type = fields.Selection(selection_add=[('payment_req', 'Payment Request')])

    # More info Tab
    reason_for_expendiure = fields.Char("Reason for Expenditure/Trip")
    destination = fields.Char("Destination")
    origin_payment = fields.Char("Origin")
    zone = fields.Integer("Zone")
    rate = fields.Monetary("Rate")
    days = fields.Integer("Days")
    responsible_expend_id = fields.Many2one(
        'hr.employee', "Name of the responsible")
    rf_person = fields.Char("RFC of the person in charge")
    responsible_category_key = fields.Many2one(
        related='manager_job_id.category_key', string="Responsible category key")
    manager_job_id = fields.Many2one(
        'hr.job', related='responsible_expend_id.job_id', string="Manager’s job")
    responsible_rfc = fields.Char(
        'VAT', related='responsible_expend_id.rfc', store=True)
    line_ids = fields.One2many('account.move.line', 'provision_id', string='Journal Items', copy=True, readonly=True,
        states={'draft': [('readonly', False)]})
    commercial_partner_id = fields.Many2one('res.partner', string='Commercial Entity', store=True, readonly=True,
        compute='_compute_commercial_partner_id')

    @api.depends('partner_id')
    def _compute_commercial_partner_id(self):
        for move in self:
            move.commercial_partner_id = move.partner_id.commercial_partner_id



    provision_line_ids = fields.One2many('provision.line', 'provision_id', string='Provision Line')
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 domain="[('company_id', '=', company_id)]",default=_get_default_journal)
    company_id = fields.Many2one(string='Company', store=True, readonly=True,
        related='journal_id.company_id', change_default=True, default=lambda self: self.env.company)
    is_show_beneficiary_key = fields.Boolean(
        'Show Beneficiary Key', default=False)
    excercise = fields.Char('excercise')

    @api.model
    def _get_default_invoice_date(self):
        today = date.today().strftime("%d/%m/%Y")
        self.invoice_date = today


    invoice_date = fields.Date(string='Invoice/Bill Date', readonly=True, index=True, copy=False,
        states={'draft': [('readonly', False)]},
        default=_get_default_invoice_date)

    is_show_student_account = fields.Boolean(
        'Show Student Account', default=False)
    is_show_category_key = fields.Boolean('Show Category Key', default=False)
    is_show_appointment = fields.Boolean('Show Appointment', default=False)
    is_show_responsible = fields.Boolean('Show Responsible', default=False)
    is_show_holder_of_dependency = fields.Boolean(
        'Show holder_of_dependency', default=False)
    is_show_commitment_date = fields.Boolean(
        'Show Commitmet Date', default=False)
    is_show_turn_type = fields.Boolean('Show Turn Type', default=False)
    is_show_reason_for_expendiure = fields.Boolean(
        'reason_for_expendiure', default=False)
    is_show_destination = fields.Boolean('is_show_destination', default=False)
    is_show_origin = fields.Boolean('is_show_origin', default=False)
    is_zone_res = fields.Boolean('Show Zone Res', default=False)
    is_show_resposible_group = fields.Boolean(
        'Resposible Group', default=False)

    period_start = fields.Date("Period")
    period_end = fields.Date("Period End")
    pension_reference = fields.Char("Reference")

    deposite_number = fields.Char("Deposit number")
    check_number = fields.Char("Check number")
    bank_key = fields.Char("Bank Key")
    previous_number = fields.Char("Previous Number", size=11)
    previous = fields.Monetary('Previous')
    agreement_type_id = fields.Many2one('agreement.type',string="Agreement Type")
    
    
    # More info Tab
    # responsible_category_key = fields.Char("Responsible category key")
    responsible_job_position = fields.Many2one(
        'hr.job', 'Responsible job position')
    operation_name = fields.Char(related='operation_type_id.name')
    ############################################################3
    #account total
    amount_untaxed = fields.Monetary(string='Untaxed Amount',compute='_compute_amount', store=True, readonly=True)
    amount_tax = fields.Monetary(string='Tax', store=True,compute='_compute_amount',readonly=True)
    amount_total = fields.Monetary(string='Total', store=True,compute='_compute_amount',readonly=True)

    @api.depends('provision_line_ids','provision_line_ids.price_unit','provision_line_ids.tax_ids')
    def _compute_amount(self):
        for rec in self:
            rec.amount_untaxed = sum(x.price_unit for x in rec.provision_line_ids)
            rec.amount_tax = sum(x.amount_tax for x in rec.provision_line_ids)
            rec.amount_total = rec.amount_untaxed + rec.amount_tax 



    @api.model
    def create(self,vals):
        res = super(Provision, self).create(vals)
        seq_no = self.env['ir.sequence'].next_by_code('provision')
        res.number = seq_no
        return res

    def action_cancel_budget(self):
        self.ensure_one()
        self.payment_state = 'cancel'


    def action_draft_budget(self):
        self.ensure_one()
        self.payment_state = 'draft'


    def unlink(self):
        for rec in self:
            if rec.payment_state not in ['draft']:
                raise UserError(_('You cannot delete an entry which has been not draft state.'))
        return super(Provision, self).unlink()

    def action_payment_request(self):
        return {
                'name': 'Operations',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'views': [(self.env.ref("jt_supplier_payment.payment_req_tree_view_diff").id, 'tree'), (self.env.ref("jt_supplier_payment.payment_req_form_view").id, 'form')],
                'res_model': 'account.move',
                'domain': [('provision_id', '=', self.id)],
                'type': 'ir.actions.act_window',
            }

    def create_payment_request(self):
        invoice_line_vals = []
        for line in self.provision_line_ids:
            line_vals = {
                'product_id':line.product_id and line.product_id.id or False,
                'name' : line.name,
                'account_id':line.account_id and line.account_id.id or False,
                'quantity' : line.quantity,
                'price_unit' : line.price_unit,
                'program_code_id' : line.program_code_id and line.program_code_id.id or False,
                'turn_type' : line.turn_type,
                'type_of_bussiness_line' : line.type_of_bussiness_line, 
                'egress_key_id' : line.egress_key_id and line.egress_key_id.id or False,
                'invoice_uuid' : line.invoice_uuid,
                'folio_invoice' : line.folio_invoice,
                'vault_folio' : line.vault_folio,
                'other_amounts' : line.other_amounts,
                'tax_ids' : [(6,0,line.tax_ids.ids)]
                }
            invoice_line_vals.append((0,0,line_vals))
            
        vals = {'payment_bank_id':self.payment_bank_id and self.payment_bank_id.id or False,
                'payment_bank_account_id': self.payment_bank_account_id and self.payment_bank_account_id.id or False,
                'payment_issuing_bank_id': self.payment_issuing_bank_id and self.payment_issuing_bank_id.id or False,
                'l10n_mx_edi_payment_method_id' : self.l10n_mx_edi_payment_method_id and self.l10n_mx_edi_payment_method_id.id or False,
                'partner_id' : self.partner_id and self.partner_id.id or False,
                'type' : 'in_invoice',
                'journal_id' : self.journal_id and self.journal_id.id or False,
                'invoice_date' : self.invoice_date,
                'invoice_line_ids':invoice_line_vals,
                'is_payment_request' : True,
                'provision_id':self.id,
                'currency_id':self.currency_id and self.currency_id.id or False,
                'folio':self.folio,
                'dependancy_id':self.dependancy_id and self.dependancy_id.id or False,
                'sub_dependancy_id' : self.sub_dependancy_id and self.sub_dependancy_id.id or False,
                'date_receipt':self.date_receipt,
                'folio_dependency':self.folio_dependency,
                'administrative_forms' : self.administrative_forms,
                'no_of_document' : self.no_of_document,
                'sheets' : self.sheets,
                'previous_number' : self.previous_number,
                'administrative_secretary_id' : self.administrative_secretary_id and self.administrative_secretary_id.id or False,
                'user_registering_id' : self.user_registering_id and self.user_registering_id.id or False,
                'upa_key' : self.upa_key and self.upa_key.id or False,
                'upa_document_type' : self.upa_document_type and self.upa_document_type.id or False,
                'document_type' : self.document_type,
                'operation_type_id' : self.operation_type_id and self.operation_type_id.id or False,
                'folio' : self.folio,
                'date_approval_request' : self.date_approval_request,
                'payment_bank_id' : self.payment_bank_id and self.payment_bank_id.id or False,
                'payment_bank_account_id' : self.payment_bank_account_id and self.payment_bank_account_id.id or False,
                'payment_issuing_bank_id' : self.payment_issuing_bank_id and self.payment_issuing_bank_id.id or False,
                'payment_issuing_bank_acc_id' : self.payment_issuing_bank_acc_id and self.payment_issuing_bank_acc_id.id or False,
                'batch_folio' : self.batch_folio,
                }

        return self.env['account.move'].create(vals)
    
    def generate_payment_request(self):
        for rec in self:
            if rec.payment_state != 'provision':
                raise UserError(_('You can generate payment request only for provision state.'))
            rec.create_payment_request()
            
    @api.onchange('partner_id')
    def onchange_partner_bak_account(self):
        if self.partner_id and self.partner_id.bank_ids:
            self.payment_bank_account_id = self.partner_id.bank_ids[0].id
            self.payment_bank_id = self.partner_id.bank_ids[
                0].bank_id and self.partner_id.bank_ids[0].bank_id.id or False
        else:
            self.payment_bank_account_id = False
            self.payment_bank_id = False



    def action_validate_budget(self):
        self.ensure_one()
        str_msg = "Budgetary Insufficiency For Program Code\n\n"
        if self.env.user.lang == 'es_MX':
            str_msg = "Insuficiencia Presupuestal para el código del programa\n\n"
        is_check = False
        budget_msg = "Budget sufficiency"
        if self.env.user.lang == 'es_MX':
            budget_msg = "Suficiencia Presupuestal"
            
        for line in self.provision_line_ids.filtered(lambda x:x.program_code_id):
            total_available_budget = 0
            if line.program_code_id:
                budget_line = self.env['expenditure.budget.line']
                budget_lines = self.env['expenditure.budget.line'].sudo().search(
                [('program_code_id', '=', line.program_code_id.id),
                 ('expenditure_budget_id', '=', line.program_code_id.budget_id.id),
                 ('expenditure_budget_id.state', '=', 'validate')])
                print('budget lines',budget_line)
                if self.invoice_date and budget_lines:
                    b_month = self.invoice_date.month
                    for b_line in budget_lines:
                        if b_line.start_date:
                            b_s_month = b_line.start_date.month
                            if b_month in (1, 2, 3) and b_s_month in (1, 2, 3):
                                budget_line += b_line
                            elif b_month in (4, 5, 6) and b_s_month in (4, 5, 6):
                                budget_line += b_line
                            elif b_month in (7, 8, 9) and b_s_month in (7, 8, 8):
                                budget_line += b_line
                            elif b_month in (10, 11, 12) and b_s_month in (10, 11, 12):
                                budget_line += b_line
                    
                    total_available_budget = sum(x.available for x in budget_line)
                    
            line_amount =  0
            line_amount = line.subtotal
            print('total available budget',total_available_budget)
            print('line amount',line_amount)
            if total_available_budget < line_amount:
                is_check = True
                program_name = ''
                if line.program_code_id:
                    program_name = line.program_code_id.program_code
                    avl_amount = " Available Amount Is "
                    if self.env.user.lang == 'es_MX':
                        avl_amount = " Disponible Monto "
                    str_msg += program_name+avl_amount+str(total_available_budget)+"\n\n"
                    
        if is_check:
            return {
                        'name': _('Budgetary Insufficiency'),
                        'type': 'ir.actions.act_window',
                        'res_model': 'budget.insufficien.wiz',
                        'view_mode': 'form',
                        'view_type': 'form',
                        'views': [(False, 'form')],
                        'target': 'new',
                        'context':{'default_msg':str_msg,'default_provision_id':self.id,'default_is_budget_suf':False}
                    }
        else:
            return {
                        'name': _('Budget sufficiency'),
                        'type': 'ir.actions.act_window',
                        'res_model': 'budget.insufficien.wiz',
                        'view_mode': 'form',
                        'view_type': 'form',
                        'views': [(False, 'form')],
                        'target': 'new',
                        'context':{'default_msg':budget_msg,'default_provision_id':self.id,'default_is_budget_suf':True}
                    }


    def generate_folio(self):
        folio = ''
        if self.upa_key and self.upa_key.organization:
            folio += self.upa_key.organization + "/"
        if self.upa_document_type and self.upa_document_type.document_number:
            folio += self.upa_document_type.document_number + "/"
        folio += self.env['ir.sequence'].next_by_code('payment.folio')
        self.folio = folio

    @api.onchange('operation_type_id')
    def onchange_operation_type_id(self):
        if self.operation_type_id and self.operation_type_id.name:
            my_str1 = "Reimbursement to third parties"
            my_str2 = "Airline tickets"
            my_str3 = "Reimbursement to the fixed fund"
            my_str4 = "Reimbursement to third parties, verification of administration"
            my_str5 = "Payment to supplier"
            is_show_turn_type = False
            is_show_reason_for_expendiure = False
            is_show_destination = False
            is_show_origin = False
            is_zone_res = False
            is_show_resposible_group = False
            if self.operation_type_id.name.upper() == my_str1.upper():
                self.is_show_beneficiary_key = True
                is_show_turn_type = True
            elif self.operation_type_id.name.upper() == my_str2.upper():
                self.is_show_beneficiary_key = True
                is_show_turn_type = True
            elif self.operation_type_id.name.upper() == my_str3.upper():
                self.is_show_beneficiary_key = True
                is_show_turn_type = True
            elif self.operation_type_id.name.upper() == my_str4.upper():
                self.is_show_beneficiary_key = True
                is_show_turn_type = True
            elif self.operation_type_id.name.upper() == my_str5.upper():
                self.is_show_beneficiary_key = True
                self.is_show_commitment_date = True
                is_show_turn_type = True
            else:
                self.is_show_beneficiary_key = False

            self.is_show_turn_type = is_show_turn_type
            str_account = "Fellows"
            if self.operation_type_id.name.upper() == str_account.upper():
                self.is_show_student_account = True
            else:
                self.is_show_student_account = False

            str_category1 = "Viaticals"
            str_category2 = "Viatical expenses replacement of resources to the fixed fund"
            if self.operation_type_id.name.upper() == str_category1.upper():
                self.is_show_category_key = True
                self.is_show_appointment = True
                is_show_reason_for_expendiure = True
                is_zone_res = True
            elif self.operation_type_id.name.upper() == str_category2.upper():
                self.is_show_category_key = True
                self.is_show_appointment = True
                is_zone_res = True
            else:
                self.is_show_category_key = False
                self.is_show_appointment = False

            #====For is_show_responsible =====#
            str_responsible1 = "Scholarship recipients"
            str_responsible2 = "Third party reimbursement"
            str_responsible3 = "Airline tickets"
            str_responsible4 = "Accounts payable creation"
            if self.operation_type_id.name.upper() == str_responsible1.upper():
                self.is_show_responsible = True
            elif self.operation_type_id.name.upper() == str_responsible2.upper():
                self.is_show_responsible = True
            elif self.operation_type_id.name.upper() == str_responsible3.upper():
                self.is_show_responsible = True
            elif self.operation_type_id.name.upper() == str_responsible4.upper():
                self.is_show_responsible = True
                is_show_resposible_group = True
                is_show_reason_for_expendiure = True
            else:
                self.is_show_responsible = False

            #======is_show_holder_of_dependency =====:
            str_holder1 = "Field work and school practices"
            str_holder2 = "Reimbursement to the fixed fund"
            str_holder3 = "Reimbursement to third parties, proof of administration"
            str_holder4 = "Exchange expenses"
            str_holder5 = "Expenses of per diem replacement of resources to the fixed fund"
            str_holder6 = "Per diem"
            str_holder7 = "Payment to supplier"
            if self.operation_type_id.name.upper() == str_holder1.upper():
                self.is_show_holder_of_dependency = True
                is_show_reason_for_expendiure = True
                is_show_destination = True
                is_show_resposible_group = True
            elif self.operation_type_id.name.upper() == str_holder2.upper():
                self.is_show_holder_of_dependency = True
            elif self.operation_type_id.name.upper() == str_holder3.upper():
                self.is_show_holder_of_dependency = True
            elif self.operation_type_id.name.upper() == str_holder4.upper():
                self.is_show_holder_of_dependency = True
                is_show_reason_for_expendiure = True
                is_show_origin = True
                is_show_resposible_group = True
            elif self.operation_type_id.name.upper() == str_holder5.upper():
                self.is_show_holder_of_dependency = True
            elif self.operation_type_id.name.upper() == str_holder6.upper():
                self.is_show_holder_of_dependency = True
            elif self.operation_type_id.name.upper() == str_holder7.upper():
                self.is_show_holder_of_dependency = True
            else:
                self.is_show_holder_of_dependency = False

            # ===== For the is_show_reason_for_expendiure ====#
            str_expendiure = "Travel expenses replacement of resources to the fixed fund"
            if self.operation_type_id.name.upper() == str_expendiure.upper():
                is_show_reason_for_expendiure = True
                is_show_destination = True
            str_destination = "Travel expenses"
            if self.operation_type_id.name.upper() == str_destination.upper():
                is_show_destination = True

            self.is_show_reason_for_expendiure = is_show_reason_for_expendiure
            self.is_show_destination = is_show_destination
            self.is_show_origin = is_show_origin
            self.is_zone_res = is_zone_res
            self.is_show_resposible_group = is_show_resposible_group

    def action_register(self):

        self.payment_state = 'registered'
        for move in self:
            move.generate_folio()
            if not self.commitment_date:
                today = datetime.today()
                current_date = today + timedelta(days=30)
                move.commitment_date = current_date
            payment_lines = move.provision_line_ids.filtered(lambda x:not x.program_code_id)
            if payment_lines:
                raise ValidationError("Please add program code into invoice lines")


    def create_journal_line_for_approved_payment(self):
        if self.journal_id and (not self.journal_id.default_credit_account_id or not \
            self.journal_id.default_debit_account_id):
            raise ValidationError(_("Configure Default Debit and Credit Account in %s!" % \
                                    self.journal_id.name))
        
        amount_total = sum(x.subtotal for x in self.provision_line_ids.filtered(lambda x:x.program_code_id))    
        if self.currency_id != self.company_id.currency_id:
            amount_currency = abs(amount_total)
            balance = self.currency_id._convert(amount_currency, self.company_currency_id, self.company_id, self.date)
            currency_id = self.currency_id and self.currency_id.id or False
        else:
            balance = abs(amount_total)
            amount_currency = 0.0
            currency_id = False
            
        self.line_ids = [(0, 0, {
                                     'account_id': self.journal_id.default_credit_account_id.id,
                                     'coa_conac_id': self.journal_id.conac_credit_account_id.id,
                                     'credit': balance, 
                                     'amount_currency' : -amount_currency,
                                     'exclude_from_invoice_tab': True,
                                     'conac_move' : True,
                                     'currency_id' : currency_id,
                                     'move_id':False,
                                 }), 
                        (0, 0, {
                                     'account_id': self.journal_id.default_debit_account_id.id,
                                     'coa_conac_id': self.journal_id.conac_debit_account_id.id,
                                     'debit': balance,
                                     'amount_currency' : amount_currency,
                                     'exclude_from_invoice_tab': True,
                                     'conac_move' : True,
                                     'currency_id' : currency_id,
                                     'move_id':False,
                                 })]
          
        #self.conac_move = True



class ProvisionLine(models.Model):

    _name = 'provision.line'
    _description = 'Provision Line'


    line = fields.Integer('Line')
    concept = fields.Char('Concept')
    vat = fields.Char('Vat')
    retIVA = fields.Char('RetIVA')
    provision_id = fields.Many2one('provision', string='Provision')
    stage = fields.Many2one(related='provision_id.stage', string='Stage',readonly=False)    
    excercise = fields.Char(related='provision_id.excercise', string='excercise',readonly=False)
    product_id = fields.Many2one('product.product',"Product")
    name = fields.Char(string='Label')
    program_code_id = fields.Many2one('program.code', string='Program Code')
    egress_key_id = fields.Many2one("egress.keys", string="Egress Key")
    operation_type_id = fields.Many2one('operation.type',
                                        related='provision_id.operation_type_id', string="Operation Type")
    operation_type_name = fields.Char(
        related='provision_id.operation_type_id.name', string='name')
    journal_id = fields.Many2one(related='provision_id.journal_id', store=True, index=True, copy=False)
    company_id = fields.Many2one(related='provision_id.company_id', store=True, readonly=True)
    type_of_bussiness_line = fields.Char("Type Of Bussiness Line")
    other_amounts = fields.Monetary("Other Amounts")
    project_key = fields.Char(string='Project Key')
    invoice_vault_folio = fields.Char('Invoice vault folio')
    turn_type = fields.Char("Turn type")
    invoice_uuid = fields.Char("Invoice UUID")
    invoice_series = fields.Char("Invoice Series")
    
    folio_invoice = fields.Char("Folio Invoice")
    vault_folio = fields.Char("Vault folio")
    
    account_id = fields.Many2one('account.account', string='Account',
        index=True, ondelete="restrict", check_company=True,
        domain=[('deprecated', '=', False)])
    quantity = fields.Float(string='Quantity',
        default=1.0, digits='Product Unit of Measure',
        help="The optional quantity expressed by this line, eg: number of product sold. "
             "The quantity is not a legal requirement but is very useful for some reports.")


    discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
    price_unit = fields.Monetary('Price',digits='Product Price')
    subtotal = fields.Monetary(string='Subtotal',compute='get_price_subtotal',store=True)
    amount_tax = fields.Monetary(string='Tax Amount',compute='get_tax_amount',store=True)
    currency_id = fields.Many2one(related='company_id.currency_id',string='Company Currency',
        readonly=True, store=True,
        help='Utility field to express amount currency')
    tax_ids = fields.Many2many('account.tax', string="Taxes")

    @api.onchange('program_code_id')
    def onchange_program_code(self):
        if self.program_code_id and self.program_code_id.item_id and self.program_code_id.item_id.unam_account_id:
            self.account_id = self.program_code_id.item_id.unam_account_id.id

    # @api.depends('subtotal', 'price_total')
    # def get_price_tax_cr(self):
    #     for rec in self:

    #         if rec.currency_id and rec.company_id.currency_id and rec.currency_id != rec.company_id.currency_id:
    #             amount_currency = abs(rec.price_total - rec.subtotal)
    #             balance = self.currency_id._convert(
    #                 amount_currency, rec.company_currency_id, rec.company_id, rec.move_id.date)
    #             rec.tax_price_cr = balance
    #         else:
    #             balance = abs(rec.price_total - rec.subtotal)
    #             rec.tax_price_cr = balance

    # tax_price_cr = fields.Monetary(string='Tax Price', store=True, readonly=True,
    #                                currency_field='currency_id', compute="get_price_tax_cr")


    def create(self, vals):
        lines = super(ProvisionLine, self).create(vals)
        if any(lines.filtered(lambda x: not x.egress_key_id)):
            raise ValidationError(_("Please add Egress Key into lines"))
        return lines

    def write(self, vals):
        result = super(ProvisionLine, self).write(vals)
        if 'egress_key_id' in vals:
            if any(self.filtered(lambda x:not x.egress_key_id and x.provision_id.payment_state == 'draft')):
                raise ValidationError(_("Please add Egress Key into lines"))
        return result

    @api.depends('price_unit','tax_ids','amount_tax')
    def get_price_subtotal(self):
        for rec in self:
            rec.subtotal = (rec.price_unit*rec.quantity) + rec.amount_tax
  
    @api.depends('price_unit','tax_ids')
    def get_tax_amount(self):
        for rec in self:
            amount = 0
            if rec.tax_ids:
                taxes_res = rec.tax_ids._origin.compute_all(rec.price_unit,quantity=1)
                amount = taxes_res['total_included'] - taxes_res['total_excluded']
            rec.amount_tax = amount 


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    total_provision_move = fields.Integer(compute="total_provision_move_ids",store=True,string="Payment Request")
    is_provision_request_generate = fields.Boolean("Provision Request",copy=False)
    provision_amount_total = fields.Float("Provision Amount Total")
    provision_payment_state = fields.Selection([('draft', 'Draft'), ('registered', 'Registered'),
                                    ('provision', 'Provisions'),
                                    ('rejected', 'Rejected'),
                                    ('cancel', 'Cancel')], default='draft', copy=False)
    is_hide_provision_from_view = fields.Boolean(string="Hide Provision",default=False,copy=False)
    
    def check_previous_number_records(self):
        provision_id = self.env['account.move'].search([('provision_payment_state','=','provision'),('is_provision_request','=',True),('previous_number','=',self.previous_number)],limit=1)
        if not provision_id:
            raise ValidationError(_("Previous Number %s not found into provision")%self.previous_number)
        if provision_id.partner_id and self.partner_id and provision_id.partner_id.id != self.partner_id.id:
            raise ValidationError(_("Should NOT allow placing a different provider"))
        
        provision_payment_ids = self.env['account.move'].search([('payment_state','!=','cancel'),('is_payment_request','=',True),('previous_number','=',self.previous_number)])
        total_payment = sum(x.amount_total for x in  provision_payment_ids)
        if provision_id.provision_amount_total < total_payment:
            raise ValidationError(_("Total Payment amount %f exceeds the original amount of the provision %f")%(total_payment,provision_id.provision_amount_total))
        provision_program_ids = provision_id.invoice_line_ids.mapped('program_code_id').ids
        
        for line in self.invoice_line_ids.filtered(lambda x:x.program_code_id):
            if line.program_code_id.id not in provision_program_ids:
                raise ValidationError(_("Program Code %s not found into provision")%(line.program_code_id.program_code))
        if not self.is_create_from_provision:
            self.provision_move_id = provision_id.id
            self.is_create_from_provision = True
            self.create_journal_line_for_approved_payment()
            self.payment_state = 'approved_payment'
            for line in self.invoice_line_ids.filtered(lambda x:x.program_code_id):
                line.update_provision_amount_data(line)
                
    @api.model_create_multi
    def create(self, vals_list):
        result = super(AccountMove, self).create(vals_list)
        for res in result: 
            if res.previous_number and res.is_payment_request:
                res.check_previous_number_records()
        return result

    def write(self,vals):
        result = super(AccountMove, self).write(vals)
        
        if vals.get('previous_number',False) or vals.get('line_ids',[]):
            for rec in self.filtered(lambda x:x.previous_number and x.is_payment_request):
                rec.check_previous_number_records()
        
        if vals.get('partner_id',False):
            for rec in self.filtered(lambda x:x.is_create_from_provision and x.previous_number and x.is_payment_request):
                rec.check_previous_number_records()
        
        return result
    
    @api.depends('provision_move_ids')
    def total_provision_move_ids(self):
        for rec in self:
            rec.total_provision_move = len(rec.provision_move_ids)
            
    @api.constrains('previous_number')
    def _check_previous_number(self):
        for rec in self.filtered(lambda x:x.is_provision_request and x.previous_number):
            code_id = self.env['account.move'].search([('is_provision_request','=',True),('previous_number','=',rec.previous_number),('id','!=',rec.id)],limit=1)
            if code_id:
                raise ValidationError(_("Previous Number Must Be Unique"))
    
    def action_register(self):
        result = super(AccountMove,self).action_register()
        for move in self:
            if move.is_provision_request:
                move.provision_payment_state = 'registered'
        return result
    
    def action_draft_budget(self):
        self.ensure_one()
        if self.is_provision_request:
            if self.provision_move_ids:
                raise ValidationError(_("Should not allow returning to draft because provision already has related requests"))
            self.provision_payment_state = 'draft'
        result = super(AccountMove,self).action_draft_budget()
        return result
    
    def button_cancel(self):
        result = super(AccountMove,self).button_cancel()
        for record in self.filtered(lambda x:x.is_create_from_provision and x.is_payment_request):
            for line in record.invoice_line_ids.filtered(lambda x:x.program_code_id):
                line.update_provision_amount_data(line)        
        return result
        
    def action_cancel_budget(self):
        for record in self.filtered(lambda x:x.is_provision_request):
            if record.provision_move_ids:
                raise ValidationError(_("Should not allow cancel because provision already has related requests"))
            record.provision_payment_state = 'cancel'
            record.cancel_payment_revers_entry()
            record.add_budget_available_amount()
        result = super(AccountMove,self).action_cancel_budget()
        return result
    
    def set_provision_payment_state_provision(self):
        self.provision_payment_state = 'provision'
        self.provision_amount_total = self.amount_total
        for line in self.invoice_line_ids:
            line.provision_price = line.price_unit
            
    def generate_payment_request(self):
        if self.amount_total==0:
            raise ValidationError(_("A new request can no longer be entered because the amount of the original request is being exceeded."))
            return 
        vals = {'folio_dependency':False,'is_provision_request':False,
                'payment_state':'approved_payment','provision_move_id':self.id,
                'is_create_from_provision':True,'invoice_date':self.invoice_date}
        new_move = self.copy(vals)
        #new_move = self.copy_data(vals)
        new_move.is_payment_request = True
        for line in new_move.invoice_line_ids.filtered(lambda x:x.program_code_id):
            current_program_lines = self.env['account.move.line'].search([('move_id.payment_state','!=','cancel'),('exclude_from_invoice_tab','=',False),('program_code_id','=',line.program_code_id.id),('move_id','!=',new_move.id),('move_id','in',self.provision_move_ids.ids)])
            total_price = sum(x.price_unit for x in current_program_lines)
            new_price = line.provision_price - total_price
            if new_price < 0:
                new_price = 0
            line.with_context(check_move_validity=False).price_unit = new_price
            new_move.with_context(check_move_validity=False)._onchange_invoice_line_ids()
            
        if new_move.previous_number:
            new_move.check_previous_number_records()
        payment_move_lines = new_move.line_ids.filtered(lambda x:x.is_for_approved_payment)
        if payment_move_lines:
            payment_move_lines.unlink()
        new_move.create_journal_line_for_approved_payment()
        
        for line in new_move.invoice_line_ids.filtered(lambda x:x.program_code_id):
            line.update_provision_amount_data(line)
        
        #====Change the amount of the provision view=============#
#         for line in self.invoice_line_ids:
#             line.with_context(check_move_validity=False).price_unit = 0
#             self.with_context(check_move_validity=False)._onchange_invoice_line_ids()
#         payment_move_lines = self.line_ids.filtered(lambda x:x.is_for_approved_payment)
#         if payment_move_lines:
#             payment_move_lines.unlink()
#         self.create_journal_line_for_approved_payment()
            
        #========================================================#
        if self.amount_total==0:
            self.state='cancel'
            self.is_hide_provision_from_view = True
        else:
            self.state='draft'
            self.is_hide_provision_from_view = False
        return self.payment_state

    def action_provision_payment_request(self):
        return {
                'name': 'Operations',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'views': [(self.env.ref("jt_supplier_payment.payment_req_tree_view_diff").id, 'tree'), (self.env.ref("jt_supplier_payment.payment_req_form_view").id, 'form')],
                'res_model': 'account.move',
                'domain': [('provision_move_id', '=', self.id)],
                'type': 'ir.actions.act_window',
                'context':{'from_provision_view':True}
            }

    def get_all_action_ids(self):
        hide_list = [] 
        generate_batch_sheet = self.env.ref("jt_supplier_payment.action_account_invoice_from_list_batch_sheet")
        if generate_batch_sheet:
             hide_list.append(generate_batch_sheet.id)
        
        reg_payment = self.env.ref("account.action_account_invoice_from_list")
        if reg_payment:
             hide_list.append(reg_payment.id)
             
        refund = self.env.ref("account.action_move_switch_invoice_to_credit_note")
        if refund:
             hide_list.append(refund.id)
             
        pac_update = self.env.ref("l10n_mx_edi.update_pac_status_server_action")
        if pac_update:
             hide_list.append(pac_update.id)
             
        cfdi = self.env.ref("l10n_mx_edi.l10n_mx_edi_revert_cancellation")
        if cfdi:
             hide_list.append(cfdi.id)
             
        other_payroll = self.env.ref("jt_supplier_payment.confirm_other_then_payroll")
        if other_payroll:
             hide_list.append(other_payroll.id)
             
        pension_payroll = self.env.ref("jt_supplier_payment.confirm_pension_payroll_payment")
        if pension_payroll:
             hide_list.append(pension_payroll.id)
        if self.env.context and not self.env.context.get('default_is_payroll_payment_request',False):
            register = self.env.ref("jt_supplier_payment.register_pension_payroll_payment")
            if register:
                 hide_list.append(register.id)
                 
        date_change = self.env.ref("jt_account_module_design.action_invoice_date_all")
        if date_change:
             hide_list.append(date_change.id)
             
        cancel_payment_method = self.env.ref("jt_check_controls.cancel_payment_method")
        if cancel_payment_method:
             hide_list.append(cancel_payment_method.id)
             
        reverse = self.env.ref("account.action_view_account_move_reversal")
        if reverse:
             hide_list.append(reverse.id)
             
        post_entry = self.env.ref("account.action_validate_account_move")
        if post_entry:
             hide_list.append(post_entry.id)

        return hide_list

    def get_all_action_ids_factura(self):
        hide_list = []
        generate_batch_sheet = self.env.ref("jt_supplier_payment.action_account_invoice_from_list_batch_sheet")
        if generate_batch_sheet:
            hide_list.append(generate_batch_sheet.id)

        refund = self.env.ref("account.action_move_switch_invoice_to_credit_note")
        if refund:
            hide_list.append(refund.id)

        pac_update = self.env.ref("l10n_mx_edi.update_pac_status_server_action")
        if pac_update:
            hide_list.append(pac_update.id)

        cfdi = self.env.ref("l10n_mx_edi.l10n_mx_edi_revert_cancellation")
        if cfdi:
            hide_list.append(cfdi.id)

        other_payroll = self.env.ref("jt_supplier_payment.confirm_other_then_payroll")
        if other_payroll:
            hide_list.append(other_payroll.id)

        pension_payroll = self.env.ref("jt_supplier_payment.confirm_pension_payroll_payment")
        if pension_payroll:
            hide_list.append(pension_payroll.id)
        if self.env.context and not self.env.context.get('default_is_payroll_payment_request', False):
            register = self.env.ref("jt_supplier_payment.register_pension_payroll_payment")
            if register:
                hide_list.append(register.id)

        date_change = self.env.ref("jt_account_module_design.action_invoice_date_all")
        if date_change:
            hide_list.append(date_change.id)

        cancel_payment_method = self.env.ref("jt_check_controls.cancel_payment_method")
        if cancel_payment_method:
            hide_list.append(cancel_payment_method.id)

        post_entry = self.env.ref("account.action_validate_account_move")
        if post_entry:
            hide_list.append(post_entry.id)

        validate_budget = self.env.ref("jt_supplier_payment.validate_supplier_payment_request")
        if validate_budget:
            hide_list.append(validate_budget.id)

        return hide_list

    def get_all_action_ids_nota(self):
        hide_list = []
        generate_batch_sheet = self.env.ref("jt_supplier_payment.action_account_invoice_from_list_batch_sheet")
        if generate_batch_sheet:
            hide_list.append(generate_batch_sheet.id)

        pac_update = self.env.ref("l10n_mx_edi.update_pac_status_server_action")
        if pac_update:
            hide_list.append(pac_update.id)

        cfdi = self.env.ref("l10n_mx_edi.l10n_mx_edi_revert_cancellation")
        if cfdi:
            hide_list.append(cfdi.id)

        other_payroll = self.env.ref("jt_supplier_payment.confirm_other_then_payroll")
        if other_payroll:
            hide_list.append(other_payroll.id)

        pension_payroll = self.env.ref("jt_supplier_payment.confirm_pension_payroll_payment")
        if pension_payroll:
            hide_list.append(pension_payroll.id)
        if self.env.context and not self.env.context.get('default_is_payroll_payment_request', False):
            register = self.env.ref("jt_supplier_payment.register_pension_payroll_payment")
            if register:
                hide_list.append(register.id)

        date_change = self.env.ref("jt_account_module_design.action_invoice_date_all")
        if date_change:
            hide_list.append(date_change.id)

        cancel_payment_method = self.env.ref("jt_check_controls.cancel_payment_method")
        if cancel_payment_method:
            hide_list.append(cancel_payment_method.id)

        post_entry = self.env.ref("account.action_validate_account_move")
        if post_entry:
            hide_list.append(post_entry.id)

        validate_budget = self.env.ref("jt_supplier_payment.validate_supplier_payment_request")
        if validate_budget:
            hide_list.append(validate_budget.id)

        return hide_list
        
class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    provision_id = fields.Many2one('provision')
    provision_price = fields.Float("Provision Price")
    
    def update_payment_approve_amount_provision(self,payment_move_lines):
        if any(payment_move_lines.filtered(lambda x: x.debit==0 and x.credit==0)):
            if payment_move_lines:
                payment_move_id = payment_move_lines[0].move_id
                payment_move_lines.unlink()
                payment_move_id.create_journal_line_for_approved_payment()
        else:
            amount_total = sum(x.price_total for x in self.move_id.invoice_line_ids.filtered(lambda x:x.program_code_id))    
            if self.move_id.currency_id != self.move_id.company_id.currency_id:
                amount_currency = abs(amount_total)
                balance = self.move_id.currency_id._convert(amount_currency, self.move_id.company_currency_id, self.move_id.company_id, self.move_id.date)
                currency_id = self.move_id.currency_id and self.move_id.currency_id.id or False
            else:
                balance = abs(amount_total)
                amount_currency = 0.0
                currency_id = False
                
            for pat_line in payment_move_lines:
                if pat_line.credit > 0:
                    pat_line.with_context(check_move_validity=False).credit = balance
                    pat_line.with_context(check_move_validity=False).amount_currency =  -amount_currency
                else:
                    pat_line.with_context(check_move_validity=False).debit = balance
                    pat_line.with_context(check_move_validity=False).amount_currency =  amount_currency
    
    def update_provision_amount_data(self,line):
        current_program_lines = self.env['account.move.line'].search([('move_id.payment_state','!=','cancel'),('exclude_from_invoice_tab','=',False),('program_code_id','=',line.program_code_id.id),('move_id.provision_move_id','=',line.move_id.provision_move_id.id)])
        provision_line = self.env['account.move.line'].search([('move_id.payment_state','!=','cancel'),('exclude_from_invoice_tab','=',False),('program_code_id','=',line.program_code_id.id),('move_id','=',line.move_id.provision_move_id.id)],limit=1)
        
        total_price = sum(x.price_unit for x in current_program_lines)
        if provision_line:
            new_price = provision_line.provision_price - total_price
            if new_price < 0:
                new_price = 0
            provision_line.with_context(check_move_validity=False).price_unit = new_price
            provision_line.with_context(check_move_validity=False)._onchange_price_subtotal()
            provision_line.move_id.with_context(check_move_validity=False)._onchange_invoice_line_ids()
            provision_line.move_id.with_context(check_move_validity=False)._recompute_dynamic_lines(recompute_all_taxes=True, recompute_tax_base_amount=True)
            
            payment_move_lines = provision_line.move_id.line_ids.filtered(lambda x:x.is_for_approved_payment)
            if payment_move_lines:
                provision_line.update_payment_approve_amount_provision(payment_move_lines)

            if provision_line.move_id.amount_total==0:
                provision_line.move_id.state='cancel'
                provision_line.move_id.is_hide_provision_from_view = True
            else:
                provision_line.move_id.state='draft'
                provision_line.move_id.is_hide_provision_from_view = False
            
    def write(self, vals):
        result = super(AccountMoveLine,self).write(vals)
        if vals.get('price_unit'):
            for line in self.filtered(lambda x:not x.exclude_from_invoice_tab and x.move_id and x.move_id.is_create_from_provision and x.move_id.previous_number and x.move_id.is_payment_request):
                rec = line.move_id
                payment_move_lines = rec.line_ids.filtered(lambda x:x.is_for_approved_payment)
                if payment_move_lines:
                    line.update_payment_approve_amount_provision(payment_move_lines)
                line.update_provision_amount_data(line)
        return result

class AccountPayment(models.Model):

    _inherit = 'account.payment'

    def get_hide_action_ids(self):
        hide_list = [] 
        payment_date_set = self.env.ref("jt_account_module_design.action_payment_date_all")
        if payment_date_set:
             hide_list.append(payment_date_set.id)

        payment_declined = self.env.ref("jt_supplier_payment.action_payment_declined_call")
        if payment_declined:
             hide_list.append(payment_declined.id)

        return hide_list            

    def get_hide_action_income_ids(self):
        hide_list = [] 
        payment_date_set = self.env.ref("jt_account_module_design.action_payment_date_all_other")
        if payment_date_set:
             hide_list.append(payment_date_set.id)

        payment_declined = self.env.ref("jt_supplier_payment.action_payment_declined_call_other")
        if payment_declined:
             hide_list.append(payment_declined.id)

        return hide_list

    def get_all_action_ids_cobro(self):
        hide_list = []
        formato_blanco = self.env.ref("jt_supplier_payment.action_generate_bank_layout_payment")
        if formato_blanco:
            hide_list.append(formato_blanco.id)

        carga_blancario = self.env.ref("jt_supplier_payment.action_load_bank_layout_payment")
        if carga_blancario:
            hide_list.append(carga_blancario.id)

        reassign_budget = self.env.ref("jt_budget_mgmt.action_reassign_budget")
        if reassign_budget:
            hide_list.append(reassign_budget.id)

        fecha_cobro = self.env.ref("jt_account_module_design.action_payment_date_all")
        if fecha_cobro:
            hide_list.append(fecha_cobro.id)
            
        payment_date_set = self.env.ref("jt_account_module_design.action_payment_date_all_other")
        if payment_date_set:
             hide_list.append(payment_date_set.id)

        payment_declined = self.env.ref("jt_supplier_payment.action_payment_declined_call_other")
        if payment_declined:
             hide_list.append(payment_declined.id)

        return hide_list