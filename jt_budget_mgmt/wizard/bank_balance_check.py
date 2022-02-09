from odoo import models, fields,_,api
from odoo.exceptions import UserError, ValidationError

class BankBalanceCheck(models.TransientModel):

    _inherit = 'bank.balance.check'
    
    
    def get_payment_data(self,invoice,data):
        data = super(BankBalanceCheck,self).get_payment_data(invoice,data)
        data.update({'dependancy_id':invoice.dependancy_id and invoice.dependancy_id.id or False,
                     'sub_dependancy_id' : invoice.sub_dependancy_id and invoice.sub_dependancy_id.id or False
                     })
        return data
        
