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

    wallet_password = fields.Integer(string='Wallet password')
    wallet_password_name = fields.Text(string='Wallet password name')
    wallet_password_desc = fields.Text(string='Wallet password description')

    _sql_constraints = [('wallet_password', 'unique(wallet_password)',
                         'The wallet password must be unique.')]

    @api.constrains('wallet_password')
    def _check_wallet_password(self):
        # To check size of the Wallet password is exact 2
        if len(str(self.wallet_password)) != 4 and self.wallet_password not in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            raise ValidationError(_('The wallet password size must be four.'))
