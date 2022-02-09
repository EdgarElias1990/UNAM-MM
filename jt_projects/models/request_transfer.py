from odoo import models, fields, api,_
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta

class RequestTransfer(models.Model):

    _name = 'request.transfer'
    _description = 'Request for transfer'
    _rec_name = 'invoice'

    invoice = fields.Text('Invoice', readonly=True,
                          default='New')
    application_date = fields.Date('Application Date')
    request_area = fields.Text('Area requesting the transfer')
    # request_area = fields.Many2one('dependency')
    user_id = fields.Many2one(
        'res.users', string='Requesting User', default=lambda self: self.env.user.id)
    destination_journal_id = fields.Many2one(
        'account.journal', 'Destination Bank')
    destination_bank_id = fields.Many2one(
        related="destination_journal_id.bank_account_id", string='Destination Bank Account')
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.user.company_id.currency_id, string="Coin")

    amount_req_tranfer = fields.Monetary(
        string='Amount of the transfer requested', currency_field='currency_id')
    handover_date = fields.Date('Required handover Date', Required=True)
    application_concept = fields.Text('Application Concept')
    journal_id = fields.Many2one('account.journal')
    origin_journal_id = fields.Many2one(
        'account.journal', 'Origin Bank')
    origin_bank_id = fields.Many2one(
        related="origin_journal_id.bank_account_id", string='Origin Bank Account')
    aggrement = fields.Text('Agreement or Project reference')
    dependency_id = fields.Many2one('dependency', "Dependency")
    subdependency_id = fields.Many2one('sub.dependency', "Sub Dependency")
    fund_type = fields.Many2one('fund.type', "Background")
    investment_fund_id = fields.Many2one('investment.funds', 'Investment Fund')
    agreement_type_id = fields.Many2one(
        'agreement.agreement.type', 'Agreement Type')
    fund_id = fields.Many2one('agreement.fund', 'Fund')
    base_collabaration_id = fields.Many2one(
        'bases.collaboration', 'Name Of Agreements')

    move_line_ids = fields.One2many(
        'account.move.line', 'transfer_request_id', string="Journal Items")

    status = fields.Selection([('draft', 'Draft'),
                               ('requested', 'Requested'),
                               ('rejected', 'Rejected'),
                               ('approved', 'Approved'),
                               ('sent', 'Sent'),
                               ('confirmed', 'Confirmed'),
                               ('done', 'Done'),
                               ('canceled', 'Canceled')], string="Status", default="draft")


    reason_rejection = fields.Text("Reason for Rejection")
    program_code_id = fields.Many2one('program.code','Program Code')
    
    @api.onchange('program_code_id')
    def onchange_program_code_id(self):
        if self.program_code_id:
            self.dependency_id = self.program_code_id and self.program_code_id.dependency_id and self.program_code_id.dependency_id.id or False
            self.subdependency_id =  self.program_code_id and self.program_code_id.sub_dependency_id and self.program_code_id.sub_dependency_id.id or False
        else:
            self.dependency_id = False
            self.subdependency_id = False
             
    @api.constrains('amount_req_tranfer')
    def check_amount_req_tranfer(self):
        if self.amount_req_tranfer == 0:
            raise UserError(_('Please add Amount of the transfer requested'))

    def generate_request(self):
        self.status = 'requested'
        record = {

            'invoice': self.invoice,
            'operation_number':self.invoice,
            'bank_account_id': self.origin_journal_id.id,
            'desti_bank_account_id': self.destination_journal_id.id,
            'date': self.application_date,
            'user_id': self.user_id.id,
            'state': self.status,
            # 'unit_req_transfer_id': self.request_area.id,
            'project_request_id': self.id,
            'amount': self.amount_req_tranfer,
            'date_required': self.handover_date,
            'concept': self.application_concept,
            'agreement_number': self.aggrement,
            'dependency_id' : self.dependency_id and self.dependency_id.id or False,
            'sub_dependency_id' : self.subdependency_id and self.subdependency_id.id or False,
            'trasnfer_request':'projects',
        }
        self.env['request.open.balance.finance'].create(record)

    @api.model
    def create(self, vals):
        if vals.get('invoice', 'New') == 'New':
            vals['invoice'] = self.env['ir.sequence'].next_by_code(
                'request.transfer') or 'New'
        result = super(RequestTransfer, self).create(vals)
        return result

    def action_approved(self):
        self.status = 'approved'

    def confirmed_finance(self):
        self.status = 'confirmed'

        if self.journal_id:
            journal = self.journal_id
            if not journal.receivable_CFDIS_credit_account_id or not journal.conac_receivable_CFDIS_credit_account_id \
                    or not journal.receivable_CFDIS_debit_account_id or not journal.conac_receivable_CFDIS_debit_account_id:
                if self.env.user.lang == 'es_MX':
                    raise ValidationError(
                        _("Por favor configure la cuenta UNAM y CONAC en diario!"))
                else:
                    raise ValidationError(
                        _("Please configure UNAM and CONAC account in journal!"))

            if not journal.ministrations_credit_account_id or not journal.conac_ministrations_credit_account_id \
                    or not journal.ministrations_debit_account_id or not journal.conac_ministrations_debit_account_id:
                if self.env.user.lang == 'es_MX':
                    raise ValidationError(
                        _("Por favor configure la cuenta UNAM y CONAC en diario!"))
                else:
                    raise ValidationError(
                        _("Please configure UNAM and CONAC account in journal!"))

            if not journal.income_CFDIS_credit_account_id or not journal.conac_income_CFDIS_credit_account_id \
                    or not journal.income_CFDIS_debit_account_id or not journal.conac_income_CFDIS_debit_account_id:
                if self.env.user.lang == 'es_MX':
                    raise ValidationError(
                        _("Por favor configure la cuenta UNAM y CONAC en diario!"))
                else:
                    raise ValidationError(
                        _("Please configure UNAM and CONAC account in journal!"))

            if not self.origin_journal_id.default_credit_account_id or not self.origin_journal_id.conac_credit_account_id:
                if self.env.user.lang == 'es_MX':
                    raise ValidationError(
                        _("Por favor configure la cuenta UNAM y CONAC en Banco!"))
                else:
                    raise ValidationError(
                        _("Please configure UNAM and CONAC account in Bank!"))

                 
            today = datetime.today().date()
            user = self.env.user
            partner_id = user.partner_id.id
            amount = self.amount_req_tranfer
            name = ''
            if self.invoice:
                name += self.invoice


            unam_move_val = {'name': name, 'ref': name,  'conac_move': True,
                            'dependancy_id' : self.dependency_id and self.dependency_id.id or False,
                             'sub_dependancy_id': self.subdependency_id and self.subdependency_id.id or False, 

                             'date': today, 'journal_id': journal.id, 'company_id': self.env.user.company_id.id,
                             'line_ids': [(0, 0, {
                                 'account_id': journal.receivable_CFDIS_credit_account_id.id,
                                 'coa_conac_id': journal.conac_receivable_CFDIS_credit_account_id.id,
                                 'credit': amount,
                                 'partner_id': partner_id,
                                 'transfer_request_id': self.id,
                             }),
                                 (0, 0, {
                                     'account_id': journal.receivable_CFDIS_debit_account_id.id,
                                     'coa_conac_id': journal.conac_receivable_CFDIS_debit_account_id.id,
                                     'debit': amount,
                                     'partner_id': partner_id,
                                     'transfer_request_id': self.id,
                                 }),

                                (0, 0, {
                                 'account_id': self.origin_journal_id.default_credit_account_id.id,
                                 'coa_conac_id': self.origin_journal_id.conac_credit_account_id.id,
                                 'credit': amount,
                                 'partner_id': partner_id,
                                 'transfer_request_id': self.id,
                             }),
                                 (0, 0, {
                                     'account_id': journal.ministrations_debit_account_id.id,
                                     'coa_conac_id': journal.conac_ministrations_debit_account_id.id,
                                     'debit': amount,
                                     'partner_id': partner_id,
                                     'transfer_request_id': self.id,
                                 }),

                                (0, 0, {
                                 'account_id': journal.income_CFDIS_credit_account_id.id,
                                 'coa_conac_id': journal.conac_income_CFDIS_credit_account_id.id,
                                 'credit': amount,
                                 'partner_id': partner_id,
                                 'transfer_request_id': self.id,
                             }),
                                 (0, 0, {
                                     'account_id': journal.income_CFDIS_debit_account_id.id,
                                     'coa_conac_id': journal.conac_income_CFDIS_debit_account_id.id,
                                     'debit': amount,
                                     'partner_id': partner_id,
                                     'transfer_request_id': self.id,
                                 }),                                 
                                                                  
                             ]}
            move_obj = self.env['account.move']
            unam_move = move_obj.create(unam_move_val)
            unam_move.action_post()

    def reject_finance(self):
        self.status = 'rejected'

    def action_canceled(self):
        self.status = 'canceled'
