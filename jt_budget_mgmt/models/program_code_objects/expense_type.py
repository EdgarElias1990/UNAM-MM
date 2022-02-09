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

    key_expenditure_type = fields.Char(string='Key expenditure type', size=2)
    description_expenditure_type = fields.Text(
        string='Description expenditure type')

    _sql_constraints = [('key_expenditure_type', 'unique(key_expenditure_type)',
                         'The key expenditure type must be unique.')]

    @api.constrains('key_expenditure_type')
    def _check_key_expenditure_type(self):
        if not str(self.key_expenditure_type).isnumeric():
            raise ValidationError(_('The Key expenditure type must be numeric value'))

    def fill_zero(self, code):
        return str(code).zfill(2)

    @api.model
    def create(self, vals):
        if vals.get('key_expenditure_type') and len(vals.get('key_expenditure_type')) != 2:
            vals['key_expenditure_type'] = self.fill_zero(vals.get('key_expenditure_type'))
        return super(ExpenseType, self).create(vals)

    def write(self, vals):
        if vals.get('key_expenditure_type') and len(vals.get('key_expenditure_type')) != 2:
            vals['key_expenditure_type'] = self.fill_zero(vals.get('key_expenditure_type'))
        return super(ExpenseType, self).write(vals)

    def unlink(self):
        for expense in self:
            program_code = self.env['program.code'].search([('expense_type_id', '=', expense.id)], limit=1)
            if program_code:
                raise ValidationError('You can not delete expense type item which are mapped with program code!')
        return super(ExpenseType, self).unlink()

    def validate_expense_type(self, expense_type_string):
        if len(str(expense_type_string)) > 1:
            expense_type_str = str(expense_type_string).zfill(2)
            if expense_type_str.isnumeric():
                expense_type = self.search(
                    [('key_expenditure_type', '=', expense_type_str)], limit=1)
                if expense_type:
                    return expense_type
        return False
