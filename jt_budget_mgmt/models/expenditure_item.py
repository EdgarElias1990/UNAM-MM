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


class ExpenditureItem(models.Model):

    _name = 'expenditure.item'
    _description = 'Item of Expenditure'
    _rec_name = 'item'

    item = fields.Integer(string='Item')
    exercise_type = fields.Selection([('r', 'R'), ('c', 'C'), ('d', 'D')], string='Exercise type')
    description = fields.Text(string='Item description')
    unam_account_id = fields.Many2one('account.account', string='UNAM account')
    shcp_id = fields.Many2one('account.account', string='Expenditure Item SHCP')
    desc_id = fields.Many2one('account.account', string='Description of expenditure item of SHCP')
    cog_id = fields.Many2one('cog.conac', string='COG CONAC')
    cog_desc_id = fields.Many2one('cog.conac', string='Description of COG CONAC')
    assigned_account_id = fields.Many2one('account.account', string='Assigned account')

    _sql_constraints = [('item', 'unique(item)', 'The item must be unique.')]

    @api.constrains('item')
    def _check_item(self):
        # To check size of the item is exact 2
        if len(str(self.item)) != 3 and self.item not in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            raise ValidationError(_('The item size must be three.'))
