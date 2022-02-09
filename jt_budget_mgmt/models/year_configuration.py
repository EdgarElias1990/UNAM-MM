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


class YearConfiguration(models.Model):

    _name = 'year.configuration'
    _description = 'Year'

    name = fields.Char(string='Year', size=4)

    #_sql_constraints = [('year_configuration', 'unique(name)', 'The year must be unique.')]
    
    @api.constrains('name')
    def _check_name(self):
        if not str(self.name).isnumeric():
            raise ValidationError(_('Year must be numeric value!'))

    def validate_year(self, year_string):
        if len(str(year_string)) > 3:
            year_str = str(year_string)[:4]
            if year_str.isnumeric():
                year = self.search(
                    [('name', '=', year_str)], limit=1)
                if not year:
                    if self._context.get('from_adequacies'):
                        return False
                    year = self.env['year.configuration'].create(
                        {'name': year_str})
                return year
        return False
