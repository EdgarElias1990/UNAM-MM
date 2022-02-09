from odoo import models, fields, api

class BankTransferRequest(models.Model):

    _name = 'bank.transfer.request'
    
    name = fields.Char('Name')
    move_id = fields.Many2one('account.move',"Batch Folio")
    application_date = fields.Date("Application Date")
    bank_id = fields.Many2one(related="move_id.payment_bank_id",string='Bank')
    bank_account_id = fields.Many2one(related="move_id.payment_bank_account_id",string='Destination Account')
    currency_id = fields.Many2one(related='bank_account_id.currency_id',string='Currency')
    amount = fields.Monetary(related="move_id.amount_total",string='Transfer Amount requested')
    area_req_transfer = fields.Char('Area requesting transfer')
    user_id = fields.Many2one('res.users','Requesting User',default=lambda self: self.env.user)
    req_transfer = fields.Char('Required Transfer')
    operation_type = fields.Char("Type Operation")
    observation = fields.Char('Observation')
    required_handover_date = fields.Date('Required Handover Date')
    origin_bank_id = fields.Many2one('res.bank','Origin Bank')
    origin_bank_account_id = fields.Many2one('res.partner.bank','Origin Bank Account')
    state = fields.Selection([('draft','Draft'),('request','Request'),('approved','Approved'),('rejected','Rejected')],string='Status',default='draft')
    concept = fields.Char("Concept")
    
    @api.model
    def create(self,vals):
        name = self.env['ir.sequence'].next_by_code('bank.transfer.request')
        vals.update({'name':name})
        res = super(BankTransferRequest,self).create(vals)
        return res
        
        