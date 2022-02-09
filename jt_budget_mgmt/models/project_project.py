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


class ProjectProject(models.Model):

    _inherit = 'project.project'

    project_type_identifier = fields.Char(
        string='PTI', size=2)
    number = fields.Char(string='Number', size=6)
    stage_identifier = fields.Char(string="SI", size=2)
    desc_stage = fields.Text(string='Description Stage')
    agreement_type = fields.Char(string='Agreement Type', size=2)
    name_agreement = fields.Text(string='Name Agreement')
    number_agreement = fields.Char(string='Number Agreement', size=6)

    # _sql_constraints = [('uniq_project_type_identifier', 'unique(project_type_identifier)',
    #                      'The Project Type Identifier must be unique!')]

    # _sql_constraints = [('uniq_number_project', 'unique(number)',
    #                      'The number must be unique!')]

    # _sql_constraints = [('uniq_number_agreement', 'unique(number_agreement)',
    #                      'The Number Agreement must be unique!')]

#     @api.constrains('project_type_identifier')
#     def _check_project_type_identifier(self):
#         if not str(self.project_type_identifier).isnumeric():
#             raise ValidationError(
#                 _('The Project Type Identifier must be numeric value'))

    @api.constrains('number')
    def _check_number(self):
        if self.number and not str(self.number).isnumeric():
            if self.env.user.lang == 'es_MX':
                raise ValidationError(_('El Número de Proyecto debe de ser un valor numérico'))
            else:
                raise ValidationError(_('The Project Number must be a numerical value'))

    @api.constrains('stage_identifier')
    def _check_stage_identifier(self):
        if self.stage_identifier and not str(self.stage_identifier).isnumeric():
            raise ValidationError(
                _('The Stage Identifier must be numeric value'))

#     @api.constrains('agreement_type')
#     def _check_agreement_type(self):
#         if not str(self.agreement_type).isnumeric():
#             raise ValidationError(
#                 _('The Agreement Type must be numeric value'))

    @api.constrains('number_agreement')
    def _check_number_agreement(self):
        if self.number_agreement and not str(self.number_agreement).isnumeric():
            raise ValidationError(
                _('The Number Agreement must be numeric value'))

    def fill_zero(self, code, digit):
        return str(code).zfill(digit)

    @api.model
    def create(self, vals):
        if vals.get('project_type_identifier') and len(vals.get('project_type_identifier')) != 2:
            vals['project_type_identifier'] = self.fill_zero(
                vals.get('project_type_identifier'), 2)
        if vals.get('number') and len(vals.get('number')) != 6:
            vals['number'] = self.fill_zero(vals.get('number'), 6)
        if vals.get('stage_identifier') and len(vals.get('stage_identifier')) != 2:
            vals['stage_identifier'] = self.fill_zero(
                vals.get('stage_identifier'), 2)
        if vals.get('agreement_type') and len(vals.get('agreement_type')) != 2:
            vals['agreement_type'] = self.fill_zero(
                vals.get('agreement_type'), 2)
        if vals.get('number_agreement') and len(vals.get('number_agreement')) != 6:
            vals['number_agreement'] = self.fill_zero(
                vals.get('number_agreement'), 6)
        res = super(ProjectProject, self).create(vals)
        
        if res.project_type_identifier:
            self.env['project.type'].create({'project_id':res.id})
        if res.stage_identifier:
            self.env['stage'].create({'project_id':res.id})
        if res.agreement_type:
            self.env['agreement.type'].create({'project_id':res.id})
            
        return res
    def write(self, vals):
        if vals.get('project_type_identifier') and len(vals.get('project_type_identifier')) != 2:
            vals['project_type_identifier'] = self.fill_zero(
                vals.get('project_type_identifier'), 2)
        if vals.get('number') and len(vals.get('number')) != 6:
            vals['number'] = self.fill_zero(vals.get('number'), 6)
        if vals.get('stage_identifier') and len(vals.get('stage_identifier')) != 2:
            vals['stage_identifier'] = self.fill_zero(
                vals.get('stage_identifier'), 2)
        if vals.get('agreement_type') and len(vals.get('agreement_type')) != 2:
            vals['agreement_type'] = self.fill_zero(
                vals.get('agreement_type'), 2)
        if vals.get('number_agreement') and len(vals.get('number_agreement')) != 6:
            vals['number_agreement'] = self.fill_zero(
                vals.get('number_agreement'), 6)
        return super(ProjectProject, self).write(vals)

    def name_get(self):
        result = []
        for project in self:
            display_name_field = project.name
            if self._context.get('display_name_custom'):
                if self._context.get('display_name_custom') == 'project_type_identifier':
                    display_name_field = project.project_type_identifier
                if self._context.get('display_name_custom') == 'stage_identifier':
                    display_name_field = project.stage_identifier
                if self._context.get('display_name_custom') == 'agreement_type':
                    display_name_field = project.agreement_type
            result.append((project.id, display_name_field))
        return result

    def unlink(self):
        for project in self:
            user_lang = self.env.user.lang
            project_type = self.env['project.type'].search([('project_id', '=', project.id)])
            if project_type:
                program_ids = self.env['program.code'].search([('project_type_id','in',project_type.ids)])
                if program_ids:
                    if user_lang == 'es_MX':
                        raise ValidationError('¡No puede eliminar proyectos asignados con el catálogo Tipo de Proyecto!!')
                    else:
                        raise ValidationError('You can not delete project which are mapped with project types!')
                else:
                    project_type.unlink()
                    
            stage = self.env['stage'].search([('project_id', '=', project.id)])
            if stage:
                program_ids = self.env['program.code'].search([('stage_id','in',stage.ids)])
                if program_ids:
                    raise ValidationError('You can not delete project which are mapped with stage identifier!')
                else:
                    stage.unlink()
                
            agreement_type = self.env['agreement.type'].search([('project_id', '=', project.id)])
            if agreement_type:
                program_ids = self.env['program.code'].search([('agreement_type_id','in',agreement_type.ids)])
                if program_ids:
                    raise ValidationError('You can not delete project which are mapped with agreement types!')
                else:
                    agreement_type.unlink()
                    
        return super(ProjectProject, self).unlink()
