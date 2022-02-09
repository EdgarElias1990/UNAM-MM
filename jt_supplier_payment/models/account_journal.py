from odoo import models, fields, api

class AccountJournal(models.Model):

    _inherit = 'account.journal'

    name = fields.Char(string='Journal Name', required=True, translate=True)
    branch_number = fields.Char('Branch Number', size=4,related='bank_account_id.branch_number')
    accured_credit_account_id = fields.Many2one('account.account', "Accured Credit Account")
    conac_accured_credit_account_id = fields.Many2one('coa.conac', "Accured CONAC Credit Account")
    accured_debit_account_id = fields.Many2one('account.account', "Accured Debit Account")
    conac_accured_debit_account_id = fields.Many2one('coa.conac', "Accured CONAC Debit Account")
    bank_format = fields.Selection([('banamex','Banamex'),
                                    ('bbva_tnn_ptc','BBVA Bancomer Net Cash (TNN or PTC)'),
                                    ('bbva_tsc_pcs','BBVA Bancomer Net Cash (TSC or PCS)'),
                                    ('bbva_sit','BBVA Bancomer SIT'),
                                    ('hsbc','HSBC'),
                                    ('santander','Santander'),
                                    ('jpmw','JP Morgan WIRES / BOOKTX'),
                                    ('jpmu','JP Morgan US Drawdowns'),
                                    ('jpma','JP Morgan Advice to Receive'),
                                    ],string="Generate Bank Layout")
    
    load_bank_format = fields.Selection([('banamex','BANAMEX'),
                                         ('bbva_bancomer','BBVA BANCOMER'),
                                         ('hsbc','HSBC'),
                                         ('santander','SANTANDER'),
                                         ('jp_morgan','JP MORGAN'),
                                         
                                         ],string="Load Bank Layout")

    @api.onchange('accured_credit_account_id', 'accured_debit_account_id')
    def onchange_accured_account(self):
        if self.accured_credit_account_id and self.accured_credit_account_id.coa_conac_id:
            self.conac_accured_credit_account_id = self.accured_credit_account_id.coa_conac_id
        else:
            self.conac_accured_credit_account_id = False
        if self.accured_debit_account_id and self.accured_debit_account_id.coa_conac_id:
            self.conac_accured_debit_account_id = self.accured_debit_account_id.coa_conac_id
        else:
            self.conac_accured_debit_account_id = False

    def write(self, vals):
        res = super(AccountJournal, self).write(vals)
        acc_obj = self.env['account.account']
        for record in self:
            if vals.get('accured_credit_account_id'):
                accured_credit_account_id = acc_obj.browse(vals.get('accured_credit_account_id'))
                if accured_credit_account_id.coa_conac_id:
                    record.conac_accured_credit_account_id = accured_credit_account_id.coa_conac_id
                else:
                    record.conac_accured_credit_account_id = False
            if vals.get('accured_debit_account_id'):
                accured_debit_account_id = acc_obj.browse(vals.get('accured_debit_account_id'))
                if accured_debit_account_id.coa_conac_id:
                    record.conac_accured_debit_account_id = accured_debit_account_id.coa_conac_id
                else:
                    record.conac_accured_debit_account_id = False
        return res
class AccountTax(models.Model):
    _inherit = "account.tax"
    
    amount = fields.Float(required=True, digits=(16, 6))
