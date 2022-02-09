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

class AgreementType(models.Model):

    _name = 'agreement.type'
    _description = 'Type of Agreement'
    _rec_name = 'agreement_type'

    project_id = fields.Many2one(
        'project.project', string='Type of Agreement')
    name = fields.Text(string='Name', )
    number = fields.Char(string='Number',)
    project_type_identifier = fields.Char(string='Project Type Identifier',
                                          related="project_id.project_type_identifier")
    desc_stage = fields.Text(string='Description', related="project_id.desc_stage")
    stage_identifier = fields.Char(string="Stage Identifier", related="project_id.stage_identifier")
    agreement_type = fields.Char(string='Agreement Type', store=True, related="project_id.agreement_type")
    name_agreement = fields.Text(string='Name Agreement', related="project_id.name_agreement")
    number_agreement = fields.Char(related='project_id.number_agreement', store=True, string='Number Agreement')

    @api.constrains('project_id')
    def _check_project_id(self):
        if self.project_id:
            p_type = self.search([('id', '!=', self.id), ('project_id', '=', self.project_id.id)], limit=1)
            if p_type:
                raise ValidationError(_('The agreement type identifier type must be unique'))

    def unlink(self):
        for agree_type in self:
            program_code = self.env['program.code'].search([('agreement_type_id', '=', agree_type.id)], limit=1)
            if program_code:
                raise ValidationError('You can not delete agreement type which are mapped with program code!')
        return super(AgreementType, self).unlink()

    def validate_agreement_type(self, agreement_type_string, project, agreement_number):
        if len(str(agreement_type_string)) > 1:
            agreement_type_str = str(agreement_type_string).zfill(2)
            #if agreement_type_str.isnumeric():
            agreement_type = self.search(
                    [('project_id.agreement_type', '=', agreement_type_str), ('number_agreement', '=', agreement_number)], limit=1)
            if agreement_type:
                return agreement_type
        return False
