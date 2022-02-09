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
    _rec_name = 'sub_program'

    unam_key_id = fields.Many2one('program', string='UNAM key')
    sub_program = fields.Char(string='Sub program', size=2)
    desc = fields.Text(string='Sub program description')
    dependency_id = fields.Many2one('dependency', string='Dependency')
    sub_dependency_id = fields.Many2one('sub.dependency', string='Sub Dependency')
    
    _sql_constraints = [('sub_program_unam_key_id', 'unique(sub_program,unam_key_id,dependency_id,sub_dependency_id)',
                         'The sub program must be unique per UNAM key,Dependency and Sub Dependency')]

    @api.constrains('sub_program')
    def _check_sub_program(self):
        if not str(self.sub_program).isnumeric():
            raise ValidationError(_('The Sub Program value must be numeric value'))

    def fill_zero(self, code):
        return str(code).zfill(2)

    @api.onchange('dependency_id')
    def onchange_dependency_id(self):
        if self.env.context and not self.env.context.get('default_sub_dependency_id',False):
            self.sub_dependency_id = False
        
    @api.model
    def create(self, vals):
        if vals.get('sub_program') and len(vals.get('sub_program')) != 2:
            vals['sub_program'] = self.fill_zero(vals.get('sub_program'))
        if vals.get('sub_dependency_id',False) and vals.get('dependency_id',False):
            sub_dep_master = self.env['sub.dependency'].browse(vals.get('sub_dependency_id',[]))
            if sub_dep_master:
                link_sub_dep = self.env['sub.dependency'].search([('dependency_id','=',vals.get('dependency_id',False)),('sub_dependency','=',sub_dep_master.sub_dependency)],limit=1)
                if link_sub_dep:
                    vals.update({'sub_dependency_id':link_sub_dep.id})
                else:
                    vals.update({'sub_dependency_id':False})
        return super(SubProgram, self).create(vals)

    def write(self, vals):
        if vals.get('sub_program') and len(vals.get('sub_program')) != 2:
            vals['sub_program'] = self.fill_zero(vals.get('sub_program'))
        return super(SubProgram, self).write(vals)

    def unlink(self):
        for subprogram in self:
            program_code = self.env['program.code'].search([('sub_program_id', '=', subprogram.id)], limit=1)
            if program_code:
                raise ValidationError('You can not delete sub-program which are mapped with program code!')
        return super(SubProgram, self).unlink()

    def validate_subprogram(self, subprogram_string, program,dependency,subdependency):
        if len(str(subprogram_string)) > 1:
            subprogram_str = str(subprogram_string).zfill(2)
            if subprogram_str.isnumeric():
                subprogram = self.search(
                    [('unam_key_id', '=', program.id),('dependency_id','=',dependency.id),('sub_dependency_id','=',subdependency.id),('sub_program', '=', subprogram_str)], limit=1)
                if subprogram:
                    return subprogram
        return False
