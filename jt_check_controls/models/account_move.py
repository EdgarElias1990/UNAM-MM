from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError

class AccounrMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    payment_batch_check_id = fields.Many2one('payment.batch.supplier', "Payment Batch", copy=False)
    check_payment_req_id = fields.Many2one('check.payment.req', "Check Payment Request", copy=False)
    
    
class SupplierPaymentRequest(models.Model):
    _inherit = 'account.move'

    payment_state = fields.Selection(selection_add=[('payment_method_cancelled', 'Payment method cancelled'),
                                                    ('rotated','Rotated'),
                                                    ('assigned_payment_method','Assigned Payment Method')])
    check_folio_id = fields.Many2one('check.log', "Check Sheet", copy=False)
    related_check_folio_ids = fields.Many2many('check.log','rel_move_check_log','check_id','move_id',
                                               string="Related Check Sheets", copy=False)
    related_check_history = fields.Char("Related Check Sheet", copy=False)
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
                          ('Reissued', 'Reissued'),('Charged','Charged')], related='check_folio_id.status',store=True)
    date_printing = fields.Date(related='check_folio_id.date_printing')
    payment_batch_check_id = fields.Many2one('payment.batch.supplier', "Payment Batch", copy=False)
    payment_check_batch_id = fields.Many2one('payment.batch.supplier','Payment Check Batch',copy=False)
    
    def cancel_payment_method(self):
        for payment_req in self:
            if payment_req:
                if payment_req.payment_state == 'assigned_payment_method':
                    payment_ids = self.env['account.payment'].search([('payment_state','=','for_payment_procedure'),
                                                                      ('payment_request_id','=',payment_req.id)])
                    for payment in payment_ids:
                        payment.cancel()
                    if payment_req.check_folio_id:
                        payment_req.check_folio_id.status = 'Cancelled'
                    payment_req.payment_state = 'payment_method_cancelled'
            if payment_req.payment_state == 'rotated' and payment_req.is_payment_request == True:
                payment_req.action_cancel_budget()

    def action_rotated(self):
#         self.ensure_one()
#         self.payment_state = 'registered'
#         self.batch_folio = ''

        return {
            'name': _('Reschedule Request'),
            'view_mode': 'form',
            'view_id': self.env.ref('jt_supplier_payment.reschedule_request_form_view').id,
            'res_model': 'reschedule.request',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

    def write(self, vals):
        res = super(SupplierPaymentRequest, self).write(vals)
        for move in self:
            if vals.get('payment_state') == 'paid' and move.check_folio_id:
                move.check_folio_id.status = 'Charged'
        return res


    @api.depends('name', 'state')
    def name_get(self):
        res = super(SupplierPaymentRequest, self).name_get()
        if self.env.context and self.env.context.get('show_name_and_folio_name', False):
            result = []
            for rec in self:
                if rec.folio:
                    name = ''
                    if rec.name:
                        name = rec.name 
                    name = name + "("+str(rec.folio)+")" or ''
                    result.append((rec.id, name))
                else:
                    result.append(
                        (rec.id, rec._get_move_display_name(show_ref=True)))
            return result and result or res

        elif self.env.context and self.env.context.get('show_folio_name', False):
            result = []
            for rec in self:
                if rec.folio:
                    name = rec.folio
                    result.append((rec.id, name))
                else:
                    result.append(
                        (rec.id, rec._get_move_display_name(show_ref=True)))
            return result and result or res
        
        else:
            return res

    def get_ticket_data(self):
        dependancy_ids = self.mapped('dependancy_id')
        ticket_data = []
        for dep in dependancy_ids:
            sub_inv_ids = self.filtered(lambda x:x.dependancy_id.id==dep.id)
            sub_dep_ids = sub_inv_ids.mapped('sub_dependancy_id')
            for sub in sub_dep_ids:
                inv_ids = self.filtered(lambda x:x.dependancy_id.id==dep.id and x.sub_dependancy_id.id==sub.id)
                dep_name = sub.description
                payment_id = self.env['payment.place'].search([('dependancy_id','=',dep.id),('sub_dependancy_id','=',sub.id)],limit=1)
                clave_no = ''
                if payment_id:
                    clave_no = payment_id.name
                
                    
                folio_min = min(x.check_folio_id.folio for x in inv_ids)
                folio_max = max(x.check_folio_id.folio for x in inv_ids)
                fornight = ''
                if not folio_min:
                    folio_min = ''
                if not folio_max:
                    folio_max = ''
                     
                if inv_ids:
                    bank_id = ''
                    for x in inv_ids:
                        bank_id = x.payment_issuing_bank_id.name
                    fornight_inv_id = inv_ids.filtered(lambda x:x.fornight)
                    if fornight_inv_id:
                        fornight = str(fornight_inv_id[0].fornight)
                        if fornight_inv_id[0].invoice_date:
                            fornight += "/"+str(fornight_inv_id[0].invoice_date.year)
                            
                ticket_data.append({'dep_name':dep_name,'clave_no':clave_no,'folio_min':folio_min,'folio_max':folio_max,'fornight':fornight,'bank_id':bank_id})
                
        return ticket_data
        
class AccountPayment(models.Model):
    _inherit = 'account.payment'

    check_folio_id = fields.Many2one('check.log', "Check Sheet", copy=False, related='payment_request_id.check_folio_id', store=True)
    payment_method_name = fields.Char(related='l10n_mx_edi_payment_method_id.name', store=True)
    
    
    def action_register_payment(self):

        active_ids = self.env.context.get('active_ids')
        record_ids = self.env['account.move'].browse(active_ids)
        for rec in record_ids.filtered(lambda x:x.is_project_payment or x.is_payment_request):
            if rec.check_folio_id and rec.check_folio_id.status not in ('Delivered','Sent to protection','Protected and in transit'):
                raise ValidationError(_('You can only schedule the payment requests that your assigned check is in status “Delivered, Sent to Protection or Protected"'))
        
        res =super(AccountPayment,self).action_register_payment()
        
        active_ids = self.env.context.get('active_ids')
        unico = []
        if active_ids:
            record_ids = self.env['account.move'].browse(active_ids)
            if len(record_ids) != 1:
                bancos = record_ids.mapped('bank_key_name')
                for x in bancos:
                    if x not in unico:
                        unico.append(x)
                    if len(unico) != 1:
                        raise ValidationError(_('No se puede realizar el registro de pago si los bancos son diferentes'))
            record_ids = record_ids.filtered(lambda x:(x.is_project_payment or x.is_payment_request or x.is_payroll_payment_request or x.is_pension_payment_request) and x.is_invoice(include_receipts=True))
            check_folio_ids = record_ids.mapped('check_folio_id')
            #print(check_folio_ids)
            #print(check_folio_ids[0].bank_id.name)
            if check_folio_ids and len(unico)==1:
                ctx = res.get('context',{})
                bank_account_id = check_folio_ids[0].bank_account_id and check_folio_ids[0].bank_account_id.id or False
                if check_folio_ids[0].bank_id:
                    ctx.update({'default_bank_account_id':bank_account_id,'default_check_journal_id':check_folio_ids[0].bank_id.id,'default_journal_id':check_folio_ids[0].bank_id.id,'default_is_bank_check':True})
                    res.update({'context':ctx})

            if check_folio_ids and len(record_ids) == 1:
                ctx = res.get('context',{})
                bank_account_id = check_folio_ids[0].bank_account_id and check_folio_ids[0].bank_account_id.id or False
                if check_folio_ids[0].bank_id:
                    ctx.update({'default_bank_account_id':bank_account_id,'default_check_journal_id':check_folio_ids[0].bank_id.id,'default_journal_id':check_folio_ids[0].bank_id.id,'default_is_bank_check':True})
                    res.update({'context':ctx})
                    
        return res
    
    def post(self):
        for payment in self:
            check_payment_method = self.env.ref('l10n_mx_edi.payment_method_cheque')
            if payment.check_folio_id and payment.l10n_mx_edi_payment_method_id and check_payment_method.id==payment.l10n_mx_edi_payment_method_id.id and payment.check_folio_id.status=='Cancelled':
                raise ValidationError(_('Is not possible to validate payment request with a cancelled check sheet'))
        result = super(AccountPayment,self).post()
#         a = self.env['account.move'].search([('folio','=',self.folio)])
#         for i in range(len(a)):
#             a[i].payment_state = 'paid'
        return result
            
                
