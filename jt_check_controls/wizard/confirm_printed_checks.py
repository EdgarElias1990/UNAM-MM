from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
from click.core import batch

class ConfirmPrintedCheck(models.TransientModel):
    _name = 'confirm.printed.check'
    _description = 'Confirm Printed Check'

    payment_req_ids = fields.One2many('confirm.check.payment.req', "confirm_id", "Check Payment Requests")
    is_cancel_req = fields.Boolean("Is Cancel Request?")
    supplier_batch_id = fields.Many2one('payment.batch.supplier')
    batch_ids = fields.Many2many("payment.batch.supplier",'rel_payment_batch_confirm_print_check','wizard_id','batch_id')
    
            
    def action_yes(self):
        batch = self.supplier_batch_id
        today_date = datetime.today().date()
        for batch in self.batch_ids:
            lines = self.env['check.payment.req']
            for line in batch.payment_req_ids:
                if line.selected and line.check_status == 'Available for printing' and line.check_folio_id:
                    lines += line
                    line.check_folio_id.status = 'Printed'
                    line.check_folio_id.date_printing = today_date
                    line.payment_req_id.payment_state = 'assigned_payment_method'
                    line.selected = False
            if lines:
                batch.create_check_printing_entry(batch,lines)        
            batch.printed_checks = False
            batch.selected = False

    def action_no(self):
        self.is_cancel_req = True
        return {
            'name': _('Select Incorrect Check'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'confirm.printed.check',
            'domain': [],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id
        }

    def action_apply(self):
        batch = self.supplier_batch_id
        today_date = datetime.today().date()
        if self.batch_ids:
            cancel_folio = []
            for line in self.payment_req_ids:
                if line.selected:
                    cancel_folio.append(line.check_folio_id.id)
            for batch in self.batch_ids:
                for line in batch.payment_req_ids.filtered(lambda x:x.selected):
                    if line.check_folio_id.id not in cancel_folio:
                        line.check_folio_id.status = 'Printed'
                        line.check_folio_id.date_printing = today_date
                        if line.payment_req_id and line.payment_req_id.check_folio_id:
                            line.payment_req_id.payment_state = 'assigned_payment_method'
                        line.selected = False
                    else:
                        line.check_folio_id.write({'status':'Cancelled','reason_cancellation':_('Error de Impresión'),'is_cancel_from_print_incorrect':True})
    #                     line.check_folio_id.status = 'Cancelled'
    #                     line.check_folio_id.reason_cancellation = 'Print Error'
                        line.selected = False
                batch.printed_checks = False
                batch.selected = False

class CheckPaymentRequests(models.TransientModel):

    _name = 'confirm.check.payment.req'
    _description = "Check Payment Request"

    confirm_id = fields.Many2one('confirm.printed.check')
    check_folio_id = fields.Many2one('check.log',"Check Folio")
    payment_id = fields.Many2one('account.payment')
    payment_req_id = fields.Many2one('account.move')
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.user.company_id.currency_id, string="Currency")
    amount_to_pay = fields.Monetary("Amount to Pay", currency_field='currency_id')
    selected = fields.Boolean("Select")
    check_status = fields.Selection([('Checkbook registration', 'Checkbook registration'),
                          ('Assigned for shipping', 'Assigned for shipping'),
                          ('Available for printing', 'Available for printing'),
                          ('Printed', 'Printed'), ('Delivered', 'Delivered'),
                          ('In transit', 'In transit'), ('Sent to protection','Sent to protection'),
                          ('Protected and in transit','Protected and in transit'),
                          ('Protected', 'Protected'), ('Detained','Detained'),
                          ('Withdrawn from circulation','Withdrawn from circulation'),
                          ('Cancelled', 'Cancelled'),
                          ('Canceled in custody of Finance', 'Canceled in custody of Finance'),
                          ('On file','On file'),('Destroyed','Destroyed'),
                          ('Reissued', 'Reissued'),('Charged','Charged')], related='check_folio_id.status', store=True)

