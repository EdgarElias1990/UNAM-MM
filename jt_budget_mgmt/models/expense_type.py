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


class ExpenseType(models.Model):

    _name = 'expense.type'
    _description = 'Expense Type'
    _rec_name = 'key_expenditure_type'

    key_expenditure_type = fields.Integer(string='Key expenditure type')
    description_expenditure_type = fields.Text(
        string='Description expenditure type')

    _sql_constraints = [('key_expenditure_type', 'unique(key_expenditure_type)',
                         'The key expenditure type must be unique.')]

    @api.constrains('key_expenditure_type')
    def _check_key_expenditure_type(self):
        # To check size of the Key expenditure type is exact 2
        if len(str(self.key_expenditure_type)) != 2 and self.key_expenditure_type not in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            raise ValidationError(
                _('The key expenditure type size must be two.'))
