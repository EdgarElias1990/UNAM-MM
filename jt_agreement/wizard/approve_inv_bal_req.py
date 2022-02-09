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


class ApproveInvestmentBalReq(models.TransientModel):
    _name = 'approve.investment.bal.req'
    _description = "Approve Investment Balance request"

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
    date = fields.Date("Application date")
    concept = fields.Text("Application Concept")
    user_id = fields.Many2one(
        'res.users', default=lambda self: self.env.user.id, string="Applicant")
    unit_req_transfer_id = fields.Many2one(
        'dependency', string="Unit requesting the transfer")
    date_required = fields.Date("Date Required")
    fund_type = fields.Many2one('fund.type', "Type Of Fund")
    agreement_type_id = fields.Many2one(
        'agreement.agreement.type', 'Agreement Type')
    fund_id = fields.Many2one('agreement.fund', 'Fund')
    base_collabaration_id = fields.Many2one(
        'bases.collaboration', 'Name Of Agreements')
    investment_fund_id = fields.Many2one('investment.funds', 'Fund')

    type_of_operation = fields.Selection([('open_bal', 'Opening Balance'),
                                          ('increase', 'Increase'),
                                          ('retirement', 'Retirement'),
                                          ('withdrawal', 'Withdrawal for settlement'),
                                          ('withdrawal_cancellation', 'Withdrawal Due to Cancellation')],
                                         string="Type of Operation")
    origin_resource_id = fields.Many2one(
        'sub.origin.resource', "Origin of the resource")
    is_balance = fields.Boolean('Is Balance', default=False)
    trust_id = fields.Many2one('agreement.trust', 'Trust')
    patrimonial_id = fields.Many2one('patrimonial.resources', 'Patrimonial')
    is_agr = fields.Boolean(string='Agreements', default=False)

    @api.onchange('base_collabaration_id')
    def onchange_base_collabaration_id(self):
        if self.base_collabaration_id:
            self.dependency_id = self.base_collabaration_id and self.base_collabaration_id.dependency_id and self.base_collabaration_id.dependency_id.id or False
            self.sub_dependency_id = self.base_collabaration_id and self.base_collabaration_id.subdependency_id and self.base_collabaration_id.subdependency_id.id or False

    @api.onchange('patrimonial_id')
    def onchange_patrimonial_id(self):
        if self.patrimonial_id:
            self.dependency_id = self.patrimonial_id and self.patrimonial_id.dependency_id and self.patrimonial_id.dependency_id.id or False
            self.sub_dependency_id = self.patrimonial_id and self.patrimonial_id.subdependency_id and self.patrimonial_id.subdependency_id.id or False

    @api.model
    def default_get(self, fields):
        res = super(ApproveInvestmentBalReq, self).default_get(fields)
        name = self.env['ir.sequence'].next_by_code('approve.bal.invest')
        res.update({'invoice': name})
        return res

    def get_open_balance_vals(self, request):
        vals = {
            'invoice': self.invoice,
            'operation_number': self.operation_number,
            'agreement_number': self.agreement_number,
            'bank_account_id': self.bank_account_id.id if self.bank_account_id else False,
            'desti_bank_account_id': self.desti_bank_account_id.id if self.desti_bank_account_id else False,
            'amount': self.amount,
            'date': self.date,
            'concept': self.concept,
            'unit_req_transfer_id': self.unit_req_transfer_id.id if self.unit_req_transfer_id else False,
            'date_required': self.date_required,
            'fund_type': self.fund_type.id if self.fund_type else False,
            'agreement_type_id': self.agreement_type_id and self.agreement_type_id.id or False,
            'fund_id': self.fund_id and self.fund_id.id or False,
            'investment_fund_id': self.investment_fund_id and self.investment_fund_id.id or False,
            'base_collabaration_id': self.base_collabaration_id and self.base_collabaration_id.id or False,
            'request_id': request.id,
            'state': 'requested',
            'dependency_id': self.dependency_id and self.dependency_id.id or False,
            'sub_dependency_id': self.sub_dependency_id and self.sub_dependency_id.id or False,
            'trasnfer_request':'investments',
        }
        return vals

    def approve(self):
        request = self.env['request.open.balance.invest'].browse(
            self.env.context.get('active_id'))
        res = False
        if request:
            vals = self.get_open_balance_vals(request)
            if request.is_manually:
                request.state = 'requested'
            else:
                request.state = 'approved'
            res = self.env['request.open.balance.finance'].create(vals)
            if request.balance_req_id:
                request.balance_req_id.state = 'approved'
        return res


class Dependency(models.Model):

    _inherit = 'dependency'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if 'bal_user_id' in self._context:
            user = self.env['res.users'].browse(
                self._context.get('bal_user_id'))
            employees = self.env['hr.employee'].search(
                [('user_id', '=', user.id)])
            dependency_ids = []
            for emp in employees:
                if emp.dependancy_id:
                    dependency_ids.append(emp.dependancy_id.id)
            args = [['id', 'in', dependency_ids]]
        res = super(Dependency, self).name_search(
            name, args=args, operator=operator, limit=limit)
        return res
