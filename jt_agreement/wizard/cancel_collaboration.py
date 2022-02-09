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

class CancelCollaboration(models.TransientModel):
    _name = 'cancel.collaboration'
    _description = "Cancel Collaboration"

    cancel_date = fields.Date("Cancellation date")
    supporing_doc = fields.Binary("Supporting Documentation")
    reason_cancel = fields.Text("Reason for Cancellations")

    def confirm(self):
        context = self.env.context
        active_model = context.get('active_model')
        active_id = context.get('active_id')
        rec = self.env[active_model].browse(active_id)
        if rec:
            rec.cancel_date = self.cancel_date
            rec.supporing_doc = self.supporing_doc
            rec.reason_cancel = self.reason_cancel
            
            self.env['request.open.balance'].create({
                'bases_collaboration_id': rec.id,
                'is_cancel_collaboration': True,
                'apply_to_basis_collaboration': True,
                'opening_balance': rec.available_bal,
                'agreement_number': rec.convention_no,
                'type_of_operation': 'withdrawal_cancellation',
                'name': rec.name,
                'cbc_format': rec.cbc_format,
                'supporting_documentation': rec.cbc_format,
                'cbc_shipping_office': rec.cbc_shipping_office,
                'liability_account_id': rec.liability_account_id.id if rec.liability_account_id
                else False,
                'interest_account_id': rec.interest_account_id.id if rec.interest_account_id
                else False,
                'investment_account_id': rec.investment_account_id.id if rec.investment_account_id
                else False,
                'availability_account_id': rec.availability_account_id.id if rec.availability_account_id
                else False
            })
            rec.state = 'to_be_cancelled'
