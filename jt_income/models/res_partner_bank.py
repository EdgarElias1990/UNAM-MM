from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResBank(models.Model):

    _inherit = 'res.partner.bank'

    for_income = fields.Boolean("Income")

    _sql_constraints = [
        ('acc_number_uniq', 'unique (acc_number)', (_('Account Number must be unique.'))),
        ('clabe_uniq', 'unique (l10n_mx_edi_clabe)', (_('CLABE must be unique.')))]

    # @api.model
    # def create(self, vals):
    #     res = super(ResBank, self).create(vals)
    #     if res.bank_id and res.bank_id.name == 'BBVA BANCOMER':
    #         other_banks = self.search([('bank_id', '=', res.bank_id.id),
    #                                    ('id', '!=', res.id)]).ids
    #         if len(other_banks) >= 2:
    #             raise UserError(_("BBVA BANCOMER Bank is not allowed more than 2 bank accounts!"))
    #     return res
    #
    # def write(self, vals):
    #     res = super(ResBank, self).write(vals)
    #     bank_acc_obj = self.env['res.partner.bank']
    #     for bank_account in self:
    #         if vals.get("bank_id"):
    #             if bank_account.bank_id and bank_account.bank_id.name == 'BBVA BANCOMER':
    #                 other_banks = bank_acc_obj.search([('bank_id', '=', bank_account.bank_id.id),
    #                                                    ('id', '!=', bank_account.id)]).ids
    #                 if len(other_banks) >= 2:
    #                     raise UserError(_("BBVA BANCOMER Bank is not allowed more than 2 bank accounts!"))
    #     return res