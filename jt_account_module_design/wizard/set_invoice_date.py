from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError

class ConfirmPaymentTerms(models.TransientModel):
    _name = 'confirm.invoice.date'
    _description = 'Set Payment Terms'

    invoice_date_due = fields.Date('Payment Terms',default=fields.Date.context_today)
    invoice_ids = fields.Many2many('account.move')



    def action_invoice_date(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return ''

        for payment in self.env['account.move'].browse(active_ids):
            if payment.payment_state not in ('registered','draft','approved_payment','for_payment_procedure '):
                raise UserError(_("You can set the Invoice date  only for those payments which are in "
                "'Draft,registered,For Payment Procedure and Approved Payment'!"))
        

        
        return {
            'name': _('Set Payment Terms'),
            'res_model': 'confirm.invoice.date',
            'view_mode': 'form',
            'view_id': self.env.ref('jt_account_module_design.view_confirm_payment_term_wizard').id,
            'context': {'default_invoice_ids':[(6,0,active_ids)]},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }    


    def set_payment_terms(self):
        for inv in self.invoice_ids:
            if inv.payment_state not in ('draft','registered','for_payment_procedure','approved_payment'):
                raise UserError(_("You can set the Invoice date  only for those payments which are in "
                "'Draft and For Payment Procedure'!"))
            if inv:
                inv.invoice_date_due = self.invoice_date_due
                
