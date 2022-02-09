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
    _inherit = 'approve.investment.bal.req'

    investment_id = fields.Many2one('investment.investment', 'First Number:')

    journal_id = fields.Many2one(related='investment_id.journal_id')
    source_ids = fields.Many2many('account.journal', 'rel_journal_inv_src_approve',
                                  'journal_id', 'opt_id', compute="get_journal_ids")
    dest_ids = fields.Many2many('account.journal', 'rel_journal_inv_dest_approve',
                                'journal_id', 'opt_id', compute="get_journal_ids")
    investment_avl_ids = fields.Many2many(
        'investment.investment', 'rel_investment_inv_approve', 'inv_id', 'opt_id', compute="get_inv_ids")
    msg = fields.Char("Message")

    @api.onchange('investment_id', 'type_of_operation')
    def onchange_check_balance(self):
        if self.type_of_operation and self.type_of_operation in ('open_bal', 'increase'):
            self.is_balance = True
        elif not self.is_agr:
            self.is_balance = True
        else:
            self.is_balance = False

    def validate_balance(self):
        if self.investment_id and self.base_collabaration_id:
            opt_lines = self.env['investment.operation'].search([('investment_id', '=', self.investment_id.id),
                                                ('line_state', '=', 'done'), '|',
                                                ('investment_fund_id', '=', self.investment_fund_id.id),
                                                ('base_collabaration_id', '=', self.base_collabaration_id.id)])
            inc = sum(a.amount for a in opt_lines.filtered(
                lambda x: x.type_of_operation in ('open_bal', 'increase')))
            ret = sum(a.amount for a in opt_lines.filtered(lambda x: x.type_of_operation in (
                'retirement', 'withdrawal', 'withdrawal_cancellation', 'withdrawal_closure', 'increase_by_closing')))
            balance = inc - ret
            if balance >= self.amount:
                self.is_balance = True
            else:
                self.is_balance = False
                self.msg = "Available balance is not enough"
        elif self.investment_id and self.patrimonial_id:
            opt_lines = self.env['investment.operation'].search([('investment_id', '=', self.investment_id.id),
                    ('line_state', '=', 'done'), '|', ('investment_fund_id', '=', self.investment_fund_id.id),
                    ('patrimonial_id', '=', self.patrimonial_id.id)])
            inc = sum(a.amount for a in opt_lines.filtered(
                lambda x: x.type_of_operation in ('open_bal', 'increase')))
            ret = sum(a.amount for a in opt_lines.filtered(lambda x: x.type_of_operation in (
                'retirement', 'withdrawal', 'withdrawal_cancellation', 'withdrawal_closure', 'increase_by_closing')))
            balance = inc - ret
            if balance >= self.amount:
                self.is_balance = True
            else:
                self.is_balance = False
                self.msg = "Available balance is not enough"
        else:
            self.is_balance = False
            self.msg = "Available balance is not enough"
        return {
            'name': 'Approve Request',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'approve.investment.bal.req',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
            'context': self.env.context,
        }

    @api.onchange('base_collabaration_id')
    def onchange_base_collabaration_investment(self):
        self.investment_id = False

    @api.onchange('patrimonial_id')
    def onchange_patrimonial_inv_id(self):
        if self.patrimonial_id:
            if self.type_of_operation and self.type_of_operation in ('retirement', 'withdrawal', 'withdrawal_cancellation'):
                inv_ids = []
                opt_lines = self.env['investment.operation'].search([('type_of_operation', 'in',
                        ('open_bal', 'increase')), ('patrimonial_id', '=', self.patrimonial_id.id),
                                                                     ('line_state', '=', 'done')])
                if opt_lines:
                    exist_inv_ids = opt_lines.mapped('investment_id')
                    inv_ids = exist_inv_ids.ids
            else:
                inv_ids = self.env['investment.investment'].search([('state', '=', 'confirmed')]).ids
            return {'domain': {'investment_id': [('id', 'in', inv_ids)]}}

    @api.depends('base_collabaration_id', 'type_of_operation')
    def get_inv_ids(self):
        for rec in self:
            if rec.type_of_operation and rec.base_collabaration_id and rec.type_of_operation in ('retirement', 'withdrawal', 'withdrawal_cancellation'):
                inv_ids = []
                opt_lines = self.env['investment.operation'].search([('type_of_operation', 'in', ('open_bal', 'increase')), (
                    'base_collabaration_id', '=', rec.base_collabaration_id.id), ('line_state', '=', 'done')])
                if opt_lines:
                    exist_inv_ids = opt_lines.mapped('investment_id')
                    inv_ids = exist_inv_ids.ids
                rec.investment_avl_ids = [(6, 0, inv_ids)]
            else:
                rec.investment_avl_ids = [(6, 0, self.env['investment.investment'].search([
                                           ('state', '=', 'confirmed')]).ids)]

    @api.depends('journal_id', 'type_of_operation', 'investment_id.journal_id', 'investment_id')
    def get_journal_ids(self):
        for rec in self:
            if rec.type_of_operation in ('open_bal', 'increase', 'increase_by_closing'):
                rec.dest_ids = [(6, 0, rec.journal_id.ids)]
            else:
                rec.dest_ids = [
                    (6, 0, self.env['account.journal'].search([('type', '=', 'bank')]).ids)]

            if rec.type_of_operation in ('retirement', 'withdrawal', 'withdrawal_cancellation', 'withdrawal_closure'):
                rec.source_ids = [(6, 0, rec.journal_id.ids)]
            else:
                rec.source_ids = [
                    (6, 0, self.env['account.journal'].search([('type', '=', 'bank')]).ids)]

    def get_open_balance_vals(self, request):
        vals = super(ApproveInvestmentBalReq,
                     self).get_open_balance_vals(request)
        vals.update(
            {'investment_link_id': self.investment_id and self.investment_id.id or False})
        return vals

    def get_investment_line(self, request):
        vals = {
            'investment_id': self.investment_id and self.investment_id.id or False,
            'invoice': self.invoice,
            'operation_number': self.operation_number,
            'agreement_number': self.agreement_number,
            'amount': self.amount,
            'dependency_id': self.dependency_id and self.dependency_id.id or False,
            'sub_dependency_id': self.sub_dependency_id and self.sub_dependency_id.id or False,
            'user_id': self.user_id and self.user_id.id or False,
            'unit_req_transfer_id': self.unit_req_transfer_id and self.unit_req_transfer_id.id or False,
            'date_required': self.date_required,
            'fund_type': self.fund_type and self.fund_type.id or False,
            'agreement_type_id': self.agreement_type_id and self.agreement_type_id.id or False,
            'base_collabaration_id': self.base_collabaration_id and self.base_collabaration_id.id or False,
            'patrimonial_id': self.patrimonial_id and self.patrimonial_id.id or False,
            'investment_fund_id': self.investment_fund_id and self.investment_fund_id.id or False,
            'inc_id': request.id,
            'type_of_operation': self.type_of_operation,
            'origin_resource_id': self.origin_resource_id and self.origin_resource_id.id or False,
            'bank_account_id': self.bank_account_id and self.bank_account_id.id or False,
            'desti_bank_account_id': self.desti_bank_account_id and self.desti_bank_account_id.id or False,
            'line_state': 'requested',
            'record_type': 'automatically'
        }
        return vals

    def create_investment_line(self, request):
        vals = self.get_investment_line(request)
        opt_id = self.env['investment.operation'].create(vals)
        return opt_id

    def approve(self):
        res = super(ApproveInvestmentBalReq, self).approve()
        request = self.env['request.open.balance.invest'].browse(
            self.env.context.get('active_id'))
        if request:
            request.finance_investment_id = self.investment_id and self.investment_id.id or False
            request.finance_investment_fund_id = self.investment_fund_id and self.investment_fund_id.id or False
            request.finance_bank_account_id = self.bank_account_id and self.bank_account_id.id or False
            request.finance_date_required = self.date_required
            request.finance_desti_bank_account_id = self.desti_bank_account_id and self.desti_bank_account_id.id or False
               
            if self.investment_id:
                opt_id = self.create_investment_line(request)
                if res:
                    res.investment_operation_id = opt_id.id
        return res
