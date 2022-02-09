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


class GeographicLocation(models.Model):

    _name = 'geographic.location'
    _description = 'Geographic Location'
    _rec_name = 'state_key'

    state_key = fields.Char(string='Geographic location', size=2)
    state_name = fields.Text(string='Name of Geographic Location')

    _sql_constraints = [('state_key', 'unique(state_key)',
                         'The state key must be unique.')]

    @api.constrains('state_key')
    def _check_state_key(self):
        if not str(self.state_key).isnumeric():
            raise ValidationError(_('The state key must be numeric value'))

    def fill_zero(self, code):
        return str(code).zfill(2)

    @api.model
    def create(self, vals):
        if vals.get('state_key') and len(vals.get('state_key')) != 2:
            vals['state_key'] = self.fill_zero(vals.get('state_key'))
        return super(GeographicLocation, self).create(vals)

    def write(self, vals):
        if vals.get('state_key') and len(vals.get('state_key')) != 2:
            vals['state_key'] = self.fill_zero(vals.get('state_key'))
        return super(GeographicLocation, self).write(vals)

    def unlink(self):
        for location in self:
            program_code = self.env['program.code'].search([('location_id', '=', location.id)], limit=1)
            if program_code:
                raise ValidationError('You can not delete geographic location item which are mapped with program code!')
        return super(GeographicLocation, self).unlink()

    def validate_geo_location(self, location_string):
        if len(str(location_string)) > 1:
            location_str = str(location_string).zfill(2)
            if location_str.isnumeric():
                location = self.search(
                    [('state_key', '=', location_str)], limit=1)
                if location:
                    return location
        return False
