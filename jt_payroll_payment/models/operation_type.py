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


class OperationType(models.Model):

    _name = 'operation.type'
    _description = 'Type of Operation'
    _rec_name = 'name'

    name = fields.Char('Request operation name')
    op_number = fields.Char('Operation Number', size=2)
    currency_type = fields.Selection([('national', 'Moneda Nacional'), (
        'foreign', 'Moneda Extranjera')], string='Currency type of the transaction')
    upa_catalog_policy_id = fields.Many2one('policy.keys', 'UPA Catalog')

    def name_get(self):
        result = []
        for rec in self:
            name = rec.name or ''
            if rec.op_number and self.env.context and self.env.context.get('show_for_supplier_payment', False):
                name = rec.op_number + " "+name
            result.append((rec.id, name))
        return result

    def fill_zero(self, number):
        return str(number).zfill(2)

    @api.constrains('op_number')
    def _check_number(self):
        if self.op_number and not str(self.op_number).isnumeric():
            raise UserError(_('The Operation Number must be numeric value'))

    @api.model
    def create(self, vals):
        res = super(OperationType, self).create(vals)
        if vals.get('op_number'):
            number = vals.get('op_number')
            if not str(number).isnumeric():
                raise UserError(
                    _('The Operation Number must be numeric value'))
            if len(number) != 2:
                new_no = self.fill_zero(vals.get('op_number'))
                res.op_number = new_no
        return res

    def write(self, vals):
        for op in self:
            number = vals.get('op_number') or op.op_number
            if not str(number).isnumeric():
                raise UserError(
                    _('The Operation Number must be numeric value'))
            if len(number) != 2:
                vals.update({'op_number': self.fill_zero(number)})
        return super(OperationType, self).write(vals)
