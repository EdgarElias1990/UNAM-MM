from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError

class ConfirmPaymentDate(models.TransientModel):
    _name = 'confirm.payment.date'
    _description = 'Confirm Payment date'

    payment_date = fields.Date('Payment Date',default=fields.Date.context_today)
    payment_ids = fields.Many2many('account.payment')



    def action_payment_date(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return ''

        for payment in self.env['account.payment'].browse(active_ids):
            if payment.payment_state not in ('for_payment_procedure','draft'):
                raise UserError(_("You can set the payment date  only for those payments which are in "
                "'Draft and For Payment Procedure'!"))
        

        
        return {
            'name': _('Set Payment Date'),
            'res_model': 'confirm.payment.date',
            'view_mode': 'form',
            'view_id': self.env.ref('jt_account_module_design.view_confirm_payment_date_wizard').id,
            'context': {'default_payment_ids':[(6,0,active_ids)]},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }    


    def set_payment_date(self):
        for payment in self.payment_ids:
            if payment.state not in ('draft','for_payment_procedure'):
                raise UserError(_("You can set the payment date  only for those payments which are in "
                "'Draft and For Payment Procedure'!"))
            if payment:
                payment.payment_date = self.payment_date
                