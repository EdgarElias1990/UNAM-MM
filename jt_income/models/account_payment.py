from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class account_payment(models.Model):
    _inherit = "account.payment"

    sub_origin_resource_id = fields.Many2one('sub.origin.resource', "Extraordinary / Own income")

    type_of_revenue_collection = fields.Selection([('billing', 'Billing'),
                                                   ('deposit_cer', 'Certificates of deposit'),
                                                   ('dgae_ref', 'Reference of DGAE'),
                                                   ('dgoae_trades', 'Trades DGOAE')], "Type of Revenue Collection")
    bank_reference = fields.Char("Bank Reference")
        
    def action_register_payment(self):
        res = super(account_payment,self).action_register_payment()
        if res:
            active_ids = self.env.context.get('active_ids')
            if len(active_ids) == 1:
                move_id = self.env['account.move'].browse(active_ids)
                context = dict(res.get('context') or {})
                
                context.update({'default_dependancy_id' : move_id.dependancy_id and move_id.dependancy_id.id or False,
                                                  'default_sub_dependancy_id' : move_id.sub_dependancy_id and move_id.sub_dependancy_id.id or False,
                                                  'default_l10n_mx_edi_payment_method_id' : move_id.l10n_mx_edi_payment_method_id and move_id.l10n_mx_edi_payment_method_id.id or False,
                                                  'default_sub_origin_resource_id' : move_id.sub_origin_resource_id and move_id.sub_origin_resource_id.id or False,
                                                  'default_type_of_revenue_collection' : move_id.type_of_revenue_collection,
                                                  'default_bank_reference' : move_id.ref, 
                                                  })
                if move_id.income_bank_journal_id:
                    context.update({'default_journal_id':move_id.income_bank_journal_id.id})
                res.update({'context':context})    
        return res

    def l10n_mx_edi_is_required(self):
        self.ensure_one()
        if self.invoice_ids:
            income_invoices= self.invoice_ids.filtered(lambda x:x.type_of_revenue_collection)
            if len(income_invoices) == len(self.invoice_ids):
                return False
        return super(account_payment,self).l10n_mx_edi_is_required()
    
    def post(self):
        result = super(account_payment,self).post()

        for payment in self:
            income_invoices= payment.invoice_ids.filtered(lambda x:x.type_of_revenue_collection)
            if income_invoices:
                if payment.journal_id and not payment.journal_id.accrued_income_credit_account_id \
                    or not payment.journal_id.conac_accrued_income_credit_account_id \
                    or not payment.journal_id.accrued_income_debit_account_id \
                    or not payment.journal_id.conac_accrued_income_debit_account_id :
                    raise ValidationError(_("Please configure UNAM and CONAC Accrued Income Account!"))

                if payment.journal_id and not payment.journal_id.recover_income_credit_account_id \
                    or not payment.journal_id.conac_recover_income_credit_account_id \
                    or not payment.journal_id.recover_income_debit_account_id \
                    or not payment.journal_id.conac_recover_income_debit_account_id :
                    raise ValidationError(_("Please configure UNAM and CONAC Recover Income Account!"))
                
                company_currency = self.company_id.currency_id
                # Manage currency.
                if payment.currency_id == company_currency:
                    # Single-currency.
                    balance = payment.amount
                    currency_id = False
                    counterpart_amount = 0
                    
                else:
                    # Multi-currencies.
                    balance = self.currency_id._convert(payment.amount, company_currency, payment.company_id, payment.payment_date)
                    currency_id = payment.currency_id.id
                    counterpart_amount = payment.amount
                    
                if payment.move_line_ids:
                    move_id = payment.move_line_ids[0].move_id
                    payment.move_line_ids = [(0, 0, {
                                                 'account_id': payment.journal_id.accrued_income_credit_account_id and payment.journal_id.accrued_income_credit_account_id.id or False,
                                                 'coa_conac_id': payment.journal_id.conac_accrued_income_credit_account_id and payment.journal_id.conac_accrued_income_credit_account_id.id or False,
                                                 'credit': balance, 
                                                 'conac_move' : True,
                                                 'amount_currency' : -counterpart_amount,
                                                 'currency_id' : currency_id,                                     
                                                 'move_id' : move_id.id,
                                                 'payment_id': payment.id,
                                                'date_maturity': payment.payment_date,
                                                'partner_id': payment.partner_id.commercial_partner_id.id,
                                                 
                                             }), 
                                    (0, 0, {
                                                 'account_id': payment.journal_id.accrued_income_debit_account_id and payment.journal_id.accrued_income_debit_account_id.id or False,
                                                 'coa_conac_id': payment.journal_id.conac_accrued_income_debit_account_id and payment.journal_id.conac_accrued_income_debit_account_id.id or False,
                                                 'debit': balance,
                                                 'conac_move' : True,
                                                 'amount_currency' : counterpart_amount,
                                                 'currency_id' : currency_id,                                     
                                                 'move_id' : move_id.id,
                                                 'payment_id': payment.id,
                                                 'date_maturity': payment.payment_date,
                                                 'partner_id': payment.partner_id.commercial_partner_id.id,
                                               
                                             })]

                    payment.move_line_ids = [(0, 0, {
                                                 'account_id': payment.journal_id.recover_income_credit_account_id and payment.journal_id.recover_income_credit_account_id.id or False,
                                                 'coa_conac_id': payment.journal_id.conac_recover_income_credit_account_id and payment.journal_id.conac_recover_income_credit_account_id.id or False,
                                                 'credit': balance, 
                                                 'conac_move' : True,
                                                 'amount_currency' : -counterpart_amount,
                                                 'currency_id' : currency_id,                                     
                                                 'move_id' : move_id.id,
                                                 'payment_id': payment.id,
                                                'date_maturity': payment.payment_date,
                                                'partner_id': payment.partner_id.commercial_partner_id.id,
                                                 
                                             }), 
                                    (0, 0, {
                                                 'account_id': payment.journal_id.recover_income_debit_account_id and payment.journal_id.recover_income_debit_account_id.id or False,
                                                 'coa_conac_id': payment.journal_id.conac_recover_income_debit_account_id and payment.journal_id.conac_recover_income_debit_account_id.id or False,
                                                 'debit': balance,
                                                 'conac_move' : True,
                                                 'amount_currency' : counterpart_amount,
                                                 'currency_id' : currency_id,                                     
                                                 'move_id' : move_id.id,
                                                 'payment_id': payment.id,
                                                 'date_maturity': payment.payment_date,
                                                 'partner_id': payment.partner_id.commercial_partner_id.id,
                                               
                                             })]
        
        return result
        
class payment_register(models.TransientModel):
    
    _inherit = 'account.payment.register'
    _description = 'Register Payment'
    
    
    def _prepare_payment_vals(self, invoices):
        res = super(payment_register,self)._prepare_payment_vals(invoices)
        if invoices and len(invoices)==1:
            move_id = invoices[0]
            res.update({'dependancy_id' : move_id.dependancy_id and move_id.dependancy_id.id or False,
                                                  'sub_dependancy_id' : move_id.sub_dependancy_id and move_id.sub_dependancy_id.id or False,
                                                  'l10n_mx_edi_payment_method_id' : move_id.l10n_mx_edi_payment_method_id and move_id.l10n_mx_edi_payment_method_id.id or False,
                                                  'sub_origin_resource_id' : move_id.sub_origin_resource_id and move_id.sub_origin_resource_id.id or False, 
                                                  })
        return res
            
            
            