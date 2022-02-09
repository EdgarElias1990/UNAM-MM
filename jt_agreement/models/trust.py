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
from odoo.exceptions import ValidationError,UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class Trust(models.Model):

    _name = 'agreement.trust'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Agreement Trust"

    name = fields.Char("Trust Name")
    bank_id = fields.Many2one('res.bank','Banking institution')
    bank_account_id = fields.Many2one('account.journal',string='Bank Account',domain=[('type','=','bank')])
    register_date = fields.Date('Date of registration in the system',default=datetime.today())
    street = fields.Char(related='bank_id.street')
    street2 = fields.Char(related='bank_id.street2')
    city = fields.Char(related='bank_id.city')
    state_id = fields.Many2one(related='bank_id.state')
    zip = fields.Char(related='bank_id.zip')
    country = fields.Many2one(related='bank_id.country')
    
    dependency_id = fields.Many2one('dependency', "Dependency")
    dependency_desc =  fields.Text(related="dependency_id.description")
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.user.company_id.currency_id)
    
    opening_balance = fields.Float("Opening balance")
    available_bal = fields.Monetary("Available Balance", compute='_compute_available_bal', store=True)
    origin_resource_id = fields.Many2one('sub.origin.resource', "Origin of the resource")
    executive_name = fields.Char("Executive name")
    phone = fields.Char("Phone")
    email = fields.Char("Email")
    home = fields.Char("Home")
    state = fields.Selection([('draft', 'Draft'),
                               ('valid', 'Valid'),
                               ('in_force', 'In Force'),
                              ('to_be_cancelled', 'To Be Cancelled'),
                              ('cancelled', 'Cancelled')], "Status", default='draft')
  
    goals = fields.Char("Goals")
    patrimonial_account_id = fields.Many2one('account.account', "Patrimonial Account")
    investment_account_id = fields.Many2one('account.account', "Investment Account")
    interest_account_id = fields.Many2one('account.account', "Interest Accounting Account")
    honorary_account_id = fields.Many2one('account.account', "Honorary Accounting Account")
    availability_account_id = fields.Many2one('account.account', "Availability Accounting Account")
    liability_account_id = fields.Many2one('account.account', "Liability Account")

    trust_agreement_file = fields.Binary("Trust Agreement")
    trust_agreement_file_name = fields.Char("Trust Agreement File Name")
    trust_office_file = fields.Binary("Trust Office")
    trust_office_file_name = fields.Char("Trust Office File Name")
    
    no_beneficiary_allowed = fields.Integer("Number of allowed beneficiaries")
    beneficiary_ids = fields.One2many('collaboration.beneficiary', 'trust_id')
    provider_ids = fields.One2many('collaboration.providers', 'trust_id')

    committe_ids = fields.One2many('committee', 'trust_id', string="Committees")

    request_open_balance_ids = fields.One2many('request.open.balance','trust_id')
    total_operations = fields.Integer("Operations", compute="compute_operations")
    total_modifications = fields.Integer("Modifications", compute="compute_modifications")

    cancel_date = fields.Date("Cancellation date")
    supporing_doc = fields.Binary("Supporting Documentation")
    reason_cancel = fields.Text("Reason for Cancellations")

    interest_date = fields.Date(string="Interest Date")
    fees = fields.Monetary(string="Fees")
    yields = fields.Monetary(string="Yields")
    next_no = fields.Integer(string="Next Number")
    interest_rate_ids= fields.One2many('interest.rate.operation','trust_id')
    
    report_start_date = fields.Date("report_start_date")
    report_end_date = fields.Date("report_end_date")

    @api.depends('interest_rate_ids', 'interest_rate_ids.yields', 'interest_rate_ids.fees','request_open_balance_ids','request_open_balance_ids.type_of_operation_trust','request_open_balance_ids.state')
    def _compute_available_bal(self):
        for trust in self:
            available_bal = 0
            if trust.request_open_balance_ids.filtered(lambda x:x.state=='confirmed' and x.type_of_operation in ('withdrawal_cancellation','withdrawal')):
                available_bal = 0
            else:
                retirement = sum(req.opening_balance for req in trust.request_open_balance_ids.filtered(lambda x:x.state=='confirmed' and x.type_of_operation == 'retirement'))
                available_bal -= retirement
                inc = sum(req.opening_balance for req in trust.request_open_balance_ids.filtered(lambda x:x.state=='confirmed' and x.type_of_operation not in ('withdrawal_cancellation','withdrawal','retirement')))
                available_bal += inc
                 
                yield_sum = sum(line.yields for line in trust.interest_rate_ids)
                fees_sum = sum(line.fees for line in trust.interest_rate_ids)
                available_bal += yield_sum
                available_bal -= fees_sum 
            trust.available_bal = available_bal
            
    def compute_operations(self):
        for rec in self:
            operations = len(rec.request_open_balance_ids)
            rec.total_operations =operations
            
    def compute_modifications(self):
        modification_obj = self.env['agreement.trust.modification']
        for rec in self:
            modifications = modification_obj.search([('trust_id', '=', rec.id)])
            rec.total_modifications = len(modifications)
            
    @api.constrains('phone')
    def _check_phone(self):
        if self.phone and not self.phone.isnumeric():
            raise ValidationError(_('Phone No must be Numeric.'))
    
    
    @api.model
    def create(self, vals):
        res = super(Trust, self).create(vals)
        if res and res.beneficiary_ids:
            if not res.no_beneficiary_allowed or (res.no_beneficiary_allowed and \
                                                  res.no_beneficiary_allowed < len(res.beneficiary_ids)):
                raise ValidationError(_("You can add only %s Beneficiaries which is mentined in "
                                        "'Number of allowed beneficiaries'" % res.no_beneficiary_allowed))

        no = 0
        for ben in res.beneficiary_ids:
            no = no + 1
            ben.sequence = no
                
        return res

    def write(self, vals):
        res = super(Trust, self).write(vals)
        for rec in self:
            if rec and rec.beneficiary_ids:
                if not rec.no_beneficiary_allowed or (rec.no_beneficiary_allowed and \
                                                      rec.no_beneficiary_allowed < len(rec.beneficiary_ids)):
                    raise ValidationError(_("You can add only %s Beneficiaries which is mentined in "
                                            "'Number of allowed beneficiaries'" % rec.no_beneficiary_allowed))

        if vals.get('beneficiary_ids'):
            for rec in self:
                no = 0
                for ben in rec.beneficiary_ids:
                    no = no + 1
                    ben.sequence = no                    
        return res
    
    def confirm(self):
        self.state = 'valid'
        if self.opening_balance==0:
            raise ValidationError(_("Please add the opening balance amount"))
            
        
    def in_force(self):
        self.state = 'in_force'
        
    def action_to_be_cancelled(self):
        self.state = 'to_be_cancelled'

    def action_set_cancel(self):
        self.state = 'cancelled'
        
    def cancel(self):
        return {
            'name': 'Cancel Trust',
            'view_mode': 'form',
            'view_id': self.env.ref('jt_agreement.cancel_trust_form_view').id,
            'res_model': 'cancel.trust',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }
        
    def action_operations(self):
        if self.request_open_balance_ids:
            return {
                'name': 'Operations',
                'view_type': 'form',
                # 'view_id': self.env.ref('jt_agreement.view_req_open_balance_tree').id,
                'view_mode': 'tree,form',
                'views': [(self.env.ref("jt_agreement.view_req_open_balance_trust_tree").id, 'tree'), (self.env.ref("jt_agreement.view_req_open_balance_trust_form").id, 'form')],
                'res_model': 'request.open.balance',
                'domain': [('trust_id', '=', self.id)],
                'type': 'ir.actions.act_window',
                'context': {'default_trust_id': self.id,
                            'default_apply_to_basis_collaboration': True,
                            'default_origin_resource_id': self.origin_resource_id and self.origin_resource_id.id or False,
                            'default_opening_balance': self.opening_balance,
                            #'default_trust_agreement_file': self.trust_agreement_file,
                            #'default_trust_agreement_file_name': self.trust_agreement_file_name,
                            #'default_trust_office_file': self.trust_office_file,
                            #'default_trust_office_file_name': self.trust_office_file_name,
                            #'default_supporting_documentation': self.trust_office_file,
                            'default_name': self.name,
                            'default_patrimonial_account_id': self.patrimonial_account_id.id if self.patrimonial_account_id
                                    else False,
                            'default_investment_account_id': self.investment_account_id.id if self.investment_account_id
                                    else False,
                            'default_interest_account_id': self.interest_account_id.id if self.interest_account_id
                            else False,
                            'default_honorary_account_id': self.honorary_account_id.id if self.honorary_account_id
                            else False,
                            'default_availability_account_id': self.availability_account_id.id if self.availability_account_id
                            else False,
                            'default_liability_account_id': self.liability_account_id.id if self.liability_account_id
                            else False
                            
                            
                            }
            }
        else:
            return {
                'name': 'Operations',
                # 'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('jt_agreement.view_req_open_balance_trust_form').id,
                'view_ids': [self.env.ref("jt_agreement.view_req_open_balance_trust_form").id],
                'res_model': 'request.open.balance',
                'domain': [('trust_id', '=', self.id)],
                'type': 'ir.actions.act_window',
                'context': {'default_trust_id': self.id,
                            'default_apply_to_basis_collaboration': True,
                            'default_origin_resource_id': self.origin_resource_id and self.origin_resource_id.id or False,
                            'default_opening_balance': self.opening_balance,
                            #'default_trust_agreement_file': self.trust_agreement_file,
                            #'default_trust_agreement_file_name': self.trust_agreement_file_name,
                            #'default_trust_office_file': self.trust_office_file,
                            #'default_trust_office_file_name': self.trust_office_file_name,
                            #'default_supporting_documentation': self.trust_office_file,
                            'default_name': self.name,
                            'default_patrimonial_account_id': self.patrimonial_account_id.id if self.patrimonial_account_id
                                    else False,
                            'default_investment_account_id': self.investment_account_id.id if self.investment_account_id
                                    else False,
                            'default_interest_account_id': self.interest_account_id.id if self.interest_account_id
                            else False,
                            'default_honorary_account_id': self.honorary_account_id.id if self.honorary_account_id
                            else False,
                            'default_availability_account_id': self.availability_account_id.id if self.availability_account_id
                            else False,
                            'default_liability_account_id': self.liability_account_id.id if self.liability_account_id
                            else False
                            }
            }
    def action_modifications(self):
        modification_obj = self.env['agreement.trust.modification']
        modifications = modification_obj.search([('trust_id', '=', self.id)])
        if modifications:
            return {
                'name': 'Modifications',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'agreement.trust.modification',
                'domain': [('trust_id', '=', self.id)],
                'type': 'ir.actions.act_window',
                'context': {'default_dependency_id': self.dependency_id and self.dependency_id.id or False,
                            'default_trust_id': self.id,
                            'default_current_target': self.goals,
                            'from_modification': True
                            }
            }
        else:
            return {
                'name': 'Modifications',
                'view_mode': 'form',
                'res_model': 'agreement.trust.modification',
                'domain': [('trust_id', '=', self.id)],
                'type': 'ir.actions.act_window',
                'context': {'default_dependency_id': self.dependency_id and self.dependency_id.id or False,
                            'default_trust_id': self.id,
                            'default_current_target': self.goals,
                            'from_modification': True
                            }
            }

    def action_schedule_withdrawal(self):
        req_obj = self.env['request.open.balance']
        for trust in self:
            for beneficiary in trust.beneficiary_ids:
                if beneficiary.validity_start and beneficiary.validity_final_beneficiary and beneficiary.withdrawal_sch_date and beneficiary.payment_rule_id:
                    
                    total_month = (beneficiary.validity_final_beneficiary.year - beneficiary.validity_start.year) * 12 +  (beneficiary.validity_final_beneficiary.month - beneficiary.validity_start.month)
                    start_date = beneficiary.validity_start
                    req_date = start_date.replace(day=beneficiary.withdrawal_sch_date.day)

                    need_skip = 1
                    if beneficiary.payment_rule_id.payment_period == 'bimonthly':
                        need_skip = 2
                    elif beneficiary.payment_rule_id.payment_period == 'quarterly':
                        need_skip = 3
                    elif beneficiary.payment_rule_id.payment_period == 'biquarterly':
                        need_skip = 6
                    elif beneficiary.payment_rule_id.payment_period == 'annual':
                        need_skip = 12
                    elif beneficiary.payment_rule_id.payment_period == 'biannual':
                        need_skip = 24
                    count = 0
                    for month in range(total_month+1):
                        if month != 0:
                            req_date = req_date + relativedelta(months=1)
                        if count != 0:
                            count += 1
                            if count==need_skip:
                                count = 0
                            continue
                        
                        count += 1
                        if count==need_skip:
                            count = 0
                        if beneficiary.partner_id:
                            partner_id = beneficiary.partner_id.id
                        else: 
                            partner_id = beneficiary.employee_id and beneficiary.employee_id.user_id and beneficiary.employee_id.user_id.partner_id and beneficiary.employee_id.user_id.partner_id.id or False   
                        req_obj.create({
                            'trust_id': trust.id,
                            'apply_to_basis_collaboration': True,
                            #'agreement_number': collaboration.convention_no,
                            'opening_balance': beneficiary.amount,
                            'supporting_documentation': trust.trust_office_file,
                            'type_of_operation': 'retirement',
                            'beneficiary_id': partner_id,
                            'name': self.name,
                            'request_date' : req_date,
                            'patrimonial_account_id' : trust.patrimonial_account_id and trust.patrimonial_account_id.id or False,
                            'investment_account_id' : trust.investment_account_id and trust.investment_account_id.id or False,
                            'interest_account_id' : trust.interest_account_id and trust.interest_account_id.id or False,
                            'honorary_account_id' : trust.honorary_account_id and trust.honorary_account_id.id or False,
                            'availability_account_id' : trust.availability_account_id and trust.availability_account_id.id or False,
                            'liability_account_id' : trust.liability_account_id and trust.liability_account_id.id or False,
                        })

        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('¡Operations were successful!'),
                'message': _('Enter the BD to continue with the process'),
                'type': 'success',  # types: success,warning,danger,info
                'sticky': True,  # True/False will display for few seconds if false
            },
        }
        return notification

#             for beneficiary in trust.provider_ids:
#                 partner_id = beneficiary.partner_id and beneficiary.partner_id.id or False    
#                 req_obj.create({
#                     'trust_id': trust.id,
#                     'apply_to_basis_collaboration': True,
#                     #'agreement_number': collaboration.convention_no,
#                     'opening_balance': trust.opening_balance,
#                     'supporting_documentation': trust.trust_office_file,
#                     'type_of_operation': 'retirement',
#                     'provider_id': partner_id,
#                     'name': self.name,
#                     'patrimonial_account_id' : trust.patrimonial_account_id and trust.patrimonial_account_id.id or False,
#                     'investment_account_id' : trust.investment_account_id and trust.investment_account_id.id or False,
#                     'interest_account_id' : trust.interest_account_id and trust.interest_account_id.id or False,
#                     'honorary_account_id' : trust.honorary_account_id and trust.honorary_account_id.id or False,
#                     'availability_account_id' : trust.availability_account_id and trust.availability_account_id.id or False,
#                     'liability_account_id' : trust.liability_account_id and trust.liability_account_id.id or False,
#                 })

    def get_report_lines(self):
        lines = []
        folio=1
        final = 0
        lang = self.env.user.lang
#         req_date = self.request_open_balance_ids.filtered(lambda x: self.report_start_date and self.report_end_date \
#             and x.state=='confirmed' and \
#             x.request_date >= self.report_start_date and x.request_date <= self.report_end_date).mapped('request_date')
#         req_date += self.interest_rate_ids.filtered(lambda x: self.report_start_date and self.report_end_date and \
#             x.interest_date >= self.report_start_date and \
#            x.interest_date <= self.report_end_date).mapped('interest_date')
        
        req_date = self.request_open_balance_ids.mapped('request_date')
        req_date += self.interest_rate_ids.mapped('interest_date')
        
        if req_date:
            req_date = list(set(req_date))
            req_date =  sorted(req_date)
        
        for req in req_date:
            opt_lines = self.request_open_balance_ids.filtered(lambda x:x.state=='confirmed' and x.type_of_operation == 'open_bal' and  x.request_date == req)
            for line in opt_lines:
                final += line.opening_balance
                lines.append({'folio':folio,
                              'date':line.request_date,
                              'opt': 'Apertura de saldo' if lang == 'es_MX' else 'Opening Balance',
                              'debit':line.opening_balance,
                              'credit' : 0.0,
                              'final' : final
                              })
                folio += 1
                
            opt_lines = self.request_open_balance_ids.filtered(lambda x:x.state=='confirmed' and x.type_of_operation == 'increase' and  x.request_date == req)
            for line in opt_lines:
                final += line.opening_balance
                lines.append({'folio':folio,
                              'date':line.request_date,
                              'opt': 'Incremento' if lang == 'es_MX' else 'Increase',
                              'debit':line.opening_balance,
                              'credit' : 0.0,
                              'final' : final
                              })
                folio += 1
            for line in self.interest_rate_ids.filtered(lambda x:x.interest_date == req):
                final += line.yields
                lines.append({'folio':folio,
                              'date':line.interest_date,
                              'opt': 'Intereses' if lang == 'es_MX' else 'Yields',
                              'debit':line.yields,
                              'credit' : 0.0,
                              'final' : final
                              })
                folio += 1
    
                final -= line.fees
                lines.append({'folio':folio,
                              'date':line.interest_date,
                              'opt': 'Honorarios' if lang == 'es_MX' else 'Fees',
                              'debit':0.0,
                              'credit' : line.fees,
                              'final' : final
                              })
                folio += 1
            opt_lines = self.request_open_balance_ids.filtered(lambda x:x.state=='confirmed' and x.type_of_operation == 'retirement' and  x.request_date == req)
            for line in opt_lines:
                final -= line.opening_balance
                lines.append({'folio':folio,
                              'date':line.request_date,
                              'opt': 'Retiro' if lang == 'es_MX' else 'Retirement',
                              'debit':0.0,
                              'credit' : line.opening_balance,
                              'final' : final
                              })
                folio += 1
    
            opt_lines = self.request_open_balance_ids.filtered(lambda x:x.state=='confirmed' and x.type_of_operation == 'withdrawal_cancellation' and  x.request_date == req)
            for line in opt_lines:
                final -= line.opening_balance
                lines.append({'folio':folio,
                              'date':line.request_date,
                              'opt': 'Retiro por cancelación' if lang == 'es_MX' else 'Withdrawal due to cancellation',
                              'debit':0.0,
                              'credit' : line.opening_balance,
                              'final' : final
                              })
                folio += 1
                
        return lines
        
class InterestRateOperation(models.Model):
    _name = 'interest.rate.operation'
    _rec_name = 'interest_date'
    
    interest_date = fields.Date('Interest Date')
    fees = fields.Float('Fees')
    yields = fields.Float('Yields')
    trust_id = fields.Many2one('agreement.trust','Trust')
    
class Beneficiary(models.Model):
    _inherit = 'collaboration.beneficiary'
    
    trust_id = fields.Many2one('agreement.trust','Trust')
    
class Providers(models.Model):
    _inherit = 'collaboration.providers'

    trust_id = fields.Many2one('agreement.trust','Trust')

class Committe(models.Model):

    _inherit = 'committee'
    
    trust_id = fields.Many2one('agreement.trust','Trust')
    trust_modi_id = fields.Many2one('agreement.trust.modification', "Trust Modification")
    new_trust_modi_id = fields.Many2one('agreement.trust.modification', "Trust Modification")

class AgreementTrustModification(models.Model):

    _name = 'agreement.trust.modification'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Agreement Trust Modification"
    _rec_name = 'folio'

    folio = fields.Char("Amendment folio")
    trust_id = fields.Many2one('agreement.trust', 'Trust')
    date = fields.Date("Modification Date")
    state = fields.Selection([('draft', 'Draft'),
                              ('confirmed', 'Confirmed')], string="State", default="draft")
    change_of = fields.Selection([('committee', 'Technical Committee'),
                                  ('goals', 'Goals'),
                                  ], string="Change Of")
    dependency_id = fields.Many2one('dependency', string="Dependence")
    new_dependency_id = fields.Many2one('dependency', string="New Dependence")
    current_target = fields.Text('Current Target')
    new_objective = fields.Text("New Objective")
    bc_modification_format = fields.Binary("BC Modification Format")
    committe_ids = fields.One2many('committee', 'trust_modi_id', string="Committees")
    new_committe_ids = fields.One2many('committee', 'new_trust_modi_id', string="Committees")

    @api.model
    def create(self, vals):
        res = super(AgreementTrustModification, self).create(vals)
        if res.trust_id and res.trust_id.state in ('cancelled','to_be_cancelled'):
            raise ValidationError(_("Can't create Modifications for Cancelled Trust!"))
        
        name = self.env['ir.sequence'].next_by_code('trust.modification')
        res.folio = name
        return res

    @api.model
    def default_get(self, fields):
        res = super(AgreementTrustModification, self).default_get(fields)
        if 'trust_id' in res.keys():
            trust_ids = self.env['agreement.trust'].browse(res.get('trust_id'))
            committee_vals = []
            for committee in trust_ids.committe_ids:
                committee_vals.append({
                    'column_id': committee.column_id and committee.column_id.id or False,
                    'column_position_id': committee.column_position_id and committee.column_position_id.id or False,
                })
            res.update({
                'committe_ids': [(0, 0, val) for val in committee_vals]
            })
        return res

    def confirm(self):
        if self.change_of == 'goals' and self.current_target and self.new_objective and self.trust_id:
            self.trust_id.goals = self.new_objective
        if self.change_of == 'committee' and self.trust_id:
            self.trust_id.committe_ids = [(5, 0)]
            vals = []
            for committee in self.new_committe_ids:
                vals.append({
                    'column_id': committee.column_id and committee.column_id.id or False,
                    'column_position_id': committee.column_position_id and committee.column_position_id.id or False,
                })
            self.trust_id.committe_ids = [(0, 0, val) for val in vals]
        self.state = 'confirmed'

    def unlink(self):
        for rec in self:
            if rec.state not in ['draft']:
                raise UserError(_('You cannot delete an entry which has been confirmed.'))
        return super(AgreementTrustModification, self).unlink()
    