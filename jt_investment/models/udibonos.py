from odoo import models, fields, api , _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError

class UDIBONOS(models.Model):

    _name = 'investment.udibonos'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Investment UDIBONOS"
    _rec_name = 'first_number'
     
    first_number = fields.Char('First Number:')
    new_journal_id = fields.Many2one("account.journal", 'Journal')
 
    folio = fields.Integer("Folio")
    date_time = fields.Datetime("Date Time")
    journal_id= fields.Many2one("account.journal",'Bank Account')
    bank_id = fields.Many2one(related="journal_id.bank_id")
    amount_invest = fields.Float("Amount to invest")
    currency_id = fields.Many2one('res.currency', string='Currency',default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    investment_rate_id = fields.Many2one("investment.period.rate","Exchange rate")
    concept = fields.Text("Application Concept")
    dependency_id = fields.Many2one('dependency', "Dependency")
    sub_dependency_id = fields.Many2one('sub.dependency', "Subdependency")
    reason_rejection = fields.Text("Reason Rejection")
    
    total_currency_rate = fields.Float(string="Total",compute="get_total_currency_amount",store=True)
    contract_id = fields.Many2one("investment.contract","Contract")
    instrument_it = fields.Selection([('bank','Bank'),('paper_government','Paper Government Paper')],string="Document")
    account_executive = fields.Char("Account Executive")
    UNAM_operator = fields.Many2one("hr.employee","UNAM Operator")
    is_federal_subsidy_resources = fields.Boolean("Federal Subsidy Resourcesss")
    observations = fields.Text("Observations")
    origin_resource_id = fields.Many2one('sub.origin.resource', "Origin of the resource")
    
    kind_of_product = fields.Selection([('investment','Investment')],string="Kind Of Product",default="investment")
    key = fields.Char("Identification Key")
    issue_date = fields.Date('Date of issue')
    due_date = fields.Date('Due Date')
    nominal_value = fields.Float(related='amount_invest',string="Nominal Value")
    interest_rate = fields.Float("Interest Rate",digits='UDIBONOS')
    time_for_each_cash_flow = fields.Integer(string="Time for each cash flow",size=4)
    time_to_expiration_date = fields.Integer(string="Time to Expiration Date",size=4)
    coupon = fields.Float(string="Coupon",compute="get_coupon_amount",store=True)
    state = fields.Selection([('draft','Draft'),('requested','Requested'),('rejected','Rejected'),('approved','Approved'),('confirmed','Confirmed'),('done','Done'),('canceled','Canceled')],string="Status",default='draft')
    
    present_value_bond = fields.Float(string="Present Value of the Bond",compute="get_present_value_bond",store=True)    
    estimated_interest = fields.Float(string="Estimated Interest",compute="get_estimated_interest",store=True)
    
    real_interest = fields.Float("Real Interest")
            
    profit_variation = fields.Float(string="Estimated vs Real Profit Variation",compute="get_profit_variation",store=True)    

    
    month_key = fields.Char("Identification Key")
    month_issue_date = fields.Date('Date of issue')
    month_due_date = fields.Date('Due Date')
    number_of_title = fields.Float("Number of Titles")
    udi_value = fields.Float("UDI value")
    udi_value_multiplied = fields.Float(string="The value of the Udi is multiplied by 100",default=100)
    coupon_rate = fields.Float("Coupon Rate",digits='UDIBONOS')
    period_days = fields.Float("Period days")  
    

    monthly_nominal_value = fields.Float(string="Nominal value of the security in investment units",compute="get_monthly_nominal_value",store=True)    
    monthly_estimated_interest = fields.Float(string="Estimated Interest",compute="get_monthly_estimated_interest",store=True)    
    monthly_real_interest = fields.Float("Real Interest")
                
    monthly_profit_variation = fields.Float(string="Estimated vs Real Profit Variation",compute="get_month_profit_variation",store=True)    
    rate_of_returns = fields.Many2one('rate.of.returns', string="Rate Of Returns")
    
    #====== Accounting Fields =========#

    investment_income_account_id = fields.Many2one('account.account','Income Account')
    investment_expense_account_id = fields.Many2one('account.account','Expense Account')
    investment_price_diff_account_id = fields.Many2one('account.account','Price Difference Account')    

    return_income_account_id = fields.Many2one('account.account','Income Account')
    return_expense_account_id = fields.Many2one('account.account','Expense Account')
    return_price_diff_account_id = fields.Many2one('account.account','Price Difference Account')    

    request_finance_ids = fields.One2many('request.open.balance.finance','udibonos_id',copy=False)

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
            self.issue_date = self.date_time
            self.month_issue_date = self.date_time
        else:
            self.issue_date = False
            self.month_issue_date = False

    @api.onchange('expiry_date')
    def onchange_expiry_date(self):
        if self.expiry_date:
            self.due_date = self.expiry_date
            self.month_due_date = self.expiry_date
        else:
            self.due_date = False
            self.month_due_date = False 

    @api.constrains('amount_invest')
    def check_min_balance(self):
        if self.amount_invest == 0:
            raise UserError(_('Please add amount invest'))

    def unlink(self):
        for rec in self:
            if rec.state not in ['draft']:
                raise UserError(_('You can delete only draft status data.'))
        return super(UDIBONOS, self).unlink()
    
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
    
    @api.depends('nominal_value','interest_rate')
    def get_coupon_amount(self):
        for rec in self:
            rec.coupon = (rec.nominal_value * rec.interest_rate)/100
            
    @api.depends('amount_invest')
    def get_total_currency_amount(self):
        for rec in self:
            if rec.amount_invest:
                rec.total_currency_rate = rec.amount_invest
            else:
                rec.total_currency_rate = 0
      
    @api.depends('interest_rate','time_for_each_cash_flow','nominal_value')
    def get_present_value_bond(self):
        for rec in self:
            VA = rec.nominal_value
            r = rec.interest_rate /100
            n = rec.time_for_each_cash_flow
            value = (VA * r) * ((1 + r) ** n-1) / (r + (1 + r) ** r) + VA * (1 / (1 + r) ** r)
            rec.present_value_bond = value
            

    @api.depends('present_value_bond','nominal_value')
    def get_estimated_interest(self):
        for rec in self:
            rec.estimated_interest = rec.present_value_bond - rec.nominal_value
    
    @api.depends('estimated_interest','real_interest')
    def get_profit_variation(self):
        for rec in self:
            rec.profit_variation = rec.real_interest - rec.estimated_interest
    
    @api.depends('number_of_title','udi_value','udi_value_multiplied')
    def get_monthly_nominal_value(self):
        for rec in self:
            rec.monthly_nominal_value = rec.number_of_title*(rec.udi_value*rec.udi_value_multiplied)
    
    
    @api.depends('monthly_nominal_value','coupon_rate','period_days')
    def get_monthly_estimated_interest(self):
        for rec in self:
            rec.monthly_estimated_interest = rec.monthly_nominal_value*rec.coupon_rate/360*rec.period_days
        
    @api.depends('monthly_estimated_interest','monthly_real_interest')
    def get_month_profit_variation(self):
        for rec in self:
            rec.monthly_profit_variation = rec.monthly_real_interest - rec.monthly_estimated_interest

    def write(self, vals):
        res = super(UDIBONOS, self).write(vals)
        if vals.get('expiry_date'):
            pay_regis_obj = self.env['calendar.payment.regis']
            pay_regis_rec = pay_regis_obj.search([('date', '=', vals.get('expiry_date')),
                                                  ('type_pay', '=', 'Non Business Day')], limit=1)
            if pay_regis_rec:
                raise ValidationError(_("You have choosen Non-Business Day on Expiry Date!"))
        return res

    @api.model
    def create(self,vals):
        if vals.get('expiry_date'):
            pay_regis_obj = self.env['calendar.payment.regis']
            pay_regis_rec = pay_regis_obj.search([('date', '=', vals.get('expiry_date')),
                                                  ('type_pay', '=', 'Non Business Day')], limit=1)
            if pay_regis_rec:
                raise ValidationError(_("You have choosen Non-Business Day on Expiry Date!"))

        vals['folio'] = self.env['ir.sequence'].next_by_code('folio.udibonos')
        res = super(UDIBONOS,self).create(vals)
        
        sequence = res.new_journal_id and res.new_journal_id.sequence_id or False 
        if not sequence:
            raise UserError(_('Please define a sequence on your journal.'))

        res.first_number = sequence.with_context(ir_sequence_date=res.date_time).next_by_id()
        
#         first_number = self.env['ir.sequence'].next_by_code('UDIB.number')
#         res.first_number = first_number
        
        return res
        
    def action_confirm(self):
        today = datetime.today().date()
        user = self.env.user
        employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
            
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
                'default_udibonos_id' : self.id,
                'default_fund_type' : self.fund_type_id and self.fund_type_id.id or False,
                'default_bank_account_id' : self.journal_id and self.journal_id.id or False,
                'show_for_supplier_payment':1,
                'default_fund_id' : self.fund_id and self.fund_id.id or False,
                'default_agreement_type': self.agreement_type_id and self.agreement_type_id.id or False,
                'default_base_collabaration_id': self.base_collaboration_id and self.base_collaboration_id.id or False,                
            }
        }
    def action_draft(self):
        self.state = 'draft'

    def action_reset_to_draft(self):
        self.state='draft'
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
            'domain': [('udibonos_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_udibonos_id': self.id}
        }
