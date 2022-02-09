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


class SubProgram(models.Model):

    _name = 'sub.program'
    _description = 'Sub-Program'
    _rec_name = 'unam_key_id'

    unam_key_id = fields.Many2one('program', string='UNAM key')
    sub_program = fields.Integer(string='Sub program')
    desc = fields.Text(string='Sub program description')

    _sql_constraints = [('sub_program_unam_key_id', 'unique(sub_program,unam_key_id)',
                         'The sub program must be unique per UNAM key')]

    @api.constrains('sub_program')
    def _check_sub_program(self):
        # To check size of the SubProgram is exact 2
        if len(str(self.sub_program)) != 2 and self.sub_program not in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            raise ValidationError(_('The sub program size must be two.'))
