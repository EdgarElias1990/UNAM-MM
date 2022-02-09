from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class BasesCollabration(models.Model):

    _inherit = 'request.open.balance.finance'

    project_request_id = fields.Many2one(
        'request.transfer', 'Project Request Transfer')

    def approve_finance(self):
        result = super(BasesCollabration, self).approve_finance()
        if self.project_request_id:
            self.project_request_id.action_approved()

        return result

    @api.model
    def create(self, vals):
        if vals.get('invoice', 'New') == 'New':
            vals['invoice'] = self.env['ir.sequence'].next_by_code(
                'request.transfer') or 'New'
        result = super(BasesCollabration, self).create(vals)
        return result

    def confirmed_finance(self):
        result = super(BasesCollabration, self).confirmed_finance()
        if self.project_request_id:
            self.project_request_id.confirmed_finance()

        return result

    def reject_finance(self):
        result = super(BasesCollabration, self).reject_finance()
        if self.project_request_id:
            self.project_request_id.reject_finance()
            self.project_request_id.reason_rejection = self.reason_rejection

        return result

    def reset_draft_finance_payment(self):
        result = super(BasesCollabration, self).reset_draft_finance_payment()
        if self.project_request_id:
            self.project_request_id.action_approved()

        return result

    def canceled_finance(self):
        result = super(BasesCollabration, self).canceled_finance()
        if self.project_request_id:
            self.project_request_id.action_canceled()

        return result
