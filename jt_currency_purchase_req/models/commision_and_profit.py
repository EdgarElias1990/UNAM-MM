from odoo import models, fields, api,_
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

class CommisionAndProfit(models.Model):

    _name = 'comission.profit'
    _description = "Commision And Profit"
    _rec_name = 'folio'

    folio = fields.Char(string='Folio',tracking=True)
    type_of_record = fields.Selection([('commision','Comission'),('interest','Interest')],string='Type Of Record')
    type_of_comission  = fields.Selection([('check_paid_per_window','Check paid per Window'),('transfer','Transfers')],string='Type Of Commision')
    journal_id = fields.Many2one('account.journal',string="Daily")
    bank_account_id = fields.Many2one(related="journal_id.bank_account_id",string="Bank Account")
    programmatic_code_id = fields.Many2one('program.code',string="Programmatic Code")
    amount = fields.Float('Amount')
    move_line_ids = fields.One2many(
        'account.move.line', 'commision_profit_id', string="Journal Items")
    description = fields.Char('Description')
    status = fields.Selection([('draft', 'Draft'),
                               ('approved', 'Approved'),
                               ], string="Status", default="draft")


    @api.onchange('bank_account_id')
    def onchange_bank_account_id(self):
        if self.bank_account_id:
            journal_id = self.env['account.journal'].search([('bank_account_id','=',self.bank_account_id.id)],limit=1)
            self.journal_id = journal_id and journal_id.id or False
             
    @api.model
    def create(self, vals):
        res = super(CommisionAndProfit,self).create(vals)
        folio = self.env['ir.sequence'].next_by_code('comission.profit')
        res.folio = folio        
        if res.folio:
            res.folio = res.folio.zfill(8)
        return res



    def approve(self):

        for record in self:

            record.status = 'approved'
            if record.journal_id and record.programmatic_code_id:
                journal = record.journal_id
                if not journal.default_credit_account_id \
                        or not journal.conac_credit_account_id:
                    if self.env.user.lang == 'es_MX':
                        raise ValidationError(_("Por favor configure la cuenta UNAM y CONAC en diario!"))
                    else:
                        raise ValidationError(_("Please configure UNAM and CONAC account in journal!"))
                if not record.programmatic_code_id.item_id.unam_account_id or not record.programmatic_code_id.item_id.unam_account_id.coa_conac_id:
                    if self.env.user.lang == 'es_MX':
                        raise ValidationError(_("Por favor configure la cuenta UNAM y CONAC en item!"))
                    else:
                        raise ValidationError(_("Please configure UNAM and CONAC account in Item!"))
                     
                today = datetime.today().date()
                user = self.env.user
                partner_id = user.partner_id.id
                amount = self.amount

                unam_move_val = {'ref': self.folio,  'conac_move': True,
                                 'date': today, 'journal_id': journal.id, 'company_id': self.env.user.company_id.id,
                                 'line_ids': [(0, 0, {
                                     'account_id': journal.default_credit_account_id.id,
                                     'coa_conac_id': journal.conac_credit_account_id.id,
                                     'credit': amount,
                                     'partner_id': partner_id,
                                     'commision_profit_id': self.id,
                                     }),
                                     (0, 0, {
                                     'account_id': record.programmatic_code_id.item_id.unam_account_id.id,
                                     'coa_conac_id': record.programmatic_code_id.item_id.unam_account_id.coa_conac_id.id,
                                     'debit': amount,
                                     'partner_id': partner_id,
                                     'commision_profit_id': self.id,
                                     }),
                                 ]}
                move_obj = self.env['account.move']
                unam_move = move_obj.create(unam_move_val)
                unam_move.action_post()



    

class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    commision_profit_id = fields.Many2one('comission.profit','Comission Profit')