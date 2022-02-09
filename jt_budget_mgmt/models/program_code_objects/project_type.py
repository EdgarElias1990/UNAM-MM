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


class ProjectType(models.Model):

    _name = 'project.type'
    _description = 'Project Type'
    _rec_name = 'project_type_identifier'

    project_id = fields.Many2one('project.project', string='Type of Project')
    project_type_identifier = fields.Char(string='Project Type Identifier', store=True, related="project_id.project_type_identifier")
    desc_stage = fields.Char(string='Description', related="project_id.name")
    number = fields.Char(string='Number', related="project_id.number")
    stage_identifier = fields.Char(string="Stage Identifier", related="project_id.stage_identifier")
    agreement_type = fields.Char(string='Agreement Type', store=True, related="project_id.agreement_type")
    name_agreement = fields.Text(string='Name Agreement', related="project_id.name_agreement")
    number_agreement = fields.Char(related='project_id.number_agreement', string='Number Agreement')

    @api.constrains('project_id')
    def _check_project_id(self):
        if self.project_id:
            p_type = self.search([('id', '!=', self.id), ('project_id', '=', self.project_id.id)], limit=1)
            if p_type:
                raise ValidationError(_('The Project type identifier must be unique'))

    def unlink(self):
        for pro_type in self:
            program_code = self.env['program.code'].search([('project_type_id', '=', pro_type.id)], limit=1)
            if program_code:
                raise ValidationError('You can not delete project type which are mapped with program code!')
        return super(ProjectType, self).unlink()

    def validate_project_type(self, project_type_string, result_dict):
        if len(str(project_type_string)) > 1:
            number = ''
            if self._context.get('from_adjustment'):
                number = result_dict
            else:
                number = result_dict.project_number
            project_type_str = str(project_type_string).zfill(2)
            #if project_type_str.isnumeric():
            project_type = self.search(
                    [('project_id.project_type_identifier', '=', project_type_str), ('number', '=', number)], limit=1)
            if project_type:
                return project_type
        return False
