from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError, UserError


class Investment(models.Model):

    _name = 'investment.investment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Productive Accounts Investment"
    _rec_name = 'first_number'

    first_number = fields.Char('First Number:')
    new_journal_id = fields.Many2one("account.journal", 'Journal')

    invesment_date = fields.Datetime("Investment Date")
    journal_id = fields.Many2one("account.journal", "Bank")
    contract_id = fields.Many2one('investment.contract', 'Contract')
    amount_to_invest = fields.Float("Amount to Invest")
    is_fixed_rate = fields.Boolean('Fixed Rate', default=False)
    is_variable_rate = fields.Boolean('Variable Rate', default=False)
    interest_rate = fields.Float("Interest rate",digits='Productive Accounts')
    extra_percentage = fields.Float("Extra percentage",digits='Productive Accounts')
    term = fields.Integer("Fixed Term")
    term_variable = fields.Integer("VT")
    term_variable_select = fields.Selection([('daily_rate','Daily Rate'),('28_days','28 Days'),('91_days','91 Days'),('182_days','182 Days')],string="Variable Term")
    capitalizable = fields.Integer("Days of capitalization")
    frequency = fields.Integer("Frequency of interest payments")
    currency_id = fields.Many2one("res.currency", "Currency")
    currency_rate = fields.Float(
        related="currency_id.rate", string="Exchange rate", store=True)

    investment_rate_id = fields.Many2one(
        "investment.period.rate", "Exchange rate")
    observations = fields.Text("Observations")
    file_data = fields.Binary("Supporting document")
    file_name = fields.Char("File Name")

    #state = fields.Selection([('draft','Draft'),('requested','Requested'),('rejected','Rejected'),('approved','Approved'),('confirmed','Confirmed'),('done','Done'),('canceled','Canceled')],string="Status",default='draft')
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'),
                              ('canceled', 'Canceled')], string="Status", default='draft')

    fund_type_id = fields.Many2one('fund.type', "Type Of Fund")
    agreement_type_id = fields.Many2one(
        'agreement.agreement.type', 'Agreement Type')
    fund_id = fields.Many2one('agreement.fund', 'Fund')
    fund_key = fields.Char(related='fund_id.fund_key',
                           string="Password of the Fund")
    base_collaboration_id = fields.Many2one(
        'bases.collaboration', 'Name Of Agreements')
    investment_fund_id = fields.Many2one(
        'investment.funds', 'Investment Funds')

    dependency_id = fields.Many2one('dependency', "Dependency")
    sub_dependency_id = fields.Many2one('sub.dependency', "Subdependency")
    reason_rejection = fields.Text("Reason Rejection")

    #=====Profit==========#
    estimated_interest = fields.Float(
        string="Estimated Interest", compute="get_estimated_interest", store=True)
    estimated_profit = fields.Float(
        string="Estimated Profit", compute="get_estimated_profit", store=True)
    real_interest = fields.Float("Real Interest")
    real_profit = fields.Float(string="Real Profit")
    profit_variation = fields.Float(
        string="Estimated vs Real Profit Variation", compute="get_profit_variation", store=True)
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
    sub_origin_resource = fields.Many2one(
        'sub.origin.resource', "Origin of the resource")
    expiry_date = fields.Date(string="Expiration Date")
    yield_id = fields.Many2one('yield.destination', 'Yield Destination')

    line_ids = fields.One2many(
        'investment.operation', 'investment_id', copy=False)
    actual_amount = fields.Float(
        string="Actual amount", compute="get_actual_amount", store=True)
    update_line_id = fields.Many2one(
        'investment.operation', 'Amount Update Line', copy=False)

    @api.onchange('term_variable_select')
    def onchange_term_variable_select(self):
        term_variable = 0
        if self.term_variable_select:
            if self.term_variable_select=='daily_rate':
                term_variable = 1
            elif self.term_variable_select=='28_days':
                term_variable = 28
            elif self.term_variable_select=='91_days':
                term_variable = 91
            elif self.term_variable_select=='182_days':
                term_variable = 182
        self.term_variable = term_variable
        
    @api.depends('line_ids', 'line_ids.type_of_operation', 'line_ids.amount', 'line_ids.line_state')
    def get_actual_amount(self):
        for rec in self:
            amount = 0
            amount += sum(a.amount for a in rec.line_ids.filtered(lambda x: x.line_state ==
                                                                  'done' and x.type_of_operation in ('open_bal', 'increase', 'increase_by_closing')))
            amount -= sum(a.amount for a in rec.line_ids.filtered(lambda x: x.line_state == 'done' and x.type_of_operation in (
                'retirement', 'withdrawal', 'withdrawal_cancellation', 'withdrawal_closure')))
            rec.actual_amount = amount

    def write(self, vals):
        res = super(Investment, self).write(vals)
        if vals.get('term_variable_select',False):
            for r in self:
                r.onchange_term_variable_select()
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
    def create(self, vals):
        res = super(Investment, self).create(vals)
        res.onchange_term_variable_select()
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

        res.first_number = sequence.with_context(
            ir_sequence_date=res.invesment_date).next_by_id()

#         first_number = self.env['ir.sequence'].next_by_code('CPRO.number')
#         res.first_number = first_number

        return res

#     @api.constrains('amount_to_invest')
#     def check_min_balance(self):
#         if self.amount_to_invest == 0:
#             raise UserError(_('Please add amount invest'))

    @api.constrains('capitalizable')
    def check_capitalizable(self):
        if self.capitalizable == 0:
            raise UserError(_('Please Add Days of capitalization'))

    @api.constrains('interest_rate')
    def check_interest_rate(self):
        if self.interest_rate == 0:
            raise UserError(_('Please Add Interest Rate'))

#     @api.constrains('extra_percentage')
#     def check_extra_percentage(self):
#         if self.extra_percentage == 0:
#             raise UserError(_('Please Add Extra Percentage'))

    @api.constrains('is_fixed_rate', 'term')
    def check_is_fixed_rate(self):
        if self.term == 0 and self.is_fixed_rate:
            raise UserError(_('Please Add Fixed Term'))

    @api.constrains('is_variable_rate', 'term_variable_select')
    def check_is_variable_rate(self):
        if not self.term_variable_select and self.is_variable_rate:
            raise UserError(_('Please Add Term Variable'))

    def unlink(self):
        for rec in self:
            if rec.state not in ['draft']:
                raise UserError(_('You can delete only draft status data.'))
        return super(Investment, self).unlink()

#     @api.onchange('contract_id')
#     def onchange_contract_id(self):
#         if self.contract_id:
#             self.fund_type_id = self.contract_id.fund_type_id and self.contract_id.fund_type_id.id or False
#             self.agreement_type_id = self.contract_id.agreement_type_id and self.contract_id.agreement_type_id.id or False
#             self.fund_id = self.contract_id.fund_id and self.contract_id.fund_id.id or False
#             self.base_collaboration_id = self.contract_id.base_collabaration_id and self.contract_id.base_collabaration_id.id or False
#         else:
#             self.fund_type_id = False
#             self.agreement_type_id = False
#             self.fund_id = False
#             self.base_collaboration_id = False

    @api.depends('estimated_profit', 'real_profit')
    def get_profit_variation(self):
        for rec in self:
            rec.profit_variation = rec.real_profit - rec.estimated_profit

    @api.depends('is_fixed_rate', 'is_variable_rate', 'actual_amount', 'interest_rate', 'extra_percentage', 'term_variable', 'term')
    def get_estimated_interest(self):
        for rec in self:
            term = 0
            if rec.is_fixed_rate:
                term = rec.term
            elif rec.is_variable_rate:
                term = rec.term_variable

            rec.estimated_interest = (
                ((rec.actual_amount * (rec.interest_rate + rec.extra_percentage)) / 100) / 360) * term

    @api.depends('estimated_interest', 'actual_amount')
    def get_estimated_profit(self):
        for rec in self:
            rec.estimated_profit = rec.estimated_interest + rec.actual_amount

    @api.onchange('is_fixed_rate')
    def onchange_is_fixed_rate(self):
        if self.is_fixed_rate:
            self.is_variable_rate = False

    @api.onchange('is_variable_rate')
    def onchange_is_variable_rate(self):
        if self.is_variable_rate:
            self.is_fixed_rate = False

    def action_confirm_inv(self):
        self.state = 'confirmed'
        maturity_report_id = self.env['maturity.report'].search([('investment_id','=',self.id)],limit=1)
        vals = {
                'name': self.first_number,
                'investment_id': self.id,
                'partner_id': self.env.user.partner_id.id,
                'date': self.expiry_date
            }
        if maturity_report_id:
            maturity_report_id.write(vals)
        else:
            self.env['maturity.report'].create(vals)

    def action_reset_inv(self):
        self.state = 'draft'

    def transfer_request(self):

        today = datetime.today().date()
        fund_ids = self.line_ids.mapped('investment_fund_id')
        opt_lines = []
        for fund in fund_ids:
            base_ids = self.line_ids.filtered(
                lambda x: x.investment_fund_id.id == fund.id).mapped('base_collabaration_id')
            for base in base_ids:
                lines = self.line_ids.filtered(
                    lambda x: x.investment_fund_id.id == fund.id and x.base_collabaration_id.id == base.id and x.line_state == 'done')
                inc = sum(a.amount for a in lines.filtered(
                    lambda x: x.type_of_operation in ('open_bal', 'increase')))
                ret = sum(a.amount for a in lines.filtered(lambda x: x.type_of_operation in (
                    'retirement', 'withdrawal', 'withdrawal_cancellation', 'withdrawal_closure', 'increase_by_closing')))
                balance = inc - ret
                if balance > 0:
                    opt_lines.append((0, 0, {'opt_line_ids': [(6, 0, lines.ids)], 'investment_fund_id': fund.id,
                                             'base_collabaration_id': base.id, 'agreement_number': base.convention_no, 'amount': balance}))

            lines = self.line_ids.filtered(lambda x: x.investment_fund_id.id ==
                                           fund.id and not x.base_collabaration_id and x.line_state == 'done')
            inc = sum(a.amount for a in lines.filtered(
                lambda x: x.type_of_operation in ('open_bal', 'increase')))
            ret = sum(a.amount for a in lines.filtered(lambda x: x.type_of_operation in (
                'retirement', 'withdrawal', 'withdrawal_cancellation', 'withdrawal_closure', 'increase_by_closing')))
            balance = inc - ret
            if balance > 0:
                opt_lines.append((0, 0, {'opt_line_ids': [
                                 (6, 0, lines.ids)], 'investment_fund_id': fund.id, 'amount': balance}))

        return {
            'name': _('Approve Request'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'inv.transfer.request',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_date': today,
                'default_bank_account_id': self.journal_id and self.journal_id.id or False,
                'default_line_ids': opt_lines,
                'show_for_agreement': True,
                'show_agreement_name': True
            }
        }

    def action_confirm(self):
        today = datetime.today().date()
        return {
            'name': 'Approve Request',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'approve.money.market.bal.req',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_amount': self.amount_to_invest,
                'default_date': today,
                'default_investment_id': self.id,
                'default_fund_type': self.fund_type_id and self.fund_type_id.id or False,
                'default_bank_account_id': self.journal_id and self.journal_id.id or False,
                'show_for_supplier_payment': 1,
                'default_agreement_type': self.agreement_type_id and self.agreement_type_id.id or False,
                'default_base_collabaration_id': self.base_collaboration_id and self.base_collaboration_id.id or False,
                'default_fund_id': self.fund_id and self.fund_id.id or False,

            }
        }

    def get_rate_history(self):
        currency = self.currency_id and self.currency_id.id or False

        return {
            'name': 'Rate',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'view_id': False,
            'res_model': 'res.currency.rate',
            'type': 'ir.actions.act_window',
            #            'target': 'new',
            'domain': [('currency_id', '=', currency)],
            'context': {
                'default_currency_id': currency,
            }
        }

    def action_reject(self):
        print("===")
        #self.state = 'rejected'

    def action_requested(self):
        print("===")
        #self.state = 'requested'
#         if self.investment_fund_id and self.investment_fund_id.state != 'requested':
#             self.investment_fund_id.with_context(call_from_product=True).action_requested()

    def action_approved(self):
        print("===")
        #self.state = 'approved'
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

class AgreementFund(models.Model):

    _inherit = 'agreement.fund'

    def unlink(self):
        for fund in self:
            opt = self.env['investment.operation'].search([('investment_fund_id.fund_id', '=', fund.id)], limit=1)
            if opt:
                raise ValidationError(_('You can not delete Fund which are mapped with investment operation!'))
        return super(AgreementFund, self).unlink()

class InvestmentOperation(models.Model):

    _name = 'investment.operation'
    _description = "Investment Operation"

    investment_id = fields.Many2one(
        'investment.investment', string='First Number:', ondelete='cascade',)
    invoice = fields.Char("Folio")
    operation_number = fields.Char("Operation Number")
    agreement_number = fields.Char("Agreement Number")
    bank_account_id = fields.Many2one(
        'account.journal', "Bank and Origin Account")
    desti_bank_account_id = fields.Many2one(
        'account.journal', "Destination Bank and Account")
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.user.company_id.currency_id)
    amount = fields.Monetary("Amount")
    dependency_id = fields.Many2one('dependency', "Dependency")
    sub_dependency_id = fields.Many2one('sub.dependency', "Subdependency")
    user_id = fields.Many2one(
        'res.users', default=lambda self: self.env.user.id, string="Applicant")
    unit_req_transfer_id = fields.Many2one(
        'dependency', string="Unit requesting the transfer")
    date_required = fields.Date("Date Required")
    fund_type = fields.Many2one('fund.type', "Type Of Fund")
    agreement_type_id = fields.Many2one('agreement.agreement.type', 'Agreement Type')
    base_collabaration_id = fields.Many2one('bases.collaboration', 'Name Of Agreements')
    patrimonial_id = fields.Many2one('patrimonial.resources', "Patrimonial Resource")
    investment_fund_id = fields.Many2one('investment.funds', 'Fund')
    inc_id = fields.Many2one(
        'request.open.balance.invest', 'Increases and Withdrawals', copy=False)

    type_of_operation = fields.Selection([('open_bal', 'Opening Balance'),
                                          ('increase', 'Increase'),
                                          ('retirement', 'Retirement'),
                                          ('withdrawal', 'Withdrawal for settlement'),
                                          ('withdrawal_cancellation',
                                           'Withdrawal Due to Cancellation'),
                                          ('withdrawal_closure',
                                           'Withdrawal due to closure'),
                                          ('increase_by_closing', 'Increase by closing')],
                                         string="Type of Operation")

    origin_resource_id = fields.Many2one(
        'sub.origin.resource', "Origin of the resource")
    line_state = fields.Selection([('draft', 'Draft'),
                                   ('requested', 'Requested'),
                                   ('rejected', 'Rejected'),
                                   ('approved', 'Approved'),
                                   ('confirmed', 'Confirmed'),
                                   ('done', 'Done'),
                                   ('canceled', 'Canceled')], default='draft', string="Status", copy=False)

    record_type = fields.Selection(
        [('manually', 'Manually'), ('automatically', 'Automatically')], string="Record Type", copy=False)
    seq = fields.Integer(
        string='Sequence', compute="get_line_seq", copy=False, store=True)
    journal_id = fields.Many2one(related='investment_id.journal_id')
    source_ids = fields.Many2many('account.journal', 'rel_journal_inv_src_operation',
                                  'journal_id', 'opt_id', compute="get_journal_ids")
    dest_ids = fields.Many2many('account.journal', 'rel_journal_inv_dest_operation',
                                'journal_id', 'opt_id', compute="get_journal_ids")
    is_request_generated = fields.Boolean(default=False, copy=False)
    concept = fields.Text("Application Concept")
    distribution_income_id = fields.Many2one('distribution.of.income','Distribution Income')
    interest_rate_base_id = fields.Many2one('interest.rate.base',copy=False)
    
    def unlink(self):
        for rec in self:
            if rec.line_state not in ['draft']:
                raise UserError(
                    _('You can delete only draft status Operation.'))
        return super(InvestmentOperation, self).unlink()

    @api.depends('journal_id', 'type_of_operation', 'investment_id.journal_id')
    def get_journal_ids(self):
        for rec in self:
            if rec.type_of_operation in ('open_bal', 'increase', 'increase_by_closing'):
                rec.dest_ids = [(6, 0, rec.journal_id.ids)]
            else:
                rec.dest_ids = [
                    (6, 0, self.env['account.journal'].search(['|',('is_productive_account','=',True),('is_investment_account','=',True),('type', '=', 'bank')]).ids)]

            if rec.type_of_operation in ('retirement', 'withdrawal', 'withdrawal_cancellation', 'withdrawal_closure'):
                rec.source_ids = [(6, 0, rec.journal_id.ids)]
            else:
                rec.source_ids = [
                    (6, 0, self.env['account.journal'].search(['|',('is_productive_account','=',True),('is_investment_account','=',True),('type', '=', 'bank')]).ids)]

    @api.onchange('amount', 'type_of_operation', 'base_collabaration_id','bank_account_id')
    def onchange_check_balance_amount(self):
        opt_lines = self.investment_id.line_ids.filtered(
            lambda x: x.line_state == 'done')

        if self.investment_fund_id:
            opt_lines = opt_lines.filtered(
                lambda x: x.investment_fund_id.id == self.investment_fund_id.id)
        if self.base_collabaration_id:
            opt_lines = opt_lines.filtered(
                lambda x: x.base_collabaration_id.id == self.base_collabaration_id.id)
        if self.type_of_operation and self.type_of_operation in ('retirement', 'withdrawal', 'withdrawal_cancellation', 'withdrawal_closure'):
            #opt_lines = self.env['investment.operation'].search([('investment_id','=',self.investment_id.id),('type_of_operation','in',('open_bal','increase')),('base_collabaration_id','=',self.base_collabaration_id.id),('line_state','=','done')])
            #opt_lines = self.investment_id.line_ids.filtered(lambda x:x.base_collabaration_id.id==self.base_collabaration_id.id)
            inc = sum(a.amount for a in opt_lines.filtered(
                lambda x: x.type_of_operation in ('open_bal', 'increase','increase_by_closing')))
            ret = sum(a.amount for a in opt_lines.filtered(lambda x: x.type_of_operation in (
                'retirement', 'withdrawal', 'withdrawal_cancellation', 'withdrawal_closure')))

            balance = inc - ret
            if balance < self.amount:
                self.amount = 0
                return {'warning': {'title': _("Warning"), 'message': 'Available balance is less then amount!!!'}}
        elif self.bank_account_id:
            values= self.env['account.move.line'].search([('account_id', '=', self.bank_account_id.default_debit_account_id.id),('move_id.state', '=', 'posted')])
            account_balance = sum(x.debit-x.credit for x in values)
            if account_balance < self.amount:
                self.amount = 0
                return {'warning': {'title': _("Warning"), 'message': 'Available balance is less then amount!!!'}}
            
            
#     @api.onchange('type_of_operation')
#     def onchange_check_balance_type_of_operation(self):
#         if self.type_of_operation and self.base_collabaration_id and self.type_of_operation in ('retirement','withdrawal','withdrawal_cancellation','withdrawal_closure','increase_by_closing'):
#             #opt_lines = self.env['investment.operation'].search([('investment_id','=',self.investment_id.id),('type_of_operation','in',('open_bal','increase')),('base_collabaration_id','=',self.base_collabaration_id.id),('line_state','=','done')])
#             opt_lines = self.investment_id.line_ids.filtered(lambda x:x.base_collabaration_id.id==self.base_collabaration_id.id)
#             inc = sum(a.amount for a in opt_lines.filtered(lambda x:x.type_of_operation in ('open_bal','increase')))
#             ret = sum(a.amount for a in opt_lines.filtered(lambda x:x.type_of_operation in ('retirement','withdrawal','withdrawal_cancellation','withdrawal_closure','increase_by_closing')))
#
#             balance = inc - ret
#             if balance < self.amount:
#                 self.type_of_operation = False
#                 return {'warning': {'title': _("Warning"), 'message': 'Available balance is less then amount!!!'}}
#
#     @api.onchange('base_collabaration_id')
#     def onchange_check_balance_base_collabaration_id(self):
#         if self.type_of_operation and self.base_collabaration_id and self.type_of_operation in ('retirement','withdrawal','withdrawal_cancellation','withdrawal_closure','increase_by_closing'):
#             #opt_lines = self.env['investment.operation'].search([('investment_id','=',self.investment_id.id),('type_of_operation','in',('open_bal','increase')),('base_collabaration_id','=',self.base_collabaration_id.id),('line_state','=','done')])
#             opt_lines = self.investment_id.line_ids.filtered(lambda x:x.base_collabaration_id.id==self.base_collabaration_id.id)
#             inc = sum(a.amount for a in opt_lines.filtered(lambda x:x.type_of_operation in ('open_bal','increase')))
#             ret = sum(a.amount for a in opt_lines.filtered(lambda x:x.type_of_operation in ('retirement','withdrawal','withdrawal_cancellation','withdrawal_closure','increase_by_closing')))
#
#             balance = inc - ret
#             if balance < self.amount:
#                 self.base_collabaration_id = False
# return {'warning': {'title': _("Warning"), 'message': 'Available balance
# is less then amount!!!'}}

    @api.onchange('type_of_operation')
    def onchange_type_of_operation(self):
        self.bank_account_id = False
        self.desti_bank_account_id = False

    @api.constrains('operation_number')
    def _check_operation_number(self):
        if self.operation_number and not self.operation_number.isnumeric():
            raise ValidationError(_('Operation Number must be Numeric.'))

    def action_reset_to_draft(self):
        self.line_state='draft'

    def action_approved(self):
        self.line_state = 'approved'

    def action_done(self):
        self.line_state = 'done'

    def action_canceled(self):
        self.line_state = 'canceled'

    def action_reject(self):
        self.line_state = 'rejected'

    @api.model
    def default_get(self, fields):
        res = super(InvestmentOperation, self).default_get(fields)
        seq_ids = self.env['ir.sequence'].search(
            [('code', '=', 'folio.inv.operation')], order='company_id')
        number_next = 0
        if seq_ids:
            number_next = seq_ids[0].number_next_actual
        res.update({
            'invoice': str(number_next)
        })
        return res

    @api.model
    def create(self, vals):
        res = super(InvestmentOperation, self).create(vals)
        if res.record_type == 'manually':
            invoice = self.env['ir.sequence'].next_by_code(
                'folio.inv.operation')
            res.invoice = invoice
            
#         if res.type_of_operation and res.type_of_operation == 'open_bal' and res.investment_id and not res.investment_id.update_line_id:
#             res.investment_id.amount_to_invest = res.amount
#             res.investment_id.update_line_id = res.id

        if res.type_of_operation and res.type_of_operation == 'open_bal' and res.investment_id:
            amount = sum(x.amount for x in res.investment_id.line_ids.filtered(lambda x:x.type_of_operation=='open_bal'))
            res.investment_id.amount_to_invest = amount

        return res

    def write(self, vals):
        result = super(InvestmentOperation, self).write(vals)
        if 'amount' in vals or 'type_of_operation' in vals:
            for res in self:
#                 if res.type_of_operation and res.type_of_operation == 'open_bal' and res.investment_id:
#                     if not res.investment_id.update_line_id:
#                         res.investment_id.amount_to_invest = res.amount
#                         res.investment_id.update_line_id = res.id
#                     elif res.investment_id.update_line_id.id == res.id:
#                         res.investment_id.amount_to_invest = res.amount

                if res.type_of_operation and res.type_of_operation == 'open_bal' and res.investment_id:
                    amount = sum(x.amount for x in res.investment_id.line_ids.filtered(lambda x:x.type_of_operation=='open_bal'))
                    res.investment_id.amount_to_invest = amount
                        
        return result

    @api.depends('type_of_operation')
    def get_line_seq(self):
        for rec in self:
            seq = 100
            if rec.type_of_operation == 'open_bal':
                seq = 1
            elif rec.type_of_operation == 'increase':
                seq = 2
            elif rec.type_of_operation == 'increase_by_closing':
                seq = 3
            elif rec.type_of_operation == 'retirement':
                seq = 4
            elif rec.type_of_operation == 'withdrawal_cancellation':
                seq = 5
            elif rec.type_of_operation == 'withdrawal':
                seq = 6
            elif rec.type_of_operation == 'withdrawal_closure':
                seq = 7
            rec.seq = seq

    def action_requested(self):
        vals = {
            'invoice': self.invoice,
            'operation_number': self.operation_number,
            'agreement_number': self.agreement_number,
            'bank_account_id': self.bank_account_id.id if self.bank_account_id else False,
            'desti_bank_account_id': self.desti_bank_account_id.id if self.desti_bank_account_id else False,
            'amount': self.amount,
            'unit_req_transfer_id': self.unit_req_transfer_id.id if self.unit_req_transfer_id else False,
            'date_required': self.date_required,
            'fund_type': self.fund_type.id if self.fund_type else False,
            'agreement_type_id': self.agreement_type_id and self.agreement_type_id.id or False,
            'investment_fund_id': self.investment_fund_id and self.investment_fund_id.id or False,
            'base_collabaration_id': self.base_collabaration_id and self.base_collabaration_id.id or False,
            'investment_operation_id': self.id,
            'state': 'requested',
            'dependency_id': self.dependency_id and self.dependency_id.id or False,
            'sub_dependency_id': self.sub_dependency_id and self.sub_dependency_id.id or False,
            'trasnfer_request':'investments',
        }

        self.env['request.open.balance.finance'].create(vals)
        self.line_state = 'approved'
