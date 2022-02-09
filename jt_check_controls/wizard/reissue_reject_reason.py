from odoo import fields, models, api, _
import datetime
from odoo.exceptions import ValidationError
import base64
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class ReissueRejectReason(models.TransientModel):
    
    _name = 'reissue.reject.reason.wizard'

    reason_rejection = fields.Text("Reason for rejection")
    reissue_checks_id = fields.Many2one('reissue.checks')
    
    def apply(self):
        if self.reissue_checks_id:
            self.reissue_checks_id.reason_rejection = self.reason_rejection
            self.reissue_checks_id.action_set_reject()
        else:
            records_ids = self.env['reissue.checks'].browse(self.env.context.get('active_ids',[]))
            for rec in records_ids:
                rec.reason_rejection =  self.reason_rejection
                rec.action_set_reject()