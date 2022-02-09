from odoo import models, fields, api

class SenderRecipientTradesFinance(models.Model):

    _name = 'finance.sender.recipient.trades'
    _description = "Finance Sender Recipient Trades"
    _rec_name = 'template'
    
    template = fields.Selection([('sign_update','Signature Update'),
                                 ('open_check_acc','Opening a checking account'),
                                 ('check_acc_cancellation','Checking account cancellation'),
                                 ('other_procedures','Other Procedures'),
                                 ],string="Template")
    
        
    bank_account_id = fields.Many2one('res.bank','Bank')
    account_bank_id = fields.Many2one('res.partner.bank','Bank Account')
    bank_acc_id = fields.Many2one('account.journal',"Bank Account")
    executive_id = fields.Many2one('executive.data',string='Executive Data')
    position_id = fields.Char(related="executive_id.position",string='Position')

    recipient_emp_id = fields.Many2one('hr.employee','Employee')
    recipient_title = fields.Char(related="recipient_emp_id.emp_title",string='Title')
    recipient_professional_title = fields.Char(related="recipient_emp_id.emp_job_title",string='Professional Title')

    sender_emp_id = fields.Many2one('hr.employee','Employee')
    sender_title = fields.Char(related="sender_emp_id.emp_title",string='Title')
    sender_professional_title = fields.Char(related="sender_emp_id.emp_job_title",string='Professional Title')
    
    employee_ids = fields.Many2many('hr.employee','rel_employee_sender_recipient_trades_finance','sender_id','emp_id','EMPLOYEES COPIED')
    



    def name_get(self):
        result = []
        for rec in self:
            name = rec.template or ''
            if rec.template: 
                name = dict(rec._fields['template'].selection).get(rec.template)
                if self.env.user.lang == 'es_MX':
                    if name=='Other Procedures':
                        name = 'otros tramites'
                    elif name=='Checking account cancellation':
                        name='cancelacion de cuenta de cheques'
                    elif name=='Opening a checking account':
                        name='apertura de cuenta de cheques'
                    elif name=='Signature Update':
                        name='actualizacion de firmas'
                    
                        
            result.append((rec.id, name))
        return result        