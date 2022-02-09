from odoo import models, fields, api, _

class RescheduleRequest(models.TransientModel):

    _inherit = 'reschedule.request'
    
    
    def reshedule_request(self):
        moves = self.env['account.move'].browse(self._context.get('active_ids'))
        for move in moves:
            move.payment_bank_id = self.payment_bank_id.id
            move.payment_bank_account_id = self.payment_bank_account_id.id
            move.l10n_mx_edi_payment_method_id = self.l10n_mx_edi_payment_method_id.id
            move.is_from_reschedule_payment = True
            move.payment_issuing_bank_id = False
            for line in move.line_ids:
                line.coa_conac_id = False
            if move.payment_state =='payment_method_cancelled':
                move.action_draft_budget()
                move.payment_state = 'approved_payment'
                move.batch_folio = ''
                if move.related_check_history and move.check_folio_id.folio_ch:
                    move.related_check_history = move.related_check_history+","+move.check_folio_id.folio_ch
                else:    
                    move.related_check_history = move.check_folio_id.folio_ch
                move.related_check_folio_ids =  [(4, move.check_folio_id.id)]
                move.check_folio_id = False
                batch_lines = self.env['check.payment.req'].search([('payment_req_id','=',move.id)])
                for batch in batch_lines:
                    batch.sudo().unlink()
            else:
                conac_move = move.line_ids.filtered(lambda x: x.conac_move and not x.is_for_approved_payment)
                conac_move.sudo().unlink()                
                move.payment_state = 'approved_payment'
                move.batch_folio = ''
                if move.related_check_history and move.check_folio_id.folio_ch:
                    move.related_check_history = move.related_check_history+","+move.check_folio_id.folio_ch
                else:    
                    move.related_check_history = move.check_folio_id.folio_ch
                move.related_check_folio_ids =  [(4, move.check_folio_id.id)]
                move.check_folio_id = False
                move.add_budget_available_amount()
    