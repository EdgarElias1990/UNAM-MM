from odoo import models, fields, api, _

class PaymentRequest(models.Model):

    _name = 'payment.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Payment Request"

    @api.depends('balance_req_id','balance_req_id.state')
    def get_is_balance_req_id_reject(self):
        for rec in self:
            is_balance_req_id_reject = False
            if rec.balance_req_id and rec.balance_req_id.state=='rejected':
                is_balance_req_id_reject = True
            rec.is_balance_req_id_reject = is_balance_req_id_reject
            
    name = fields.Char("Agreement Name")
    operation_number = fields.Char("Operation Number")
    balance_req_id = fields.Many2one("request.open.balance")
    type_of_operation = fields.Selection([('open_bal', 'Opening Balance'),
                                          ('increase', 'Increase'),
                                          ('retirement', 'Retirement'),
                                          ('withdrawal', 'Withdrawal for settlement')], string="Type of Operation")
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.user.company_id.currency_id)
    amount = fields.Monetary("Amount to withdraw")
    payment_method_id = fields.Many2one('l10n_mx_edi.payment.method', string="Payment Method")
    date = fields.Date("Date of operation")
    reference = fields.Char("Reference")
    counter_receipt_sheet = fields.Char("Counter Receipt Sheet")
    beneficiary_id = fields.Many2one('res.partner', "Beneficiary's name")
    bank_id = fields.Many2one("res.partner.bank", "Bank")
    account_number = fields.Char("Beneficiary account number")
    payment_request_number = fields.Char("Payment Request Number")
    state = fields.Selection([('draft', 'Draft'),
                              ('requested', 'Requested'),('paid','Paid'),('reject','Rejected')], 'State', default='draft')

    is_balance_req_id_reject = fields.Boolean(default=False,copy=False,store=True,compute=get_is_balance_req_id_reject)
    
    def action_paid(self):
        self.state = 'paid'

    def action_reject(self):

        self.state = 'reject'

    @api.depends('beneficiary_id','balance_req_id','balance_req_id.bases_collaboration_id','balance_req_id.bases_collaboration_id.beneficiary_ids')
    def get_bank_ids(self):
        for rec in self:
            partner_ids = []
            if rec.balance_req_id and rec.balance_req_id.bases_collaboration_id and rec.balance_req_id.bases_collaboration_id.beneficiary_ids:
                if self.beneficiary_id:
                    user = self.env['res.users'].sudo().search([('partner_id','=',self.beneficiary_id.id)],limit=1)
                    if user: 
                        emp_id = self.env['hr.employee'].sudo().search([('user_id','=',user.id)],limit=1)
                        if emp_id:
                            beneficiary = self.env['collaboration.beneficiary'].search([
                            ('collaboration_id', '=', rec.balance_req_id.bases_collaboration_id.id), ('employee_id', '=', emp_id.id)])
                            bank_ids = beneficiary.mapped('bank_id')
                            if bank_ids:
                                partner_ids =  bank_ids.ids
                                
            rec.bank_ids = [(6,0,partner_ids)]

    bank_ids = fields.Many2many('res.partner.bank','payment_req_bank_id','bank_id','payment_id',compute="get_bank_ids")
    
    @api.onchange('bank_id')
    def onchage_bank(self):
        if self.bank_id:
            self.account_number = self.bank_id.acc_number

    def request(self):

        # request_open_bal_id = self.env['request.open.balance.invest'].create({
        #     'name': self.name,
        #     'operation_number': self.operation_number,
        #     'agreement_number': self.balance_req_id and self.balance_req_id.agreement_number or '',
        #     #'is_cancel_collaboration': True if self.type_of_operation == 'withdrawal_cancellation' else False,
        #     'type_of_operation': self.balance_req_id and self.balance_req_id.type_of_operation or False,
        #     'apply_to_basis_collaboration': self.balance_req_id and self.balance_req_id.apply_to_basis_collaboration or False,
        #     'origin_resource_id': self.balance_req_id and self.balance_req_id.origin_resource_id and self.balance_req_id.origin_resource_id.id or False,
        #     'state': 'requested',
        #     'request_date': self.date,
        #     'trade_number': self.balance_req_id and self.balance_req_id.trade_number,
        #     'currency_id': self.balance_req_id and self.balance_req_id.currency_id and self.balance_req_id.currency_id.id or False,
        #     'opening_balance': self.amount,
        #     'observations': self.balance_req_id and self.balance_req_id.observations,
        #     'user_id': self.balance_req_id and self.balance_req_id.user_id and self.balance_req_id.user_id.id or False,
        #     'cbc_format': self.balance_req_id and self.balance_req_id.cbc_format or False,
        #     'cbc_shipping_office': self.balance_req_id and self.balance_req_id.cbc_shipping_office or False,
        #     'liability_account_id': self.balance_req_id and self.balance_req_id.liability_account_id and self.balance_req_id.liability_account_id.id or False,
        #     'investment_account_id': self.balance_req_id and self.balance_req_id.investment_account_id and self.balance_req_id.investment_account_id.id or False,
        #     'interest_account_id': self.balance_req_id and self.balance_req_id.interest_account_id and self.balance_req_id.interest_account_id.id or False,
        #     'availability_account_id': self.balance_req_id and self.balance_req_id.availability_account_id and self.balance_req_id.availability_account_id.id or False,
        #     'payment_request_id': self.id,
        #     'balance_req_id': False,
        #     'patrimonial_account_id': self.balance_req_id and self.balance_req_id.patrimonial_account_id and self.balance_req_id.patrimonial_account_id.id or False,
        #     'interest_account_id': self.balance_req_id and self.balance_req_id.interest_account_id and self.balance_req_id.interest_account_id.id or False,
        #     'honorary_account_id': self.balance_req_id and self.balance_req_id.honorary_account_id and self.balance_req_id.honorary_account_id.id or False,
        #     'trust_agreement_file': self.balance_req_id and self.balance_req_id.trust_agreement_file or False,
        #     'trust_agreement_file_name': self.balance_req_id and self.balance_req_id.trust_agreement_file_name or False,
        #     'trust_office_file': self.balance_req_id and self.balance_req_id.trust_office_file or False,
        #     'trust_office_file_name': self.balance_req_id and self.balance_req_id.trust_office_file_name or False,
        #     'trust_id': self.balance_req_id and self.balance_req_id.trust_id and self.balance_req_id.trust_id.id or False,
        #     'origin_journal_id': self.balance_req_id and self.balance_req_id.origin_journal_id and self.balance_req_id.origin_journal_id.id or False,
        #     "destination_journal_id": self.balance_req_id and self.balance_req_id.destination_journal_id and self.balance_req_id.destination_journal_id.id or False,
        #     'patrimonial_id': self.balance_req_id and self.balance_req_id.patrimonial_resources_id and self.balance_req_id.patrimonial_resources_id.id or False,
        #     'patrimonial_yield_account_id': self.balance_req_id and self.balance_req_id.patrimonial_yield_account_id and self.balance_req_id.patrimonial_yield_account_id.id or False,
        #     'patrimonial_equity_account_id': self.balance_req_id and self.balance_req_id.patrimonial_equity_account_id and self.balance_req_id.patrimonial_equity_account_id.id or False,
        #     'bases_collaboration_id': self.balance_req_id and self.balance_req_id.bases_collaboration_id and self.balance_req_id.bases_collaboration_id.id or False,
        #     'fund_type_id': self.balance_req_id and self.balance_req_id.bases_collaboration_id and self.balance_req_id.bases_collaboration_id.fund_type_id and self.balance_req_id.bases_collaboration_id.fund_type_id.id or False,
        #     'type_of_agreement_id': self.balance_req_id and self.balance_req_id.bases_collaboration_id and self.balance_req_id.bases_collaboration_id.agreement_type_id and self.balance_req_id.bases_collaboration_id.agreement_type_id.id or False,
        #     'fund_id':  self.balance_req_id and self.balance_req_id.bases_collaboration_id and self.balance_req_id.bases_collaboration_id.fund_id and self.balance_req_id.bases_collaboration_id.fund_id.id or False,
        #     'beneficiary_id': self.balance_req_id and self.balance_req_id.beneficiary_id.id or False,
        #     'provider_id': self.balance_req_id and self.balance_req_id.provider_id.id or False,
        #     'specifics_project_id': self.balance_req_id and self.balance_req_id.specifics_project_id and self.balance_req_id.specifics_project_id.id or False,
        # })

        # activity_type = self.env.ref('mail.mail_activity_data_todo').id
        # summary = "Payment Request '" + str(self.name) + "'In Increases and withdrawals"
        # activity_obj = self.env['mail.activity']
        # model_id = self.env['ir.model'].sudo().search([('model', '=', 'request.open.balance.invest')]).id
        # user_id = self.balance_req_id and self.balance_req_id.user_id and self.balance_req_id.user_id.id or False,
        # activity_obj.create({'activity_type_id': activity_type,
        #                    'res_model': 'request.open.balance.invest', 'res_id': request_open_bal_id.id,
        #                    'res_model_id':model_id,
        #                    'summary': summary, 'user_id': user_id})
        
        self.state = 'requested'
        
    @api.model
    def create(self,vals):
        res = super(PaymentRequest,self).create(vals)
        if res.amount and res.date and res.payment_method_id and res.beneficiary_id:
            folio_rec = ''
            payment_ids = self.env['account.move'].search([('is_payment_request', '=', True),('partner_id','=',res.beneficiary_id.id),('l10n_mx_edi_payment_method_id','=',res.payment_method_id.id),('amount_total','=',res.amount)])
            for payment in payment_ids:
                if payment.date_receipt and payment.date_receipt.date()== res.date:
                    folio_rec = payment.folio 
            res.counter_receipt_sheet = folio_rec
        return res
    
    def write(self,vals):
        result = super(PaymentRequest,self).write(vals)
        if 'counter_receipt_sheet' not in vals:
            for res in self:
                if res.amount and res.date and res.payment_method_id and res.beneficiary_id:
                    folio_rec = ''
                    payment_ids = self.env['account.move'].search([('is_payment_request', '=', True),('partner_id','=',res.beneficiary_id.id),('l10n_mx_edi_payment_method_id','=',res.payment_method_id.id),('amount_total','=',res.amount)])
                    for payment in payment_ids:
                        if payment.date_receipt and payment.date_receipt.date()== res.date:
                            folio_rec = payment.folio 
                    res.counter_receipt_sheet = folio_rec
        return result
    
    def action_validates_payment_request(self):
        for res in self:
            if res.amount and res.date and res.payment_method_id and res.beneficiary_id:
                folio_rec = ''
                payment_ids = self.env['account.move'].search([('is_payment_request', '=', True),('partner_id','=',res.beneficiary_id.id),('l10n_mx_edi_payment_method_id','=',res.payment_method_id.id),('amount_total','=',res.amount)])
                for payment in payment_ids:
                    if payment.date_receipt and payment.date_receipt.date()== res.date:
                        folio_rec = payment.folio 
                res.counter_receipt_sheet = folio_rec

    def action_validates_payment_request_auto(self):
        records = self.env['payment.request'].search(['|',('counter_receipt_sheet','=',False),('counter_receipt_sheet','=','')])
        for res in records:
            if res.amount and res.date and res.payment_method_id and res.beneficiary_id:
                folio_rec = ''
                payment_ids = self.env['account.move'].search([('is_payment_request', '=', True),
                                                               ('partner_id','=',res.beneficiary_id.id),
                                        ('l10n_mx_edi_payment_method_id','=',res.payment_method_id.id),
                                                               ('amount_total','=',res.amount)])
                for payment in payment_ids:
                    if payment.date_receipt and payment.date_receipt.date()== res.date:
                        folio_rec = payment.folio 
                res.counter_receipt_sheet = folio_rec            