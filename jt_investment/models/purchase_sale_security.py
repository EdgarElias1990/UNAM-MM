from odoo import models, fields, api,_
from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError

class PurchaseSaleSecurity(models.Model):

    _name = 'purchase.sale.security'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Purchase Sale Security"
    _rec_name = 'first_number' 
    
    name = fields.Char("Reference")

    first_number = fields.Char('First Number:')
    new_journal_id = fields.Many2one("account.journal", 'Journal')

    last_quote_id = fields.Many2one('investment.stock.quotation','Last Quote')
    last_quote_price = fields.Float(related='last_quote_id.price',string="Last Quote Price")
    last_quote_date = fields.Date(related="last_quote_id.date",string="Last Quote Date")

    
    invesment_date = fields.Date("Investment Date")
    type_of_investment = fields.Char("Type of Investment")
    price = fields.Float(related='last_quote_id.price',string="Price")
    price_previous_day = fields.Float(compute='get_previous_price_days',string="Price previous day")
    average_price_of_the_month = fields.Float(compute='get_average_price_of_the_month',string="Average price of the month")
    title = fields.Integer("Title")
    term = fields.Integer("Term")
    due_date = fields.Date("Due Date")
    movement = fields.Selection([('buy','Purchase'),('sell','Sale')],string="What move do I want to make?")
    state = fields.Selection([('draft','Draft'),('requested','Requested'),('rejected','Rejected'),('approved','Approved'),('confirmed','Confirmed'),('done','Done'),('canceled','Canceled')],string="Status",default='draft')
    observations = fields.Text("Observations")    
    file_data = fields.Binary("Supporting document")
    file_name = fields.Char("File Name")
    
    bank_id = fields.Many2one('account.journal','Bank')
    journal_id = fields.Many2one(related="bank_id")
    bank_account_id = fields.Many2one(related='journal_id.bank_account_id')
    account_balance = fields.Float("Account Balance",compute="get_account_balance",store=True)
    movement_price = fields.Float(related='last_quote_id.price',string="Price")
    number_of_titles = fields.Integer(related='title',string="Quantity of Securities")
    amount = fields.Float(string="Investment amount",compute="get_investment_amount",store=True)

    contract_id = fields.Many2one("investment.contract", "Contract")
    fund_type_id = fields.Many2one('fund.type', "Type Of Fund")
    agreement_type_id = fields.Many2one('agreement.agreement.type', 'Agreement Type')
    fund_id = fields.Many2one('agreement.fund','Fund') 
    fund_key = fields.Char(related='fund_id.fund_key',string="Password of the Fund")
    base_collaboration_id = fields.Many2one('bases.collaboration','Name Of Agreements')
    reason_rejection = fields.Text("Reason Rejection")
    
    dependency_id = fields.Many2one('dependency', "Dependency")
    sub_dependency_id = fields.Many2one('sub.dependency', "Subdependency")
    expiry_date = fields.Date(string="Expiration Date")
    concept = fields.Text("Application Concept")
    
    request_finance_ids = fields.One2many(
        'request.open.balance.finance', 'purchase_sale_security_id',copy=False)
    rate_of_returns = fields.Many2one('rate.of.returns', string="Rate Of Returns")
    
    #====== Accounting Fields =========#

    investment_income_account_id = fields.Many2one('account.account','Income Account')
    investment_expense_account_id = fields.Many2one('account.account','Expense Account')
    investment_price_diff_account_id = fields.Many2one('account.account','Price Difference Account')    

    return_income_account_id = fields.Many2one('account.account','Income Account')
    return_expense_account_id = fields.Many2one('account.account','Expense Account')
    return_price_diff_account_id = fields.Many2one('account.account','Price Difference Account')    

    #=====Profit==========#
    estimated_interest = fields.Float(string="Estimated Interest")
    estimated_profit = fields.Float(string="Estimated Profit")
    real_interest = fields.Float("Real Interest")
    real_profit = fields.Float(string="Real Profit")
    profit_variation = fields.Float(string="Estimated vs Real Profit Variation",compute="get_profit_variation",store=True)
    investment_fund_id = fields.Many2one('investment.funds','Investment Funds',copy=False)
    sub_origin_resource = fields.Many2one('sub.origin.resource', "Origin of the resource")
    yield_id = fields.Many2one('yield.destination','Yield Destination')
    currency_id = fields.Many2one(
        'res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

#     @api.constrains('account_balance')
#     def check_min_balance(self):
#         if self.account_balance == 0:
#             raise UserError(_('Please add Account Balance'))

    @api.constrains('title')
    def check_title(self):
        for rec in self:
            if rec.title == 0:
                raise UserError(_('Please add Investment Title'))

    @api.constrains('term')
    def check_term(self):
        if self.term == 0:
            raise UserError(_('Please add Investment Term'))
    
    def unlink(self):
        for rec in self:
            if rec.state not in ['draft']:
                raise UserError(_('You can delete only draft status data.'))
        return super(PurchaseSaleSecurity, self).unlink()
    
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

    @api.depends('last_quote_id','last_quote_id.price_id')
    def get_previous_price_days(self):
        for rec in self:
            if rec.last_quote_id and rec.last_quote_id.price_id:
                bank_id = rec.bank_id and rec.bank_id.id or False
                previous_rec = self.env['stock.quote.price'].search([('journal_id','=',bank_id),('date','<',rec.last_quote_id.price_id.date)],limit=1,order='date desc')
                if previous_rec:
                    rec.price_previous_day = previous_rec.price
                else:
                    rec.price_previous_day = 0.0
            else:
                rec.price_previous_day = 0.0

    @api.depends('last_quote_id','last_quote_id.price_id')
    def get_average_price_of_the_month(self):
        for rec in self:
            if rec.last_quote_id and rec.last_quote_id.price_id:
                p_date = rec.last_quote_id.price_id.date.replace(day=1)
                day_diff = rec.last_quote_id.price_id.date - p_date
                day_diff = day_diff.days+1
                bank_id = rec.bank_id and rec.bank_id.id or False
                previous_rec = self.env['stock.quote.price'].search([('journal_id','=',bank_id),('date','>=',p_date),('date','<=',rec.last_quote_id.price_id.date)],order='date desc')
                if previous_rec:
                    sum_price =  sum(x.price for x in previous_rec)
                    if day_diff:
                        sum_price = sum_price/day_diff
                        rec.average_price_of_the_month = sum_price
                    else: 
                        rec.average_price_of_the_month = sum_price
                else:
                    rec.average_price_of_the_month = 0.0
            else:
                rec.average_price_of_the_month = 0.0
                
    @api.depends('journal_id','bank_account_id','journal_id.default_debit_account_id')
    def get_account_balance(self):     
        for rec in self:
            if rec.journal_id and rec.bank_account_id and rec.journal_id.default_debit_account_id:
                values= self.env['account.move.line'].search([('account_id', '=', rec.journal_id.default_debit_account_id.id),('move_id.state', '=', 'posted')])
                rec.account_balance = sum(x.debit-x.credit for x in values)
                
            else:
                rec.account_balance = 0
    @api.depends('estimated_profit','real_profit')
    def get_profit_variation(self):
        for rec in self:
            rec.profit_variation =  rec.real_profit - rec.estimated_profit
            

    @api.depends('movement_price','number_of_titles')
    def get_investment_amount(self):
        for rec in self:
            rec.amount = rec.movement_price * rec.number_of_titles

    def write(self, vals):
        res = super(PurchaseSaleSecurity, self).write(vals)
        if vals.get('invesment_date') or vals.get('expiry_date'):
            pay_regis_obj = self.env['calendar.payment.regis']
            if vals.get('invesment_date'):
                pay_regis_rec = pay_regis_obj.search([('date', '=', vals.get('invesment_date')),
                                               ('type_pay', '=', 'Non Business Day')], limit=1)
                if pay_regis_rec:
                    raise ValidationError(_("You have choosen Non-Business Day in Investment Date!"))
            if vals.get('expiry_date'):
                pay_regis_rec = pay_regis_obj.search([('date', '=', vals.get('expiry_date')),
                                               ('type_pay', '=', 'Non Business Day')], limit=1)
                if pay_regis_rec:
                    raise ValidationError(_("You have choosen Non-Business Day in Expiration Date!"))
        return res

    @api.model
    def create(self,vals):
        res = super(PurchaseSaleSecurity,self).create(vals)
        if vals.get('invesment_date') or vals.get('expiry_date'):
            pay_regis_obj = self.env['calendar.payment.regis']
            if vals.get('invesment_date'):
                pay_regis_rec = pay_regis_obj.search([('date', '=', vals.get('invesment_date')),
                                               ('type_pay', '=', 'Non Business Day')], limit=1)
                if pay_regis_rec:
                    raise ValidationError(_("You have choosen Non-Business Day in Investment Date!"))
            if vals.get('expiry_date'):
                pay_regis_rec = pay_regis_obj.search([('date', '=', vals.get('expiry_date')),
                                               ('type_pay', '=', 'Non Business Day')], limit=1)
                if pay_regis_rec:
                    raise ValidationError(_("You have choosen Non-Business Day in Expiration Date!"))

        sequence = res.new_journal_id and res.new_journal_id.sequence_id or False 
        if not sequence:
            raise UserError(_('Please define a sequence on your journal.'))

        res.first_number = sequence.with_context(ir_sequence_date=res.invesment_date).next_by_id()

        
#         first_number = self.env['ir.sequence'].next_by_code('purchase.sale.security.number')
#         res.first_number = first_number
        
        return res
    
    def action_confirm(self):
        today = datetime.today().date()
        fund_type = False
        if self.amount == 0:
            raise ValidationError(_("Please Add Investment amount to approve"))

        if self.movement_price == 0:
            raise ValidationError(_("Please Add Price to approve"))

        if self.number_of_titles==0:
            raise ValidationError(_("Please Add Quantity of Securities to approve"))

#         if self.account_balance==0:
#             raise ValidationError(_("Please Add Account Balance to approve"))
                
        return {
            'name': _('Approve Request'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'approve.money.market.bal.req',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_amount': self.amount,
                'default_date': today,
                'default_purchase_sale_security_id' : self.id,
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

    def action_reject(self):
        self.state = 'rejected'

    def action_done(self):
        self.state = 'done'
     
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

    def action_canceled(self):
        self.state = 'canceled'
#         if self.investment_fund_id and self.investment_fund_id.state != 'canceled':
#             self.investment_fund_id.with_context(call_from_product=True).action_canceled()
    