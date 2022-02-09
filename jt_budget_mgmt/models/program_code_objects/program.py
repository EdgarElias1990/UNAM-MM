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


class Program(models.Model):

    _name = 'program'
    _description = 'Program'
    _rec_name = 'key_unam'

    key_unam = fields.Char(string='Key UNAM', size=2)
    desc_key_unam = fields.Text(string='Description Key UNAM')
    program_key_id = fields.Many2one('program.key','Key UNAM Digit')
    #digit = fields.Char(string="Key UNAM Digit",size=1,compute="get_key_unam_digit",store=True)
    _sql_constraints = [('key_unam', 'unique(key_unam)',
                         'The key UNAM must be unique.')]


    @api.constrains('key_unam')
    def _check_key_unam(self):
        if not str(self.key_unam).isnumeric():
            raise ValidationError(_('The Key UNAM must be numeric value'))

    def fill_zero(self, code):
        return str(code).zfill(2)

#     @api.depends('key_unam')
#     def get_key_unam_digit(self):
#         for rec in self:
#             if rec.key_unam:
#                 rec.digit = rec.key_unam[0]
                 
    @api.model
    def create(self, vals):
        if vals.get('key_unam') and len(vals.get('key_unam')) != 2:
            vals['key_unam'] = self.fill_zero(vals.get('key_unam'))
        return super(Program, self).create(vals)

    def write(self, vals):
        if vals.get('key_unam') and len(vals.get('key_unam')) != 2:
            vals['key_unam'] = self.fill_zero(vals.get('key_unam'))
        return super(Program, self).write(vals)

    def unlink(self):
        for program in self:
            program_code = self.env['program.code'].search([('program_id', '=', program.id)], limit=1)
            if program_code:
                raise ValidationError(_('You can not delete program which are mapped with program code!'))
            sub_program = self.env['sub.program'].search([('unam_key_id', '=', program.id)], limit=1)
            if sub_program:
                raise ValidationError(_('You can not delete Program which are mapped with Sub Program!'))
            conpp = self.env['budget.program.conversion'].search([('unam_key_id', '=', program.id)], limit=1)
            if conpp    :
                raise ValidationError(_('You can not delete Program which are mapped with Budget Program Conversion '
                                        '(CONPP)!'))
        return super(Program, self).unlink()

    def validate_program(self, program_string):
        if len(str(program_string)) > 1:
            program_str = str(program_string).zfill(2)
            if program_str.isnumeric():
                program = self.search(
                    [('key_unam', '=', program_str)], limit=1)
                if program:
                    return program
        return False

class ProgramKey(models.Model):
    
    _name = 'program.key'
    
    name = fields.Char(string="Key UNAM Digit",size=1)

    @api.constrains('name')
    def _check_key_unam(self):
        for rec in self:
            if rec.name:
                exits = self.env['program.key'].search([('id','!=',rec.id),('name','=',rec.name)])
                if exits:
                    raise ValidationError(_('The Key UNAM Digit must be unique.'))
    
    
    