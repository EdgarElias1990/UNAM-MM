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


class Stage(models.Model):

    _name = 'stage'
    _description = 'Stage'
    _rec_name = 'stage_identifier'

    project_id = fields.Many2one('project.project', string='Stage')
    desc = fields.Text(string='Description', related="project_id.desc_stage")
    project_type_identifier = fields.Char(string='Project Type Identifier', related="project_id.project_type_identifier")
    desc_stage = fields.Text(string='Description', related="project_id.desc_stage")
    number = fields.Char(string='Number', related="project_id.number")
    stage_identifier = fields.Char(string="Stage Identifier", store=True, related="project_id.stage_identifier")
    agreement_type = fields.Char(string='Agreement Type', related="project_id.agreement_type")
    name_agreement = fields.Text(string='Name Agreement', related="project_id.name_agreement")
    number_agreement = fields.Char(related='project_id.number_agreement', string='Number Agreement')

    @api.constrains('project_id')
    def _check_project_id(self):
        if self.project_id:
            p_type = self.search([('id', '!=', self.id), ('project_id', '=', self.project_id.id)], limit=1)
            if p_type:
                raise ValidationError(_('The agreement type identifier type must be unique'))

    def unlink(self):
        for stage in self:
            program_code = self.env['program.code'].search([('stage_id', '=', stage.id)], limit=1)
            if program_code:
                raise ValidationError('You can not delete stage identifier which are mapped with program code!')
        return super(Stage, self).unlink()

    def validate_stage(self, stage_string, project):
        if len(str(stage_string)) > 1:
            stage_str = str(stage_string).zfill(2)
            if stage_str.isnumeric():
                stage = self.search(
                    [('project_id.stage_identifier', '=', stage_str)], limit=1)
                if stage:
                    return stage
        return False
