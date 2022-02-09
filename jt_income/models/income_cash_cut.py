from odoo import models, fields

class ActivityCatalog(models.Model):

    _name = 'income.cash.cut'
    _description = "Income Cash Cut"
    

    name = fields.Char("Name")
    folio_cfs = fields.Char("Folio CFS")
    folio_cfd = fields.Char("Folio CFD")
    cut_date = fields.Datetime("Date")
    user_id = fields.Many2one("res.users","User",default=lambda self: self.env.user)
    l10n_mx_edi_payment_method_id = fields.Many2one(
        'l10n_mx_edi.payment.method',
        string='Payment Method',
        help='Indicates the way the payment was/will be received, where the '
        'options could be: Cash, Nominal Check, Credit Card, etc.')
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id)
    tax_id = fields.Many2one('account.tax','Tax')
    subtotal = fields.Float("Subtotal")
    total = fields.Float("Total")
    
    dependancy_id = fields.Many2one('dependency', string='Dependency')
    sub_dependancy_id = fields.Many2one('sub.dependency', 'Sub Dependency')
    