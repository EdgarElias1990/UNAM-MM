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
from odoo import models, fields,_
from odoo.exceptions import UserError, ValidationError

class PaymentDeclined(models.TransientModel):

    _name = 'payment.declined.wizard'
    _description = 'Payment Declined'
    
    reason_for_rejection = fields.Text('Reason For Rejection')
    reason_for_cancel = fields.Text('Reason For Cancellation')
    payment_ids = fields.Many2many('account.payment','account_payment_delinced_wizard_rel','dec_id','payment_id','Payments')
    is_reject = fields.Boolean('Reject',default=False)
    is_cancel = fields.Boolean('Cancel',default=False)
    
    def action_payment_declined(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return ''
        for payment in self.env['account.payment'].browse(active_ids):
            if payment.payment_state != 'for_payment_procedure':
                raise UserError(_("You can Reject only for those payments which are in "
                "'For Payment Procedure'!"))
        
        return {
            'name': _('Payment Declined'),
            'res_model': 'payment.declined.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('jt_supplier_payment.view_payment_declined_wizard').id,
            'context': {'default_payment_ids':[(6,0,active_ids)],'default_is_reject':True},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }    

    def action_payment_cancel(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return ''
        
        return {
            'name': _('Cancel'),
            'res_model': 'payment.declined.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('jt_supplier_payment.view_payment_declined_wizard').id,
            'context': {'default_payment_ids':[(6,0,active_ids)],'default_is_cancel':True},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }    

    def action_reject(self):
        for payment in self.payment_ids:
            if payment.state in ('cancelled','reconciled'):
                raise UserError(_("You can not reject Cancelled or Reconciled payment"))
            if payment.invoice_ids:
                payment.invoice_ids.button_draft()
                payment.invoice_ids.write({'payment_state': 'payment_not_applied','reason_rejection':self.reason_for_rejection})
                payment.invoice_ids.button_cancel()
                
            if payment.state == 'posted':
                payment.action_draft()
            payment.reason_for_rejection = self.reason_for_rejection
            payment.with_context(call_from_reject=True).cancel()
            payment.write({'payment_state': 'rejected'})
            
            
    def action_cancel(self):
        for payment in self.payment_ids:
            if payment.state in ('cancelled','reconciled'):
                raise UserError(_("You can not reject Cancelled or Reconciled payment"))
            if payment.invoice_ids:
                payment.invoice_ids.button_draft()
                payment.invoice_ids.write({'payment_state': 'cancel','reason_cancellation':self.reason_for_cancel})
                payment.invoice_ids.button_cancel()
                
            if payment.state == 'posted':
                payment.action_draft()
                
            payment.reason_for_cancel = self.reason_for_cancel
            payment.cancel()

            if payment.payment_request_id:
                payment.payment_request_id.payment_state = 'cancel'
    
    
    
    