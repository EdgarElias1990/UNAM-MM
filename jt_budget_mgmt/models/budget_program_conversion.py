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
from odoo.exceptions import ValidationError, UserError
import re


class BudgetProgramConversion(models.Model):

    _name = 'budget.program.conversion'
    _description = 'Budget Program Conversion'
    _rec_name = 'shcp'

    unam_key_id = fields.Many2one('program', string='Key UNAM')
    desc = fields.Many2one('program', string='Description of key UNAM')
    shcp = fields.Char(string='Conversion of SHCP program')
    description = fields.Text(string='Description conversion of SHCP program')

    _sql_constraints = [('shcp', 'unique(shcp)',
                         'The shcp must be unique.')]

    @api.constrains('shcp')
    def _check_shcp(self):
        # To check size of the position is exact 2
        if len(self.shcp) != 4:
            raise ValidationError(_('The shcp size must be four.'))
        if self.shcp and len(self.shcp) == 4:
            if not (re.match("[A-Z]{1}\d{3}", self.shcp.upper())):
                raise UserError(
                    _('Please enter first digit as letter and last 3 digits as numbers for SHCP.'))
