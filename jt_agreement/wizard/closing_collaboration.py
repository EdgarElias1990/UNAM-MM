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
from datetime import datetime,timedelta

class ClosingCollaboration(models.TransientModel):
    _name = 'closing.collaboration'
    _description = "Closing Collaboration"

    start_date = fields.Date("Start Date of Period")
    end_date = fields.Date("End Date of Period")
    registration_date = fields.Date("Date of registration in the basis")
    
    #====================================
    '''
    and \
                    collab.fund_name_transfer_id.name in ('Special Chairs Faculty of Engineering',
                    'Fund for payment to beneficiaries Special Chairs Faculty of Engineering',
                    'Special Chairs Faculty of Law',
                    'Regulatory Fund Special Chairs Faculty of Law',
                    'Chairs and special general incentives',
                    'Fund for payment to beneficiaries of Chairs and Special General Stimuli',
                    'Extraordinary Chairs Faculty of Law',
                    'Regulatory Fund Extraordinary Chairs Faculty of Law'
                    ):
    '''
    #=================================#

    def confirm(self):
        if not (self.registration_date >= self.start_date and self.registration_date <= self.end_date):
            raise ValidationError(_("You have not selected Registration date between selected period!"))
        active_ids = self._context.get('active_ids')
        collaborations = self.env['bases.collaboration'].browse(active_ids)
        req_obj = self.env['request.open.balance']
        today = datetime.today().date()
        for collab in collaborations.filtered(lambda x:x.state == 'valid' and not x.is_specific):
            if collab.periods_closing_ids.filtered(lambda  x: x.start_date == self.start_date and \
                                                   x.end_date == self.end_date):
                raise ValidationError(_("You can not generate new close collaboration bases with same period!"))
            
            if self.start_date > today or self.end_date > today:
                raise ValidationError(_("You can not generate close collaboration bases with future period!"))
            if not collab.periods_closing_ids.filtered(lambda  x: x.start_date == self.start_date and \
                                                   x.end_date == self.end_date):
                if collab.fund_name_transfer_id and \
                        collab.closing_amt != 0 and collab.available_bal != 0 :
                    if collab.available_bal < collab.closing_amt:
                         raise ValidationError(_("The available balance is less than the withdrawal amount!"))
                    withdrawal_req = req_obj.with_context(call_from_closing=True).create({
                        'bases_collaboration_id': collab.id,
                        'name': collab.name,
                        'opening_balance': collab.closing_amt,
                        'agreement_number' : collab and collab.convention_no or '',
                        'observations': 'Withdrawal by transfer',
                        'type_of_operation': 'withdrawal_closure',
                        'origin_resource_id': self.env.ref('jt_agreement.acc_transfer_fund_origin_res').id,
                        'state': 'confirmed',
                        'apply_to_basis_collaboration':True,
                        'request_date': self.registration_date,
                        'liability_account_id':collab.liability_account_id.id,
                        'investment_account_id':collab.investment_account_id.id,
                        'interest_account_id':collab.interest_account_id.id,
                        'availability_account_id':collab.availability_account_id.id,
                    })
                    collab.available_bal -= collab.closing_amt
                    withdrawal_req.action_confirmed()
                    increase_req = req_obj.with_context(call_from_closing=True).create({
                        'bases_collaboration_id': collab.fund_name_transfer_id.id,
                        'name': collab.fund_name_transfer_id.name,
                        'opening_balance': collab.closing_amt,
                        'observations': 'Deposit by transfer',
                        'agreement_number' : collab.fund_name_transfer_id and collab.fund_name_transfer_id.convention_no or '',
                        'type_of_operation': 'increase_by_closing',
                        'origin_resource_id': self.env.ref('jt_agreement.acc_transfer_fund_origin_res').id,
                        'state': 'confirmed',
                        'apply_to_basis_collaboration':True,
                        'request_date': self.registration_date,
                        'liability_account_id':collab.liability_account_id.id,
                        'investment_account_id':collab.investment_account_id.id,
                        'interest_account_id':collab.interest_account_id.id,
                        'availability_account_id':collab.availability_account_id.id,
                    })
                    collab.fund_name_transfer_id.available_bal += collab.closing_amt
                    increase_req.action_confirmed()
                    collab.periods_closing_ids = [(0, 0, {
                        'start_date': self.start_date,
                        'end_date': self.end_date
                    })]
