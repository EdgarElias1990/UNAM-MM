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
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta


class PatrimonialResources(models.Model):

    _name = 'patrimonial.resources'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Patrimonial Resources"

    name = fields.Char("Fund Name")
    key = fields.Char("Key")
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.user.company_id.currency_id)

    state = fields.Selection([('draft', 'Draft'),
                              ('valid', 'Valid'),
                              ('in_force', 'In Force'),
                              ('to_be_cancelled', 'To Be Cancelled'),
                              ('cancelled', 'Cancelled')], "Status", default='draft')

    opening_balance = fields.Float("Opening balance")
    available_bal = fields.Monetary("Available Balance")
    dependency_id = fields.Many2one('dependency', "Unit No.")
    desc_dependency = fields.Text("Description Dependency")
    subdependency_id = fields.Many2one('sub.dependency', "Sub Dependency")
    desc_subdependency = fields.Text("Sub-unit Name")

    origin_resource_id = fields.Many2one(
        'sub.origin.resource', "Origin of the resource")
    goals = fields.Char("Goals")
    registration_date = fields.Date("Date of registration in the system")

    background_project_id = fields.Many2one(
        'background.project', 'Background Project', related="specifics_project_id.backgound_project_id")
    specifics_project_id = fields.Many2one(
        'specific.project', 'Specific project')

    patrimonial_equity_account_id = fields.Many2one(
        'account.account', "Equity accounting account")
    patrimonial_liability_account_id = fields.Many2one(
        'account.account', "Liability Accounting Account")
    patrimonial_yield_account_id = fields.Many2one(
        'account.account', "Yield account of the productive investment account")

    employee_id = fields.Many2one('hr.employee', 'Holder of the unit')
    job_id = fields.Many2one(
        related="employee_id.job_id", string='Market Stall')
    work_phone = fields.Char(
        related="employee_id.work_phone", string="Work Phone")

    administrative_employee_id = fields.Many2one(
        'hr.employee', 'Administrative secretary')
    administrative_work_phone = fields.Char(
        related="administrative_employee_id.work_phone", string="Work Phone")

    direct_responsable_employee_id = fields.Many2one(
        'hr.employee', 'Direct responsable')
    direct_responsable_work_phone = fields.Char(
        related="direct_responsable_employee_id.work_phone", string="Work Phone")
    direct_responsable_email = fields.Char(
        related='direct_responsable_employee_id.work_email', string="Email")

    unit_address = fields.Text("Unit address")
    observations = fields.Text("Additional observations of the agency")

    no_beneficiary_allowed = fields.Integer("Number of allowed beneficiaries")
    beneficiary_ids = fields.One2many(
        'collaboration.beneficiary', 'patrimonial_id')

    provider_ids = fields.One2many('collaboration.providers', 'patrimonial_id')
    
    fund_registration_file = fields.Binary("Fund registration format")
    fund_registration_file_name = fields.Char(
        "Fund registration format File Name")
    fund_office_file = fields.Binary("Fund office")
    fund_office_file_name = fields.Char("Fund office File Name")

    cancel_date = fields.Date("Cancellation date")
    supporing_doc = fields.Binary("Supporting Documentation")
    reason_cancel = fields.Text("Reason for Cancellations")

    request_open_balance_ids = fields.One2many(
        'request.open.balance', 'patrimonial_resources_id')
    total_operations = fields.Integer(
        "Operations", compute="compute_operations")

    next_no = fields.Integer(string="Next Number")

    journal_id = fields.Many2one('account.journal')
    move_line_ids = fields.One2many(
        'account.move.line', 'patrimonial_id', string="Journal Items")

#     @api.model
#     def default_get(self, fields):
#         res = super(PatrimonialResources, self).default_get(fields)
#         collaboration_jou = self.env.ref('jt_agreement.collaboration_jou_id')
#         if collaboration_jou:
#             res.update({'journal_id': collaboration_jou.id})
#         return res

    def compute_operations(self):
        for rec in self:
            operations = len(rec.request_open_balance_ids)
            rec.total_operations = operations

    @api.model
    def create(self, vals):
        res = super(PatrimonialResources, self).create(vals)
        if res and res.beneficiary_ids:
            if not res.no_beneficiary_allowed or (res.no_beneficiary_allowed and
                                                  res.no_beneficiary_allowed < len(res.beneficiary_ids)):
                raise ValidationError(_("You can add only %s Beneficiaries which is mentined in "
                                        "'Number of allowed beneficiaries'" % res.no_beneficiary_allowed))

        no = 0
        for ben in res.beneficiary_ids:
            no = no + 1
            ben.sequence = no

        return res

    def write(self, vals):
        res = super(PatrimonialResources, self).write(vals)
        for rec in self:
            if rec and rec.beneficiary_ids:
                if not rec.no_beneficiary_allowed or (rec.no_beneficiary_allowed and
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

    @api.constrains('key')
    def _check_key_no(self):
        if self.key and not self.key.isnumeric():
            raise ValidationError(_('Convention No must be Numeric.'))
        if self.key and len(self.key) != 8:
            raise ValidationError(_('Convention No must be 8 characters.'))
        if self.dependency_id and self.subdependency_id:
            name = self.dependency_id.dependency + self.subdependency_id.sub_dependency
            if not self.key.startswith(name):
                raise ValidationError(
                    _('First 5 character of Convention must be Dependency and Sub Dependency.'))

    @api.onchange('dependency_id', 'subdependency_id')
    def onchange_dep_subdep(self):
        if self.dependency_id or self.subdependency_id:
            self.key = ''
            number = ''
            if self.dependency_id:
                number += self.dependency_id.dependency
                self.desc_dependency = self.dependency_id.description
            if self.subdependency_id:
                number += self.subdependency_id.sub_dependency
                self.desc_subdependency = self.subdependency_id.description
            self.key = number

    def confirm(self):
        self.state = 'valid'

        if self.opening_balance == 0:
            raise ValidationError(_("Please add the opening balance amount"))

#         if self.journal_id:
#             journal = self.journal_id
#             if not journal.default_debit_account_id or not journal.default_credit_account_id \
#                     or not journal.conac_debit_account_id or not journal.conac_credit_account_id:
#                 if self.env.user.lang == 'es_MX':
#                     raise ValidationError(_("Por favor configure la cuenta UNAM y CONAC en diario!"))
#                 else:
#                     raise ValidationError(_("Please configure UNAM and CONAC account in journal!"))
#
#             today = datetime.today().date()
#             user = self.env.user
#             partner_id = user.partner_id.id
#             amount = self.opening_balance
#
#             unam_move_val = {'ref': self.name,  'conac_move': True,
#                              'date': today, 'journal_id': journal.id, 'company_id': self.env.user.company_id.id,
#                              'line_ids': [(0, 0, {
#                                  'account_id': journal.default_credit_account_id.id,
#                                  'coa_conac_id': journal.conac_credit_account_id.id,
#                                  'credit': amount,
#                                  'partner_id': partner_id,
#                                  'patrimonial_id': self.id,
#                                  }),
#                                  (0, 0, {
#                                  'account_id': journal.default_debit_account_id.id,
#                                  'coa_conac_id': journal.conac_debit_account_id.id,
#                                  'debit': amount,
#                                  'partner_id': partner_id,
#                                  'patrimonial_id': self.id,
#                                  }),
#                              ]}
#             move_obj = self.env['account.move']
#             unam_move = move_obj.create(unam_move_val)
#             unam_move.action_post()

    def in_force(self):
        self.state = 'in_force'

    def action_to_be_cancelled(self):
        self.state = 'to_be_cancelled'

    def action_set_cancel(self):
        self.state = 'cancelled'

    def cancel(self):
        return {
            'name': 'Cancel Patrimonial',
            'view_mode': 'form',
            'view_id': self.env.ref('jt_agreement.cancel_patrimonial_form_view').id,
            'res_model': 'cancel.patrimonial',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

    def action_operations(self):
        journal_id = False

        collaboration_jou = self.env.ref('jt_agreement.collaboration_jou_id')
        if collaboration_jou:
            journal_id = collaboration_jou.id

        if self.request_open_balance_ids:
            return {
                'name': 'Operations',
                'view_type': 'form',
                # 'view_id': self.env.ref('jt_agreement.view_req_open_balance_tree').id,
                'view_mode': 'tree,form',
                'views': [(self.env.ref("jt_agreement.view_req_open_balance_patrimonial_tree").id, 'tree'), (self.env.ref("jt_agreement.view_req_open_balance_patrimonial_form").id, 'form')],
                'res_model': 'request.open.balance',
                'domain': [('patrimonial_resources_id', '=', self.id)],
                'type': 'ir.actions.act_window',
                'context': {'default_patrimonial_resources_id': self.id,
                            'default_apply_to_basis_collaboration': True,
                            'default_origin_resource_id': self.origin_resource_id and self.origin_resource_id.id or False,
                            'default_opening_balance': self.opening_balance,
                            #'default_trust_agreement_file': self.fund_registration_file,
                            #'default_trust_agreement_file_name': self.fund_registration_file_name,
                            #'default_trust_office_file': self.fund_office_file,
                            #'default_trust_office_file_name': self.fund_office_file_name,
                            #'default_supporting_documentation': self.fund_registration_file,
                            'default_name': self.name,
                            'default_patrimonial_equity_account_id': self.patrimonial_equity_account_id and self.patrimonial_equity_account_id.id or False,
                            'default_liability_account_id': self.patrimonial_liability_account_id and self.patrimonial_liability_account_id.id or False,
                            'default_patrimonial_yield_account_id': self.patrimonial_yield_account_id.id and self.patrimonial_yield_account_id.id or False,
                            'default_journal_id': journal_id,
                            'default_specifics_project_id': self.specifics_project_id and self.specifics_project_id.id or False,
                            }
            }
        else:
            return {
                'name': 'Operations',
                # 'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('jt_agreement.view_req_open_balance_patrimonial_form').id,
                'view_ids': [self.env.ref("jt_agreement.view_req_open_balance_patrimonial_form").id],
                'res_model': 'request.open.balance',
                'domain': [('patrimonial_resources_id', '=', self.id)],
                'type': 'ir.actions.act_window',
                'context': {'default_patrimonial_resources_id': self.id,
                            'default_apply_to_basis_collaboration': True,
                            'default_origin_resource_id': self.origin_resource_id and self.origin_resource_id.id or False,
                            'default_opening_balance': self.opening_balance,
                            #'default_trust_agreement_file': self.fund_registration_file,
                            #'default_trust_agreement_file_name': self.fund_registration_file_name,
                            #'default_trust_office_file': self.fund_office_file,
                            #'default_trust_office_file_name': self.fund_office_file_name,
                            #'default_supporting_documentation': self.fund_registration_file,
                            'default_name': self.name,
                            'default_patrimonial_equity_account_id': self.patrimonial_equity_account_id and self.patrimonial_equity_account_id.id or False,
                            'default_liability_account_id': self.patrimonial_liability_account_id and self.patrimonial_liability_account_id.id or False,
                            'default_patrimonial_yield_account_id': self.patrimonial_yield_account_id.id and self.patrimonial_yield_account_id.id or False,
                            'default_journal_id': journal_id,
                            'default_specifics_project_id': self.specifics_project_id and self.specifics_project_id.id or False,
                            }
            }

    def action_schedule_withdrawal(self):
        req_obj = self.env['request.open.balance']
        for patimonial in self:
            for beneficiary in patimonial.beneficiary_ids:
                if beneficiary.validity_start and beneficiary.validity_final_beneficiary and beneficiary.withdrawal_sch_date and beneficiary.payment_rule_id:

                    total_month = (beneficiary.validity_final_beneficiary.year - beneficiary.validity_start.year) * 12 + (
                        beneficiary.validity_final_beneficiary.month - beneficiary.validity_start.month)
                    start_date = beneficiary.validity_start
                    req_date = start_date.replace(
                        day=beneficiary.withdrawal_sch_date.day)
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
                    for month in range(total_month + 1):
                        if month != 0:
                            req_date = req_date + relativedelta(months=1)
                        if count != 0:
                            count += 1
                            if count == need_skip:
                                count = 0
                            continue

                        count += 1
                        if count == need_skip:
                            count = 0

                        if beneficiary.partner_id:
                            partner_id = beneficiary.partner_id.id
                        else: 
                            partner_id = beneficiary.employee_id and beneficiary.employee_id.user_id and beneficiary.employee_id.user_id.partner_id and beneficiary.employee_id.user_id.partner_id.id or False
                            
                        req_obj.create({
                            'patrimonial_resources_id': patimonial.id,
                            'apply_to_basis_collaboration': True,
                            #'agreement_number': collaboration.convention_no,
                            'opening_balance': beneficiary.amount,
                            'supporting_documentation': patimonial.fund_registration_file,
                            'type_of_operation': 'retirement',
                            'beneficiary_id': partner_id,
                            'name': self.name,
                            'request_date': req_date,
                            'patrimonial_equity_account_id': patimonial.patrimonial_equity_account_id and patimonial.patrimonial_equity_account_id.id or False,
                            'liability_account_id': patimonial.patrimonial_liability_account_id and patimonial.patrimonial_liability_account_id.id or False,
                            'patrimonial_yield_account_id': patimonial.patrimonial_yield_account_id.id and patimonial.patrimonial_yield_account_id.id or False,
                            'specifics_project_id': patimonial.specifics_project_id and patimonial.specifics_project_id.id or False,

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


class Beneficiary(models.Model):
    _inherit = 'collaboration.beneficiary'

    patrimonial_id = fields.Many2one(
        'patrimonial.resources', 'Patrimonial Resources')

class Providers(models.Model):
    _inherit = 'collaboration.providers'

    patrimonial_id = fields.Many2one('patrimonial.resources','Patrimonial Resources')


class OpenBalance(models.Model):
    _inherit = 'request.open.balance'

    patrimonial_beneficiary_ids = fields.Many2many(
        'res.partner', 'rel_req_bal_patrimonial_beneficiary', 'partner_id', 'req_id', compute="get_patrimonial_beneficiary_ids")
    # patrimonial_resources_id = fields.Many2one(
    #     'patrimonial.resources', 'Patrimonial Resources')

    patrimonial_provider_ids = fields.Many2many(
        'res.partner', 'rel_req_bal_patrimonial_partner', 'partner_id', 'req_id', compute="get_patrimonial_provider_ids")

    @api.depends('patrimonial_resources_id', 'patrimonial_resources_id.beneficiary_ids', 'patrimonial_resources_id.beneficiary_ids.employee_id')
    def get_patrimonial_beneficiary_ids(self):
        for rec in self:
            partner_ids = []
            if rec.patrimonial_resources_id and rec.patrimonial_resources_id.beneficiary_ids:

                for emp in rec.patrimonial_resources_id.beneficiary_ids.mapped('employee_id'):
                    if emp.user_id and emp.user_id.partner_id:
                        partner_ids.append(emp.user_id.partner_id.id)
            rec.patrimonial_beneficiary_ids = [(6, 0, partner_ids)]

    @api.depends('patrimonial_resources_id', 'patrimonial_resources_id.provider_ids', 'patrimonial_resources_id.provider_ids.partner_id')
    def get_patrimonial_provider_ids(self):
        for rec in self:
            if rec.patrimonial_resources_id and rec.patrimonial_resources_id.provider_ids:
                rec.patrimonial_provider_ids = [
                    (6, 0, rec.patrimonial_resources_id.provider_ids.mapped('partner_id').ids)]
            else:
                rec.patrimonial_provider_ids = [(6, 0, [])]
