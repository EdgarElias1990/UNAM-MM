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

class CancelPatrimonial(models.TransientModel):
    
    _name = 'cancel.patrimonial'
    _description = "Cancel Patrimonial"

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
            rec.in_force()
            self.env['request.open.balance'].create({
                'patrimonial_resources_id' : rec.id,
                'is_cancel_collaboration': True,
                'apply_to_basis_collaboration': True,
                'opening_balance': rec.available_bal,
                'type_of_operation': 'withdrawal_cancellation',
                'name': rec.name,
                'patrimonial_equity_account_id': rec.patrimonial_equity_account_id and  rec.patrimonial_equity_account_id.id or False,
                'liability_account_id': rec.patrimonial_liability_account_id and rec.patrimonial_liability_account_id.id or False,
                'patrimonial_yield_account_id': rec.patrimonial_yield_account_id.id and rec.patrimonial_yield_account_id.id or False,
                'trust_agreement_file': rec.fund_registration_file,
                'trust_agreement_file_name': rec.fund_registration_file_name,
                'trust_office_file': rec.fund_office_file,
                'trust_office_file_name': rec.fund_office_file_name,
                'supporting_documentation': rec.fund_registration_file,
                'specifics_project_id': rec.specifics_project_id.id if rec.specifics_project_id else False,
                'background_project_id': rec.background_project_id.id if rec.background_project_id else False,
            })