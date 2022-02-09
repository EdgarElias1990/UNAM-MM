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
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.osv import expression

class BasesCollabration(models.Model):

    _name = 'bases.collaboration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Bases of collaboration"
    #_rec_name = 'convention_no'

    name = fields.Char("Agreement Name")
    convention_no = fields.Char("Convention No.")
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.user.company_id.currency_id)
    opening_bal = fields.Monetary("Opening Balance")
    available_bal = fields.Monetary("Available Balance")
    agreement_type_id = fields.Many2one(
        'agreement.agreement.type', 'Agreement Type')
    agreement_type_group = fields.Char("Agreement Type Group",size=1)
    
    fund_type_id = fields.Many2one('fund.type', "Fund Type")
    fund_id = fields.Many2one('agreement.fund', 'Fund')
    dependency_obs = fields.Text("Dependency Observations")
    dependency_id = fields.Many2one('dependency', "Unit No.")
    desc_dependency = fields.Text("Description Dependency")
    subdependency_id = fields.Many2one('sub.dependency', "Sub Dependency")
    desc_subdependency = fields.Text("Sub-unit Name")
    origin_resource_id = fields.Many2one(
        'sub.origin.resource', "Origin of the resource")
    goals = fields.Char("Goals")
    registration_date = fields.Date("Date of registration in the system")
    is_specific = fields.Boolean(string='Specific', default=False)
    liability_account_id = fields.Many2one(
        'account.account', "Liability Accounting Account")
    investment_account_id = fields.Many2one(
        'account.account', "Investment Accounting Account")
    interest_account_id = fields.Many2one(
        'account.account', "Interest Accounting Account")
    availability_account_id = fields.Many2one(
        'account.account', "Availability Accounting Account")
    state = fields.Selection([('draft', 'Draft'),
                              ('valid', 'Valid'),
                              ('in_force', 'In Force'),
                              ('to_be_cancelled', 'To Be Cancelled'),
                              ('cancelled', 'Cancelled')], "Status", default='draft')
    total_operations = fields.Integer(
        "Operations", compute="compute_operations")
    total_modifications = fields.Integer(
        "Modifications", compute="compute_modifications")
    request_open_balance_ids = fields.One2many(
        'request.open.balance', 'bases_collaboration_id')

    employee_id = fields.Many2one('hr.employee', 'Holder of the unit')
    job_id = fields.Many2one('hr.job', string="Market Stall")
    phone = fields.Char(related="employee_id.work_phone",
                        string="Telephone of the unit holder")
    holder_email = fields.Char(
        related="employee_id.work_email", string="Email")

    administrative_secretary_id = fields.Many2one(
        'hr.employee', "Administrative Secretary")
    administrative_secretary_phone = fields.Char(
        related="administrative_secretary_id.work_phone", string="Administrative Secretary Telephone")
    administrative_secretary_email = fields.Char(
        related="administrative_secretary_id.work_email", string="Administrative Secretary Email")

    direct_manager_cbc_id = fields.Many2one(
        "hr.employee", "Direct manager of CBC")
    cbc_responsible_phone = fields.Char(
        related="direct_manager_cbc_id.work_phone", string="CBC responsible phone number")
    email = fields.Char(
        related="direct_manager_cbc_id.work_email", string="Email")
    unit_address = fields.Text("Unit Address")
    additional_observation = fields.Text(
        "Additional observations of the agency")
    cbc_format = fields.Binary("CBC Format")
    cbc_shipping_office = fields.Binary("CBC Shipping Office")
    committe_ids = fields.One2many(
        'committee', 'collaboration_id', string="Committees")

    no_beneficiary_allowed = fields.Integer("Number of allowed beneficiaries")
    beneficiary_ids = fields.One2many(
        'collaboration.beneficiary', 'collaboration_id')
    provider_ids = fields.One2many(
        'collaboration.providers', 'collaboration_id')

    cancel_date = fields.Date("Cancellation date")
    supporing_doc = fields.Binary("Supporting Documentation")
    reason_cancel = fields.Text("Reason for Cancellations")

    fund_name_transfer_id = fields.Many2one(
        'bases.collaboration', 'Fund name for transfers')
    closing_amt = fields.Monetary("Amount")

    interest_date = fields.Date(string="Interest Date")
    interest_rate = fields.Monetary(string="Interest Rate")
    yields = fields.Monetary(string="Yields")

    report_start_date = fields.Date("Report Start Date")
    report_end_date = fields.Date("Report End Date")
    n_report = fields.Char(string="N° para reporte")
    next_no = fields.Integer(string="Next Number")
    journal_id = fields.Many2one('account.journal')
    move_line_ids = fields.One2many(
        'account.move.line', 'collaboration_id', string="Journal Items")
    rate_base_ids = fields.One2many('interest.rate.base','base_id')

    periods_closing_ids = fields.One2many('periods.closing', 'collaboration_id', "Closing Periods")
    
    _sql_constraints = [
        ('folio_convention_no', 'unique(convention_no)', 'The Convention No. must be unique.')]

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('convention_no', '=ilike', name), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        base_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return models.lazy_name_get(self.browse(base_ids).with_user(name_get_uid))
        
    def name_get(self):
        if not 'show_agreement_name' in self._context:
            res = []
            for base in self:
                base_name = ''
                if base.convention_no:
                    base_name = base.convention_no
                res.append((base.id, base_name))
        else:
            res = super(BasesCollabration, self).name_get()
        return res

#     @api.model
#     def default_get(self, fields):
#         res = super(BasesCollabration, self).default_get(fields)
#         collaboration_jou = self.env.ref('jt_agreement.collaboration_jou_id')
#         if collaboration_jou:
#             res.update({'journal_id': collaboration_jou.id})
#         return res

    def unlink(self):
        for rec in self:
            if rec.state not in ['draft']:
                raise UserError(_('You can erase only draft status data.'))
        return super(BasesCollabration, self).unlink()

    @api.constrains('n_report')
    def _check_n_report(self):
        if self.n_report and not self.n_report.isnumeric():
            raise ValidationError(_('N° para reporte must be Numeric.'))
        if self.n_report and len(self.n_report) != 8:
            raise ValidationError(_('N° para reporte must be 8 Digits.'))

    @api.onchange('dependency_id', 'agreement_type_id')
    def onchange_dependency_agrtype(self):
        for rec in self:
            if rec.dependency_id and self.agreement_type_id and self.agreement_type_id.group:
                rec.convention_no = '%s' % (
                    rec.dependency_id.dependency) + '%s' % (rec.agreement_type_id.group)

    @api.onchange('dependency_id', 'agreement_type_id', 'subdependency_id','convention_no')
    def onchange_deb_sub_agr(self):
        for rec in self:
            if rec.dependency_id and rec.agreement_type_id and rec.subdependency_id:
                group = rec.agreement_type_id.group and rec.agreement_type_id.group or ''
                con = ''
                if rec.convention_no and len(rec.convention_no)==6:
                   con =  rec.convention_no[-2:]
                rec.n_report = '%s' % (rec.dependency_id.dependency) + '%s' % (
                    rec.subdependency_id.sub_dependency) + '%s' % (group) + '%s' % (con)

    def get_month_name(self, month):
        month_name = ''
        if month == 1:
            month_name = 'Enero'
        elif month == 2:
            month_name = 'Febrero'
        elif month == 3:
            month_name = 'Marzo'
        elif month == 4:
            month_name = 'Abril'
        elif month == 5:
            month_name = 'Mayo'
        elif month == 6:
            month_name = 'Junio'
        elif month == 7:
            month_name = 'Julio'
        elif month == 8:
            month_name = 'Agosto'
        elif month == 9:
            month_name = 'Septiembre'
        elif month == 10:
            month_name = 'Octubre'
        elif month == 11:
            month_name = 'Noviembre'
        elif month == 12:
            month_name = 'Diciembre'

        return month_name.upper()

    def get_amount_invest_dict(self, collaborations, start_date, end_date):
        balance_dict = {}
        increments = intial_bal = withdrawals = interest = 0
        for collab in collaborations:
            collaboration = self.browse(collab)
            deposite = sum(
              x.opening_balance for x in collaboration.request_open_balance_ids.filtered(lambda x: x.state == 'confirmed'
                                             and x.request_date and x.request_date < start_date and \
                                                x.type_of_operation in ('open_bal', 'increase', 'increase_by_closing')))
            retiros = sum(x.opening_balance for x in collaboration.request_open_balance_ids.filtered(lambda x:
                                            x.state == 'confirmed'
                                             and x.request_date and x.request_date < start_date and \
                    x.type_of_operation in ('retirement', 'withdrawal', 'withdrawal_cancellation', 'withdrawal_closure')))
            intial_bal = deposite - retiros
            operations = collaboration.request_open_balance_ids.filtered(lambda x:x.state=='confirmed'
                    and x.request_date and x.request_date >= start_date and x.request_date <= end_date)
            for operation in operations:
                if operation.type_of_operation in ('open_bal', 'increase','increase_by_closing'):
                    increments += operation.opening_balance
                elif operation.type_of_operation in ('retirement', 'withdrawal_cancellation', 'withdrawal',
                                                     'withdrawal_closure'):
                    withdrawals += operation.opening_balance
            interest = sum(x.interest_rate for x in collaboration.rate_base_ids.filtered(lambda x:x.interest_date and x.interest_date >= start_date and x.interest_date <= end_date))
            interest = round(interest,2)
        balance_dict.update({
            'intial_bal': intial_bal,
            'increments': increments,
            'sub_total': intial_bal + increments,
            'withdrawals': withdrawals,
            'balance_at_the_end': (intial_bal + increments) - withdrawals,
            'interest': interest,
            'to_be_invested': ((intial_bal + increments) - withdrawals) + interest

        })
        return balance_dict

    def get_interes(self):
        interest = sum(x.interest_rate for x in self.rate_base_ids.filtered(lambda x:x.interest_date and x.interest_date >= self.report_start_date and x.interest_date <= self.report_end_date))
        interest = round(interest,2)
        print('interest',interest)
        return interest

    def get_next_year_name(self, date):
        year_name = ''
        if date:
            year = date.year + 1
            year_name = str(year)
        return year_name

    def get_date_name(self, date):
        period_name = ''
        if date:
            period_name += str(date.day) + ' ' + self.get_month_name(date.month) + ' ' + str(date.year)
        return period_name

    def get_period_name_amount_invest(self, start_date, end_date):
        period_name = ''
        if start_date and end_date:
            period_name += "Del " + str(start_date.day)

            if start_date.month != end_date.month:
                if start_date.year == end_date.year:
                    period_name += " de " + \
                                   self.get_month_name(start_date.month)

            if start_date.year != end_date.year:
                period_name += " de " + \
                               self.get_month_name(
                                   start_date.month) + " de" + str(start_date.year)

            period_name += " al " + str(end_date.day) + " de " + self.get_month_name(end_date.month) + " " + \
                           str(end_date.year)

        return period_name

    def get_period_name(self):
        period_name = ''
        if self.report_start_date and self.report_end_date:
            period_name += "Del " + str(self.report_start_date.day)

            if self.report_start_date.month != self.report_end_date.month:
                if self.report_start_date.year == self.report_end_date.year:
                    period_name += " de " + \
                        self.get_month_name(self.report_start_date.month)

            if self.report_start_date.year != self.report_end_date.year:
                period_name += " de " + \
                    self.get_month_name(
                        self.report_start_date.month) + " de" + str(self.report_start_date.year)

            period_name += " al " + str(self.report_end_date.day) + " de " + self.get_month_name(
                self.report_end_date.month) + " " + str(self.report_end_date.year)

        return period_name

    def get_opening_balance(self):
        deposite = sum(x.opening_balance for x in self.request_open_balance_ids.filtered(lambda x: x.state == 'confirmed'
              and x.request_date and x.request_date < self.report_start_date and \
              x.type_of_operation in ('open_bal', 'increase', 'increase_by_closing')))
        retiros = sum(x.opening_balance for x in self.request_open_balance_ids.filtered(lambda x: x.state == 'confirmed'
              and x.request_date and x.request_date < self.report_start_date and \
              x.type_of_operation in ('retirement', 'withdrawal', 'withdrawal_cancellation', 'withdrawal_closure')))
        bal = deposite - retiros
        return bal

    def get_deposite(self):
        deposite = sum(x.opening_balance for x in self.request_open_balance_ids.filtered(lambda x: x.state == 'confirmed' and x.request_date and x.request_date >=
                                                                                         self.report_start_date and x.request_date <= self.report_end_date and x.type_of_operation in ('open_bal', 'increase', 'increase_by_closing')))
        return deposite

    def get_retiros(self):
        retiros = sum(x.opening_balance for x in self.request_open_balance_ids.filtered(lambda x: x.state == 'confirmed' and x.request_date and x.request_date >=
                                                                                        self.report_start_date and x.request_date <= self.report_end_date and x.type_of_operation in ('retirement', 'withdrawal', 'withdrawal_cancellation', 'withdrawal_closure')))
        return retiros
    
    def opening_opt_number(self):
        opt_ids = self.request_open_balance_ids.filtered(lambda x:x.type_of_operation=='open_bal')
        opt_number = ''
        if opt_ids:
            opt_number = opt_ids[0].operation_number
        return opt_number

    def opening_opt_date(self):
        opt_ids = self.request_open_balance_ids.filtered(lambda x:x.type_of_operation=='open_bal')
        opt_date = ''
        if opt_ids:
            opt_date = opt_ids[0].request_date
        return opt_date
    
    def get_contract_assistant_report_lines(self):

        req_date = self.request_open_balance_ids.filtered(lambda x: self.report_start_date and self.report_end_date \
            and x.state=='confirmed' and x.type_of_operation in ('increase','retirement') and \
            x.request_date and x.request_date >= self.report_start_date and x.request_date <= self.report_end_date).mapped('request_date')

        req_date += self.rate_base_ids.filtered(lambda x: self.report_start_date and self.report_end_date and \
            x.interest_date >= self.report_start_date and \
           x.interest_date <= self.report_end_date).mapped('interest_date')

        lang = self.env.user.lang

        if req_date:
            req_date = list(set(req_date))
            req_date =  sorted(req_date)
        
        final = 0
        lines = []
        for req in req_date:
            opt_lines = self.request_open_balance_ids.filtered(lambda x:x.state=='confirmed' and x.request_date == req)
            for line in opt_lines:
                opt = dict(line._fields['type_of_operation'].selection).get(line.type_of_operation)
                #opt = line.type_of_operation
                if lang == 'es_MX':
                    if line.type_of_operation=='increase':
                        opt = 'Incremento'
                    elif line.type_of_operation=='open_bal':
                        opt = 'Importe de apertura'
                    elif line.type_of_operation=='retirement':
                        opt = 'Retiro'
                debit = 0
                credit = 0  
                retiros = 0
                increments = 0
                bal_final = 0
#                 if line.type_of_operation in ('open_bal'):         
#                     final += line.opening_balance
#                     debit = line.opening_balance
                if line.type_of_operation in ('increase'):         
                    final += line.opening_balance
                    debit = line.opening_balance
                elif line.type_of_operation in ('retirement'):
                    final -= line.opening_balance
                    credit = line.opening_balance
                intial_bal = 0
                intial_bal = debit - credit
                bal_final = intial_bal + debit - credit 
                lines.append({
                              'date':line.request_date,
                              'operation_number':line.operation_number,
                              'inital_bal':intial_bal,
                              'opt': opt,
                              'debit':debit,
                              'credit' : credit,
                              'final' : final,
                              'bal_final':bal_final
                              })

            for line in self.rate_base_ids.filtered(lambda x:x.interest_date == req):
                final += line.interest_rate
                lines.append({
                              'date':line.interest_date,
                              'operation_number':'',
                              'opt': 'Intereses' if lang == 'es_MX' else 'Interest',
                              'debit':line.interest_rate,
                              'credit' : 0.0,
                              'final' : final,

                              })
        
        return lines

    def get_report_lines(self):

        req_date = self.request_open_balance_ids.filtered(lambda x: self.report_start_date and self.report_end_date \
            and x.state=='confirmed' and \
            x.request_date and x.request_date >= self.report_start_date and x.request_date <= self.report_end_date).mapped('request_date')

        lang = self.env.user.lang
        req_date += self.rate_base_ids.filtered(lambda x: self.report_start_date and self.report_end_date and \
            x.interest_date >= self.report_start_date and \
           x.interest_date <= self.report_end_date).mapped('interest_date')

        if req_date:
            req_date = list(set(req_date))
            req_date =  sorted(req_date)
        
        final = 0
        lines = []
        for req in req_date:
            opt_lines = self.request_open_balance_ids.filtered(lambda x:x.state=='confirmed' and x.request_date == req)
            for line in opt_lines:
                opt = dict(line._fields['type_of_operation'].selection).get(line.type_of_operation)
                #opt = line.type_of_operation
                if lang == 'es_MX':
                    if line.type_of_operation=='open_bal':
                        opt = 'Importe de apertura'
                    elif line.type_of_operation=='increase':
                        opt = 'Incremento'
                    elif line.type_of_operation=='retirement':
                        opt = 'Retiro'
                    elif line.type_of_operation=='withdrawal':
                        opt = 'Retiro por liquidación'
                    elif line.type_of_operation=='withdrawal_cancellation':
                        opt = 'Retiro por cancelación'
                    elif line.type_of_operation=='withdrawal_closure':
                        opt = 'Retiro por cierre'
                    elif line.type_of_operation=='increase_by_closing':
                        opt = 'Incremento por cierre'
                debit = 0
                credit = 0  
                retiros = 0
                increments = 0
                bal_final = 0
                if line.type_of_operation in ('open_bal','increase','increase_by_closing'):         
                    final += line.opening_balance
                    debit = line.opening_balance
                elif line.type_of_operation in ('withdrawal','retirement','withdrawal_cancellation','withdrawal_closure'):
                    final -= line.opening_balance
                    credit = line.opening_balance
                intial_bal = 0
                intial_bal = debit - credit
                bal_final = intial_bal + debit - credit 
                lines.append({
                              'date':line.request_date,
                              'operation_number':line.operation_number,
                              'inital_bal':intial_bal,
                              'opt': opt,
                              'debit':debit,
                              'credit' : credit,
                              'final' : final,
                              'bal_final':bal_final
                              })

            for line in self.rate_base_ids.filtered(lambda x:x.interest_date == req):
                final += line.interest_rate
                lines.append({
                              'date':line.interest_date,
                              'opt': 'Intereses' if lang == 'es_MX' else 'Interest',
                              'debit':line.interest_rate,
                              'credit' : 0.0,
                              'final' : final,

                              })
        
        return lines

    @api.model
    def create(self, vals):
        res = super(BasesCollabration, self).create(vals)
        if res.dependency_id:
            res.desc_dependency = res.dependency_id.description
        if res.subdependency_id:
            res.desc_subdependency = res.subdependency_id.description
        if res.agreement_type_id and res.agreement_type_group:
            type_id = self.env['agreement.agreement.type'].search([('group','=',res.agreement_type_group),('name','=',res.agreement_type_id.name)],limit=1)
            if type_id:
                res.agreement_type_id = type_id.id
                
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
        res = super(BasesCollabration, self).write(vals)
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

    def compute_operations(self):
        operation_obj = self.env['request.open.balance']
        for rec in self:
            if rec.name:
                operations = operation_obj.search(
                    [('bases_collaboration_id', '=', rec.id)])
                rec.total_operations = len(operations)

    def compute_modifications(self):
        modification_obj = self.env['bases.collaboration.modification']
        for rec in self:
            if rec.name:
                modifications = modification_obj.search(
                    [('bases_collaboration_id', '=', rec.id)])
                rec.total_modifications = len(modifications)

    def action_closing_collaboration(self):
        return {
            'name': 'Closing Collaboration',
            'view_mode': 'form',
            'view_id': self.env.ref('jt_agreement.closing_collaboration_form_view').id,
            'res_model': 'closing.collaboration',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'active_ids': self.ids}
        }

    def cancel(self):
        return {
            'name': 'Cancel Collaboration',
            'view_mode': 'form',
            'view_id': self.env.ref('jt_agreement.cancel_collaboration_form_view').id,
            'res_model': 'cancel.collaboration',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

    def action_operations(self):
        journal_id = False

        collaboration_jou = self.env.ref('jt_agreement.collaboration_jou_id')
        if collaboration_jou:
            journal_id = collaboration_jou.id

        operation_obj = self.env['request.open.balance']
        operations = operation_obj.search(
            [('bases_collaboration_id', '=', self.id)])
        if operations:
            return {
                'name': 'Operations',
                'view_type': 'form',
                # 'view_id': self.env.ref('jt_agreement.view_req_open_balance_tree').id,
                'view_mode': 'tree,form',
                'views': [(self.env.ref("jt_agreement.view_req_open_balance_tree").id, 'tree'), (self.env.ref("jt_agreement.view_req_open_balance_form").id, 'form')],
                'res_model': 'request.open.balance',
                'domain': [('bases_collaboration_id', '=', self.id)],
                'type': 'ir.actions.act_window',
                'context': {'default_bases_collaboration_id': self.id,
                            'default_apply_to_basis_collaboration': True,
                            'default_agreement_number': self.convention_no,
                            'default_opening_balance': 0,
                            #'default_cbc_format': self.cbc_format,
                            #'default_supporting_documentation': self.cbc_format,
                            #'default_cbc_shipping_office': self.cbc_shipping_office,
                            'default_name': self.name,
                            'default_liability_account_id': self.liability_account_id.id if self.liability_account_id
                            else False,
                            'default_interest_account_id': self.interest_account_id.id if self.interest_account_id
                            else False,
                            'default_investment_account_id': self.investment_account_id.id if self.investment_account_id
                            else False,
                            'default_availability_account_id': self.availability_account_id.id if self.availability_account_id
                            else False,
                            'default_journal_id': journal_id,
                            }
            }
        else:
            return {
                'name': 'Operations',
                # 'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('jt_agreement.view_req_open_balance_form').id,
                'view_ids': [self.env.ref("jt_agreement.view_req_open_balance_form").id],
                'res_model': 'request.open.balance',
                'domain': [('bases_collaboration_id', '=', self.id)],
                'type': 'ir.actions.act_window',
                'context': {'default_bases_collaboration_id': self.id,
                            'default_apply_to_basis_collaboration': True,
                            'default_opening_balance': 0,
                            'default_agreement_number': self.convention_no,
                            'default_name': self.name,
                            'default_operation_number': self.next_no,
                            #'default_cbc_format': self.cbc_format,
                            #'default_supporting_documentation': self.cbc_format,
                            #'default_cbc_shipping_office': self.cbc_shipping_office,
                            'default_liability_account_id': self.liability_account_id.id if self.liability_account_id
                            else False,
                            'default_interest_account_id': self.interest_account_id.id if self.interest_account_id
                            else False,
                            'default_investment_account_id': self.investment_account_id.id if self.investment_account_id
                            else False,
                            'default_availability_account_id': self.availability_account_id.id if self.availability_account_id
                            else False,
                            'default_journal_id': journal_id,
                            }
            }

    def action_modifications(self):
        modification_obj = self.env['bases.collaboration.modification']
        modifications = modification_obj.search(
            [('bases_collaboration_id', '=', self.id)])
        if modifications:
            return {
                'name': 'Modifications',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'bases.collaboration.modification',
                'domain': [('bases_collaboration_id', '=', self.id)],
                'type': 'ir.actions.act_window',
                'context': {'default_dependency_id': self.dependency_id and self.dependency_id.id or False,
                            'default_bases_collaboration_id': self.id,
                            'default_current_target': self.goals,
                            'from_modification': True,
                            'show_agreement_name': True
                            }
            }
        else:
            return {
                'name': 'Modifications',
                'view_mode': 'form',
                'res_model': 'bases.collaboration.modification',
                'domain': [('bases_collaboration_id', '=', self.id)],
                'type': 'ir.actions.act_window',
                'context': {'default_dependency_id': self.dependency_id and self.dependency_id.id or False,
                            'default_bases_collaboration_id': self.id,
                            'default_current_target': self.goals,
                            'from_modification': True
                            }
            }

    def confirm(self):
        self.state = 'valid'

        if self.opening_bal == 0:
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
#             amount = self.opening_bal
#
#             unam_move_val = {'ref': self.name,  'conac_move': True,
#                              'date': today, 'journal_id': journal.id, 'company_id': self.env.user.company_id.id,
#                              'line_ids': [(0, 0, {
#                                  'account_id': journal.default_credit_account_id.id,
#                                  'coa_conac_id': journal.conac_credit_account_id.id,
#                                  'credit': amount,
#                                  'partner_id': partner_id,
#                                  'collaboration_id': self.id,
#                                  }),
#                                  (0, 0, {
#                                  'account_id': journal.default_debit_account_id.id,
#                                  'coa_conac_id': journal.conac_debit_account_id.id,
#                                  'debit': amount,
#                                  'partner_id': partner_id,
#                                  'collaboration_id': self.id,
#                                  }),
#                              ]}
#             move_obj = self.env['account.move']
#             unam_move = move_obj.create(unam_move_val)
#             unam_move.action_post()

    def action_schedule_withdrawal(self):
        req_obj = self.env['request.open.balance']
        for collaboration in self:
            for beneficiary in collaboration.beneficiary_ids:
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
                            'bases_collaboration_id': collaboration.id,
                            'collaboration_beneficiary_id' : beneficiary.id,
                            'apply_to_basis_collaboration': True,
                            'agreement_number': collaboration.convention_no,
                            'opening_balance': beneficiary.amount,
                            'supporting_documentation': collaboration.cbc_format,
                            'type_of_operation': 'retirement',
                            'beneficiary_id': partner_id,
                            'name': collaboration.name,
                            'request_date': req_date,
                            'liability_account_id': collaboration.liability_account_id.id if collaboration.liability_account_id
                            else False,
                            'interest_account_id': collaboration.interest_account_id.id if collaboration.interest_account_id
                            else False,
                            'investment_account_id': collaboration.investment_account_id.id if collaboration.investment_account_id
                            else False,
                            'availability_account_id': collaboration.availability_account_id.id if collaboration.availability_account_id
                            else False
                        })
        print ("Calllll===")
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
        print('Calllll===')

#             for beneficiary in collaboration.provider_ids:
#                 partner_id = beneficiary.partner_id and beneficiary.partner_id.id or False
#                 req_obj.create({
#                     'bases_collaboration_id': collaboration.id,
#                     'apply_to_basis_collaboration': True,
#                     'agreement_number': collaboration.convention_no,
#                     'opening_balance': collaboration.available_bal,
#                     'supporting_documentation': collaboration.cbc_format,
#                     'type_of_operation': 'retirement',
#                     'provider_id': partner_id,
#                     'name': self.name,
#                     'liability_account_id': collaboration.liability_account_id.id if collaboration.liability_account_id
#                     else False,
#                     'interest_account_id': collaboration.interest_account_id.id if collaboration.interest_account_id
#                     else False,
#                     'investment_account_id': collaboration.investment_account_id.id if collaboration.investment_account_id
#                     else False,
#                     'availability_account_id': collaboration.availability_account_id.id if collaboration.availability_account_id
#                     else False
#                 })

    @api.constrains('convention_no')
    def _check_convention_no(self):
        if self.convention_no and not self.convention_no.isnumeric():
            raise ValidationError(_('Convention No must be Numeric.'))
        if self.convention_no and len(self.convention_no) != 6:
            raise ValidationError(_('Convention No must be 6 characters.'))
        if self.dependency_id and self.agreement_type_id and self.agreement_type_id.group:
            name = self.dependency_id.dependency + self.agreement_type_id.group
            if not self.convention_no.startswith(name):
                raise ValidationError(
                    _('First 4 character of Convention must be Dependency and Group.'))

    @api.onchange('dependency_id', 'subdependency_id')
    def onchange_dep_subdep(self):
        if self.dependency_id or self.subdependency_id:
            number = ''
            if self.dependency_id:
                number += self.dependency_id.dependency
                self.desc_dependency = self.dependency_id.description
            if self.subdependency_id:
                number += self.subdependency_id.sub_dependency
                self.desc_subdependency = self.subdependency_id.description
            #self.convention_no = number

    @api.onchange('agreement_type_id')
    def onchange_agreement_type_id(self):
        if self.agreement_type_id and self.agreement_type_id.fund_type_id:
            self.fund_type_id = self.agreement_type_id.fund_type_id.id

class InterestRateBase(models.Model):
    _name = 'interest.rate.base'
    _rec_name = 'interest_date'
    
    interest_date = fields.Date('Interest Date')
    interest_rate = fields.Float('Interest Rate')
    cuenta = fields.Char('Cuenta')
    tipo = fields.Char('Tipo')
    base_id = fields.Many2one('bases.collaboration','Base')

class Committe(models.Model):

    _name = 'committee'
    _description = "Committee"

    column_id = fields.Many2one('hr.employee', "Column Name")
    column_position_id = fields.Many2one(
        'hr.job', "Job")
    collaboration_id = fields.Many2one('bases.collaboration')
    position_column = fields.Char("Position / Appointment column")
    
    @api.onchange('column_id')
    def onchange_column_id(self):
        if self.column_id and self.column_id.job_id:
            self.column_position_id = self.column_id.job_id.id


class Providers(models.Model):
    _name = 'collaboration.providers'
    _description = "Collaboration Providers"

    collaboration_id = fields.Many2one('bases.collaboration')
    partner_id = fields.Many2one('res.partner', "Name")
    bank_id = fields.Many2one('res.partner.bank', "Bank")
    account_number = fields.Char("Account Number")

    @api.onchange('bank_id')
    def onchage_bank(self):
        if self.bank_id:
            self.account_number = self.bank_id.acc_number


class Beneficiary(models.Model):
    _name = 'collaboration.beneficiary'
    _description = "Collaboration Beneficiary"

    collaboration_id = fields.Many2one('bases.collaboration')
    employee_id = fields.Many2one('hr.employee', "Employee")
    partner_id =  fields.Many2one('res.partner', "Contact")
    is_employee = fields.Boolean('Employee',copy=False,default=False)
    is_contact = fields.Boolean('Contact',copy=False,default=False
                                 )
    bank_id = fields.Many2one('res.partner.bank', "Bank")
    bank_account_ids = fields.Many2many('res.partner.bank','rel_bank_account_ben','account_id','ben_id',compute='get_bank_account_ids')
    account_number = fields.Char("Account Number")
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.user.company_id.currency_id)
    amount = fields.Monetary("Payment Amount")
    payment_rule_id = fields.Many2one(
        'recurring.payment.template', "Payment Rule")
    validity_start = fields.Date("Validity of the beneficiary start")
    validity_final_beneficiary = fields.Date(
        "Validity of the Final Beneficiary")
    withdrawal_sch_date = fields.Date("Withdrawal scheduling date")
    sequence = fields.Integer()

    @api.depends('is_contact', 'is_employee', 'partner_id','employee_id')
    def get_bank_account_ids(self):
        for rec in self:
            if rec.is_contact and rec.partner_id:
                rec.bank_account_ids = [
                    (6, 0, rec.partner_id.bank_ids.ids)]
            else:
                rec.bank_account_ids = [(6, 0, rec.employee_id.bank_ids.ids)]

    @api.onchange('is_employee')
    def onchange_is_employee(self):
        if self.is_employee:
            self.is_contact = False
            self.partner_id = False
    @api.onchange('is_contact')
    def onchange_is_contact(self):
        if self.is_contact:
            self.is_employee = False
            self.employee_id = False
            
    @api.onchange('bank_id')
    def onchage_bank(self):
        if self.bank_id:
            self.account_number = self.bank_id.acc_number


class ResPartnerBank(models.Model):

    _inherit = 'res.partner.bank'
    #_rec_name = 'bank_id'

    def name_get(self):
        if 'from_agreement' in self._context:
            res = []
            for bank in self:
                bank_name = ''
                if bank.bank_id:
                    bank_name = bank.bank_id.name
                res.append((bank.id, bank_name))
        else:
            res = super(ResPartnerBank, self).name_get()
        return res

    for_agreements = fields.Boolean("Agreements",copy=False,default=False)
    for_investments = fields.Boolean("Investments",copy=False,default=False)

class ResPartner(models.Model):

    _inherit = 'res.partner'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if 'from_retier_operation' in self._context and 'collaboration_id' in self._context:
            collaboration = self.env['bases.collaboration'].browse(
                self._context.get('collaboration_id'))
            partner_ids = []
            if collaboration and collaboration.provider_ids:
                for provider in collaboration.provider_ids:
                    partner_ids.append(provider.partner_id.id)
            args = [['id', 'in', partner_ids]]

#         if 'from_trust_provider' in self._context and 'collaboration_id' in self._context:
#             collaboration = self.env['bases.collaboration'].browse(self._context.get('collaboration_id'))
#             partner_ids = []
#             if collaboration and collaboration.provider_ids:
#                 for provider in collaboration.provider_ids:
#                     partner_ids.append(provider.partner_id.id)
#             args = [['id', 'in', partner_ids]]

        res = super(ResPartner, self).name_search(
            name, args=args, operator=operator, limit=limit)
        return res


class RequestOpenBalance(models.Model):

    _name = 'request.open.balance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Request to Open Balance"

    @api.depends('type_of_operation')
    def get_order_seq(self):
        for rec in self:
            seq = 0
            if rec.type_of_operation and rec.type_of_operation == 'open_bal':
                seq = 1
            elif rec.type_of_operation and rec.type_of_operation == 'increase':
                seq = 2
            elif rec.type_of_operation and rec.type_of_operation == 'increase_by_closing':
                seq = 3
            elif rec.type_of_operation and rec.type_of_operation == 'retirement':
                seq = 4
            elif rec.type_of_operation and rec.type_of_operation == 'withdrawal_cancellation':
                seq = 5
            elif rec.type_of_operation and rec.type_of_operation == 'withdrawal':
                seq = 6
            elif rec.type_of_operation and rec.type_of_operation == 'withdrawal_closure':
                seq = 7
        rec.order_seq = seq

    name = fields.Char("Name")
    bases_collaboration_id = fields.Many2one('bases.collaboration')
    operation_number = fields.Char("Operation Number")
    agreement_number = fields.Char("Agreement Number")
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

    type_of_operation_trust = fields.Selection([('open_bal', 'Opening Balance'),
                                                ('increase', 'Increase'),
                                                ('retirement', 'Retirement'),
                                                ('withdrawal_cancellation',
                                                 'Withdrawal Due to Cancellation'),
                                                ],
                                               string="Type of Operation")

    journal_id = fields.Many2one('account.journal')
    collaboration_beneficiary_id = fields.Many2one('collaboration.beneficiary','Collaboration Beneficiary')
    move_line_ids = fields.One2many(
        'account.move.line', 'request_id', string="Journal Items")

    apply_to_basis_collaboration = fields.Boolean(
        "Apply to Basis of Collaboration")
    order_seq = fields.Integer(compute='get_order_seq', store=True, copy=False)

    origin_resource_id = fields.Many2one(
        'sub.origin.resource', "Origin of the resource")
    state = fields.Selection([('draft', 'Draft'),
                              ('requested', 'Requested'),
                              ('approved', 'Approved'),
                              ('rejected', 'Rejected'),
                              ('confirmed', 'Confirmed'),
                              ('canceled', 'Canceled')], string="Status", default="draft")

    request_date = fields.Date("Request Date")
    trade_number = fields.Char("Trade Number")
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.user.company_id.currency_id)
    opening_balance = fields.Monetary("Opening Amount")
    observations = fields.Text("Observations")
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id,
                              string="Requesting User")

    cbc_format = fields.Binary("CBC Format")
    cbc_shipping_office = fields.Binary("CBC Shipping Office")
    liability_account_id = fields.Many2one(
        'account.account', "Liability Accounting Account")
    investment_account_id = fields.Many2one(
        'account.account', "Investment Accounting Account")
    interest_account_id = fields.Many2one(
        'account.account', "Interest Accounting Account")
    availability_account_id = fields.Many2one(
        'account.account', "Availability Accounting Account")
    reason_rejection = fields.Text("Reason for Rejection")
    supporting_documentation = fields.Binary("Supporting Documentation")
    create_payment_request = fields.Boolean("Create Payment Request")
    beneficiary_id = fields.Many2one('res.partner', "Beneficiary")
    provider_id = fields.Many2one('res.partner', "Provider")
    is_cancel_collaboration = fields.Boolean(
        "Operation of cancel collaboration", default=False)

    #==== fields for trust investment =======#

    trust_id = fields.Many2one('agreement.trust', 'Trust')

    patrimonial_account_id = fields.Many2one(
        'account.account', "Patrimonial Account")
    investment_account_id = fields.Many2one(
        'account.account', "Investment Account")
    interest_account_id = fields.Many2one(
        'account.account', "Interest Accounting Account")
    honorary_account_id = fields.Many2one(
        'account.account', "Honorary Accounting Account")
    availability_account_id = fields.Many2one(
        'account.account', "Availability Accounting Account")

    trust_agreement_file = fields.Binary("Trustee Agreement")
    trust_agreement_file_name = fields.Char("Trust Agreement File Name")
    trust_office_file = fields.Binary("Trust Contract Official Letter")
    trust_office_file_name = fields.Char("Trust Office File Name")

    origin_journal_id = fields.Many2one(
        'account.journal', 'Origin Bank Account')
    origin_bank_account_id = fields.Many2one(
        related='origin_journal_id.bank_account_id')
    destination_journal_id = fields.Many2one(
        'account.journal', 'Destination Bank Account')
    destination_bank_account_id = fields.Many2one(
        related='destination_journal_id.bank_account_id')

    trust_provider_ids = fields.Many2many(
        'res.partner', 'rel_req_bal_trust_partner', 'partner_id', 'req_id', compute="get_trust_provider_ids")
    trust_beneficiary_ids = fields.Many2many(
        'res.partner', 'rel_req_bal_trust_beneficiary', 'partner_id', 'req_id', compute="get_trust_beneficiary_ids")
    bases_collaboration_beneficiary_ids = fields.Many2many(
        'res.partner', 'rel_req_bal_bases_collaboration_beneficiary', 'partner_id', 'req_id', compute="get_bases_collaboration_beneficiary_ids")

    #==== fields for patrimonial =======#

    patrimonial_resources_id = fields.Many2one(
        'patrimonial.resources', 'Patrimonial Resources')
    patrimonial_equity_account_id = fields.Many2one(
        'account.account', "Equity accounting account")
    patrimonial_yield_account_id = fields.Many2one(
        'account.account', "Yield account of the productive investment account")

    specifics_project_id = fields.Many2one(
        'specific.project', 'Specific project')
    background_project_id = fields.Many2one(
        'background.project', 'Background Project', related="specifics_project_id.backgound_project_id")

    @api.onchange('type_of_operation')
    def onchange_type_of_operation_amount(self):
        if self.bases_collaboration_id and self.type_of_operation :
            if self.type_of_operation == 'open_bal':
                self.opening_balance = self.bases_collaboration_id.opening_bal
            else:
                self.opening_balance = 0.0

        elif self.patrimonial_resources_id and self.type_of_operation:
            if self.type_of_operation == 'open_bal':
                self.opening_balance = self.patrimonial_resources_id.opening_balance
            else:
                self.opening_balance = 0.0
        else:
            if self.trust_id and self.type_of_operation :
                if self.type_of_operation == 'open_bal':
                    self.opening_balance = self.trust_id.opening_balance
                else:
                    self.opening_balance = 0.0

    @api.constrains('opening_balance')
    def _check_opening_balance(self):
        print ('opening_balance')
        if self.opening_balance == 0:
            raise ValidationError(_('Opening amount must be different to 0.'))

    @api.onchange('type_of_operation_trust')
    def type_of_operation_trust_change(self):
        self.type_of_operation = self.type_of_operation_trust

    def unlink(self):
        for rec in self:
            if rec.state not in ['draft']:
                raise UserError(
                    _('You cannot delete an entry which has been requested.'))
        return super(RequestOpenBalance, self).unlink()

    @api.constrains('type_of_operation')
    def _check_type_of_operation(self):
        if self.type_of_operation and self.bases_collaboration_id and self.type_of_operation == 'open_bal':
            records = self.env['request.open.balance'].search([('id', '!=', self.id), ('bases_collaboration_id', '=', self.bases_collaboration_id.id), (
                'type_of_operation', '=', 'open_bal'), ('state', 'not in', ('rejected', 'canceled'))])
            if records:
                raise ValidationError(
                    _('Operation of opening balance can be performed just one time in each agreement'))

    @api.depends('trust_id', 'trust_id.provider_ids', 'trust_id.provider_ids.partner_id')
    def get_trust_provider_ids(self):
        for rec in self:
            if rec.trust_id and rec.trust_id.provider_ids:
                rec.trust_provider_ids = [
                    (6, 0, rec.trust_id.provider_ids.mapped('partner_id').ids)]
            else:
                rec.trust_provider_ids = [(6, 0, [])]

    @api.depends('trust_id', 'trust_id.beneficiary_ids', 'trust_id.beneficiary_ids.employee_id')
    def get_trust_beneficiary_ids(self):
        for rec in self:
            partner_ids = []
            if rec.trust_id and rec.trust_id.beneficiary_ids:

                for emp in rec.trust_id.beneficiary_ids.mapped('employee_id'):
                    if emp.user_id and emp.user_id.partner_id:
                        partner_ids.append(emp.user_id.partner_id.id)
                for pat in rec.trust_id.beneficiary_ids.mapped('partner_id'):
                    partner_ids.append(pat.id)
            rec.trust_beneficiary_ids = [(6, 0, partner_ids)]

    @api.depends('bases_collaboration_id', 'bases_collaboration_id.beneficiary_ids', 'bases_collaboration_id.beneficiary_ids.employee_id')
    def get_bases_collaboration_beneficiary_ids(self):
        for rec in self:
            partner_ids = []
            if rec.bases_collaboration_id and rec.bases_collaboration_id.beneficiary_ids:
                for emp in rec.bases_collaboration_id.beneficiary_ids.mapped('employee_id'):
                    if emp.user_id and emp.user_id.partner_id:
                        partner_ids.append(emp.user_id.partner_id.id)
                for pat in rec.bases_collaboration_id.beneficiary_ids.mapped('partner_id'):
                    partner_ids.append(pat.id)
            rec.bases_collaboration_beneficiary_ids = [(6, 0, partner_ids)]

    @api.model
    def default_get(self, fields):
        res = super(RequestOpenBalance, self).default_get(fields)
        if res.get('bases_collaboration_id', False):

            base_id = self.env['bases.collaboration'].browse(
                res.get('bases_collaboration_id'))
            number = 0
            if base_id:
                number = base_id.next_no + 1

            res.update({
                'operation_number': str(number)
            })
            collaboration_jou = self.env.ref(
                'jt_agreement.collaboration_jou_id')
            if collaboration_jou:
                res.update({'journal_id': collaboration_jou.id})

        elif res.get('trust_id', False):
            trust_id = self.env['agreement.trust'].browse(res.get('trust_id'))
            number = 0
            if trust_id:
                number = trust_id.next_no + 1

            res.update({
                'operation_number': str(number)
            })
        elif res.get('patrimonial_resources_id', False):
            patrimonial_resources_id = self.env['patrimonial.resources'].browse(
                res.get('patrimonial_resources_id'))
            number = 0
            if patrimonial_resources_id:
                number = patrimonial_resources_id.next_no + 1

            res.update({
                'operation_number': str(number)
            })
            collaboration_jou = self.env.ref(
                'jt_agreement.collaboration_jou_id')
            if collaboration_jou:
                res.update({'journal_id': collaboration_jou.id})

        else:
            res.update({
                'operation_number': str(0)
            })

        return res

    @api.model
    def create(self, vals):
        res = super(RequestOpenBalance, self).create(vals)
        if res and res.is_cancel_collaboration and res.type_of_operation != 'withdrawal_cancellation':
            raise ValidationError(
                _("Type of Operation must be 'Withdrawal Due to Cancellation' for this operation!"))
        if res and not res.is_cancel_collaboration and res.type_of_operation == 'withdrawal_cancellation':
            raise ValidationError(
                _("Can't create Operation with 'Withdrawal Due to Cancellation' Type of Operation manually!"))
        if self.env.context and not self.env.context.get('call_from_closing', False) and res.type_of_operation == 'withdrawal_closure':
            raise ValidationError(
                _("Can't create Operation with 'Withdrawal due to closure' Type of Operation manually!"))
        if self.env.context and not self.env.context.get('call_from_closing', False) and res.type_of_operation == 'increase_by_closing':
            raise ValidationError(
                _("Can't create Operation with 'Increase by closing' Type of Operation manually!"))
        if res.bases_collaboration_id and res.bases_collaboration_id.state in ('cancelled', 'to_be_cancelled'):
            raise ValidationError(
                _("Can't create Operation for Cancelled Bases of Collabration!"))
        if res.trust_id and res.trust_id.state in ('cancelled', 'to_be_cancelled'):
            raise ValidationError(
                _("Can't create Operation for Cancelled Trust!"))
        if res.patrimonial_resources_id and res.patrimonial_resources_id.state in ('cancelled', 'to_be_cancelled'):
            raise ValidationError(
                _("Can't create Operation for Cancelled Patrimonial resources!"))

        # name = self.env['ir.sequence'].next_by_code('agreement.operation')
        if res.bases_collaboration_id:
            res.bases_collaboration_id.next_no += 1
            res.operation_number = res.bases_collaboration_id.next_no
            #===========set Document data=============
            if not res.cbc_format:
                res.cbc_format = res.bases_collaboration_id.cbc_format
            if not res.supporting_documentation:
                res.supporting_documentation = res.bases_collaboration_id.cbc_format
            if not res.cbc_shipping_office:
                res.cbc_shipping_office = res.bases_collaboration_id.cbc_shipping_office
             
        if res.trust_id:
            res.trust_id.next_no += 1
            res.operation_number = res.trust_id.next_no
            if not res.trust_agreement_file:
                res.trust_agreement_file = res.trust_id.trust_agreement_file
                res.trust_agreement_file_name = res.trust_id.trust_agreement_file_name
            if not res.trust_office_file:
                res.trust_office_file = res.trust_id.trust_office_file
                res.trust_office_file_name = res.trust_id.trust_office_file_name
            if not res.supporting_documentation:
                res.supporting_documentation = res.trust_id.trust_office_file
                
        if res.patrimonial_resources_id:
            res.patrimonial_resources_id.next_no += 1
            res.operation_number = res.patrimonial_resources_id.next_no
            #===== Set Documents data================
            if not res.trust_agreement_file:
                res.trust_agreement_file = res.patrimonial_resources_id.fund_registration_file
                res.trust_agreement_file_name = res.patrimonial_resources_id.fund_registration_file_name
            if not res.trust_office_file:
                res.trust_office_file = res.patrimonial_resources_id.fund_office_file
                res.trust_office_file_name = res.patrimonial_resources_id.fund_office_file_name
            if not res.supporting_documentation:
                res.supporting_documentation = res.patrimonial_resources_id.fund_registration_file
        if not res.journal_id:
            collaboration_jou = self.env.ref(
                'jt_agreement.collaboration_jou_id')
            if collaboration_jou:
                res.journal_id = collaboration_jou.id
        if not res.type_of_operation_trust and res.type_of_operation and res.trust_id:
            if res.type_of_operation in ('open_bal', 'increase', 'retirement', 'withdrawal_cancellation'):
                res.type_of_operation_trust = res.type_of_operation

        # res.operation_number = name
        return res

    def write(self, vals):
        res = super(RequestOpenBalance, self).write(vals)
        for rec in self:
            if rec.is_cancel_collaboration and rec.type_of_operation != 'withdrawal_cancellation':
                raise ValidationError(
                    _("Type of Operation must be 'Withdrawal Due to Cancellation' for this operation!"))
            if not rec.is_cancel_collaboration and rec.type_of_operation == 'withdrawal_cancellation':
                raise ValidationError(
                    _("Can't create Operation with 'Withdrawal Due to Cancellation' Type of Operation manually!"))
        return res

    def action_create_payment_req(self):
        payment_req_obj = self.env['payment.request']
        payment_reqs = payment_req_obj.search(
            [('balance_req_id', '=', self.id)])
        beneficiary = False
        bank_id = False
        account_number = False
        partner_id = False
        if self.beneficiary_id:
            partner_id = self.beneficiary_id.id
        if self.beneficiary_id and self.bases_collaboration_id:
            user = self.env['res.users'].sudo().search(
                [('partner_id', '=', self.beneficiary_id.id)], limit=1)
            if user:
                emp_id = self.env['hr.employee'].sudo().search(
                    [('user_id', '=', user.id)], limit=1)
                if emp_id:
                    beneficiary = self.env['collaboration.beneficiary'].search([
                        ('collaboration_id', '=', self.bases_collaboration_id.id), ('employee_id', '=', emp_id.id)])
        if not beneficiary and self.beneficiary_id and self.bases_collaboration_id:
            beneficiary = self.env['collaboration.beneficiary'].search([
                ('collaboration_id', '=', self.bases_collaboration_id.id), ('partner_id', '=', self.beneficiary_id.id)])
        if beneficiary:
            bank_id = beneficiary.bank_id.id if beneficiary and beneficiary.bank_id else False
            account_number = beneficiary.account_number if beneficiary else '',
        elif self.beneficiary_id:
            bank_id = self.beneficiary_id and self.beneficiary_id.bank_ids and self.beneficiary_id.bank_ids[0].bank_id and self.beneficiary_id.bank_ids[0].id or False 
            account_number = self.beneficiary_id and self.beneficiary_id.bank_ids and self.beneficiary_id.bank_ids[0] and self.beneficiary_id.bank_ids[0].acc_number or '' 
        
        if not self.beneficiary_id and self.provider_id and self.patrimonial_resources_id:
            partner_id = self.provider_id.id
            col_provider = self.env['collaboration.providers'].search([
                ('patrimonial_id', '=', self.patrimonial_resources_id.id),('partner_id', '=', self.provider_id.id)],limit=1)
            if col_provider:
                bank_id = col_provider.bank_id and col_provider.bank_id.id or False
                account_number = col_provider.account_number
                 
        is_balance_req_id_reject = False
        if self.state and self.state=='rejected':
            is_balance_req_id_reject = True
         
        if payment_reqs:
            
            return {
                'name': _('Payment Requests'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'payment.request',
                'domain': [('balance_req_id', '=', self.id)],
                'type': 'ir.actions.act_window',
                'context': {'default_balance_req_id': self.id,
                            'default_name': self.name,
                            'default_type_of_operation': 'retirement',
                            'default_operation_number': self.operation_number,
                            'default_amount': self.opening_balance,
                            'default_beneficiary_id': partner_id,
                            'default_bank_id': bank_id,
                            'default_account_number': account_number,
                            'from_agreement': True,
                            'default_is_balance_req_id_reject':is_balance_req_id_reject,
                            }
            }
        else:
            return {
                'name': 'Payment Request',
                'view_mode': 'form',
                'res_model': 'payment.request',
                'domain': [('balance_req_id', '=', self.id)],
                'type': 'ir.actions.act_window',
                'context': {'default_balance_req_id': self.id,
                            'default_name': self.name,
                            'default_type_of_operation': 'retirement',
                            'default_operation_number': self.operation_number,
                            'default_amount': self.opening_balance,
                            'default_beneficiary_id': partner_id,
                            'default_bank_id': bank_id,
                            'default_account_number': account_number,
                            'from_agreement': True,
                            'default_is_balance_req_id_reject':is_balance_req_id_reject,
                            }
            }

    @api.constrains('operation_number')
    def _check_operation_number(self):
        if self.operation_number and not self.operation_number.isnumeric():
            raise ValidationError(_('Operation Number must be Numeric.'))

    def action_confirmed(self):
        self.state = 'confirmed'
        if self.patrimonial_resources_id or self.bases_collaboration_id:
            if self.journal_id:
                journal = self.journal_id
                if not journal.default_debit_account_id or not journal.default_credit_account_id \
                        or not journal.conac_debit_account_id or not journal.conac_credit_account_id:
                    if self.env.user.lang == 'es_MX':
                        raise ValidationError(
                            _("Por favor configure la cuenta UNAM y CONAC en diario!"))
                    else:
                        raise ValidationError(
                            _("Please configure UNAM and CONAC account in journal!"))

                today = datetime.today().date()
                user = self.env.user
                partner_id = user.partner_id.id
                amount = self.opening_balance
                name = ''
                dep = False
                sub_dep = False
                if self.bases_collaboration_id:
                    dep = self.bases_collaboration_id.dependency_id and self.bases_collaboration_id.dependency_id.id or False
                    sub_dep = self.bases_collaboration_id.subdependency_id and self.bases_collaboration_id.subdependency_id.id or False
                if self.patrimonial_resources_id:
                    print ("callll====")
                    dep = self.patrimonial_resources_id.dependency_id and self.patrimonial_resources_id.dependency_id.id or False
                    sub_dep = self.patrimonial_resources_id.subdependency_id and self.patrimonial_resources_id.subdependency_id.id or False
                
                     
                if self.name:
                    name += self.name
                if self.operation_number:
                    name += "-" + self.operation_number

                if self.type_of_operation in ('open_bal', 'increase', 'increase_by_closing'):
                    unam_move_val = {'name': name, 'ref': name,  'conac_move': True,
                                     'dependancy_id' : dep,
                                     'sub_dependancy_id' : sub_dep,
                                     'date': today, 'journal_id': journal.id, 'company_id': self.env.user.company_id.id,
                                     'line_ids': [(0, 0, {
                                         'account_id': journal.default_credit_account_id.id,
                                         'coa_conac_id': journal.conac_credit_account_id.id,
                                         'credit': amount,
                                         'partner_id': partner_id,
                                         'request_id': self.id,
                                     }),
                                         (0, 0, {
                                             'account_id': journal.default_debit_account_id.id,
                                             'coa_conac_id': journal.conac_debit_account_id.id,
                                             'debit': amount,
                                             'partner_id': partner_id,
                                             'request_id': self.id,
                                         }),
                                     ]}
                    move_obj = self.env['account.move']
                    unam_move = move_obj.create(unam_move_val)
                    unam_move.action_post()
                elif self.type_of_operation in ('retirement', 'withdrawal', 'withdrawal_cancellation', 'withdrawal_closure'):
                    unam_move_val = {'name': name, 'ref': name,  'conac_move': True,
                                     'date': today, 'journal_id': journal.id, 'company_id': self.env.user.company_id.id,
                                     'line_ids': [(0, 0, {
                                         'account_id': journal.default_debit_account_id.id,
                                         'coa_conac_id': journal.conac_debit_account_id.id,
                                         'credit': amount,
                                         'partner_id': partner_id,
                                         'request_id': self.id,
                                     }),
                                         (0, 0, {
                                             'account_id': journal.default_credit_account_id.id,
                                             'coa_conac_id': journal.conac_credit_account_id.id,
                                             'debit': amount,
                                             'partner_id': partner_id,
                                             'request_id': self.id,
                                         }),
                                     ]}
                    move_obj = self.env['account.move']
                    unam_move = move_obj.create(unam_move_val)
                    unam_move.action_post()

    def request(self):
        if self.type_of_operation in ('retirement','withdrawal','withdrawal_cancellation','withdrawal_closure') and self.bases_collaboration_id and self.bases_collaboration_id.available_bal < self.opening_balance:
            raise ValidationError(_('​Available Balance Is Less Then Requested Balance!'))

        elif self.type_of_operation in ('retirement','withdrawal','withdrawal_cancellation','withdrawal_closure') and self.trust_id and self.trust_id.available_bal < self.opening_balance:
            raise ValidationError(_('​Available Balance Is Less Then Requested Balance!'))

        elif self.type_of_operation in ('retirement','withdrawal','withdrawal_cancellation','withdrawal_closure') and self.patrimonial_resources_id and self.patrimonial_resources_id.available_bal < self.opening_balance:
            raise ValidationError(_('​Available Balance Is Less Then Requested Balance!'))
        
        req_open_bal_id = False
        if self.state=='rejected':
            req_open_bal_id = self.env['request.open.balance.invest'].search([('state','=','rejected'),('balance_req_id','=',self.id)],limit=1)
        
        if req_open_bal_id:
            req_open_bal_id.type_of_operation = self.type_of_operation  
            req_open_bal_id.state = 'requested'
            req_open_bal_id.opening_balance = self.opening_balance 
            req_open_bal_id.origin_resource_id = self.origin_resource_id and self.origin_resource_id.id or False
            req_open_bal_id.beneficiary_id = self.beneficiary_id.id
        else:
            self.env['request.open.balance.invest'].create({
                'name': self.name,
                'operation_number': self.operation_number,
                'agreement_number': self.agreement_number,
                'is_cancel_collaboration': True if self.type_of_operation == 'withdrawal_cancellation' else False,
                'type_of_operation': self.type_of_operation,
                'apply_to_basis_collaboration': self.apply_to_basis_collaboration,
                'origin_resource_id': self.origin_resource_id and self.origin_resource_id.id or False,
                'state': 'requested',
                'request_date': self.request_date,
                'trade_number': self.trade_number,
                'currency_id': self.currency_id and self.currency_id.id or False,
                'opening_balance': self.opening_balance,
                'observations': self.observations,
                'user_id': self.user_id and self.user_id.id or False,
                'cbc_format': self.cbc_format,
                'cbc_shipping_office': self.cbc_shipping_office,
                'liability_account_id': self.liability_account_id and self.liability_account_id.id or False,
                'investment_account_id': self.investment_account_id and self.investment_account_id.id or False,
                'interest_account_id': self.interest_account_id and self.interest_account_id.id or False,
                'availability_account_id': self.availability_account_id and self.availability_account_id.id or False,
                'balance_req_id': self.id,
                'patrimonial_account_id': self.patrimonial_account_id and self.patrimonial_account_id.id or False,
                'interest_account_id': self.interest_account_id and self.interest_account_id.id or False,
                'honorary_account_id': self.honorary_account_id and self.honorary_account_id.id or False,
                'trust_agreement_file': self.trust_agreement_file,
                'trust_agreement_file_name': self.trust_agreement_file_name,
                'trust_office_file': self.trust_office_file,
                'trust_office_file_name': self.trust_office_file_name,
                'trust_id': self.trust_id and self.trust_id.id or False,
                'origin_journal_id': self.origin_journal_id and self.origin_journal_id.id or False,
                "destination_journal_id": self.destination_journal_id and self.destination_journal_id.id or False,
                'patrimonial_id': self.patrimonial_resources_id and self.patrimonial_resources_id.id or False,
                'patrimonial_yield_account_id': self.patrimonial_yield_account_id and self.patrimonial_yield_account_id.id or False,
                'patrimonial_equity_account_id': self.patrimonial_equity_account_id and self.patrimonial_equity_account_id.id or False,
                'bases_collaboration_id': self.bases_collaboration_id and self.bases_collaboration_id.id or False,
                'fund_type_id': self.bases_collaboration_id and self.bases_collaboration_id.fund_type_id and self.bases_collaboration_id.fund_type_id.id or False,
                'type_of_agreement_id': self.bases_collaboration_id and self.bases_collaboration_id.agreement_type_id and self.bases_collaboration_id.agreement_type_id.id or False,
                'fund_id':  self.bases_collaboration_id and self.bases_collaboration_id.fund_id and self.bases_collaboration_id.fund_id.id or False,
                'beneficiary_id': self.beneficiary_id.id,
                'provider_id': self.provider_id.id,
                'specifics_project_id': self.specifics_project_id and self.specifics_project_id.id or False,
            })
        self.state = 'requested'
        if self.type_of_operation == 'withdrawal_cancellation' and self.bases_collaboration_id:
            self.bases_collaboration_id.state = 'to_be_cancelled'
        if self.type_of_operation == 'withdrawal_cancellation' and self.trust_id:
            self.trust_id.action_to_be_cancelled()
        if self.type_of_operation == 'withdrawal_cancellation' and self.patrimonial_resources_id:
            self.patrimonial_resources_id.action_to_be_cancelled()
        elif self.type_of_operation == 'retirement':
            self.create_payment_request = True

#     def download_file(self):
#         self.ensure_one()
#         return {
#                 'type': 'ir.actions.act_url',
#                 'target':'download',
#                  'url': "web/content/?model=bases.collaboration&id=" + str(self.bases_collaboration_id.id) + "&filename_field=name&field=cbc_format&download=true&filename=" + self.bases_collaboration_id.name,
#             }    

class RequestOpenBalanceInvestment(models.Model):

    _name = 'request.open.balance.invest'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Request to Open Balance Investment"

    _rec_name = 'first_number'

    first_number = fields.Char('First Number:')
    new_journal_id = fields.Many2one("account.journal", 'Journal')

    name = fields.Char("Name")
    balance_req_id = fields.Many2one(
        'request.open.balance', "Opening Balance Request")
    operation_number = fields.Char("Operation Number")
    agreement_number = fields.Char("Agreement Number")
    type_of_operation = fields.Selection([('open_bal', 'Opening Balance'),
                                          ('increase', 'Increase'),
                                          ('retirement', 'Retirement'),
                                          ('withdrawal', 'Withdrawal for settlement'),
                                          ('withdrawal_cancellation', 'Withdrawal Due to Cancellation')],
                                         string="Type of Operation")
    apply_to_basis_collaboration = fields.Boolean(
        "Apply to Basis of Collaboration")
    apply_to_trust = fields.Boolean(
        related='apply_to_basis_collaboration', string="Apply to Trust")

    apply_to_patrimonial = fields.Boolean(
        related='apply_to_basis_collaboration', string="Apply to patrimonial resources")

    origin_resource_id = fields.Many2one(
        'sub.origin.resource', "Origin of the resource")
    state = fields.Selection([('draft', 'Draft'),
                              ('requested', 'Requested'),
                              ('rejected', 'Rejected'),
                              ('approved', 'Approved'),
                              ('confirmed', 'Confirmed'),
                              ('done', 'Done'),
                              ('canceled', 'Canceled')], string="Status", default="draft")

    request_date = fields.Date("Request Date")
    trade_number = fields.Char("Trade Number")
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.user.company_id.currency_id)
    opening_balance = fields.Monetary("Opening Amount")
    observations = fields.Text("Observations")
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id,
                              string="Requesting User")
    is_manually = fields.Float("Manually Records", default=False)

    cbc_format = fields.Binary("CBC Format")
    cbc_shipping_office = fields.Binary("CBC Shipping Office")
    liability_account_id = fields.Many2one(
        'account.account', "Liability Accounting Account")
    investment_account_id = fields.Many2one(
        'account.account', "Investment Accounting Account")
    interest_account_id = fields.Many2one(
        'account.account', "Interest Accounting Account")
    availability_account_id = fields.Many2one(
        'account.account', "Availability Accounting Account")
    supporting_documentation = fields.Binary("Supporting Documentation")

    origin_journal_id = fields.Many2one(
        'account.journal', 'Origin Bank Account')
    destination_journal_id = fields.Many2one(
        'account.journal', 'Destination Bank Account')

    patrimonial_account_id = fields.Many2one(
        'account.account', "Patrimonial Account")
    investment_account_id = fields.Many2one(
        'account.account', "Investment Account")
    interest_account_id = fields.Many2one(
        'account.account', "Interest Accounting Account")
    honorary_account_id = fields.Many2one(
        'account.account', "Honorary Accounting Account")
    availability_account_id = fields.Many2one(
        'account.account', "Availability Accounting Account")
    liability_account_id = fields.Many2one(
        'account.account', "Liability Account")

    trust_agreement_file = fields.Binary("Trustee Agreement")
    trust_agreement_file_name = fields.Char("Trust Agreement File Name")
    trust_office_file = fields.Binary("Trust Contract Official Letter")
    trust_office_file_name = fields.Char("Trust Office File Name")

    trust_id = fields.Many2one('agreement.trust', 'Trust')

    patrimonial_id = fields.Many2one('patrimonial.resources', 'Patrimonial')
    patrimonial_yield_account_id = fields.Many2one(
        'account.account', "Yield account of the productive investment account")
    patrimonial_equity_account_id = fields.Many2one(
        'account.account', "Equity accounting account")

    specifics_project_id = fields.Many2one(
        'specific.project', 'Specific project')
    background_project_id = fields.Many2one(
        'background.project', 'Background Project', related="specifics_project_id.backgound_project_id")

    reason_rejection = fields.Text("Reason for Rejection")
    is_cancel_collaboration = fields.Boolean(
        "Operation of cancel collaboration", default=False)
    yield_id = fields.Many2one('yield.destination', 'Yield Destination')

    #====== fields for the Investment Funds View   ====>

    fund_id = fields.Many2one('agreement.fund', 'Fund')
    fund_key = fields.Char(related='fund_id.fund_key',
                           string="Password of the Fund")

    fund_type_id = fields.Many2one('fund.type', 'Type of Fund')
    type_of_agreement_id = fields.Many2one(
        'agreement.agreement.type', 'Type of Agreement')
    bases_collaboration_id = fields.Many2one(
        'bases.collaboration', 'Name of Agreement')
    is_fund = fields.Boolean(default=False, string="Fund")

    fund_request_date = fields.Date('Request')
    dependency_id = fields.Many2one('dependency', "Dependency")
    subdependency_id = fields.Many2one('sub.dependency', "Sub Dependency")
    dependency_holder = fields.Char("Dependency Holder")
    responsible_user_id = fields.Many2one('res.users', string='Responsible')
    type_of_resource = fields.Char("Type Of Resource")

    bank_id = fields.Many2one('res.partner.bank', "Bank")
    account_number = fields.Char(
        related="bank_id.acc_number", string='Account Number')
    request_office = fields.Char("Request Office")
    permanent_instructions = fields.Text("Permanent Instructions")
    fund_observation = fields.Text("Observations")

    hide_is_manually = fields.Boolean(
        'Hide Manully Button', default=True, compute='get_record_state_change')
    hide_is_auto = fields.Boolean(
        'Hide Auto Button', default=True, compute='get_record_state_change')
    beneficiary_id = fields.Many2one('res.partner', "Beneficiary")
    provider_id = fields.Many2one('res.partner', "Provider")
    payment_request_id = fields.Many2one('payment.request',copy=False)
    
    @api.depends('state', 'is_manually')
    def get_record_state_change(self):
        for rec in self:
            hide_is_manually = True
            hide_is_auto = True
            if rec.is_manually and rec.state == 'draft':
                hide_is_manually = False
            if not rec.is_manually and rec.state == 'requested':
                hide_is_auto = False
            rec.hide_is_manually = hide_is_manually
            rec.hide_is_auto = hide_is_auto

    @api.model
    def create(self, vals):
        res = super(RequestOpenBalanceInvestment, self).create(vals)
        if res and res.is_cancel_collaboration and res.type_of_operation != 'withdrawal_cancellation':
            raise ValidationError(
                _("Type of Operation must be 'Withdrawal Due to Cancellation' for this operation!"))
        if res and not res.is_cancel_collaboration and res.type_of_operation == 'withdrawal_cancellation':
            raise ValidationError(
                _("Can't create Operation with 'Withdrawal Due to Cancellation' Type of Operation manually!"))

        if res.new_journal_id:
            sequence = res.new_journal_id and res.new_journal_id.sequence_id or False
            if not sequence:
                raise UserError(_('Please define a sequence on your journal.'))

            res.first_number = sequence.with_context(
                ir_sequence_date=res.request_date).next_by_id()

#         first_number = self.env['ir.sequence'].next_by_code('IRF.number')
#         res.first_number = first_number

        return res

    def write(self, vals):
        res = super(RequestOpenBalanceInvestment, self).write(vals)
        for rec in self:
            if rec.is_cancel_collaboration and rec.type_of_operation != 'withdrawal_cancellation':
                raise ValidationError(
                    _("Type of Operation must be 'Withdrawal Due to Cancellation' for this operation!"))
            if not rec.is_cancel_collaboration and rec.type_of_operation == 'withdrawal_cancellation':
                raise ValidationError(
                    _("Can't create Operation with 'Withdrawal Due to Cancellation' Type of Operation manually!"))
        return res

    @api.constrains('operation_number')
    def _check_operation_number(self):
        if self.operation_number and not self.operation_number.isnumeric():
            raise ValidationError(_('Operation Number must be Numeric.'))

    def reject_request(self):

        activity_type = self.env.ref('mail.mail_activity_data_todo').id
        summary = "Rejection'" + str(self.name) + "'Increases and withdrawals"
        activity_obj = self.env['mail.activity']
        model_id = self.env['ir.model'].sudo().search([('model', '=', 'request.open.balance.invest')]).id
        activity_obj.create({'activity_type_id': activity_type,
                           'res_model': 'request.open.balance.invest', 'res_id': self.id,
                           'res_model_id':model_id,
                           'summary': summary, 'user_id': self.user_id.id})


        return {
            'name': 'Reason for Rejection',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'reason.rejection.open.bal',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

    def approve_investment(self):
        today = datetime.today().date()
        user = self.env.user
        unit_req_transfer_id = False
        employee = self.env['hr.employee'].search(
            [('user_id', '=', user.id)], limit=1)
        if employee and employee.dependancy_id:
            unit_req_transfer_id = employee.dependancy_id.id
        is_agr = True
        is_balance = False
        dependency_id = False
        if self.trust_id:
            is_agr = False
            is_balance = True
            dependency_id = self.trust_id and self.trust_id.dependency_id and self.trust_id.dependency_id.id or False
        activity_type = self.env.ref('mail.mail_activity_data_todo').id
        summary = "Approve'" + str(self.name) + "'Increases and withdrawals"
        activity_obj = self.env['mail.activity']
        model_id = self.env['ir.model'].sudo().search([('model', '=', 'request.open.balance.invest')]).id
        activity_obj.create({'activity_type_id': activity_type,
                           'res_model': 'request.open.balance.invest', 'res_id': self.id,
                           'res_model_id':model_id,
                           'summary': summary, 'user_id': self.user_id.id})

        return {
            'name': 'Approve Request',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'approve.investment.bal.req',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_operation_number': self.operation_number,
                'default_agreement_number': self.agreement_number,
                'default_amount': self.opening_balance,
                'default_date': today,
                'default_employee_id': employee.id if employee else False,
                'default_fund_type': self.fund_type_id and self.fund_type_id.id or False,
                'show_for_agreement': 1,
                'show_agreement_name': 1,
                'default_bank_account_id': self.origin_journal_id and self.origin_journal_id.id or False,
                'default_desti_bank_account_id': self.destination_journal_id and self.destination_journal_id.id or False,
                'default_unit_req_transfer_id': unit_req_transfer_id,
                'default_fund_id': self.fund_id and self.fund_id.id or False,
                'default_agreement_type_id': self.type_of_agreement_id and self.type_of_agreement_id.id or False,
                'default_base_collabaration_id': self.bases_collaboration_id and self.bases_collaboration_id.id or False,
                'default_type_of_operation': self.type_of_operation,
                'default_origin_resource_id': self.origin_resource_id and self.origin_resource_id.id or False,
                'default_is_agr': is_agr,
                'default_is_balance': is_balance,
                'default_dependency_id': dependency_id,
                'default_patrimonial_id': self.patrimonial_id.id if self.patrimonial_id else False,
                'default_trust_id': self.trust_id.id if self.trust_id else False
            }
        }


class Project(models.Model):
    _inherit = 'project.project'

    def name_get(self):
        result = []
        for rec in self:
            name = rec.name
            if rec.number_agreement and self.env.context and self.env.context.get('from_agreement', True):
               
                name = rec.number_agreement
            result.append((rec.id, name))
        return result


class RequestOpenBalanceFinance(models.Model):

    _name = 'request.open.balance.finance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Request to Open Balance For Finanace"
    _rec_name = 'operation_number'

    request_id = fields.Many2one('request.open.balance.invest', "Request")
    invoice = fields.Char("Invoice")
    operation_number = fields.Char("Operation Number")
    agreement_number = fields.Char("Agreement Number")
    bank_account_id = fields.Many2one(
        'account.journal', "Origin Bank")
    origin_account = fields.Many2one(related="bank_account_id.bank_account_id" , string="Account Origin")
    desti_bank_account_id = fields.Many2one(
        'account.journal', "Destination Bank")
    desti_account = fields.Many2one(related="desti_bank_account_id.bank_account_id" , string="Destination Account")
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.user.company_id.currency_id)
    amount = fields.Monetary("Amount")
    dependency_id = fields.Many2one('dependency', "Dependency")
    sub_dependency_id = fields.Many2one('sub.dependency', "Subdependency")
    date = fields.Date("Application date",default=fields.Date.today)
    concept = fields.Text("Application Concept")
    user_id = fields.Many2one(
        'res.users', default=lambda self: self.env.user.id, string="Applicant")
    unit_req_transfer_id = fields.Many2one(
        'dependency', string="Unit requesting the transfer")
    date_required = fields.Date("Date Required")
    fund_type = fields.Many2one('fund.type', "Background")
    investment_fund_id = fields.Many2one('investment.funds', 'Investment Fund')

    agreement_type_id = fields.Many2one(
        'agreement.agreement.type', 'Agreement Type')
    fund_id = fields.Many2one('agreement.fund', 'Fund')
    base_collabaration_id = fields.Many2one(
        'bases.collaboration', 'Name Of Agreements')

    reason_rejection = fields.Text("Reason Rejection")
    state = fields.Selection([('draft', 'Draft'),
                              ('requested', 'Requested'),
                              ('rejected', 'Rejected'),
                              ('approved', 'Approved'),
                              ('sent', 'Sent'),
                              ('confirmed', 'Confirmed'),
                              ('done', 'Done'),
                              ('canceled', 'Canceled')], string="Status", default="draft")
    payment_ids = fields.Many2many('account.payment', 'rel_req_payment', 'payment_id', 'payment_request_rel_id',
                                   "Payments")
    payment_count = fields.Integer(compute="count_payment", string="Payments")

    #=== New fields OS-Odoo-06 =========#
    def _get_prepare_by_employe(self):
        emp_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        if emp_id:
            return emp_id.id
        else:
            return False
        
    trasnfer_request = fields.Selection([('investments','Investments'),('projects','Projects'),('finances','Finances')],string='Transfer Request')
    is_manual = fields.Boolean(string="Manual Registration",copy=False,default=False)
    attention_to_emp_id = fields.Many2one("hr.employee","Attention to")
    prepared_by_emp_id = fields.Many2one("hr.employee","Prepared by",default=_get_prepare_by_employe)
    prepared_by_user_id = fields.Many2one("res.users",string="Creation Users",default=lambda self: self.env.user.id)
    prepared_by_dept_id = fields.Many2one(related="prepared_by_user_id.department_id",string="Department to which it belongs")
    
    authorized_by_emp_id = fields.Many2one("hr.employee","Authorized by")
    authorized_by_user_id = fields.Many2one("res.users",string="Authorized Users")
    authorized_by_dept_id = fields.Many2one(related="authorized_by_user_id.department_id",string="Department to which the authorizing person belongs")
    
    @api.constrains('operation_number')
    def _check_operation_number(self):
        if self.operation_number and not self.operation_number.isnumeric():
            raise ValidationError(_('Operation Number must be Numeric.'))

    @api.model
    def create(self, vals):
        res = super(RequestOpenBalanceFinance, self).create(vals)
        if res.is_manual:
            name = self.env['ir.sequence'].next_by_code('request.open.balance.finance.manual')
            res.invoice = name
        if not res.operation_number:
            rec = self.env['ir.sequence'].next_by_code('request.open.balance.finance')
            res.operation_number = rec
        return res

    def open_payments(self):
        action = self.env.ref('account.action_account_payments').read()[0]
        action['context'] = {'default_payment_type': 'inbound',
                             'default_partner_type': 'customer',
                             #'search_default_inbound_filter': 1,
                             #'res_partner_search_mode': 'customer',
                             'show_for_agreement': True
                             }

        if self.payment_ids:
            action['domain'] = [('id', 'in', self.payment_ids.ids)]
        else:
            action['domain'] = [('id', 'in', [])]
        return action

    def count_payment(self):
        for rec in self:
            rec.payment_count = len(self.payment_ids)

    def reject_request(self):
        other_rec = self.filtered(lambda x:x.state!='requested')
        if other_rec:
           raise ValidationError(_('This action can only be performed for transfers in Requested status')) 
        
        return {
            'name': 'Reason for Rejection',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'reason.rejection.open.bal',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context':{'active_model':'request.open.balance.finance','active_ids':self.ids}
        }

    def mass_approve_finance(self):
        other_rec = self.filtered(lambda x:x.state!='requested')
        if other_rec:
           raise ValidationError(_('This action can only be performed for transfers in Requested status'))
        return {
            'name': _('Approve Transfers'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'mass.approve.transfer',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context':{'active_model':'request.open.balance.finance','active_ids':self.ids}
        }
        
#         for rec in self:
#             rec.approve_finance()
            
    def approve_finance(self):
        self.state = 'approved'
        self.authorized_by_user_id = self.env.user.id
        emp_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        if emp_id:
            self.authorized_by_emp_id = emp_id.id
        if self.prepared_by_user_id:
            activity_type = self.env.ref('mail.mail_activity_data_todo').id
            summary = "Approve Transfer Request"
            if self.invoice:
                summary = _("Approve '%s' Transfer Request") % str(self.invoice)
            
            activity_obj = self.env['mail.activity']
            model_id = self.env['ir.model'].sudo().search([('model', '=', 'request.open.balance.finance')]).id
            activity_obj.create({'activity_type_id': activity_type,
                               'res_model': 'request.open.balance.finance', 'res_id': self.id,
                               'res_model_id':model_id,
                               'summary': summary, 'user_id': self.prepared_by_user_id.id})
            
    def canceled_finance(self):
        self.state = 'canceled'

    def confirmed_finance(self):
        self.state = 'confirmed'

    def reject_finance(self):
        self.state = 'rejected'
        if self.prepared_by_user_id:
            activity_type = self.env.ref('mail.mail_activity_data_todo').id
            summary = "Reject Transfer Request"
            if self.invoice:
                summary = "Reject '" + str(self.invoice) + "' Transfer Request"
            
            activity_obj = self.env['mail.activity']
            model_id = self.env['ir.model'].sudo().search([('model', '=', 'request.open.balance.finance')]).id
            activity_obj.create({'activity_type_id': activity_type,
                               'res_model': 'request.open.balance.finance', 'res_id': self.id,
                               'res_model_id':model_id,
                               'summary': summary, 'user_id': self.prepared_by_user_id.id})

    def action_schedule_transfers(self):
        payment_obj = self.env['account.payment']
        today = datetime.today().date()
        data = {}
        for rec in self:
            if rec.state == 'approved' and rec.bank_account_id:
                bank_acc = rec.bank_account_id
                if bank_acc not in data.keys():
                    data.update({
                        bank_acc: [rec]
                    })
                else:
                    data.update({
                        bank_acc: data.get(bank_acc) + [rec]
                    })
        for acc, rec_list in data.items():
            dest_acc = {}
            for rec in rec_list:
                if rec.desti_bank_account_id:
                    dest_bank_acc = rec.desti_bank_account_id
                    if dest_bank_acc not in dest_acc.keys():
                        dest_acc.update({
                            dest_bank_acc: [rec]
                        })
                    else:
                        dest_acc.update({
                            dest_bank_acc: dest_acc.get(dest_bank_acc) + [rec]
                        })
            for dest_acc, rec_list in dest_acc.items():
                amt = 0
                for rec in rec_list:
                    amt += rec.amount
                dep_id = False
                sub_dep_id = False
                payment_date = fields.Date().today()
                if rec_list:
                    dep_id = rec_list[0].dependency_id and rec_list[
                        0].dependency_id.id or False
                    sub_dep_id = rec_list[0].sub_dependency_id and rec_list[
                        0].sub_dependency_id.id or False
                    payment_date = rec_list[0].date_required
                    
                payment = payment_obj.create({
                    'payment_type': 'transfer',
                    'amount': amt,
                    'journal_id': acc.id,
                    'destination_journal_id': dest_acc.id,
                    'payment_date': today,
                    'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
                    'dependancy_id': dep_id,
                    'sub_dependancy_id': sub_dep_id,
                    'payment_date':payment_date,
                })
                if payment:
                    for rec in rec_list:
                        rec.payment_ids = [(4, payment.id)]
                        rec.state = 'sent'


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def post(self):
        res = super(AccountPayment, self).post()
        finance_req_obj = self.env['request.open.balance.finance']
        for payment in self:
            #================Validate the request payments====================#
            for inv in payment.invoice_ids.filtered(lambda x:x.is_project_payment or x.is_payment_request and x.invoice_payment_state=='paid' and x.folio):
                pay_req_ids = self.env['payment.request'].search([('counter_receipt_sheet','=',inv.folio),('state','=','requested')])
                for pay_req in pay_req_ids:
                    pay_req.action_paid()
            #========================END=========================#
            finance_reqs = finance_req_obj.search(
                [('payment_ids', 'in', payment.id)])
            for fin_req in finance_reqs:
                fin_req.confirmed_finance()
                if fin_req.request_id:
                    fin_req.request_id.state = 'done'
                    if fin_req.request_id.balance_req_id:
                        print ("=======",fin_req.request_id.balance_req_id)
                        balance_req = fin_req.request_id.balance_req_id
                        balance_req.action_confirmed()
                        #balance_req.state = 'confirmed'
                        if balance_req.bases_collaboration_id:
                            if balance_req.type_of_operation == 'withdrawal_cancellation':
                                balance_req.bases_collaboration_id.available_bal = 0
                                balance_req.bases_collaboration_id.state = 'cancelled'
                            elif balance_req.type_of_operation == 'withdrawal':
                                balance_req.bases_collaboration_id.available_bal = 0
                                balance_req.bases_collaboration_id.state = 'cancelled'
                            elif balance_req.type_of_operation == 'retirement':
                                balance_req.create_payment_request = True
                                balance_req.bases_collaboration_id.available_bal -= fin_req.amount
                            else:
                                balance_req.bases_collaboration_id.available_bal += fin_req.amount

#                         if balance_req.trust_id:
#                             if balance_req.type_of_operation == 'withdrawal_cancellation':
#                                 balance_req.trust_id.available_bal = 0
#                                 balance_req.trust_id.action_set_cancel()
#                             elif balance_req.type_of_operation == 'withdrawal':
#                                 balance_req.trust_id.available_bal = 0
#                                 balance_req.trust_id.action_set_cancel()
#                             elif balance_req.type_of_operation == 'retirement':
#                                 balance_req.create_payment_request = True
#                                 balance_req.trust_id.available_bal -= fin_req.amount
#                             else:
#                                 balance_req.trust_id.available_bal += fin_req.amount

                        if balance_req.patrimonial_resources_id:
                            if balance_req.type_of_operation == 'withdrawal_cancellation':
                                balance_req.patrimonial_resources_id.available_bal = 0
                                balance_req.patrimonial_resources_id.action_set_cancel()
                            elif balance_req.type_of_operation == 'withdrawal':
                                balance_req.patrimonial_resources_id.available_bal = 0
                                balance_req.patrimonial_resources_id.action_set_cancel()
                            elif balance_req.type_of_operation == 'retirement':
                                balance_req.create_payment_request = True
                                balance_req.patrimonial_resources_id.available_bal -= fin_req.amount
                            else:
                                balance_req.patrimonial_resources_id.available_bal += fin_req.amount

        return res


class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    collaboration_id = fields.Many2one('bases.collaboration')
    patrimonial_id = fields.Many2one(
        'patrimonial.resources', 'Patrimonial Resources')
    request_id = fields.Many2one('request.open.balance', 'Operation Request')

class PeriodsClosing(models.Model):

    _name = 'periods.closing'
    _description = "Closing Period"

    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    collaboration_id = fields.Many2one('bases.collaboration')
