from odoo import fields, models, api, _
from datetime import datetime

class CancelAvailableCheck(models.TransientModel):
    _name = 'cancel.available.check'
    _description = 'Cancel Available Check'

    check_folio_ids = fields.Many2many('check.log',string="Check number")
    reason_cancellation = fields.Text(string='Reason Cancellation')
    is_physical_check = fields.Boolean(string="Do you have the physical check?",copy=False,default=False)
    
    def apply(self):
        total_checks = 0
        for folio in self.check_folio_ids:
            folio.reason_cancellation = self.reason_cancellation
            folio.is_physical_check = self.is_physical_check
            folio.general_status = 'cancelled'
            if self.is_physical_check:
                folio.status = 'Canceled in custody of Finance'
                total_checks = total_checks + 1
            else:
                folio.status = 'Cancelled'
                folio.date_cancellation = datetime.now().today()

        if self.is_physical_check:
            lines_vals = []
            for line in self.check_folio_ids:
                
                lines_vals.append({
                    'check_log_id': line.id if line else False,
                    'dependency_id': line.dependence_id.id if line.dependence_id else False,
            })

            send_checks = self.env['send.checks']
            folio = self.env['ir.sequence'].next_by_code('batch.folio')
            send_checks.create({
            'batch_folio': folio,
            'status':'draft',
            'total_checks': total_checks,
            'date': datetime.today().date(),
            'check_line_ids': [(0, 0, val) for val in lines_vals]
            })

