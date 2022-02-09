from odoo import models, fields, api, _

class RescheduleRequest(models.TransientModel):

    _name = 'reschedule.request'
    _description = "Reschedule Request"

    payment_bank_id = fields.Many2one('res.bank', string="Bank of receipt of payment")
    payment_bank_account_id = fields.Many2one('res.partner.bank', string="Payment Receipt bank account")
    l10n_mx_edi_payment_method_id = fields.Many2one('l10n_mx_edi.payment.method', string="Payment Method")

    def reshedule_request(self):
        moves = self.env['account.move'].browse(self._context.get('active_ids'))
        for move in moves:
            move.payment_bank_id = self.payment_bank_id.id
            move.payment_bank_account_id = self.payment_bank_account_id.id
            move.l10n_mx_edi_payment_method_id = self.l10n_mx_edi_payment_method_id.id
            move.is_from_reschedule_payment = True
            move.payment_issuing_bank_id = False
            move.batch_folio = 0
            conac_move = move.line_ids.filtered(lambda x: x.conac_move)
            conac_move.sudo().unlink()
            for line in move.line_ids:
                line.coa_conac_id = False
            #move.payment_state = 'for_payment_procedure'
            move.payment_state = 'approved_payment'
            move.add_budget_available_amount()
