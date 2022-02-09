from odoo import models, fields, api

class InvestementContract(models.Model):

    _name = 'investment.contract'
    _description = "Investment Contract"
    
    name = fields.Char("Associate Contract")
    journal_id = fields.Many2one('account.journal','Bank')
    bank_account_id = fields.Many2one(related="journal_id.bank_account_id",string="Bank Account")
    investent_type = fields.Selection([('bank_paper','Bank Paper'),('government_role','Government Role')],string="Investment Type")
    term = fields.Integer("Term")
    observations = fields.Text("Observations")
     
    fund_type_id = fields.Many2one('fund.type', "Type Of Fund")
    agreement_type_id = fields.Many2one('agreement.agreement.type', 'Agreement Type')
    fund_id = fields.Many2one('agreement.fund','Fund') 
    base_collabaration_id = fields.Many2one('bases.collaboration','Name Of Agreements')

