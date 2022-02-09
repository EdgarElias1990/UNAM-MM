# -*- coding: utf-8 -*-
##############################################################################
#
#    Jupical Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Jupical Technologies(<http://www.jupical.com>).
#    Author: Jupical Technologies Pvt. Ltd.(<http://www.jupical.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import re

class ResBank(models.Model):
    _inherit = 'res.partner.bank'

    branch_number = fields.Char('Branch number', size=4)
    key_bank = fields.Char("KeyBank")
    account_type = fields.Selection([('checks', 'Checks'), ('card', 'Card'),
                                     ('master_acc', 'Master Account'),
                                     ('clabe_acc', 'Clabe Account'),
                                     ('payment_card', 'Payment Card'),
                                     ('payment_order', 'Payment Order'),
                                     ('con_acc', 'Concentrating Account')],
                                    string='Account type')
    bic_swift = fields.Char('BIC/SWIFT', size=11)
    aba = fields.Char('ABA')

    check_name = fields.Char('Check name')
    bank_account_name = fields.Char('Bank account name')
    status = fields.Char('Status')
    bank_status = fields.Char('Bank status')
    registration_date = fields.Date('Registration date')
    authorization_date = fields.Date('Authorization date')
    low_date = fields.Date('Low Date')
    bank_registration_date = fields.Date('Bank registration date')
    bank_authorization_date = fields.Date('Bank authorization date')

    @api.onchange('bank_id')
    def onchange_bak_keybank(self):
        if self.bank_id and self.bank_id.l10n_mx_edi_code:
            self.key_bank = self.bank_id.l10n_mx_edi_code

    @api.constrains('branch_number')
    def check_branch_number(self):
        if self.branch_number:
            pattern = "^[a-zA-Z0-9_]+$"
            if not re.match(pattern, self.branch_number):
                raise UserError(_('The Branch Number value should be alphanumeric type.'))
        if self.branch_number and len(self.branch_number) != 4:
            raise UserError(_('The Branch Number should be of 4 digits.'))

    @api.onchange('bic_swift')
    def onchange_bic_swift(self):
        if self.bic_swift:
            if len(self.bic_swift) > 11:
                raise UserError(
                    _('The length of BIC/SWIFT should not be more than 11.'))
            if not self.bic_swift.isalnum():
                raise UserError(_('The value should be alphanumeric for BIC/SWIFT.'))
            if not self.bic_swift.isupper():
                raise UserError(_('Capital letters should be used for BIC/SWIFT.'))


class Bank(models.Model):

    _inherit = 'res.bank'

    company_name = fields.Char("Company Name")
    
