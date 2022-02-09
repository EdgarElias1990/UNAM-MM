from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
from datetime import datetime


class VerficationOfExpense(models.Model):

    _name = 'expense.verification'
    _description = 'Verification Of Expense'

    status = fields.Selection([('eraser', 'Eraser'),
                               ('approve', 'Approved'),
                               ('reject', 'Rejected')], string="Status", default="eraser")
    project_id = fields.Many2one('project.project', string='Project Code')
    program_code_id = fields.Many2one(related='project_id.program_code') 
    project_number_id = fields.Char(
        related='project_id.number', string="Project Number")
    custom_stage_id = fields.Many2one('project.custom.stage', string='Stage')
    
    exercise = fields.Text('Exercise')
    exchange_rate = fields.Float('Exchange Rate')
    expense_journal_id = fields.Many2one(
        'account.journal', string="Expense Journal")
    dependence = fields.Many2one('dependency', string="Dependency")
    subdependence = fields.Many2one('sub.dependency', string='Sub Dependence')
    upa_code = fields.Many2one('policy.keys', string='UPA Code')
    type_of_operation = fields.Many2one(
        'operation.type', string='Type Of Operation')
    doc_type = fields.Many2one(
        'upa.document.type', string='Document Type')
    number = fields.Text(
        rejected='project_id.stage_identifier', string='Number')
    type_of_currency = fields.Selection(
        [('national', 'National Currency'),
            ('foreign', 'Foreign currency')
         ], string="Type Of Currency", default='national')
    administrative_forum = fields.Text('Administrative Forms')
    Vouchers = fields.Binary('Vouchers')
    reg_date = fields.Date('Registration Date')
    application_approval_date = fields.Date('Application Approval Date')
    beneficiary_name = fields.Many2one(
        'res.partner', string='Beneficiary Name')
    rfc = fields.Char(related='beneficiary_name.vat', string='RFC')
    invoice_vault_folio = fields.Text('Invoice vault folio')
    uuid_invoice = fields.Text('UUID Invoice')
    invoice_series = fields.Text('Invoice Series')
    invoice_folio = fields.Text('Invoice Folio')
    type_of_aggrement = fields.Many2one(
        'agreement.agreement.type', string='Type Of Agreement')
    currency_id = fields.Many2one(
        'res.currency', help='The currency used to enter statement', string="Currency",default=lambda self: self.env.user.company_id.currency_id)
    agreement_number = fields.Many2one(
        'bases.collaboration', string='Agreement Number')
    agreement_name = fields.Char(
        related='agreement_number.name', string='Agreement Name')
    
    custom_type_of_aggrement = fields.Char("Type Of Agreement")
    custom_agreement_number = fields.Char("Agreement Number")
    custom_agreement_name = fields.Char("Agreement Name")
    
    tech_support = fields.Many2one('hr.employee', string='Technical Support')
    admin_manager = fields.Many2one(
        'hr.employee', string='Administrative manager')
    ext_sponsor = fields.Text('External sponsor')
    observation = fields.Text('Observations')
    move_line_ids = fields.One2many(
        'account.move.line', 'expense_id', string="Journal Items")
    reason_for_rejection = fields.Char('Reason for rejection')
    verifcation_expense_ids = fields.One2many(
        'verification.expense.line', 'verification_expense_id', string='Verfication Expense Line')

    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True,
        compute='_compute_amount')
    amount_tax = fields.Monetary(string='Tax', store=True, readonly=True,
        compute='_compute_amount')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True,
        compute='_compute_amount',)

    program_code_ids = fields.Many2many('program.code',string='Program Codes',compute="get_program_code_ids",store=True)
    
    @api.depends('project_id','project_id.project_programcode_ids','project_id.project_programcode_ids.program_code_id')
    def get_program_code_ids(self):
        for rec in self:
            program_code_ids = []
            if rec.project_id:
                program_code_ids = rec.project_id.project_programcode_ids.mapped('program_code_id').ids
            rec.program_code_ids = [(6, 0, program_code_ids)]
            
    @api.depends('verifcation_expense_ids','verifcation_expense_ids.price','verifcation_expense_ids.tax_ids')
    def _compute_amount(self):
        for rec in self:
            rec.amount_untaxed = sum(x.price for x in rec.verifcation_expense_ids)
            rec.amount_tax = sum(x.amount_tax for x in rec.verifcation_expense_ids)
            rec.amount_total = rec.amount_untaxed + rec.amount_tax 
            
    def check_program_code_assign_amount(self):
        for rec in self:
            if rec.verifcation_expense_ids:
                for program in rec.verifcation_expense_ids.mapped('program_code'):
                    lines = rec.verifcation_expense_ids.filtered(lambda x:x.program_code.id == program.id)
                    total_verification_amount = sum(x.subtotal for x in lines)
                    total_assign_amount = 0
                    
                    b_s_month = rec.reg_date.month
                    if b_s_month in (1, 2, 3):
                        total_assign_amount = program.total_1_assigned_amt
                    elif b_s_month in (4, 5, 6):
                        total_assign_amount = program.total_2_assigned_amt
                    elif b_s_month in (7, 8, 9):
                        total_assign_amount = program.total_3_assigned_amt
                    elif b_s_month in (10, 11, 12):
                        total_assign_amount = program.total_4_assigned_amt
                    
                    if total_assign_amount < total_verification_amount:
                        raise ValidationError(_("There is not enough allocated to approve this verification of expense,verify the amount allocated to the corresponding quarter"))
                        
    def action_approve(self):
        self.check_program_code_assign_amount()
        self.status = 'approve'
        
        if self.expense_journal_id:
            journal = self.expense_journal_id
            if not journal.ai_credit_account_id or not journal.conac_ai_credit_account_id \
                    or not journal.ai_debit_account_id or not journal.conac_ai_debit_account_id:
                if self.env.user.lang == 'es_MX':
                    raise ValidationError(
                        _("Por favor configure la cuenta UNAM y CONAC en diario!"))
                else:
                    raise ValidationError(
                        _("Please configure UNAM and CONAC account in journal!"))

            if not journal.ei_credit_account_id or not journal.conac_ei_credit_account_id \
                    or not journal.ei_debit_account_id or not journal.conac_ei_debit_account_id:
                if self.env.user.lang == 'es_MX':
                    raise ValidationError(
                        _("Por favor configure la cuenta UNAM y CONAC en diario!"))
                else:
                    raise ValidationError(
                        _("Please configure UNAM and CONAC account in journal!"))

            today = datetime.today().date()
            user = self.env.user
            partner_id = user.partner_id.id
            if self.beneficiary_name:
                partner_id = self.beneficiary_name.id
                
            amount = self.amount_total

            lines = [(0, 0, {
                                 'account_id': journal.ei_credit_account_id.id,
                                 'coa_conac_id': journal.conac_ei_credit_account_id.id,
                                 'credit': amount,
                                 'partner_id': partner_id,
                                 'expense_id': self.id,
                             }),
                                 (0, 0, {
                                     'account_id': journal.ei_debit_account_id.id,
                                     'coa_conac_id': journal.conac_ei_debit_account_id.id,
                                     'debit': amount,
                                     'partner_id': partner_id,
                                     'expense_id': self.id,
                                 }),                                 


#                                 (0, 0, {
#                                  'account_id': journal.ai_credit_account_id.id,
#                                  'coa_conac_id': journal.conac_ai_credit_account_id.id,
#                                  'credit': amount,
#                                  'partner_id': partner_id,
#                                  'expense_id': self.id,
#                              }),
#                                  (0, 0, {
#                                      'account_id': journal.ai_debit_account_id.id,
#                                      'coa_conac_id': journal.conac_ai_debit_account_id.id,
#                                      'debit': amount,
#                                      'partner_id': partner_id,
#                                      'expense_id': self.id,
#                                  }),
                             ]
            item_expense_account_ids = self.verifcation_expense_ids.mapped('program_code.item_id.unam_account_id')
            for account_id in item_expense_account_ids:
                item_amount = sum(x.subtotal for x in self.verifcation_expense_ids.filtered(lambda x:x.program_code and x.program_code.item_id and x.program_code.item_id.unam_account_id and x.program_code.item_id.unam_account_id.id==account_id.id))

                lines.append((0, 0, {
                                 'account_id': journal.ai_credit_account_id.id,
                                 'coa_conac_id': journal.conac_ai_credit_account_id.id,
                                 'credit': item_amount,
                                 'partner_id': partner_id,
                                 'expense_id': self.id,
                             }))                
                lines.append((0, 0, {
                                 'account_id': account_id.id,
                                 'coa_conac_id': account_id.coa_conac_id and account_id.coa_conac_id.id or False,
                                 'debit': item_amount,
                                 'partner_id': partner_id,
                                 'expense_id': self.id,
                             }))
                
            #===================particular Item records ===============#
                #===== Group 511 ======#
            item_line_ids = self.verifcation_expense_ids.filtered(lambda x:x.program_code and x.program_code.item_id.item in ('511','512','513','514','515','516','517','521','523','524','531'))
            if item_line_ids:

                if not journal.capitalizable_credit_account_id or not journal.conac_capitalizable_credit_account_id \
                        or not journal.capitalizable_debit_account_id or not journal.conac_capitalizable_debit_account_id:
                    if self.env.user.lang == 'es_MX':
                        raise ValidationError(
                            _("Por favor configure la cuenta UNAM y CONAC en diario!"))
                    else:
                        raise ValidationError(
                            _("Please configure UNAM and CONAC account in journal!"))
                
                item_amount = sum(x.subtotal for x in item_line_ids)
#                 account_id = journal.capitalizable_debit_account_id.id
#                 coa_conac_id =  journal.conac_capitalizable_debit_account_id.id
#                 
#                 item_id = item_line_ids.mapped('program_code.item_id')
#                 if item_id and item_id[0].unam_account_id:
#                     account_id = item_id[0].unam_account_id.id
#                     coa_conac_id = item_id[0].unam_account_id.coa_conac_id and item_id[0].unam_account_id.coa_conac_id.id or False
                     
                lines.append((0, 0, {
                                 'account_id': journal.capitalizable_credit_account_id.id,
                                 'coa_conac_id': journal.conac_capitalizable_credit_account_id.id,
                                 'credit': item_amount,
                                 'partner_id': partner_id,
                                 'expense_id': self.id,
                             }))
                
                lines.append((0, 0, {
                                     'account_id': journal.capitalizable_debit_account_id.id,
                                     'coa_conac_id': journal.conac_capitalizable_debit_account_id.id,
                                     'debit': item_amount,
                                     'partner_id': partner_id,
                                     'expense_id': self.id,
                                 }))
                

#                 #===== Group 512 ======#
#             item_line_ids = self.verifcation_expense_ids.filtered(lambda x:x.program_code and x.program_code.item_id.item =='512' )
#             if item_line_ids:
# 
#                 if not journal.capitalizable_credit_account_id or not journal.conac_capitalizable_credit_account_id \
#                         or not journal.capitalizable_debit_account_id or not journal.conac_capitalizable_debit_account_id:
#                     if self.env.user.lang == 'es_MX':
#                         raise ValidationError(
#                             _("Por favor configure la cuenta UNAM y CONAC en diario!"))
#                     else:
#                         raise ValidationError(
#                             _("Please configure UNAM and CONAC account in journal!"))
#                 
#                 item_amount = sum(x.subtotal for x in item_line_ids)
#                 account_id = journal.capitalizable_debit_account_id.id
#                 coa_conac_id =  journal.conac_capitalizable_debit_account_id.id
#                 
# #                 item_id = item_line_ids.mapped('program_code.item_id')
# #                 if item_id and item_id[0].unam_account_id:
# #                     account_id = item_id[0].unam_account_id.id
# #                     coa_conac_id = item_id[0].unam_account_id.coa_conac_id and item_id[0].unam_account_id.coa_conac_id.id or False
#                      
#                 lines.append(                                (0, 0, {
#                                  'account_id': journal.capitalizable_credit_account_id.id,
#                                  'coa_conac_id': journal.conac_capitalizable_credit_account_id.id,
#                                  'credit': item_amount,
#                                  'partner_id': partner_id,
#                                  'expense_id': self.id,
#                              }))
#                 
#                 lines.append((0, 0, {
#                                      'account_id': account_id,
#                                      'coa_conac_id': coa_conac_id,
#                                      'debit': item_amount,
#                                      'partner_id': partner_id,
#                                      'expense_id': self.id,
#                                  }))
# 
#                 #===== Group 513 ======#
#             item_line_ids = self.verifcation_expense_ids.filtered(lambda x:x.program_code and x.program_code.item_id.item =='513' )
#             if item_line_ids:
# 
#                 if not journal.capitalizable_credit_account_id or not journal.conac_capitalizable_credit_account_id \
#                         or not journal.capitalizable_debit_account_id or not journal.conac_capitalizable_debit_account_id:
#                     if self.env.user.lang == 'es_MX':
#                         raise ValidationError(
#                             _("Por favor configure la cuenta UNAM y CONAC en diario!"))
#                     else:
#                         raise ValidationError(
#                             _("Please configure UNAM and CONAC account in journal!"))
#                 
#                 item_amount = sum(x.subtotal for x in item_line_ids)
#                 account_id = journal.capitalizable_debit_account_id.id
#                 coa_conac_id =  journal.conac_capitalizable_debit_account_id.id
#                 
#                 item_id = item_line_ids.mapped('program_code.item_id')
#                 if item_id and item_id[0].unam_account_id:
#                     account_id = item_id[0].unam_account_id.id
#                     coa_conac_id = item_id[0].unam_account_id.coa_conac_id and item_id[0].unam_account_id.coa_conac_id.id or False
#                      
#                 lines.append(                                (0, 0, {
#                                  'account_id': journal.capitalizable_credit_account_id.id,
#                                  'coa_conac_id': journal.conac_capitalizable_credit_account_id.id,
#                                  'credit': item_amount,
#                                  'partner_id': partner_id,
#                                  'expense_id': self.id,
#                              }))
#                 
#                 lines.append((0, 0, {
#                                      'account_id': account_id,
#                                      'coa_conac_id': coa_conac_id,
#                                      'debit': item_amount,
#                                      'partner_id': partner_id,
#                                      'expense_id': self.id,
#                                  }))
# 
#                 #===== Group 514 ======#
#             item_line_ids = self.verifcation_expense_ids.filtered(lambda x:x.program_code and x.program_code.item_id.item =='514' )
#             if item_line_ids:
# 
#                 if not journal.capitalizable_credit_account_id or not journal.conac_capitalizable_credit_account_id \
#                         or not journal.capitalizable_debit_account_id or not journal.conac_capitalizable_debit_account_id:
#                     if self.env.user.lang == 'es_MX':
#                         raise ValidationError(
#                             _("Por favor configure la cuenta UNAM y CONAC en diario!"))
#                     else:
#                         raise ValidationError(
#                             _("Please configure UNAM and CONAC account in journal!"))
#                 
#                 item_amount = sum(x.subtotal for x in item_line_ids)
#                 account_id = journal.capitalizable_debit_account_id.id
#                 coa_conac_id =  journal.conac_capitalizable_debit_account_id.id
#                 
#                 item_id = item_line_ids.mapped('program_code.item_id')
#                 if item_id and item_id[0].unam_account_id:
#                     account_id = item_id[0].unam_account_id.id
#                     coa_conac_id = item_id[0].unam_account_id.coa_conac_id and item_id[0].unam_account_id.coa_conac_id.id or False
#                      
#                 lines.append(                                (0, 0, {
#                                  'account_id': journal.capitalizable_credit_account_id.id,
#                                  'coa_conac_id': journal.conac_capitalizable_credit_account_id.id,
#                                  'credit': item_amount,
#                                  'partner_id': partner_id,
#                                  'expense_id': self.id,
#                              }))
#                 
#                 lines.append((0, 0, {
#                                      'account_id': account_id,
#                                      'coa_conac_id': coa_conac_id,
#                                      'debit': item_amount,
#                                      'partner_id': partner_id,
#                                      'expense_id': self.id,
#                                  }))
# 
#                 #===== Group 515 ======#
#             item_line_ids = self.verifcation_expense_ids.filtered(lambda x:x.program_code and x.program_code.item_id.item =='515' )
#             if item_line_ids:
# 
#                 if not journal.capitalizable_credit_account_id or not journal.conac_capitalizable_credit_account_id \
#                         or not journal.capitalizable_debit_account_id or not journal.conac_capitalizable_debit_account_id:
#                     if self.env.user.lang == 'es_MX':
#                         raise ValidationError(
#                             _("Por favor configure la cuenta UNAM y CONAC en diario!"))
#                     else:
#                         raise ValidationError(
#                             _("Please configure UNAM and CONAC account in journal!"))
#                 
#                 item_amount = sum(x.subtotal for x in item_line_ids)
#                 account_id = journal.capitalizable_debit_account_id.id
#                 coa_conac_id =  journal.conac_capitalizable_debit_account_id.id
#                 
#                 item_id = item_line_ids.mapped('program_code.item_id')
#                 if item_id and item_id[0].unam_account_id:
#                     account_id = item_id[0].unam_account_id.id
#                     coa_conac_id = item_id[0].unam_account_id.coa_conac_id and item_id[0].unam_account_id.coa_conac_id.id or False
#                      
#                 lines.append(                                (0, 0, {
#                                  'account_id': journal.capitalizable_credit_account_id.id,
#                                  'coa_conac_id': journal.conac_capitalizable_credit_account_id.id,
#                                  'credit': item_amount,
#                                  'partner_id': partner_id,
#                                  'expense_id': self.id,
#                              }))
#                 
#                 lines.append((0, 0, {
#                                      'account_id': account_id,
#                                      'coa_conac_id': coa_conac_id,
#                                      'debit': item_amount,
#                                      'partner_id': partner_id,
#                                      'expense_id': self.id,
#                                  }))
#                 #===== Group 516 ======#
#             item_line_ids = self.verifcation_expense_ids.filtered(lambda x:x.program_code and x.program_code.item_id.item =='516' )
#             if item_line_ids:
# 
#                 if not journal.capitalizable_credit_account_id or not journal.conac_capitalizable_credit_account_id \
#                         or not journal.capitalizable_debit_account_id or not journal.conac_capitalizable_debit_account_id:
#                     if self.env.user.lang == 'es_MX':
#                         raise ValidationError(
#                             _("Por favor configure la cuenta UNAM y CONAC en diario!"))
#                     else:
#                         raise ValidationError(
#                             _("Please configure UNAM and CONAC account in journal!"))
#                 
#                 item_amount = sum(x.subtotal for x in item_line_ids)
#                 account_id = journal.capitalizable_debit_account_id.id
#                 coa_conac_id =  journal.conac_capitalizable_debit_account_id.id
#                 
#                 item_id = item_line_ids.mapped('program_code.item_id')
#                 if item_id and item_id[0].unam_account_id:
#                     account_id = item_id[0].unam_account_id.id
#                     coa_conac_id = item_id[0].unam_account_id.coa_conac_id and item_id[0].unam_account_id.coa_conac_id.id or False
#                      
#                 lines.append(                                (0, 0, {
#                                  'account_id': journal.capitalizable_credit_account_id.id,
#                                  'coa_conac_id': journal.conac_capitalizable_credit_account_id.id,
#                                  'credit': item_amount,
#                                  'partner_id': partner_id,
#                                  'expense_id': self.id,
#                              }))
#                 
#                 lines.append((0, 0, {
#                                      'account_id': account_id,
#                                      'coa_conac_id': coa_conac_id,
#                                      'debit': item_amount,
#                                      'partner_id': partner_id,
#                                      'expense_id': self.id,
#                                  }))
#                 #===== Group 517 ======#
#             item_line_ids = self.verifcation_expense_ids.filtered(lambda x:x.program_code and x.program_code.item_id.item =='517' )
#             if item_line_ids:
# 
#                 if not journal.capitalizable_credit_account_id or not journal.conac_capitalizable_credit_account_id \
#                         or not journal.capitalizable_debit_account_id or not journal.conac_capitalizable_debit_account_id:
#                     if self.env.user.lang == 'es_MX':
#                         raise ValidationError(
#                             _("Por favor configure la cuenta UNAM y CONAC en diario!"))
#                     else:
#                         raise ValidationError(
#                             _("Please configure UNAM and CONAC account in journal!"))
#                 
#                 item_amount = sum(x.subtotal for x in item_line_ids)
#                 account_id = journal.capitalizable_debit_account_id.id
#                 coa_conac_id =  journal.conac_capitalizable_debit_account_id.id
#                 
#                 item_id = item_line_ids.mapped('program_code.item_id')
#                 if item_id and item_id[0].unam_account_id:
#                     account_id = item_id[0].unam_account_id.id
#                     coa_conac_id = item_id[0].unam_account_id.coa_conac_id and item_id[0].unam_account_id.coa_conac_id.id or False
#                      
#                 lines.append(                                (0, 0, {
#                                  'account_id': journal.capitalizable_credit_account_id.id,
#                                  'coa_conac_id': journal.conac_capitalizable_credit_account_id.id,
#                                  'credit': item_amount,
#                                  'partner_id': partner_id,
#                                  'expense_id': self.id,
#                              }))
#                 
#                 lines.append((0, 0, {
#                                      'account_id': account_id,
#                                      'coa_conac_id': coa_conac_id,
#                                      'debit': item_amount,
#                                      'partner_id': partner_id,
#                                      'expense_id': self.id,
#                                  }))
#                 #===== Group 521 ======#
#             item_line_ids = self.verifcation_expense_ids.filtered(lambda x:x.program_code and x.program_code.item_id.item =='521' )
#             if item_line_ids:
# 
#                 if not journal.capitalizable_credit_account_id or not journal.conac_capitalizable_credit_account_id \
#                         or not journal.capitalizable_debit_account_id or not journal.conac_capitalizable_debit_account_id:
#                     if self.env.user.lang == 'es_MX':
#                         raise ValidationError(
#                             _("Por favor configure la cuenta UNAM y CONAC en diario!"))
#                     else:
#                         raise ValidationError(
#                             _("Please configure UNAM and CONAC account in journal!"))
#                 
#                 item_amount = sum(x.subtotal for x in item_line_ids)
#                 account_id = journal.capitalizable_debit_account_id.id
#                 coa_conac_id =  journal.conac_capitalizable_debit_account_id.id
#                 
#                 item_id = item_line_ids.mapped('program_code.item_id')
#                 if item_id and item_id[0].unam_account_id:
#                     account_id = item_id[0].unam_account_id.id
#                     coa_conac_id = item_id[0].unam_account_id.coa_conac_id and item_id[0].unam_account_id.coa_conac_id.id or False
#                      
#                 lines.append(                                (0, 0, {
#                                  'account_id': journal.capitalizable_credit_account_id.id,
#                                  'coa_conac_id': journal.conac_capitalizable_credit_account_id.id,
#                                  'credit': item_amount,
#                                  'partner_id': partner_id,
#                                  'expense_id': self.id,
#                              }))
#                 
#                 lines.append((0, 0, {
#                                      'account_id': account_id,
#                                      'coa_conac_id': coa_conac_id,
#                                      'debit': item_amount,
#                                      'partner_id': partner_id,
#                                      'expense_id': self.id,
#                                  }))
#                 #===== Group 523 ======#
#             item_line_ids = self.verifcation_expense_ids.filtered(lambda x:x.program_code and x.program_code.item_id.item =='523' )
#             if item_line_ids:
# 
#                 if not journal.capitalizable_credit_account_id or not journal.conac_capitalizable_credit_account_id \
#                         or not journal.capitalizable_debit_account_id or not journal.conac_capitalizable_debit_account_id:
#                     if self.env.user.lang == 'es_MX':
#                         raise ValidationError(
#                             _("Por favor configure la cuenta UNAM y CONAC en diario!"))
#                     else:
#                         raise ValidationError(
#                             _("Please configure UNAM and CONAC account in journal!"))
#                 
#                 item_amount = sum(x.subtotal for x in item_line_ids)
#                 account_id = journal.capitalizable_debit_account_id.id
#                 coa_conac_id =  journal.conac_capitalizable_debit_account_id.id
#                 
#                 item_id = item_line_ids.mapped('program_code.item_id')
#                 if item_id and item_id[0].unam_account_id:
#                     account_id = item_id[0].unam_account_id.id
#                     coa_conac_id = item_id[0].unam_account_id.coa_conac_id and item_id[0].unam_account_id.coa_conac_id.id or False
#                      
#                 lines.append(                                (0, 0, {
#                                  'account_id': journal.capitalizable_credit_account_id.id,
#                                  'coa_conac_id': journal.conac_capitalizable_credit_account_id.id,
#                                  'credit': item_amount,
#                                  'partner_id': partner_id,
#                                  'expense_id': self.id,
#                              }))
#                 
#                 lines.append((0, 0, {
#                                      'account_id': account_id,
#                                      'coa_conac_id': coa_conac_id,
#                                      'debit': item_amount,
#                                      'partner_id': partner_id,
#                                      'expense_id': self.id,
#                                  }))
#                 #===== Group 524 ======#
#             item_line_ids = self.verifcation_expense_ids.filtered(lambda x:x.program_code and x.program_code.item_id.item =='524' )
#             if item_line_ids:
# 
#                 if not journal.capitalizable_credit_account_id or not journal.conac_capitalizable_credit_account_id \
#                         or not journal.capitalizable_debit_account_id or not journal.conac_capitalizable_debit_account_id:
#                     if self.env.user.lang == 'es_MX':
#                         raise ValidationError(
#                             _("Por favor configure la cuenta UNAM y CONAC en diario!"))
#                     else:
#                         raise ValidationError(
#                             _("Please configure UNAM and CONAC account in journal!"))
#                 
#                 item_amount = sum(x.subtotal for x in item_line_ids)
#                 account_id = journal.capitalizable_debit_account_id.id
#                 coa_conac_id =  journal.conac_capitalizable_debit_account_id.id
#                 
#                 item_id = item_line_ids.mapped('program_code.item_id')
#                 if item_id and item_id[0].unam_account_id:
#                     account_id = item_id[0].unam_account_id.id
#                     coa_conac_id = item_id[0].unam_account_id.coa_conac_id and item_id[0].unam_account_id.coa_conac_id.id or False
#                      
#                 lines.append(                                (0, 0, {
#                                  'account_id': journal.capitalizable_credit_account_id.id,
#                                  'coa_conac_id': journal.conac_capitalizable_credit_account_id.id,
#                                  'credit': item_amount,
#                                  'partner_id': partner_id,
#                                  'expense_id': self.id,
#                              }))
#                 
#                 lines.append((0, 0, {
#                                      'account_id': account_id,
#                                      'coa_conac_id': coa_conac_id,
#                                      'debit': item_amount,
#                                      'partner_id': partner_id,
#                                      'expense_id': self.id,
#                                  }))
#                 #===== Group 531 ======#
#             item_line_ids = self.verifcation_expense_ids.filtered(lambda x:x.program_code and x.program_code.item_id.item =='531')
#             if item_line_ids:
# 
#                 if not journal.capitalizable_credit_account_id or not journal.conac_capitalizable_credit_account_id \
#                         or not journal.capitalizable_debit_account_id or not journal.conac_capitalizable_debit_account_id:
#                     if self.env.user.lang == 'es_MX':
#                         raise ValidationError(
#                             _("Por favor configure la cuenta UNAM y CONAC en diario!"))
#                     else:
#                         raise ValidationError(
#                             _("Please configure UNAM and CONAC account in journal!"))
#                 
#                 item_amount = sum(x.subtotal for x in item_line_ids)
#                 account_id = journal.capitalizable_debit_account_id.id
#                 coa_conac_id =  journal.conac_capitalizable_debit_account_id.id
#                 
#                 item_id = item_line_ids.mapped('program_code.item_id')
#                 if item_id and item_id[0].unam_account_id:
#                     account_id = item_id[0].unam_account_id.id
#                     coa_conac_id = item_id[0].unam_account_id.coa_conac_id and item_id[0].unam_account_id.coa_conac_id.id or False
#                      
#                 lines.append(                                (0, 0, {
#                                  'account_id': journal.capitalizable_credit_account_id.id,
#                                  'coa_conac_id': journal.conac_capitalizable_credit_account_id.id,
#                                  'credit': item_amount,
#                                  'partner_id': partner_id,
#                                  'expense_id': self.id,
#                              }))
#                 
#                 lines.append((0, 0, {
#                                      'account_id': account_id,
#                                      'coa_conac_id': coa_conac_id,
#                                      'debit': item_amount,
#                                      'partner_id': partner_id,
#                                      'expense_id': self.id,
#                                  }))
            
            unam_move_val = {'ref': self.display_name,  'conac_move': True,
                             'dependancy_id' : self.dependence and self.dependence.id or False,
                             'sub_dependancy_id': self.subdependence and self.subdependence.id or False,
                             'date': today, 'journal_id': journal.id, 'company_id': self.env.user.company_id.id,
                             'line_ids': lines}
            
            move_obj = self.env['account.move']
            unam_move = move_obj.create(unam_move_val)
            unam_move.action_post()


class VerificationOfExpenseLine(models.Model):

    _name = 'verification.expense.line'
    _description = 'Verification Expense Line'

    row = fields.Text('Row')
    verification_expense_id = fields.Many2one(
        'expense.verification', string='Verification Expense')
    program_code = fields.Many2one('program.code', string='Program Code')
    price = fields.Monetary('Price')
    subtotal = fields.Monetary(string='Subtotal',compute='get_price_subtotal',store=True)
    amount_tax = fields.Monetary(string='Tax Amount',compute='get_tax_amount',store=True)
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.user.company_id.currency_id)
    amount = fields.Selection(
        [('mn_amount', 'MN amount'),
            ('amount_me', 'Amount ME')
         ], string="Amount")
    tax_ids = fields.Many2many('account.tax', string="Taxes")
    custom_stage_id = fields.Many2one('project.custom.stage', string='Stage')
    
    @api.depends('price','tax_ids','amount_tax')
    def get_price_subtotal(self):
        for rec in self:
            rec.subtotal = rec.price + rec.amount_tax
  
    @api.depends('price','tax_ids')
    def get_tax_amount(self):
        for rec in self:
            amount = 0
            if rec.tax_ids:
                taxes_res = rec.tax_ids._origin.compute_all(rec.price,quantity=1)
                amount = taxes_res['total_included'] - taxes_res['total_excluded']
            rec.amount_tax = amount 

class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    expense_id = fields.Many2one('expense.verification')
