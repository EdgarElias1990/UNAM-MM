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
from odoo.exceptions import ValidationError


class KeyWallet(models.Model):

    _name = 'key.wallet'
    _description = 'Key Wallet'
    _rec_name = 'wallet_password'

    wallet_password = fields.Char(string='Wallet password', size=4)
    wallet_password_name = fields.Text(string='Wallet password name')
    wallet_password_desc = fields.Text(string='Wallet password description')

    _sql_constraints = [('wallet_password', 'unique(wallet_password)',
                         'The wallet password must be unique.')]

    @api.constrains('wallet_password')
    def _check_wallet_password(self):
        if not str(self.wallet_password).isnumeric():
            raise ValidationError(_('The wallet password must be numeric value'))

    def fill_zero(self, code):
        return str(code).zfill(4)

    @api.model
    def create(self, vals):
        if vals.get('wallet_password') and len(vals.get('wallet_password')) != 4:
            vals['wallet_password'] = self.fill_zero(vals.get('wallet_password'))
        return super(KeyWallet, self).create(vals)

    def write(self, vals):
        if vals.get('wallet_password') and len(vals.get('wallet_password')) != 4:
            vals['wallet_password'] = self.fill_zero(vals.get('wallet_password'))
        return super(KeyWallet, self).write(vals)

    def unlink(self):
        for key in self:
            program_code = self.env['program.code'].search([('portfolio_id', '=', key.id)], limit=1)
            if program_code:
                raise ValidationError('You can not delete key portfolio item which are mapped with program code!')
        return super(KeyWallet, self).unlink()

    def validate_wallet_key(self, wallet_key_string):
        if len(str(wallet_key_string)) > 3:
            wallet_key_str = str(wallet_key_string).zfill(4)
            if wallet_key_str.isnumeric():
                wallet_key = self.search(
                    [('wallet_password', '=', wallet_key_str)], limit=1)
                if wallet_key:
                    return wallet_key
        return False
