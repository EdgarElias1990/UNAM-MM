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

class ReasonRejection(models.TransientModel):
    _name = 'reason.rejection.open.bal'
    _description = "Reason Rejection of Open Balance"

    name = fields.Text("Reason Rejection")

    def reject(self):
        context = self.env.context
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        recs = self.env[active_model].browse(active_ids)
        if active_model == 'request.open.balance.finance':
            for rec in recs:
                rec.reason_rejection = self.name
                rec.reject_finance()
                if rec.request_id:
                    rec.request_id.state = 'rejected'
                    rec.request_id.reason_rejection = self.name
                    if rec.request_id.type_of_operation != 'withdrawal_cancellation':
                        if rec.request_id.balance_req_id:
                            rec.request_id.balance_req_id.state = 'rejected'
                            rec.request_id.balance_req_id.reason_rejection = self.name
        elif active_model == 'request.open.balance.invest':
            for rec in recs:
                rec.state = 'rejected'
                rec.reason_rejection = self.name
                if rec.balance_req_id:
                    rec.balance_req_id.state = 'rejected'
                    rec.balance_req_id.reason_rejection = self.name
                    
#                     if rec.balance_req_id.type_of_operation in ('increase', 'retirement', 'withdrawal_cancellation'):
#                         rec.balance_req_id.state = 'canceled'
#                         rec.balance_req_id.reason_rejection = self.name
#                     else:
#                         rec.balance_req_id.state = 'rejected'
#                         rec.balance_req_id.reason_rejection = self.name
          

