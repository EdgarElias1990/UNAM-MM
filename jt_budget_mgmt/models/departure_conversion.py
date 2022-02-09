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


class DepartureConversion(models.Model):

    _name = 'departure.conversion'
    _description = 'Conversion with Departure'
    _rec_name = 'federal_part'

    federal_part = fields.Integer(string='Federal part')
    federal_part_desc = fields.Text(string='Federal part description')

    _sql_constraints = [('federal_part', 'unique(federal_part)', 'The federal part must be unique.')]

    @api.constrains('federal_part')
    def _check_federal_part(self):
        # To check size of the position is exact 2
        if len(str(self.federal_part)) != 5 and self.federal_part not in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            raise ValidationError(_('The federal part size must be five.'))
