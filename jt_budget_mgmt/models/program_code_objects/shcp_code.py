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
import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class SHCPCode(models.Model):

    _name = 'shcp.code'
    _description = 'SHCP Program Code'

    name = fields.Char("Code")
    desc = fields.Text(string='Description')

    _sql_constraints = [('shcp_code', 'unique(name)', 'The SHCP Program Code must be unique.')]
    
    @api.constrains('name')
    def _check_name(self):
        if self.name:
            # To check size of the position is exact 2
            if len(self.name) != 4:
                raise ValidationError(_('The SHCP program value size must be four.'))
            if self.name and len(self.name) == 4:
                if not (re.match("[A-Z]{1}\d{3}", str(self.name).upper())):
                    raise UserError(
                        _('Please enter first digit as letter and last 3 digits as numbers for SHCP.'))

    def unlink(self):
        for code in self:
            conpp = self.env['budget.program.conversion'].search([('shcp', '=', code.id)], limit=1)
            if conpp:
                raise ValidationError(_('You can not delete SHCP Program Code which are mapped with'
                                        ' Budget Program Conversion (CONPP)!'))
        return super(Program, self).unlink()