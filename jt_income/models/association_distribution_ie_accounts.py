from odoo import models, fields,api,_
from odoo.exceptions import ValidationError

class AssociationDistributionIEAccounts(models.Model):

    _name = 'association.distribution.ie.accounts'
    _description = "Association Distribution IE Accounts"
    _rec_name = 'ie_key'

    ie_key = fields.Char("IE Key")
    desc = fields.Char("Description")
    scope_of_application = fields.Selection([('income','Income')],string="Scope Of Application")
    proration_calculation = fields.Selection([('percentage_price','Percentage of the price')],string="Proration calculation")
    amount = fields.Float('Amount')
    active = fields.Boolean('Active',default=True)
    ie_account_line_ids = fields.One2many('association.distribution.ie.accounts.line','ie_account_id','Definition')

    @api.constrains('ie_key')
    def _check_federal_part(self):
        if self.ie_key and not str(self.ie_key).isnumeric():
            raise ValidationError(_('The IE Key must be numeric value'))
    
class AssociationDistributionIEAccountsLines(models.Model):
    
    _name = 'association.distribution.ie.accounts.line'
    _description = "Association Distribution IE Accounts Lines"
    
    ie_account_id = fields.Many2one('association.distribution.ie.accounts',string='IE Account',ondelete='cascade')
    percentage = fields.Float('%')
    account_id = fields.Many2one("account.account",'Accounts')
    
    