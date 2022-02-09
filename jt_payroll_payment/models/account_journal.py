from odoo import models, fields, api

class AccountJournal(models.Model):

    _inherit = 'account.journal'

    payroll_bank_format = fields.Selection([('santander','SANTANDER:'),
                                    ('hsbc','HSBC'),        
                                    ('bbva_nomina','BBVA BANCOMER NOMINA'),
                                    ('bbva_232','BBVA BANCOMER DISPERSION 232'),
                                    ('banamex','Banamex'),
                                    ('scotiabank','SCOTIABANK'),
                                    ('banorte','BANORTE'),
                                    ],string="Layout generation for payroll payments")
    
    payroll_load_bank_format = fields.Selection([('santander','SANTANDER'),
                                         ('hsbc','HSBC'),
                                         ('bbva_nomina','BBVA BANCOMER NOMINA'),
                                         ('bbva_232','BBVA BANCOMER DISPERSIÓN 232'),
                                         ('banamex','BANAMEX'),
                                         ('scotiabank','SCOTIABANK'),
                                         ('banorte','BANORTE'),
                                         
                                         ],string="Load bank layout for payroll")

    payroll_beneficiaries_bank_format = fields.Selection([('BANORTE','BANORTE')],string="Registration of Payroll beneficiaries")