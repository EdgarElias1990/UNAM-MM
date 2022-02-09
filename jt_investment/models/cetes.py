from odoo import models, fields, api , _ 
from datetime import datetime
from odoo.exceptions import UserError, ValidationError

class CETES(models.Model):

    _name = 'investment.cetes'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Investment CETES"
    _rec_name = 'first_number'
    
    first_number = fields.Char('First Number:')
    new_journal_id = fields.Many2one("account.journal", 'Journal')
    
    folio = fields.Integer("Folio")
    date_time = fields.Datetime("Date Time")
    journal_id = fields.Many2one("account.journal", 'Bank Account')
    bank_id = fields.Many2one(related="journal_id.bank_id")
    amount_invest = fields.Float("Amount to invest")
    currency_id = fields.Many2one(
        'res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)

    investment_rate_id = fields.Many2one(
        "investment.period.rate", "Exchange rate")
    total_currency_rate = fields.Float(
        string="Total", compute="get_total_currency_amount", store=True)
    contract_id = fields.Many2one("investment.contract", "Contract")
    instrument_it = fields.Selection(
        [('bank', 'Bank'), ('paper_government', 'Paper Government Paper')], string="Document")
    account_executive = fields.Char("Account Executive")
    UNAM_operator = fields.Many2one("hr.employee","UNAM Operator")
    is_federal_subsidy_resources = fields.Boolean(
        "Federal Subsidy Resourcesss")
    observations = fields.Text("Observations")

    dependency_id = fields.Many2one('dependency', "Dependency")
    sub_dependency_id = fields.Many2one('sub.dependency', "Subdependency")
    reason_rejection = fields.Text("Reason Rejection")
    
    kind_of_product = fields.Selection(
        [('investment', 'Investment')], string="Kind Of Product", default="investment")
    key = fields.Char("Identification Key")
    start_date = fields.Date('Start Date')
    due_date = fields.Date('Due Date')
    nominal_value = fields.Float(related='amount_invest',string="Nominal Value")
    yield_rate = fields.Float("Yield Rate",digits='CETES')
    term = fields.Selection([('28', '28 Days'),
                             ('91', '91 Days'),
                             ('182', '182 Days'),
                             ('364', '364 Days')
                             ], string="Term")

    cetes_price = fields.Float(
        string="CETES Price", compute="get_cetes_price", store=True)
    cetes_quantity = fields.Float(
        string="CETES Quantity", compute="get_cetes_quantity", store=True)
    estimated_interest = fields.Float(
        string="Estimated Interest", compute="get_estimated_interest", store=True)
    estimated_profit = fields.Float(
        string="Estimated Profit", compute="get_estimated_profit", store=True)
    real_interest = fields.Float("Real Interest")
    real_profit = fields.Float(
        string="Real Profit", compute="get_real_profit", store=True)
    state = fields.Selection([('draft', 'Draft'), ('requested', 'Requested'), ('rejected', 'Rejected'), ('approved', 'Approved'),
                              ('confirmed', 'Confirmed'), ('done', 'Done'), ('canceled', 'Canceled')], string="Status", default='draft')

    origin_resource_id = fields.Many2one('sub.origin.resource', "Origin of the resource")
    concept = fields.Text("Application Concept")
    rate_of_returns = fields.Many2one('rate.of.returns', string="Rate Of Returns")
    
    #====== Accounting Fields =========#

    investment_income_account_id = fields.Many2one(
        'account.account', 'Income Account')
    investment_expense_account_id = fields.Many2one(
        'account.account', 'Expense Account')
    investment_price_diff_account_id = fields.Many2one(
        'account.account', 'Price Difference Account')

    return_income_account_id = fields.Many2one(
        'account.account', 'Income Account')
    return_expense_account_id = fields.Many2one(
        'account.account', 'Expense Account')
    return_price_diff_account_id = fields.Many2one(
        'account.account', 'Price Difference Account')

    request_finance_ids = fields.One2many(
        'request.open.balance.finance', 'cetes_id',copy=False)

    fund_type_id = fields.Many2one('fund.type', "Type Of Fund")
    agreement_type_id = fields.Many2one('agreement.agreement.type', 'Agreement Type')
    fund_id = fields.Many2one('agreement.fund','Fund') 
    fund_key = fields.Char(related='fund_id.fund_key',string="Password of the Fund")
    base_collaboration_id = fields.Many2one('bases.collaboration','Name Of Agreements')
    investment_fund_id = fields.Many2one('investment.funds','Investment Funds',copy=False)
    expiry_date = fields.Date(string="Expiration Date")
    yield_id = fields.Many2one('yield.destination','Yield Destination')

    @api.onchange('date_time')
    def onchange_date_time(self):
        if self.date_time:
            self.start_date = self.date_time
        else:
            self.start_date = False

    @api.onchange('expiry_date')
    def onchange_expiry_date(self):
        if self.expiry_date:
            self.due_date = self.expiry_date
        else:
            self.due_date = False
             
    @api.constrains('amount_invest')
    def check_min_balance(self):
        if self.amount_invest == 0:
            raise UserError(_('Please add amount invest'))
    
    def unlink(self):
        for rec in self:
            if rec.state not in ['draft']:
                raise UserError(_('You can delete only draft status data.'))
        return super(CETES, self).unlink()
    
    @api.onchange('contract_id')
    def onchange_contract_id(self):
        if self.contract_id:
            self.fund_type_id = self.contract_id.fund_type_id and self.contract_id.fund_type_id.id or False 
            self.agreement_type_id = self.contract_id.agreement_type_id and self.contract_id.agreement_type_id.id or False
            self.fund_id = self.contract_id.fund_id and self.contract_id.fund_id.id or False
            self.base_collaboration_id = self.contract_id.base_collabaration_id and self.contract_id.base_collabaration_id.id or False
        else:
            self.fund_type_id = False
            self.agreement_type_id = False
            self.fund_id = False
            self.base_collaboration_id = False

    @api.depends('amount_invest')
    def get_total_currency_amount(self):
        for rec in self:
            if rec.amount_invest:
                rec.total_currency_rate = rec.amount_invest
            else:
                rec.total_currency_rate = 0

    @api.depends('term', 'yield_rate', 'nominal_value')
    def get_cetes_price(self):
        for rec in self:
            term_value = 0
            if rec.term:
                term_value = int(rec.term)
            rec.cetes_price = (
                1 / (rec.yield_rate * term_value / 36000 + 1)) * rec.nominal_value

    @api.depends('nominal_value')
    def get_cetes_quantity(self):
        for rec in self:
            rec.cetes_quantity = rec.nominal_value / 10

    @api.depends('nominal_value', 'yield_rate', 'term')
    def get_estimated_interest(self):
        for rec in self:
            term_value = 0
            if rec.term:
                term_value = int(rec.term)
            rec.estimated_interest = rec.yield_rate / \
                100 * term_value * rec.nominal_value / 360

    @api.depends('nominal_value', 'yield_rate', 'term', 'estimated_interest')
    def get_estimated_profit(self):
        for rec in self:
            rec.estimated_profit = rec.nominal_value + rec.estimated_interest

    @api.depends('nominal_value', 'real_interest')
    def get_real_profit(self):
        for rec in self:
            rec.real_profit = rec.nominal_value + rec.real_interest

    @api.depends('estimated_profit', 'real_profit')
    def get_profit_variation(self):
        for rec in self:
            rec.profit_variation = rec.real_profit - rec.estimated_profit

    profit_variation = fields.Float(
        string="Estimated vs Real Profit Variation", compute="get_profit_variation", store=True)

    def write(self, vals):
        res = super(CETES, self).write(vals)
        if vals.get('expiry_date'):
            pay_regis_obj = self.env['calendar.payment.regis']
            pay_regis_rec = pay_regis_obj.search([('date', '=', vals.get('expiry_date')),
                                                  ('type_pay', '=', 'Non Business Day')], limit=1)
            if pay_regis_rec:
                raise ValidationError(_("You have choosen Non-Business Day on Expiry Date!"))
        return res

    @api.model
    def create(self, vals):
        if vals.get('expiry_date'):
            pay_regis_obj = self.env['calendar.payment.regis']
            pay_regis_rec = pay_regis_obj.search([('date', '=', vals.get('expiry_date')),
                                                  ('type_pay', '=', 'Non Business Day')], limit=1)
            if pay_regis_rec:
                raise ValidationError(_("You have choosen Non-Business Day on Expiry Date!"))
        vals['folio'] = self.env['ir.sequence'].next_by_code('folio.cetes')
        res = super(CETES, self).create(vals)
        
        sequence = res.new_journal_id and res.new_journal_id.sequence_id or False 
        if not sequence:
            raise UserError(_('Please define a sequence on your journal.'))

        res.first_number = sequence.with_context(ir_sequence_date=res.date_time).next_by_id()
        
#         first_number = self.env['ir.sequence'].next_by_code('CETES.number')
#         res.first_number = first_number
        
        return res

    def action_confirm(self):
        today = datetime.today().date()
        user = self.env.user
        employee = self.env['hr.employee'].search(
            [('user_id', '=', user.id)], limit=1)

        return {
            'name': _('Approve Request'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'approve.money.market.bal.req',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_amount': self.amount_invest,
                'default_date': today,
                'default_employee_id': employee.id if employee else False,
                'default_cetes_id': self.id,
                'default_fund_type' : self.fund_type_id and self.fund_type_id.id or False,
                'default_bank_account_id' : self.journal_id and self.journal_id.id or False,
                'default_fund_id' : self.fund_id and self.fund_id.id or False,
                'show_for_supplier_payment': 1,
                'default_agreement_type': self.agreement_type_id and self.agreement_type_id.id or False,
                'default_base_collabaration_id': self.base_collaboration_id and self.base_collaboration_id.id or False,

            }
        }

    def action_draft(self):
        self.state = 'draft'
        
    def action_reset_to_draft(self):
        self.state = 'draft'
        for rec in self.request_finance_ids:
            rec.canceled_finance()

    def action_requested(self):
        self.state = 'requested'
#         if self.investment_fund_id and self.investment_fund_id.state != 'requested':
#             self.investment_fund_id.with_context(call_from_product=True).action_requested()

    def action_approved(self):
        self.state = 'approved'
#         if self.investment_fund_id and self.investment_fund_id.state != 'approved':
#             self.investment_fund_id.with_context(call_from_product=True).action_approved()

    def action_confirmed(self):
        self.state = 'confirmed'
#         if self.investment_fund_id and self.investment_fund_id.state != 'confirmed':
#             self.investment_fund_id.with_context(call_from_product=True).action_confirmed()

    def action_done(self):
        self.state = 'done'
        
    def action_reject(self):
        self.state = 'rejected'

    def action_canceled(self):
        self.state = 'canceled'
#         if self.investment_fund_id and self.investment_fund_id.state != 'canceled':
#             self.investment_fund_id.with_context(call_from_product=True).action_canceled()

    def action_calculation(self):
        return

    def action_reinvestment(self):
        return

    def action_published_entries(self):
        return {
            'name': 'Published Entries',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'request.open.balance.finance',
            'domain': [('cetes_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_cetes_id': self.id}
        }
    def action_rate_history(self):

        token = 'fccfd1e45c7e54ef7a6896f25f7dcf01d51cfa033424abd345707b6a8d2b59c3'
        url = 'https://www.banxico.org.mx/SieAPIRest/service/v1/series/'
        
        # url +=  series_str+"/datos/oportuno?token=%s"%token
        pre_date = '2020-01-01'
        date_range = datetime.now()
        date_range = datetime.strftime(date_range,'%Y-%m-%d')
        date_range = pre_date+"/"+date_range
        
        self.env['investment.period.rate'].get_investment_product_rate(token,url,date_range)
        self.env['investment.period.rate'].get_cetes_product_rate(token,url,date_range)
        self.env['investment.period.rate'].get_UDIBONOS_product_rate(token,url,date_range)
        self.env['investment.period.rate'].get_BONUS_product_rate(token,url,date_range)
        self.env['investment.period.rate'].get_PAGARE_product_rate(token,url,date_range)
        