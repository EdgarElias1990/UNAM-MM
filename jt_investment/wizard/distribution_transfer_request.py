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
from odoo.exceptions import UserError,ValidationError,UserError
from datetime import datetime

class DistributionTransferRequest(models.TransientModel):
    _name = 'distribution.transfer.request'
    _description = "Distribution Transfer Request"

    bank_account_id = fields.Many2one('account.journal', "Bank and Origin Account")
    desti_bank_account_id = fields.Many2one('account.journal', "Destination Bank and Account")
    amount = fields.Float("Amount To Transfer")
    date = fields.Date("Application date")
    concept = fields.Text("Application Concept")
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id, string="Applicant")
    line_ids = fields.One2many('distribution.transfer.request.line','wizard_id')
    destination_investment_id = fields.Many2one('investment.investment', "Destination Investment")
    distribution_income_id = fields.Many2one('distribution.of.income','Distribution Income')
    
#     @api.onchange('bank_account_id')
#     def onchange_bank_account_id(self):
#         self.line_ids = False
#         opt_lines = []    
#         if self.env.context and self.env.context.get('active_id') and self.env.context.get('active_model')=='investment.investment':
#             inv_id = self.env['investment.investment'].browse(self.env.context.get('active_id'))
#             
#             fund_ids = inv_id.line_ids.mapped('investment_fund_id')
#             opt_lines = []
#             for fund in fund_ids:
#                 base_ids = inv_id.line_ids.filtered(lambda x:x.bank_account_id.id == self.bank_account_id.id and x.investment_fund_id.id==fund.id).mapped('base_collabaration_id')
#                 for base in base_ids:
#                     lines = inv_id.line_ids.filtered(lambda x:x.bank_account_id.id == self.bank_account_id.id and x.investment_fund_id.id==fund.id and x.base_collabaration_id.id == base.id and x.line_state == 'done')
#                     inc = sum(a.amount for a in lines.filtered(lambda x:x.type_of_operation in ('open_bal','increase')))
#                     ret = sum(a.amount for a in lines.filtered(lambda x:x.type_of_operation in ('retirement','withdrawal','withdrawal_cancellation','withdrawal_closure','increase_by_closing')))
#                     balance = inc - ret
#                     if balance > 0:
#                         opt_lines.append((0,0,{'opt_line_ids':[(6,0,lines.ids)],'investment_fund_id':fund.id,'base_collabaration_id':base.id,'agreement_number':base.convention_no,'amount':balance}))
#     
#                 lines = inv_id.line_ids.filtered(lambda x:x.bank_account_id.id == self.bank_account_id.id and x.investment_fund_id.id==fund.id and not x.base_collabaration_id and x.line_state == 'done')
#                 inc = sum(a.amount for a in lines.filtered(lambda x:x.type_of_operation in ('open_bal','increase')))
#                 ret = sum(a.amount for a in lines.filtered(lambda x:x.type_of_operation in ('retirement','withdrawal','withdrawal_cancellation','withdrawal_closure','increase_by_closing')))
#                 balance = inc - ret
#                 if balance > 0:
#                     opt_lines.append((0,0,{'opt_line_ids':[(6,0,lines.ids)],'investment_fund_id':fund.id,'amount':balance}))
#         self.line_ids = opt_lines
               
    def approve(self):
#         line_amount = sum(x.amount_to_transfer for x in self.line_ids.filtered(lambda a:a.check))
#         if line_amount != self.amount:
#             raise UserError(_('Sum of amount in line is not equal to header amount'))
        opt_lines = []
        inv_opt_lines = []
        for line in self.line_ids.filtered(lambda a:a.check):
            opt_lines.append((0,0,{'investment_fund_id':line.investment_fund_id and line.investment_fund_id.id or False,
                                   'base_collabaration_id' : line.base_collabaration_id and line.base_collabaration_id.id or False,
                                   'agreement_number': line.agreement_number,
                                   'amount_to_transfer' : line.amount_to_transfer,
                                   'amount' : line.amount,
                                   #'opt_line_ids' : line.opt_line_ids,
                                   }))
            for opt_line in line.opt_line_ids:
                opt_line.is_request_generated = True

        origin_resource_id = self.env.ref('jt_agreement.acc_transfer_fund_origin_res').id if \
            self.env.ref('jt_agreement.acc_transfer_fund_origin_res') else False
        for line in self.line_ids.filtered(lambda a:a.check):
#             self.env['investment.operation'].create({
#                 'investment_id':self.env.context.get('active_id',0),
#                 'agreement_number': line.agreement_number,
#                 'bank_account_id' :  self.bank_account_id.id if self.bank_account_id else False,
#                 'desti_bank_account_id' : self.desti_bank_account_id.id if self.desti_bank_account_id else False,
#                 'amount' : line.amount_to_transfer,
#                 'investment_fund_id' : line.investment_fund_id and line.investment_fund_id.id or False,
#                 'type_of_operation':'retirement',
#                 'line_state' : 'done',
#                 'base_collabaration_id' : line.base_collabaration_id and line.base_collabaration_id.id or False,
#                 'fund_type': line.base_collabaration_id.fund_type_id.id if line.base_collabaration_id and \
#                         line.base_collabaration_id.fund_type_id else False,
#                 'agreement_type_id': line.base_collabaration_id.agreement_type_id.id if \
#                        line.base_collabaration_id and line.base_collabaration_id.agreement_type_id else False,
#                 'dependency_id': line.base_collabaration_id.dependency_id.id if \
#                     line.base_collabaration_id and line.base_collabaration_id.dependency_id else False,
#                 'sub_dependency_id': line.base_collabaration_id.subdependency_id.id if \
#                     line.base_collabaration_id and line.base_collabaration_id.subdependency_id else False,
#                 'origin_resource_id': origin_resource_id,
#                 'user_id': self.user_id.id if self.user_id else False,
#                 'date_required' : self.date,
#                 })

            if self.date:
                today = self.date
            else:
                today = datetime.today().date()

            interest_rate_base_id = False
            if line.base_collabaration_id:
                interest_rate_base_id = self.env['interest.rate.base'].create({'base_id':line.base_collabaration_id.id,'cuenta':self.bank_account_id.default_debit_account_id.code, 'tipo':'Cargo','interest_rate':line.amount_to_transfer,'interest_date':today})
                interest_rate_base_id = interest_rate_base_id.id


            interest_rate_base_id_c = False
            if line.base_collabaration_id:
                interest_rate_base_id_c = self.env['interest.rate.base'].create(
                    {'base_id': line.base_collabaration_id.id, 'cuenta': self.desti_bank_account_id.default_debit_account_id.code,
                     'tipo':'Abono', 'interest_rate': line.amount_to_transfer, 'interest_date': today})
                interest_rate_base_id_c = interest_rate_base_id_c.id
                
            ot_id=self.env['investment.operation'].create({
                'investment_id': self.destination_investment_id.id,
                'agreement_number': line.agreement_number,
                'bank_account_id' :  self.bank_account_id.id if self.bank_account_id else False,
                'desti_bank_account_id' : self.desti_bank_account_id.id if self.desti_bank_account_id else False,
                'amount' : line.amount_to_transfer,
                'investment_fund_id' : line.investment_fund_id and line.investment_fund_id.id or False,
                'type_of_operation':'increase',
                'line_state' : 'requested',
                'base_collabaration_id' : line.base_collabaration_id and line.base_collabaration_id.id or False,
                'fund_type': line.base_collabaration_id.fund_type_id.id if line.base_collabaration_id and \
                                                              line.base_collabaration_id.fund_type_id else False,
                'agreement_type_id': line.base_collabaration_id.agreement_type_id.id if \
                    line.base_collabaration_id and line.base_collabaration_id.agreement_type_id else False,
                'dependency_id': line.base_collabaration_id.dependency_id.id if line.base_collabaration_id and \
                            line.base_collabaration_id.dependency_id else False,
                'sub_dependency_id': line.base_collabaration_id.subdependency_id.id if \
                   line.base_collabaration_id and line.base_collabaration_id.subdependency_id else False,
                'origin_resource_id': origin_resource_id,
                'user_id': self.user_id.id if self.user_id else False,
                'date_required' : self.date,
                'distribution_income_id' : self.distribution_income_id and self.distribution_income_id.id or False,
                'interest_rate_base_id' : interest_rate_base_id,
                })
            inv_opt_lines.append(ot_id.id)
                 
                 
        self.env['request.open.balance.finance'].create(
            {
                'bank_account_id': self.bank_account_id.id if self.bank_account_id else False,
                'desti_bank_account_id': self.desti_bank_account_id.id if self.desti_bank_account_id else False,
                'amount': self.amount,
                'date': self.date,
                'date_required':self.date,
                'concept': self.concept,
                'state': 'requested',
                'line_opt_ids' : opt_lines,
                'investment_operation_ids' : [(6,0,inv_opt_lines)],
                'from_opt_transfer' : True,
                'distribution_income_id' : self.distribution_income_id and self.distribution_income_id.id or False,
                'trasnfer_request':'investments',
            }
        )
        self.distribution_income_id.action_requested()
        
class DistributionTransferRequestLine(models.TransientModel):
    _name = 'distribution.transfer.request.line'
    _description = "Distribution Transfer Request Line"

    wizard_id = fields.Many2one('distribution.transfer.request')
    investment_fund_id = fields.Many2one('investment.funds','Fund')
    base_collabaration_id = fields.Many2one('bases.collaboration','Name Of Agreements')
    agreement_number = fields.Char("Agreement Number")
    amount = fields.Float("Amount")
    amount_to_transfer = fields.Float("Amount")
    check = fields.Boolean('Transfer')
    opt_line_ids = fields.Many2many('distribution.of.income.calculation','des_cal_operation_wizard_line','opt_id','line_id')

    @api.onchange('amount_to_transfer')
    def onchange_amount_to_transfer(self):
        if self.amount_to_transfer > self.amount:
            self.amount_to_transfer = 0
            return {'warning': {'title': _("Warning"), 'message': 'Not Enough Balance'}}
            
