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
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo import models, fields, api, _

class ProjectProgramCode(models.TransientModel):
    _name = 'project.program.code'


    _description = 'Program Code'
    _rec_name = 'program_code'

    conacyt_project_id = fields.Many2one('project.project','CONACYT Project',copy=False)
    
    year = fields.Many2one('year.configuration', string='Year (YEAR)', states={
                           'validated': [('readonly', True)]})

    # Program Relations
    program_id = fields.Many2one('program', string='Program')
    desc_program = fields.Text(
        string='Description KEY UNAM', related="program_id.desc_key_unam")

    # Sub Program Relation
    sub_program_id = fields.Many2one('sub.program', string='Sub program', states={
                                     'validated': [('readonly', True)]})
    desc_sub_program = fields.Text(
        string='Sub Program Description', related="sub_program_id.desc")

    # Dependency Relation
    dependency_id = fields.Many2one('dependency', string='Dependency')
    desc_dependency = fields.Text(
        string='Dependency Description', related="dependency_id.description")

    # Sub Dependency Relation
    sub_dependency_id = fields.Many2one(
        'sub.dependency', string='Sub dependency')
    desc_sub_dependency = fields.Text(
        string='Sub-dependency Description', related="sub_dependency_id.description")






    # Item Relation
    item_id = fields.Many2one(
        'expenditure.item', string='Item')
    desc_item = fields.Text(string='Description of Item',
                            related="item_id.description")

    @api.depends('program_id', 'program_id.key_unam',
                 'sub_program_id', 'sub_program_id.sub_program',
                 'dependency_id', 'dependency_id.dependency',
                 'sub_dependency_id', 'sub_dependency_id.sub_dependency',
                 'item_id', 'item_id.item'
                 )
    def _compute_check_digit(self):
        dv_obj = self.env['verifying.digit']
        for pc in self:
            pc.check_digit = '00'
            if pc.program_id and pc.sub_program_id and pc.dependency_id and pc.sub_dependency_id and pc.item_id:
                vd = dv_obj.check_digit_from_codes(
                    pc.program_id, pc.sub_program_id, pc.dependency_id, pc.sub_dependency_id, pc.item_id)
                pc.check_digit = vd

    check_digit = fields.Char(
        string='Check Digit (DV)', size=2, compute="_compute_check_digit", store=True)

    # Resource Origin Relation
    resource_origin_id = fields.Many2one(
        'resource.origin', string='Key Origin resource', states={'validated': [('readonly', True)]})
    desc_resource_origin = fields.Selection([
        ('subsidy', 'Federal Subsidy'),
        ('income', 'Extraordinary Income'),
        ('service', 'Education Services'),
        ('financial', 'Financial'),
        ('other', 'Other Products'),
        ('pef', 'Returns Reassignment PEF')],
        string='Description Resource Origin', related="resource_origin_id.desc")

    # Institutional Activity Relation
    institutional_activity_id = fields.Many2one(
        'institutional.activity', string='Institutional Activity Number', states={'validated': [('readonly', True)]})
    desc_institutional_activity = fields.Text(
        string='Activity Description Institutional', related="institutional_activity_id.description")

    # Budget ProgramConversion Relation
    budget_program_conversion_id = fields.Many2one(
        'budget.program.conversion', string='Conversion Program SHCP', states={'validated': [('readonly', True)]})
    desc_budget_program_conversion = fields.Text(
        string='Description Conversion Program SHCP', related="budget_program_conversion_id.description")

    # Federal Item Relation
    conversion_item_id = fields.Many2one(
        'departure.conversion', string='Federal Item', states={'validated': [('readonly', True)]})
    desc_conversion_item = fields.Text(
        string='Description of Federal Item', related="conversion_item_id.federal_part_desc")

    # Expense Type Relation
    expense_type_id = fields.Many2one(
        'expense.type', string='Key Expenditure Type', states={'validated': [('readonly', True)]})
    desc_expense_type = fields.Text(
        string='Description Expenditure Type', related="expense_type_id.description_expenditure_type")

    # Geographic Location Relation
    location_id = fields.Many2one(
        'geographic.location', string='Geographic Location', states={'validated': [('readonly', True)]})
    desc_location = fields.Text(
        string='Name of Geographic Location', related="location_id.state_name")

    # Wallet Password Relation
    portfolio_id = fields.Many2one('key.wallet', string='Key portfolio', states={
                                   'validated': [('readonly', True)]})
    name_portfolio = fields.Text(
        string='Name of Portfolio Key', related="portfolio_id.wallet_password_name")

    # Project Type Relation
    project_type_id = fields.Many2one('project.type', string='Type of Project', states={
                                      'validated': [('readonly', True)]})
    desc_project_type = fields.Char(
        string='Description Type of Project', related="project_type_id.desc_stage")
    project_number = fields.Char(
        string='Project Number', related='project_type_id.number')

    # Stage Relation
    stage_id = fields.Many2one('stage', string='Stage', states={
                               'validated': [('readonly', True)]})
    desc_stage = fields.Text(string='Stage Description',
                             related='stage_id.desc_stage')
    # Agreement Relation
    agreement_type_id = fields.Many2one('agreement.type', string='Type of Agreement', states={
                                        'validated': [('readonly', True)]})
    name_agreement = fields.Char(
        string='Name type of Agreement', related='agreement_type_id.name')
    number_agreement = fields.Char(
        string='Agreement number', related='agreement_type_id.number')

    @api.constrains('program_code')
    def _check_program_code(self):
        for record in self:
            if len(record.program_code) != 60:
                raise ValidationError('Program code must be 60 characters!')

    @api.depends('year', 'year.name', 'program_id', 'program_id.key_unam',
                 'sub_program_id', 'sub_program_id.sub_program',
                 'dependency_id', 'dependency_id.dependency',
                 'sub_dependency_id', 'sub_dependency_id.sub_dependency',
                 'item_id', 'item_id.item', 'check_digit',
                 'resource_origin_id', 'resource_origin_id.key_origin',
                 'institutional_activity_id', 'institutional_activity_id.number',
                 'budget_program_conversion_id', 'budget_program_conversion_id.shcp', 'budget_program_conversion_id.shcp.name',
                 'conversion_item_id', 'conversion_item_id.federal_part',
                 'expense_type_id', 'expense_type_id.key_expenditure_type',
                 'location_id', 'location_id.state_key',
                 'portfolio_id', 'portfolio_id.wallet_password',
                 'project_type_id', 'project_type_id.project_type_identifier', 'project_type_id.number',
                 'stage_id', 'stage_id.stage_identifier',
                 'agreement_type_id', 'agreement_type_id.agreement_type', 'agreement_type_id.number_agreement',
                 )
    def _compute_program_code(self):
        for pc in self:
            program_code = ''
            if pc.year:
                program_code += str(pc.year.name)
            if pc.program_id and pc.program_id.key_unam:
                program_code += str(pc.program_id.key_unam)
            if pc.sub_program_id and pc.sub_program_id.sub_program:
                program_code += str(pc.sub_program_id.sub_program)
            if pc.dependency_id and pc.dependency_id.dependency:
                program_code += str(pc.dependency_id.dependency)
            if pc.sub_dependency_id and pc.sub_dependency_id.sub_dependency:
                program_code += str(pc.sub_dependency_id.sub_dependency)
            if pc.item_id and pc.item_id.item:
                program_code += str(pc.item_id.item)
            if pc.check_digit:
                program_code += str(pc.check_digit)
            if pc.resource_origin_id and pc.resource_origin_id.key_origin:
                program_code += str(pc.resource_origin_id.key_origin)
            if pc.institutional_activity_id and pc.institutional_activity_id.number:
                program_code += str(pc.institutional_activity_id.number)
            if pc.budget_program_conversion_id and pc.budget_program_conversion_id.shcp and pc.budget_program_conversion_id.shcp.name:
                program_code += str(pc.budget_program_conversion_id.shcp.name)
            if pc.conversion_item_id and pc.conversion_item_id.federal_part:
                program_code += str(pc.conversion_item_id.federal_part)
            if pc.expense_type_id and pc.expense_type_id.key_expenditure_type:
                program_code += str(pc.expense_type_id.key_expenditure_type)
            if pc.location_id and pc.location_id.state_key:
                program_code += str(pc.location_id.state_key)
            if pc.portfolio_id and pc.portfolio_id.wallet_password:
                program_code += str(pc.portfolio_id.wallet_password)

            # Project Related Fields Data
            if pc.project_type_id and pc.project_type_id.project_type_identifier:
                program_code += str(pc.project_type_id.project_type_identifier)

            if pc.project_type_id and pc.project_type_id.number:
                program_code += str(pc.project_type_id.number)

            if pc.stage_id and pc.stage_id.stage_identifier:
                program_code += str(pc.stage_id.stage_identifier)

            if pc.agreement_type_id and pc.agreement_type_id.agreement_type:
                program_code += str(pc.agreement_type_id.agreement_type)

            if pc.agreement_type_id and pc.agreement_type_id.number_agreement:
                program_code += str(pc.agreement_type_id.number_agreement)

            pc.program_code = program_code
            pc.program_code_copy = program_code

    program_code = fields.Text(
        string='Programmatic Code', compute="_compute_program_code", store=True)
    program_code_copy = fields.Text(string='Programmatic Code')
    state = fields.Selection(
        [('draft', 'Draft'), ('validated', 'Validated')], default='draft', string='Status')

    def create_record(self):
        vals = {
            'conacyt_project_id' : self.conacyt_project_id and self.conacyt_project_id.id or False,
            'conacyt_code' : True,
            'year' : self.year and self.year.id or False,
            'program_id' : self.program_id and self.program_id.id or False,
            'sub_program_id' : self.sub_program_id and self.sub_program_id.id or False,
            'dependency_id' : self.dependency_id and self.dependency_id.id or False,
            'sub_dependency_id' : self.sub_dependency_id and self.sub_dependency_id.id or False,
            'item_id' : self.item_id and self.item_id.id or False,
            'resource_origin_id' : self.resource_origin_id and self.resource_origin_id.id or False,
            'institutional_activity_id' : self.institutional_activity_id and self.institutional_activity_id.id or False,
            'budget_program_conversion_id' : self.budget_program_conversion_id and self.budget_program_conversion_id.id or False,
            'conversion_item_id' : self.conversion_item_id and self.conversion_item_id.id or False,
            'expense_type_id' : self.expense_type_id and self.expense_type_id.id or False,
            'location_id' : self.location_id and self.location_id.id or False,
            'portfolio_id' : self.portfolio_id and self.portfolio_id.id or False,
            'project_type_id' : self.project_type_id and self.project_type_id.id or False,
            'stage_id' : self.stage_id and self.stage_id.id or False,
            'agreement_type_id' : self.agreement_type_id and self.agreement_type_id.id or False,
            'state' : self.state, 
            }
        program_code_id = self.env['program.code'].create(vals)
        self.env['custom.project.programcode'].create({'project_id':self.conacyt_project_id.id,'program_code_id':program_code_id.id})
        #self.conacyt_project_id.program_code = program_code_id.id
        self.conacyt_project_id.is_code_create = True 


    @api.onchange('project_type_id')
    def set_project_details(self):

        if self.project_type_id and self.project_type_id.project_id:
            project = self.project_type_id.project_id
            stage = self.env['stage'].search([('project_id','=',project.id)])
            if stage:
                self.stage_id = stage.id      

            agreement_type = self.env['agreement.type'].search([('project_id','=',project.id)])
            print ("agreement_type ::",agreement_type)
            if agreement_type:
                self.agreement_type_id = agreement_type.id