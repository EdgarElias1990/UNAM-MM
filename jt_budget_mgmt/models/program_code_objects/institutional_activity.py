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


class InstitutionalActivity(models.Model):

    _name = 'institutional.activity'
    _description = 'Institutional Activity'
    _rec_name = 'number'

    number = fields.Char(string='Institutional activity number', size=5)
    description = fields.Text(string='Description')

    _sql_constraints = [('number', 'unique(number)', 'The number must be unique.')]

    @api.constrains('number')
    def _check_number(self):
        if not str(self.number).isnumeric():
            raise ValidationError(_('The Institutional activity number must be numeric value'))

    def fill_zero(self, code):
        return str(code).zfill(5)

    @api.model
    def create(self, vals):
        if vals.get('number') and len(vals.get('number')) != 5:
            vals['number'] = self.fill_zero(vals.get('number'))
        return super(InstitutionalActivity, self).create(vals)

    def write(self, vals):
        if vals.get('number') and len(vals.get('number')) != 5:
            vals['number'] = self.fill_zero(vals.get('number'))
        return super(InstitutionalActivity, self).write(vals)

    def unlink(self):
        for ai in self:
            program_code = self.env['program.code'].search([('institutional_activity_id', '=', ai.id)], limit=1)
            if program_code:
                raise ValidationError('You can not delete institutional activity which are mapped with program code!')
        return super(InstitutionalActivity, self).unlink()

    def validate_institutional_activity(self, institutional_activity_string):
        if len(str(institutional_activity_string)) > 2:
            institutional_activity_str = str(
                institutional_activity_string).zfill(5)
            if institutional_activity_str.isnumeric():
                institutional_activity = self.search(
                    [('number', '=', institutional_activity_str)], limit=1)
                if institutional_activity:
                    return institutional_activity
        return False
