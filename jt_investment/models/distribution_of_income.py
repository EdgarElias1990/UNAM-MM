from odoo import models, fields, api , _
from datetime import datetime
from odoo.exceptions import UserError
from datetime import timedelta

class DistributionOfIncome(models.Model):

    _name = 'distribution.of.income'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Distribution Of Income"
    
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    line_ids = fields.One2many('distribution.of.income.line','distribution_id',string='Lines')
    calculation_line_ids = fields.One2many('distribution.of.income.calculation','distribution_id',string='Lines')
    
    
    all_agreement = fields.Boolean(string='All the Agreement',default=False)
    all_types_of_Agreements = fields.Boolean(string='All Types of Agreements',default=False)
    all_base = fields.Boolean(string='All Bases Of Collaboration',default=False)
    all_dependencies = fields.Boolean(string='All Dependencies',default=False)
    
    fund_ids = fields.Many2many('agreement.fund','fund_dist_inc_link','fund_id','dist_link','By Funds')
    agreement_type_ids = fields.Many2many('agreement.agreement.type','agreement_dist_inc_link','fund_id','dist_link','By Type of Agreements')
    base_ids = fields.Many2many('bases.collaboration','base_co_dist_inc_link','fund_id','dist_link','By Collaboration Base')
    dependency_ids = fields.Many2many('dependency','depen_dist_inc_link','fund_id','dist_link','By Unit')
    reason_rejection = fields.Text("Reason Rejection")
    
    state = fields.Selection([('draft', 'Draft'),
                               ('requested', 'Requested'),
                               ('confirmed', 'Confirmed'),
                               ], string="Status", default="draft")
    
    investment_id = fields.Many2one('investment.investment', "Investment")
    journal_id = fields.Many2one('account.journal','Bank', related='investment_id.journal_id')
    # if_fixed = fields.Boolean("Fixed")
    # if_average = fields.Boolean("Average")
    # if_variable = fields.Boolean("Variable")
    #
    # fixed_rate = fields.Float("Rate")
    # average_rate = fields.Float("Rate")
    # variable_rate = fields.Float("Rate")
    #
    # fixed_extra = fields.Float("Extra Percentage")
    # average_extra = fields.Float("Extra Percentage")
    # variable_extra = fields.Float("Extra Percentage")
    
    #@api.onchange('start_date','end_date','dependency_ids','agreement_type_ids','base_ids','fund_ids')


    def unlink(self):
        for rec in self:
            if rec.state not in ['draft']:
                raise UserError(_('You can delete only draft status data.'))
        return super(DistributionOfIncome, self).unlink()

    def get_avg_rate(self,inv):
        rate = 0
        day_diff = self.end_date - self.start_date
        day_diff = day_diff.days+1
        new_date = self.start_date
        count = 0
        for r in range(day_diff):
            count += 1
            period_rate_id = self.env['investment.period.rate'].search([('rate_date','=',new_date),('product_type','=','TIIE')],limit=1)
            if period_rate_id:
                if inv.term_variable == 28:
                    rate += period_rate_id.rate_days_28
                elif inv.term_variable == 91:
                    rate += period_rate_id.rate_days_91
                elif inv.term_variable == 182:
                    rate += period_rate_id.rate_days_182
                elif inv.term_variable == 1:
                    rate += period_rate_id.rate_daily
                
            else:
                period_rate_id = self.env['investment.period.rate'].search([('rate_date','<',new_date),('product_type','=','TIIE')],limit=1,order='rate_date desc')
                if period_rate_id:
                    if inv.term_variable == 28:
                        rate += period_rate_id.rate_days_28
                    elif inv.term_variable == 91:
                        rate += period_rate_id.rate_days_91
                    elif inv.term_variable == 182:
                        rate += period_rate_id.rate_days_182
                    elif inv.term_variable == 1:
                        rate += period_rate_id.rate_daily
            
            new_date =  self.start_date + timedelta(days=count)
        if day_diff > 0:
            rate = rate/day_diff
        else:
            rate = 0
        return rate

    def create_line_records(self,line,opt_line,capital,cal_vals,pre_line,days):
        inc = 0
        withdrawal = 0
        if line.type_of_operation in ('increase','increase_by_closing','open_bal'):
            inc = line.amount
        elif line.type_of_operation in ('retirement','withdrawal','withdrawal_cancellation','withdrawal_closure'):
            withdrawal = line.amount
            
        inv = line.investment_id
        
        term = 0
        rate = 0
        if inv.is_fixed_rate:
            if opt_line==line:
                if not pre_line:
                    
                    term = (self.end_date - line.date_required).days + 1
                    days += term
                else:
                    term = (self.end_date - line.date_required).days + 1
                    days += term
            else:
                if opt_line.date_required and line.date_required:
                    term = (opt_line.date_required - line.date_required).days
                    days += term 
                     
            rate = inv.interest_rate + inv.extra_percentage
            
        elif inv.is_variable_rate:
            v_rate = self.get_avg_rate(inv)
            if opt_line==line:
                term = (self.end_date - line.date_required).days + 1
                
                #term = inv.term_variable - opt_line.date_required.day + 1
            else:
                if opt_line.date_required and line.date_required:
                    term = (opt_line.date_required - line.date_required).days
                    #term = opt_line.date_required.day - line.date_required.day
            
            #term = inv.term_variable
#             if inv.investment_rate_id:
#                 other_rate_id = False
#                 if not other_rate_id: 
#                     if inv.term_variable == 28 and inv.investment_rate_id.rate_days_28:
#                         v_rate = inv.investment_rate_id.rate_days_28
#                         other_rate_id = True
#                     else:
#                         other_rate_id = self.env['investment.period.rate'].search([('rate_days_28','>',0),('rate_date','<=',inv.investment_rate_id.rate_date),('product_type','=',inv.investment_rate_id.product_type)],limit=1,order='rate_date desc')
#                         if other_rate_id:
#                             v_rate = other_rate_id.rate_days_28
#                         other_rate_id = True
#                         
#                 if not other_rate_id:
#                     if inv.term_variable == 91 and inv.investment_rate_id.rate_days_91:
#                         v_rate = inv.investment_rate_id.rate_days_91
#                         other_rate_id = True
#                     else:
#                         other_rate_id = self.env['investment.period.rate'].search([('rate_days_91','>',0),('rate_date','<=',inv.investment_rate_id.rate_date),('product_type','=',inv.investment_rate_id.product_type)],limit=1,order='rate_date desc')
#                         if other_rate_id:
#                             v_rate = other_rate_id.rate_days_91
#                         other_rate_id = True
#                         
#                 if not other_rate_id:                                    
#                     if inv.term_variable == 182 and inv.investment_rate_id.rate_days_182:
#                         v_rate = inv.investment_rate_id.rate_days_182
#                         other_rate_id = True
#                     else:
#                         other_rate_id = self.env['investment.period.rate'].search([('rate_days_182','>',0),('rate_date','<=',inv.investment_rate_id.rate_date),('product_type','=',inv.investment_rate_id.product_type)],limit=1,order='rate_date desc')
#                         if other_rate_id:
#                             v_rate = other_rate_id.rate_days_182
#                         other_rate_id = True
                        
            rate = v_rate + inv.extra_percentage
        
        final_balance = capital + inc - withdrawal
        income = (((final_balance * rate)/100)/360)*term
        
        cal_vals.append([0, 0, 
                    {
                     'fund_id':line.investment_fund_id and line.investment_fund_id.fund_id and line.investment_fund_id.fund_id.id or False,
                     'investment_fund_id' : line.investment_fund_id and line.investment_fund_id.id or False,
                     'agreement_type_id':line.agreement_type_id and line.agreement_type_id.id or False,
                     'base_id' : line.base_collabaration_id and line.base_collabaration_id.id or False,
                     'dependency_id' : line.dependency_id and line.dependency_id.id or False,
                     'capital' : capital,
                     'increments' : inc,
                     'withdrawals' : withdrawal,
                     'final_balance' : final_balance,
                     'income' : income,
                     'rounded': income,
                     'rate' : rate,
                     'days': term,
                     #'days':  (self.end_date - line.date_required).days + 1,
                     'date_required' : line.date_required,
                     }]) 
        if line.type_of_operation in ('increase','increase_by_closing','open_bal'):
            capital += line.amount
        elif line.type_of_operation in ('retirement','withdrawal','withdrawal_cancellation','withdrawal_closure'):
            capital -= line.amount
        return cal_vals,capital,days
    
    # def set_rate_data(self,inv):
    #     if inv.is_fixed_rate:
    #         self.if_fixed = True
    #         self.fixed_rate = inv.interest_rate
    #         self.fixed_extra = inv.extra_percentage
    #     elif inv.is_variable_rate:
    #         self.if_variable = True
    #         self.variable_extra = inv.extra_percentage
    #         total_rate = 0.0
    #         total_days = self.end_date.day - self.start_date.day + 1
    #
    #         rate_ids = self.env['investment.period.rate'].search([('rate_date','>=',self.start_date),('rate_date','<=',self.end_date),('product_type','=','TIIE')])
    #         if inv.term_variable and inv.term_variable==28:
    #             total_rate = sum(x.rate_days_28 for x in rate_ids)
    #         elif inv.term_variable and inv.term_variable==91:
    #             total_rate = sum(x.rate_days_91 for x in rate_ids)
    #         elif inv.term_variable and inv.term_variable==182:
    #             total_rate = sum(x.rate_days_182 for x in rate_ids)
    #
    #
    #         self.variable_rate = total_rate/total_days
    
    def get_previous_capital(self,cal_vals,pre_lines,capital_next_line,inv,fund,base):
        
        if capital_next_line and capital_next_line.date_required:
            term = (capital_next_line.date_required - self.start_date).days 
        else:
            term = (self.end_date - self.start_date).days + 1
        rate = 0
        if inv.is_fixed_rate:                     
            rate = inv.interest_rate + inv.extra_percentage
            
        elif inv.is_variable_rate:
            v_rate = 0
            
            #term = inv.term_variable
            if inv.investment_rate_id:
                other_rate_id = False
                if not other_rate_id: 
                    if inv.term_variable == 28 and inv.investment_rate_id.rate_days_28:
                        v_rate = inv.investment_rate_id.rate_days_28
                        other_rate_id = True
                    else:
                        other_rate_id = self.env['investment.period.rate'].search([('rate_days_28','>',0),('rate_date','<=',inv.investment_rate_id.rate_date),('product_type','=',inv.investment_rate_id.product_type)],limit=1,order='rate_date desc')
                        if other_rate_id:
                            v_rate = other_rate_id.rate_days_28
                        other_rate_id = True
                        
                if not other_rate_id:
                    if inv.term_variable == 91 and inv.investment_rate_id.rate_days_91:
                        v_rate = inv.investment_rate_id.rate_days_91
                        other_rate_id = True
                    else:
                        other_rate_id = self.env['investment.period.rate'].search([('rate_days_91','>',0),('rate_date','<=',inv.investment_rate_id.rate_date),('product_type','=',inv.investment_rate_id.product_type)],limit=1,order='rate_date desc')
                        if other_rate_id:
                            v_rate = other_rate_id.rate_days_91
                        other_rate_id = True
                        
                if not other_rate_id:                                    
                    if inv.term_variable == 182 and inv.investment_rate_id.rate_days_182:
                        v_rate = inv.investment_rate_id.rate_days_182
                        other_rate_id = True
                    else:
                        other_rate_id = self.env['investment.period.rate'].search([('rate_days_182','>',0),('rate_date','<=',inv.investment_rate_id.rate_date),('product_type','=',inv.investment_rate_id.product_type)],limit=1,order='rate_date desc')
                        if other_rate_id:
                            v_rate = other_rate_id.rate_days_182
                        other_rate_id = True
            v_rate = self.get_avg_rate(inv)
            rate = v_rate + inv.extra_percentage
        capital = 0
        for line in pre_lines:
            if line.type_of_operation in ('increase','increase_by_closing','open_bal'):
                capital += line.amount
            elif line.type_of_operation in ('retirement','withdrawal','withdrawal_cancellation','withdrawal_closure'):
                capital -= line.amount

            
        final_balance = capital 
        income = (((final_balance * rate)/100)/360)*term
        
        cal_vals.append([0, 0, 
                    {
                     'fund_id':fund and fund.fund_id and fund.fund_id.id or False,
                     'investment_fund_id' : fund and fund.id or False,
                     'agreement_type_id':False,
                     'base_id' : base and base.id or False,
                     'dependency_id' : False,
                     'capital' : capital,
                     'increments' : 0,
                     'withdrawals' : 0,
                     'final_balance' : final_balance,
                     'income' : income,
                     'rounded': income,
                     'rate' : rate,
                     'days':  term,
                     'date_required' : self.start_date,
                     }]) 
        return cal_vals,capital
         
    def action_calculation(self):
        #domain = [('bases_collaboration_id','!=',False)]
        domain = [('line_state','=','done'), ('investment_id', '=', self.investment_id.id)]
        capital_domain = [('line_state','=','done'), ('investment_id', '=', self.investment_id.id)]
        
        self.line_ids = [(6, 0, [])]
        self.calculation_line_ids = [(6, 0, [])]
        vals = []
        cal_vals = []
        
        if self.start_date:
            domain.append(('date_required','>=',self.start_date))
            capital_domain.append(('date_required','<',self.start_date))
        if self.end_date:
            domain.append(('date_required','<=',self.end_date))
            
            
        if self.journal_id:
            domain.append(('investment_id.journal_id','=',self.journal_id.id))
            capital_domain.append(('investment_id.journal_id','=',self.journal_id.id))
            
        #base_ids = self.env['bases.collaboration'].search(domain)
        #base_ids = requests.mapped('bases_collaboration_id')
        
        opt_lines = self.env['investment.operation'].search(domain,order='date_required,id')
        capital_lines = self.env['investment.operation'].search(capital_domain,order='date_required,id')
        
        if self.dependency_ids and not self.all_dependencies:
            opt_lines = opt_lines.filtered(lambda x:x.dependency_id.id in self.dependency_ids.ids)
            capital_lines = capital_lines.filtered(lambda x:x.dependency_id.id in self.dependency_ids.ids)
            
        if self.agreement_type_ids and not self.all_types_of_Agreements:
            opt_lines = opt_lines.filtered(lambda x:x.agreement_type_id.id in self.agreement_type_ids.ids)
            capital_lines = capital_lines.filtered(lambda x:x.agreement_type_id.id in self.agreement_type_ids.ids)
            
        if self.base_ids and not self.all_base:
            opt_lines = opt_lines.filtered(lambda x:x.base_collabaration_id.id in self.base_ids.ids)
            capital_lines = capital_lines.filtered(lambda x:x.base_collabaration_id.id in self.base_ids.ids)
            
        if self.fund_ids and not self.all_agreement:
            opt_lines = opt_lines.filtered(lambda x:x.investment_fund_id.fund_id.id in self.fund_ids.ids)
            capital_lines = capital_lines.filtered(lambda x:x.investment_fund_id.fund_id.id in self.fund_ids.ids)
        
        inv_ids = opt_lines.mapped('investment_id')
        if not inv_ids and capital_lines:
            cal_vals,capital = self.get_previous_capital(cal_vals,capital_lines,False,self.investment_id,False,False)
        for inv  in inv_ids:
            # self.set_rate_data(inv)
            investment_fund_ids = opt_lines.filtered(lambda x:x.investment_id.id == inv.id and not x.base_collabaration_id).mapped('investment_fund_id')
            
            for capital_fund in capital_lines.filtered(lambda x:not x.base_collabaration_id and x.investment_id.id == inv.id and x.investment_fund_id.id not in investment_fund_ids.ids).mapped('investment_fund_id'):
                capital_next_line = False
                pre_capital_lines = capital_lines.filtered(lambda x:not x.base_collabaration_id and x.investment_id.id == inv.id and x.investment_fund_id.id == capital_fund.id)
                
                cal_vals,capital = self.get_previous_capital(cal_vals,pre_capital_lines,capital_next_line,inv,capital_fund,False)
                
            for fund in investment_fund_ids:
                capital = 0
                days = 0
                line = False
                pre_line = False
                capital_next_line = False
                fund_lines = opt_lines.filtered(lambda x:not x.base_collabaration_id and x.investment_id.id == inv.id and x.investment_fund_id.id == fund.id)

                pre_capital_lines = capital_lines.filtered(lambda x:not x.base_collabaration_id and x.investment_id.id == inv.id and x.investment_fund_id.id == fund.id)
                
                if pre_capital_lines:
                    if fund_lines:
                        capital_next_line = fund_lines[0]  
                    cal_vals,capital = self.get_previous_capital(cal_vals,pre_capital_lines,capital_next_line,inv,fund,False)
                      
                for opt_line in fund_lines:
                    if not line:
                        line = opt_line
                        continue
                    pre_line = opt_line
                    cal_vals,capital,days = self.create_line_records(line,opt_line,capital,cal_vals,pre_line,days)
                    line = opt_line
                if line:
                    cal_vals,capital,days = self.create_line_records(line,line,capital,cal_vals,pre_line,days)

            #Prevois Line #
            investment_fund_ids = opt_lines.filtered(lambda x:x.investment_id.id == inv.id and x.base_collabaration_id).mapped('investment_fund_id')
            capital_investment_fund_ids = capital_lines.filtered(lambda x:x.investment_id.id == inv.id and x.base_collabaration_id and x.investment_fund_id.id not in investment_fund_ids.ids).mapped('investment_fund_id')
            for fund in capital_investment_fund_ids:

                clb_base_ids = capital_lines.filtered(lambda x:x.investment_id.id == inv.id and x.investment_fund_id.id == fund.id).mapped('base_collabaration_id')
                for capital_base in clb_base_ids:
                    capital_next_line = False
                    pre_capital_lines = capital_lines.filtered(lambda x:x.base_collabaration_id.id==capital_base.id and x.investment_id.id == inv.id and x.investment_fund_id.id == fund.id)
                    cal_vals,capital = self.get_previous_capital(cal_vals,pre_capital_lines,capital_next_line,inv,fund,capital_base)
            
            for fund in investment_fund_ids:
                clb_base_ids = opt_lines.filtered(lambda x:x.investment_id.id == inv.id and x.investment_fund_id.id == fund.id).mapped('base_collabaration_id')
                for capital_base in capital_lines.filtered(lambda x:x.investment_id.id == inv.id and x.investment_fund_id.id == fund.id and x.base_collabaration_id.id not in clb_base_ids.ids).mapped('base_collabaration_id'):
                    capital_next_line = False
                    pre_capital_lines = capital_lines.filtered(lambda x:x.base_collabaration_id.id==capital_base.id and x.investment_id.id == inv.id and x.investment_fund_id.id == fund.id)
                    cal_vals,capital = self.get_previous_capital(cal_vals,pre_capital_lines,capital_next_line,inv,fund,capital_base)
                
                 
                for base in clb_base_ids:
                    capital = 0
                    days = 0 
                    line = False
                    pre_line = False
                    capital_next_line = False
                    base_lines = opt_lines.filtered(lambda x:x.base_collabaration_id.id==base.id and x.investment_id.id == inv.id and x.investment_fund_id.id == fund.id)

                    if base_lines:
                        capital_next_line = base_lines[0]
                         
                    pre_capital_lines = capital_lines.filtered(lambda x:x.base_collabaration_id and x.investment_id.id == inv.id and x.investment_fund_id.id == fund.id)
                    if pre_capital_lines:
                        cal_vals,capital = self.get_previous_capital(cal_vals,pre_capital_lines,capital_next_line,inv,fund,base)
                          
                    for opt_line in base_lines:
                        if not line:
                            line = opt_line
                            continue
                        
                        pre_line = opt_line
                        cal_vals,capital,days = self.create_line_records(line,opt_line,capital,cal_vals,pre_line,days)
                        line = opt_line
                        
                    if line:
                        cal_vals,capital,days = self.create_line_records(line,line,capital,cal_vals,pre_line,days)
        self.calculation_line_ids = cal_vals 

    def action_confirm(self):
        today = datetime.today().date()
        user = self.env.user
        employee = self.env['hr.employee'].search(
            [('user_id', '=', user.id)], limit=1)
        fund_type = False
        amount = sum(x.income for x in self.calculation_line_ids)
        return {
            'name': _('Approve Request'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'approve.money.market.bal.req',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_amount': amount,
                'default_date': today,
                'default_employee_id': employee.id if employee else False,
                'default_distribution_id': self.id,
                'default_fund_type': fund_type,
                #'default_bank_account_id' : self.journal_id and self.journal_id.id or False,
                'show_for_supplier_payment': 1,
            }
        }

    def transfer_request(self):

        today = datetime.today().date()
        fund_ids = self.calculation_line_ids.mapped('investment_fund_id')
        opt_lines = []
        total_transfer = 0
        for fund in fund_ids:
            base_ids = self.calculation_line_ids.filtered(
                lambda x: x.investment_fund_id.id == fund.id).mapped('base_id')
            for base in base_ids:
                lines = self.calculation_line_ids.filtered(
                    lambda x: x.investment_fund_id.id == fund.id and x.base_id.id == base.id)
                
                balance = sum(a.rounded for a in lines)
                #balance = inc - ret
                if balance > 0:
                    opt_lines.append((0, 0, {'opt_line_ids': [(6, 0, lines.ids)], 'investment_fund_id': fund.id,
                                             'base_collabaration_id': base.id, 'agreement_number': base.convention_no, 'amount': balance,'amount_to_transfer':balance,'check':True}))
                    total_transfer += balance
                    
            lines = self.calculation_line_ids.filtered(lambda x: x.investment_fund_id.id ==
                                           fund.id and not x.base_id)
            
            balance = sum(a.rounded for a in lines)
            
            if balance > 0:
                opt_lines.append((0, 0, {'opt_line_ids': [
                                 (6, 0, lines.ids)], 'investment_fund_id': fund.id, 'amount': balance,'amount_to_transfer':balance,'check':True}))
                total_transfer += balance 
        dis_journal = self.env.ref(
            'jt_investment.distribution_of_income')
        journal_id = False
        if dis_journal:
            journal_id = dis_journal.id
        
        return {
            'name': 'Approve Request',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'distribution.transfer.request',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_distribution_income_id':self.id,
                'default_date': today,
                'default_bank_account_id': journal_id,
                'default_line_ids': opt_lines,
                'show_for_agreement': True,
                'show_agreement_name': True,
                'default_amount' : total_transfer,
            }
        }

    def action_requested(self):
        self.state = 'requested'

    def action_confirmed(self):
        self.state = 'confirmed'
        
        
class DistributionOfIncomeLine(models.Model):
    
    _name = 'distribution.of.income.line'
    _description = "Distribution Of Income Line"
    
    distribution_id = fields.Many2one('distribution.of.income','Distribution') 
    
    fund_id = fields.Many2one('agreement.fund','Fund')
    agreement_type_id = fields.Many2one('agreement.agreement.type','Type Of Agreements')
    base_id = fields.Many2one('bases.collaboration','Name of the B.C')
    dependency_id = fields.Many2one('dependency','Dependency')
    dependency_name = fields.Char(related='dependency_id.dependency',string='Dependency')
    dependency_description = fields.Text(related='dependency_id.description',string='Dependency Description')
    capital = fields.Float("Capital")
    increments = fields.Float("Increments")
    withdrawals = fields.Float("Withdrawals")
    final_balance = fields.Float("Final Balance")
    
class DistributionOfIncomecalculation(models.Model):
    
    _name = 'distribution.of.income.calculation'
    _description = "Distribution Of Income Line"
    _order= 'date_required'
    
    distribution_id = fields.Many2one('distribution.of.income','Distribution')    

    investment_fund_id = fields.Many2one('investment.funds','Fund')
    fund_id = fields.Many2one('agreement.fund','Fund')
    agreement_type_id = fields.Many2one('agreement.agreement.type','Type Of Agreements')
    base_id = fields.Many2one('bases.collaboration','Basis of Collaboration')    
    dependency_id = fields.Many2one('dependency','Dependency')
    dependency_name = fields.Char(related='dependency_id.dependency',string='Dependency')
    dependency_description = fields.Text(related='dependency_id.description',string='Dependency Description')
    capital = fields.Float("Capital")
    increments = fields.Float("Increments")
    withdrawals = fields.Float("Withdrawals")
    final_balance = fields.Float("Final Balance")
    income = fields.Float('Income')
    rounded = fields.Float("Rounded")
    rate = fields.Float("Average Rate")
    days = fields.Integer("Days")
    date_required = fields.Date("Date Required")
    
    
    