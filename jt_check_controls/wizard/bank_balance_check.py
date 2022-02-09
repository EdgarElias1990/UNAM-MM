from odoo import models, fields,_,api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class BankBalanceCheck(models.TransientModel):

    _inherit = 'bank.balance.check'

    check_balance_in_transit = fields.Float("Check balance in transit")
    balance_available = fields.Float("Balance Available")
    amount_trasnfer_sent = fields.Float("Amount of transfers between accounts scheduled for the day")
    amount_trasnfer_confirmed= fields.Float("Amount of transfers between accounts confirmed during the day")
    is_bank_check = fields.Boolean('Bank Check Set',default=False)
    check_journal_id = fields.Many2one('account.journal','Check Journal')
    
    @api.onchange('journal_id')
    def onchange_check_journal(self):
        if self.is_bank_check and self.check_journal_id.id != self.journal_id.id:
            raise ValidationError(_("The selected bank does not correspond to the bank with which the payment request must be paid"))
        
    def verify_balance(self):
        account_balance = 0
        if not self.account_id:
            raise ValidationError("Please Configure default debit account into Bank Journal")

        if self.account_id:
            values = self.env['account.move.line'].search(
                [('account_id', '=', self.account_id.id), ('move_id.state', '=', 'posted')])
            check_req = self.env['check.log'].search([('checklist_id.checkbook_req_id.bank_id', '=', self.journal_id.id),
                                                      ('status', 'in', ('Delivered','In transit'))])
            total_check_amt = sum(x.check_amount for x in check_req)
            account_balance = sum(x.debit - x.credit for x in values)
            
            today_date = datetime.today().date()  
            transfer_request_sent = self.env['request.open.balance.finance'].search([('date_required','=',today_date),('state','=','sent'),('desti_bank_account_id','=',self.journal_id.id)])
            transfer_request_confirm = self.env['request.open.balance.finance'].search([('date_required','=',today_date),('state','=','confirmed'),('desti_bank_account_id','=',self.journal_id.id)])

            self.account_balance = account_balance
            self.minimum_balance = self.journal_id and self.journal_id.min_balance or 0
            self.required_balance = self.total_amount + self.minimum_balance
            self.different_balance = account_balance - self.total_amount - self.minimum_balance
            self.check_balance_in_transit = total_check_amt
            self.amount_trasnfer_sent = sum(x.amount for x in transfer_request_sent)
            self.amount_trasnfer_confirmed = sum(x.amount for x in transfer_request_confirm)
            
            self.balance_available = account_balance - total_check_amt + self.amount_trasnfer_sent + self.amount_trasnfer_confirmed
            
            if account_balance >= self.total_amount:
                self.is_balance = True
                
                return {
                    'name': 'Balance',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'view_id': False,
                    'res_model': 'balance.check.wizard',
                    'domain': [],
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': {'default_balance_available':self.balance_available,'default_check_balance_in_transit':self.check_balance_in_transit,'default_different_balance':self.different_balance,'default_required_balance':self.required_balance,'default_minimum_balance':self.minimum_balance,'default_account_balance': account_balance, 'default_is_balance': True,
                                'default_wizard_id': self.id,'default_amount_trasnfer_sent':self.amount_trasnfer_sent,'default_amount_trasnfer_confirmed':self.amount_trasnfer_confirmed},
                }
            else:
                self.is_balance = False
                return {
                    'name': 'Balance',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'view_id': False,
                    'res_model': 'balance.check.wizard',
                    'domain': [],
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': {'default_balance_available':self.balance_available,'default_check_balance_in_transit':self.check_balance_in_transit,'default_different_balance':self.different_balance,'default_required_balance':self.required_balance,'default_minimum_balance':self.minimum_balance,'default_account_balance': account_balance, 'default_is_balance': False,
                                'default_wizard_id': self.id,'default_amount_trasnfer_sent':self.amount_trasnfer_sent,'default_amount_trasnfer_confirmed':self.amount_trasnfer_confirmed},
                }
                

class BalanceCheckWizard(models.TransientModel):
    
    _inherit = 'balance.check.wizard'
    
    check_balance_in_transit = fields.Float("Check balance in transit")
    balance_available = fields.Float("Balance Available")
    amount_trasnfer_sent = fields.Float("Amount of transfers between accounts scheduled for the day")
    amount_trasnfer_confirmed= fields.Float("Amount of transfers between accounts confirmed during the day")
                    
