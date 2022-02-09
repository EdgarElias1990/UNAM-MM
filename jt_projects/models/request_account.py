from odoo import models, fields, api,_
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta

class RequestAccounts(models.Model):

    _name = 'request.accounts'
    _description = "Request to open account"
    _rec_name = 'invoice'

    @api.depends('project_id', 'project_id.project_programcode_ids', 'project_id.project_programcode_ids.program_code_id')
    def get_project_program_code(self):
        for req in self:
            if req.project_id:
                program_ids = req.project_id.project_programcode_ids.mapped('program_code_id')
                req.project_program_ids = [(6, 0, program_ids.ids)]
            else:
                req.project_program_ids = [(6, 0, [])]
                
    invoice = fields.Char("Invoice", readonly=True, copy=False)
    invoice_cancel = fields.Char("Invoice", readonly=True, copy=False)
    project_id = fields.Many2one('project.project', "Project Number")
    project_name = fields.Char(
        related='project_id.name', string="Project Name")
    program_code = fields.Many2one('program.code', string='Program Code')
    user_id = fields.Many2one('hr.employee',
                              related='project_id.responsible_name', string="Project Manager")
    project_type_identifier = fields.Many2one(
        related='project_id.project_type_identifier_id', string="Project Type Identifier")
    project_stage_identifier = fields.Many2one(
        related='project_id.stage_identifier_id', string="Number of stages")

    custom_stage_id = fields.Many2one(related='project_id.custom_stage_id',string='Number of stages')
    custom_project_type_id = fields.Many2one(related='project_id.custom_project_type_id',string='Project Type Identifier')
    
    ministrations_amount = fields.Float("Amount of ministrations")
    authorized_amount = fields.Float("Authorized Amount")
    observations = fields.Text("Observations")
    journal_id = fields.Many2one('account.journal')
    bank_account_id = fields.Many2one(
        "account.journal", string="Bank account", domain=[('type', '=', 'bank')])
    bank_acc_number_id = fields.Many2one('res.partner.bank',
                                         related='bank_account_id.bank_account_id', string="Bank Account")
    no_contract = fields.Char(
        related='bank_account_id.contract_number', string='Contract No.')
    customer_number = fields.Char(
        related='bank_account_id.customer_number', string="Contact No.")
    supporting_documentation = fields.Binary("Supporting Documentation")
    supporting_doc_name = fields.Char('supporting documentation name')
    reason_rejection = fields.Text(string="Reason for rejection")
    rejection_observations = fields.Text("Rejection observation")
    status = fields.Selection([('eraser', 'Eraser'),
                               ('request', 'Request'),
                               ('approved', 'Approved'),
                               ('confirmed', 'Confirmed'),
                               ('rejected', 'Rejected')], default='eraser', copy=False)

    move_type = fields.Selection([
        ('account cancel', 'Account Cancellation'),
        ('account open', 'Account Open'),
    ], 'Move Type')

    move_line_ids = fields.One2many(
        'account.move.line', 'open_request_id', string="Journal Items")

    project_program_ids = fields.Many2many('program.code', 'rel_project_program_code', 'req_id', 'code_id', compute="get_project_program_code")
    off_number = fields.Char('Número de Oficio')
    _sql_constraints = [
        ('oficiounico', 'unique(off_number)', 'El número de oficio ya existe')]

    @api.constrains('ministrations_amount')
    def check_ministrations_amount(self):
        if self.ministrations_amount == 0:
            raise UserError(_('Please add Amount of ministrations'))

    @api.constrains('authorized_amount')
    def check_authorized_amount(self):
        if self.authorized_amount == 0:
            raise UserError(_('Please add Authorized Amount'))

    def generate_request(self):
        self.status = 'request'
        if self.move_type == 'account cancel':
            if self.bank_account_id and not self.bank_account_id.default_debit_account_id:
                raise UserError(_('Please configure account into bank'))
            values= self.env['account.move.line'].search([('account_id', '=', self.bank_account_id.default_debit_account_id.id),('move_id.state', '=', 'posted')])
            account_balance = sum(x.debit-x.credit for x in values)
            if account_balance > 0:
                raise UserError(_('To request the cancellation of a bank account the account balance must be 0'))
        
    # @api.model
    # def create(self, vals):
    #     if vals.get('invoice', 'New') == 'New':
    #         vals['invoice'] = self.env['ir.sequence'].next_by_code(
    #             'request.accounts') or 'New'
    #     result = super(RequestAccounts, self).create(vals)
    #     return result


    @api.model
    def create(self, vals):
        result = super(RequestAccounts, self).create(vals)
        if result.move_type == 'account open':
            invoice = self.env['ir.sequence'].next_by_code('request.accounts')
            result.invoice = invoice

        elif result.move_type == 'account cancel':
            cancel = self.env['ir.sequence'].next_by_code('request.accounts.cancel') or 'New'
            result.invoice_cancel = cancel
            result.invoice = cancel.zfill(6)
    
        print("***",vals)
        return result


#     @api.onchange('project_no')
#     def onchage_project_no(self):
#         if self.project_no:
#             project = self.project_no
#             self.project_name = project.name
#             self.user_id = project.user_id if project.user_id else False
#             self.project_type_identifier = project.project_type
#             self.project_stage_identifier = project.stage_identifier

    def approve_account(self):
        self.write({'status': 'approved'})

    def confirm_account(self):
        self.write({'status': 'confirmed'})

        if self.journal_id and self.bank_account_id:
            journal = self.journal_id
            if not journal.default_debit_account_id or not journal.default_credit_account_id \
                    or not journal.conac_debit_account_id or not journal.conac_credit_account_id:
                if self.env.user.lang == 'es_MX':
                    raise ValidationError(
                        _("Por favor configure la cuenta UNAM y CONAC en diario!"))
                else:
                    raise ValidationError(
                        _("Please configure UNAM and CONAC account in journal!"))
                
            if self.bank_account_id and  not self.bank_account_id.default_debit_account_id or not self.bank_account_id.default_credit_account_id \
                    or not self.bank_account_id.conac_debit_account_id or not self.bank_account_id.conac_credit_account_id:
                if self.env.user.lang == 'es_MX':
                    raise ValidationError(
                        _("Por favor configure la cuenta UNAM y CONAC en diario!"))
                else:
                    raise ValidationError(
                        _("Please configure UNAM and CONAC account in journal!"))

            today = datetime.today().date()
            user = self.env.user
            partner_id = user.partner_id.id
            amount = self.authorized_amount
            name = ''
            if self.invoice:
                name += self.invoice


            unam_move_val = {'name': name, 'ref': name,  'conac_move': True,
                             'date': today, 'journal_id': journal.id, 'company_id': self.env.user.company_id.id,
                             'line_ids': [(0, 0, {
                                 'account_id': journal.default_credit_account_id.id,
                                 'coa_conac_id': journal.conac_credit_account_id.id,
                                 'credit': amount,
                                 'partner_id': partner_id,
                                 'open_request_id': self.id,
                             }),
                                 (0, 0, {
                                     'account_id': self.bank_account_id.default_debit_account_id.id,
                                     'coa_conac_id': self.bank_account_id.conac_debit_account_id.id,
                                     'debit': amount,
                                     'partner_id': partner_id,
                                     'open_request_id': self.id,
                                 }),
                             ]}
            move_obj = self.env['account.move']
            unam_move = move_obj.create(unam_move_val)
            unam_move.action_post()

    def reject_account(self):
        self.write({'status': 'rejected'})

    @api.onchange('project_id')
    def onchange_project_id(self):
        if self.project_id:
            self.program_code = self.project_id.program_code and self.project_id.program_code.id or False  
            self.bank_account_id = self.project_id and self.project_id.bank_account_id and self.project_id.bank_account_id.id or False 
        