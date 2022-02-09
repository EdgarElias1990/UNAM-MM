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
import base64
import io
import math
from datetime import datetime, timedelta
from xlrd import open_workbook
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import re

class Standardization(models.Model):

    _name = 'standardization'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Re-standardization'
    _rec_name = 'folio'

    def _get_count(self):
        for record in self:
            record.record_number = len(record.line_ids)
            record.all_line_count = len(record.line_ids)
            record.imported_record_number = len(
                record.line_ids.filtered(lambda l: l.imported == True))
            record.draft_count = len(
                record.line_ids.filtered(lambda l: l.state == 'draft'))
            record.received_count = len(
                record.line_ids.filtered(lambda l: l.state == 'received'))
            record.in_process_count = len(
                record.line_ids.filtered(lambda l: l.state == 'in_process'))
            record.authorized_count = len(
                record.line_ids.filtered(lambda l: l.state == 'authorized'))
            record.cancelled_count = len(
                record.line_ids.filtered(lambda l: l.state == 'cancelled'))

    cron_running = fields.Boolean(string='Running CRON?')
    folio = fields.Char(string='Folio', states={
        'confirmed': [('readonly', True)], 'cancelled': [('readonly', True)]}, tracking=True)
    record_number = fields.Integer(
        string='Number of records', compute='_get_count')
    imported_record_number = fields.Integer(
        string='Number of imported records', compute='_get_count')
    observations = fields.Text(string='Observations', tracking=True)
    select_box = fields.Boolean(string='Select Box')
    line_ids = fields.One2many(
        'standardization.line', 'standardization_id', string='Standardization lines', states={'cancelled': [('readonly', True)]})
    success_line_ids = fields.One2many(
        'standardization.line', 'standardization_id', string='Standardization lines', domain=[('line_state','not in',('draft','fail'))],states={'cancelled': [('readonly', True)]})

    import_line_ids = fields.One2many(
        'standardization.line', 'standardization_id',domain=[('line_state','in',('draft','fail'))] ,string='Standardization lines', states={'cancelled': [('readonly', True)]})

    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'),
                              ('cancelled', 'Cancelled')], default='draft', required=True, string='State')

    # Counter fields for line stage
    draft_count = fields.Integer(string='Draft', compute='_get_count')
    received_count = fields.Integer(string='Received', compute='_get_count')
    in_process_count = fields.Integer(
        string='In process', compute='_get_count')
    authorized_count = fields.Integer(
        string='Authorized', compute='_get_count')
    cancelled_count = fields.Integer(string='Cancelled', compute='_get_count')
    all_line_count = fields.Integer(string='Cancelled', compute='_get_count')
    check_line_state = fields.Boolean(
        compute="_compute_check_line_state", store=True)
    is_dgpo_authorization = fields.Boolean("DGPo authorization of games",copy=False,default=False)
    
    # journal_id = fields.Many2one('account.journal',string="Daily")
    # move_line_ids = fields.One2many("account.move.line", 'budget_standardization_id', string="Journal Items")
    #
    # @api.model
    # def default_get(self, fields):
    #     res = super(Standardization, self).default_get(fields)
    #     stand_app_jou = self.env.ref('jt_conac.re_standardization_jour')
    #     if stand_app_jou:
    #         res.update({'journal_id': stand_app_jou.id})
    #     return res
    
    @api.depends('line_ids', 'line_ids.state')
    def _compute_check_line_state(self):
        for standardization in self:
            standardization.check_line_state = False
            lines = standardization.line_ids.filtered(
                lambda l: l.amount_effected == False and l.state == 'authorized')
            for line in lines:
                if line.origin_id and line.quarter:
                    budget_lines = self.env['expenditure.budget.line'].search(
                        [('program_code_id', '=', line.code_id.id), ('expenditure_budget_id', '=', line.budget_id.id)])

                    origin_start_date_day = False
                    origin_start_date_month = False
                    origin_end_date_day = False
                    origin_end_date_month = False

                    date_start = str(line.origin_id.start_date).split('/')
                    if len(date_start) > 1:
                        origin_start_date_day = date_start[0]
                        origin_start_date_month = date_start[1]
                    date_end = str(line.origin_id.end_date).split('/')
                    if len(date_end) > 1:
                        origin_end_date_day = date_end[0]
                        origin_end_date_month = date_end[1]

                    origin_budget_line = False
                    for budget_line in budget_lines:
                        if budget_line.start_date and str(budget_line.start_date.day).zfill(2) == origin_start_date_day and str(budget_line.start_date.month).zfill(2) == origin_start_date_month and budget_line.end_date and str(budget_line.end_date.day).zfill(2) == origin_end_date_day and str(budget_line.end_date.month).zfill(2) == origin_end_date_month:
                            origin_budget_line = budget_line
                            break

                    quarter_start_date_day = False
                    quarter_start_date_month = False
                    quarter_end_date_day = False
                    quarter_end_date_month = False

                    date_start = str(line.quarter.start_date).split('/')
                    if len(date_start) > 1:
                        quarter_start_date_day = date_start[0]
                        quarter_start_date_month = date_start[1]
                    date_end = str(line.quarter.end_date).split('/')
                    if len(date_end) > 1:
                        quarter_end_date_day = date_end[0]
                        quarter_end_date_month = date_end[1]

                    quarter_budget_line = False
                    for budget_line in budget_lines:
                        if budget_line.start_date and str(budget_line.start_date.day).zfill(2) == quarter_start_date_day and str(budget_line.start_date.month).zfill(2) == quarter_start_date_month and budget_line.end_date and str(budget_line.end_date.day).zfill(2) == quarter_end_date_day and str(budget_line.end_date.month).zfill(2) == quarter_end_date_month:
                            quarter_budget_line = budget_line
                            break

                    if origin_budget_line and quarter_budget_line: 
                        if origin_budget_line.available >= line.amount:
                            amount = origin_budget_line.available - line.amount
                            origin_budget_line.write({'available': amount})
                            increase_amount = quarter_budget_line.available + line.amount
                            quarter_budget_line.write({'available': increase_amount})
                            line.amount_effected = True
                        if origin_budget_line.authorized >= line.amount:
                            amount = origin_budget_line.authorized - line.amount
                            origin_budget_line.write({'authorized': amount})
                            increase_amount = quarter_budget_line.authorized + line.amount
                            quarter_budget_line.write({'authorized': increase_amount})
                            line.amount_effected = True

                    #=====Update Control Assign Line===================#                    
                    contorl_lines = self.env['control.assigned.amounts.lines'].sudo().search(
                        [('program_code_id', '=', line.code_id.id),
                         ('assigned_amount_id.budget_id', '=', line.budget_id.id)])

                    origin_contorl_line = False
                    for contorl_line in contorl_lines:
                        if contorl_line.start_date and str(contorl_line.start_date.day).zfill(2) == origin_start_date_day and str(contorl_line.start_date.month).zfill(2) == origin_start_date_month and contorl_line.end_date and str(contorl_line.end_date.day).zfill(2) == origin_end_date_day and str(contorl_line.end_date.month).zfill(2) == origin_end_date_month:
                            origin_contorl_line = contorl_line
                            break                     

                    quarter_contorl_line = False
                    for contorl_line in contorl_lines:
                        if contorl_line.start_date and str(contorl_line.start_date.day).zfill(2) == quarter_start_date_day and str(contorl_line.start_date.month).zfill(2) == quarter_start_date_month and contorl_line.end_date and str(contorl_line.end_date.day).zfill(2) == quarter_end_date_day and str(contorl_line.end_date.month).zfill(2) == quarter_end_date_month:
                            quarter_contorl_line = contorl_line
                            break    

                    if origin_contorl_line:
                        amount = origin_contorl_line.available
                        origin_contorl_line.write({'available':amount - line.amount})     

                    if quarter_contorl_line:
                        amount = quarter_contorl_line.available
                        quarter_contorl_line.write({'available':amount + line.amount})     
                                
    _sql_constraints = [
        ('folio_uniq_const', 'unique(folio)', 'The folio must be unique.')]

    @api.constrains('folio')
    def _check_folio(self):
        if not str(self.folio).isnumeric():
            if self.env.user.lang == 'es_MX':
                raise ValidationError('Folio Debe ser un valor numérico!')
            else:
                raise ValidationError('Folio Must be numeric value!')
        folio = self.search(
            [('id', '!=', self.id), ('folio', '=', self.folio)], limit=1)
        if folio:
            if self.env.user.lang == 'es_MX':
                raise ValidationError('El folio debe ser único!')
            else:
                raise ValidationError('Folio Must be unique!')  

    def _compute_failed_rows(self):
        for record in self:
            record.failed_rows = 0
            try:
                data = eval(record.failed_row_ids)
                record.failed_rows = len(data)
            except:
                pass

    def _compute_success_rows(self):
        for record in self:
            record.success_rows = 0
            try:
                data = eval(record.success_row_ids)
                record.success_rows = len(data)
            except:
                pass

    def _compute_total_rows(self):
        for record in self:
            record.failed_rows = self.env['standardization.line'].search_count(
                [('standardization_id', '=', record.id), ('line_state', '=', 'fail')])
            record.success_rows = self.env['standardization.line'].search_count(
                [('standardization_id', '=', record.id), ('line_state', '=', 'success')])
            record.total_rows = len(record.line_ids.filtered(lambda l: l.imported == True))

    # Import process related fields
    allow_upload = fields.Boolean(string='Allow Update XLS File?')
    budget_file = fields.Binary(string='Uploaded File', states={
        'confirmed': [('readonly', True)], 'cancelled': [('readonly', True)]})
    filename = fields.Char(string='File name')
    import_status = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Completed')], default='draft', copy=False)
    failed_row_file = fields.Binary(string='Failed Rows File')
    fialed_row_filename = fields.Char(
        string='File name', default=lambda self: _("Failed_Rows.txt"))
    failed_rows = fields.Integer(
        string='Failed Rows',compute='_compute_total_rows')
    success_rows = fields.Integer(
        string='Success Rows', compute='_compute_total_rows')
    success_row_ids = fields.Text(
        string='Success Row Ids', default="[]", copy=False)
    failed_row_ids = fields.Text(
        string='Failed Row Ids', default="[]", copy=False)
    pointer_row = fields.Integer(
        string='Current Pointer Row', default=1, copy=False)
    total_rows = fields.Integer(string="Total Rows", copy=False,compute='_compute_total_rows')


    def check_program_item_games(self,program_code,item_name=False):
        item_name = item_name
        if not item_name and program_code and program_code.item_id:
            item_name = program_code.item_id.item
        program_code_msg = program_code and program_code.program_code or ''
        user_lang = self.env.user.lang
        
        if item_name and not self.is_dgpo_authorization:
            if item_name >= '100' and item_name <= '199':
                if item_name not in ('180','191','154','196','197'):
                    if user_lang == 'es_MX':
                        raise ValidationError(
                            _("Del grupo de partida 100 solo se permiten registrar laspartidas(180, 191, 154, 196 y 197): \n %s" %
                              program_code_msg))
                    else:
                        raise ValidationError(_("Form the group 100,only the following games are allowed (180,191,154,196 and 197): \n %s" %
                                                program_code_msg))
                    
            if item_name >= '700' and item_name <= '799':
                if item_name == '711':
                    if user_lang == 'es_MX':
                        raise ValidationError(
                            _("Forma el grupo 700, solo el Partida 711 no está permitido: \n %s" %
                              program_code_msg))
                    else:
                        raise ValidationError(_("Form the group 700, only 711 game is not allowed: \n %s" %
                                                program_code_msg))

            if item_name >= '300' and item_name <= '399':
                if user_lang == 'es_MX':
                    raise ValidationError(
                        _("No se pueden crear recalendarizaciones de la partida 300: \n %s" %
                          program_code_msg))
                else:
                    raise ValidationError(_("Cannot create reschedule of party group 300: \n %s" %
                                            program_code_msg))

    def check_year_exist(self, line):

        if len(str(line.year)) > 3:
            year_str = str(line.year)[:4]
            if year_str.isnumeric():
                year_obj = self.env['year.configuration'].search_read([], fields=['id', 'name'])
                if not list(filter(lambda yr: yr['name']==year_str, year_obj)):
                    self.env['year.configuration'].create({'name': year_str}).id
        else:
            raise ValidationError('Invalid Year Format Of line one!')

    def validate_and_add_budget_line(self, record_id=False, cron_id=False):
        if record_id:
            self = self.env['standardization'].browse(int(record_id))
        lines_to_validate = self.line_ids.filtered(lambda x:x.line_state in ('draft','fail'))
        if len(lines_to_validate) > 0:
            counter = 0
            failed_line_ids = []
            success_line_ids = []
            failed_row = ""
            self.check_year_exist(lines_to_validate[0])
            # Objects
            year_obj = self.env['year.configuration'].search_read([], fields=['id', 'name'])
            program_obj = self.env['program'].search_read([('program_key_id','!=',False)], fields=['id', 'key_unam','program_key_id'])
            subprogram_obj = self.env['sub.program'].search_read([('dependency_id','!=',False),('sub_dependency_id','!=',False),('unam_key_id','!=',False)], fields=['id','dependency_id','sub_dependency_id' ,'unam_key_id', 'sub_program'])
            dependancy_obj = self.env['dependency'].search_read([], fields=['id', 'dependency'])
            subdependancy_obj = self.env['sub.dependency'].search_read([],
                                                                       fields=['id', 'dependency_id', 'sub_dependency'])
            item_obj = self.env['expenditure.item'].search_read([], fields=['id', 'item', 'exercise_type'])
            origin_obj = self.env['resource.origin'].search_read([], fields=['id', 'key_origin'])
            activity_obj = self.env['institutional.activity'].search_read([], fields=['id', 'number'])
            
            #shcp_obj = self.env['budget.program.conversion'].search_read([('shcp_name','!=',False),('program_key_id','!=',False),('dep_con_id','!=',False)], fields=['id','program_key_id', 'shcp_name','dep_con_id','federal_part'])
            shcp_obj = self.env['budget.program.conversion'].search_read([('shcp_name','!=',False),('program_key_id','!=',False),('conversion_key_id','!=',False)], fields=['id','program_key_id', 'shcp_name','conversion_key_id','federal_part'])
            #shcp_obj = self.env['budget.program.conversion'].search_read([], fields=['id','unam_key_id', 'unam_key_code', 'shcp_name','dep_con_id','federal_part'])
            dpc_obj = self.env['departure.conversion'].search_read([('item_id','!=',False)], fields=['id', 'federal_part','item_id'])
            expense_type_obj = self.env['expense.type'].search_read([], fields=['id', 'key_expenditure_type'])
            location_obj = self.env['geographic.location'].search_read([], fields=['id', 'state_key'])
            wallet_obj = self.env['key.wallet'].search_read([], fields=['id', 'wallet_password'])
            project_type_obj = self.env['project.type'].search_read([],
                                                                    fields=['id', 'project_type_identifier', 'number'])
            stage_obj = self.env['stage'].search_read([], fields=['id', 'stage_identifier'])
            agreement_type_obj = self.env['agreement.type'].search_read([], fields=['id', 'agreement_type',
                                                                                    'number_agreement'])
            
            quarter_budget_obj = self.env['quarter.budget'].search_read([], fields=['id', 'name'])
            
#             cron = False
#             if cron_id:
#                 cron = self.env['ir.cron'].sudo().browse(int(cron_id))

            budget_obj = self.env['expenditure.budget'].sudo(
            ).with_context(from_adequacies=True)

            # If user re-scan for failed rows
            #re_scan_failed_rows_ids = eval(self.failed_row_ids)
            lines_to_execute = lines_to_validate
            for line in lines_to_execute:
                counter += 1
                line_vals = [line.year, line.program, line.subprogram, line.dependency, line.subdependency, line.item,
                             line.dv, line.origin_resource, line.ai, line.conversion_program,
                             line.departure_conversion, line.expense_type, line.location, line.portfolio,
                             line.project_type, line.project_number, line.stage, line.agreement_type,
                             line.agreement_number, line.exercise_type,line.folio,line.budget,line.origin,line.quarter_data]
                
                # Validate year format
                if len(str(line.year)) > 3:
                    year_str = str(line.year)[:4]
                    if year_str.isnumeric():
                        year = list(filter(lambda yr: yr['name'] == year_str, year_obj))
                        if year:
                            year = year[0]['id']
                        else:
                            if not self._context.get('from_adequacies'):
                                year = self.env['year.configuration'].create({'name': year_str}).id
                    if not year:
                        failed_row += str(line_vals) + \
                            "------>> Invalid Year Format\n"
                        failed_line_ids.append(line.id)
                        continue

                # Validate Program(PR)
                program = False
                program_key_id = False
                if len(str(line.program)) > 1:
                    program_str = str(line.program).zfill(2)
                    if program_str.isnumeric():
                        program = list(filter(lambda prog: prog['key_unam'] == program_str, program_obj))
                        program_key_id = program[0]['program_key_id'][0] if program else False
                        program = program[0]['id'] if program else False
                if not program:
                    failed_row += str(line_vals) + \
                        "------>> Invalid Program(PR) Format\n"
                    failed_line_ids.append(line.id)
                    continue

                # Validation Conversion Program SHCP
                shcp = False
                #program = False
                conversion_item = False
                
                departure_conversion_str = False
                if len(str(line.departure_conversion)) > 4:
                    departure_conversion_str = str(line.departure_conversion).zfill(4)
                    
                program_str = False
                if len(str(line.program)) > 1:
                    program_str = str(line.program).zfill(2)
                    
                if len(str(line.conversion_program)) > 3:
                    shcp_str = str(line.conversion_program)
                    if len(shcp_str) == 4 and (re.match("[A-Z]{1}\d{3}", str(shcp_str).upper())):
                        shcp = list(
                            filter(lambda tmp: tmp['shcp_name'] == shcp_str and tmp['program_key_id'][0] == program_key_id and tmp['federal_part']==departure_conversion_str,
                                   shcp_obj))
                        #program = shcp[0]['unam_key_id'][0] if shcp and shcp[0]['unam_key_id'] else False
                        #conversion_item  = shcp[0]['dep_con_id'][0] if shcp and shcp[0]['dep_con_id'] else False
                        shcp = shcp[0]['id'] if shcp else False
                        
                if not shcp:
                    failed_row += str(line_vals) + \
                                  "------>> Invalid Conversion Program SHCP(CONPP) Format\n"
                    failed_line_ids.append(line.id)
                    continue


                # Validate Dependency
                dependency = False
                if len(str(line.dependency)) > 2:
                    dependency_str = str(line.dependency).zfill(3)
                    if dependency_str.isnumeric():
                        dependency = list(filter(lambda dep: dep['dependency'] == dependency_str, dependancy_obj))
                        dependency = dependency[0]['id'] if dependency else False
                if not dependency:
                    failed_row += str(line_vals) + \
                        "------>> Invalid Dependency(DEP) Format\n"
                    failed_line_ids.append(line.id)
                    continue

                # Validate Sub-Dependency
                subdependency = False
                subdependency_str = str(line.subdependency).zfill(2)
                if subdependency_str.isnumeric():
                    subdependency = list(filter(
                        lambda sdo: sdo['sub_dependency'] == subdependency_str and sdo['dependency_id'][
                            0] == dependency, subdependancy_obj))
                    subdependency = subdependency[0]['id'] if subdependency else False
                if not subdependency:
                    failed_row += str(line_vals) + \
                        "------>> Invalid Sub Dependency(DEP) Format\n"
                    failed_line_ids.append(line.id)
                    continue

                # Validate Sub-Program
                subprogram = False
                if len(str(line.subprogram)) > 1:
                    subprogram_str = str(line.subprogram).zfill(2)
                    if subprogram_str.isnumeric():
                        subprogram = list(filter(lambda subp: subp['sub_program'] == subprogram_str and subp['unam_key_id'][0] == program and subp['dependency_id'][0] == dependency and subp['sub_dependency_id'][0] == subdependency, subprogram_obj))
                        subprogram = subprogram[0]['id'] if subprogram else False
                if not subprogram:
                    failed_row += str(line_vals) + \
                        "------>> Invalid SubProgram(SP) Format\n"
                    failed_line_ids.append(line.id)
                    continue
                
                #Validate item games group
                if len(str(line.item)) > 2 and not self.is_dgpo_authorization:
                    user_lang = self.env.user.lang
                    item_name =  str(line.item).zfill(3) 
                    if item_name >= '100' and item_name <= '199':
                        if item_name not in ('180','191','154','196','197'):
                            if user_lang == 'es_MX':
                                failed_row += str(line_vals) + \
                                              "------>> Del grupo de partida 100 solo se permiten registrar las partidas(180,191, 154, 196 y 197)\n"
                                failed_line_ids.append(line.id)
                                continue
                            else:
                                failed_row += str(line_vals) + \
                                              "------>> Form the group 100,only the following games are allowed (180,191,154,197 and 197):\n"
                                failed_line_ids.append(line.id)
                                continue
                                                             
                    elif item_name >= '700' and item_name <= '799':
                        if item_name == '711':                        
                            if user_lang == 'es_MX':
                                failed_row += str(line_vals) + \
                                              "------>> Forma el grupo 700, solo el Partida 711 no está permitido\n"
                                failed_line_ids.append(line.id)
                                continue
                            else:
                                failed_row += str(line_vals) + \
                                              "------>> Form the group 700, only 711 game is not allowed:\n"
                                failed_line_ids.append(line.id)
                                continue
         
                    elif item_name >= '300' and item_name <= '399':
                        if user_lang == 'es_MX':
                            failed_row += str(line_vals) + \
                                          "------>> No se pueden crear recalendarizaciones de la partida 300\n"
                            failed_line_ids.append(line.id)
                            continue
                        else:
                            failed_row += str(line_vals) + \
                                          "------>> Cannot create reschedule of party group 300:\n"
                            failed_line_ids.append(line.id)
                            continue
                    
                # Validate Item
                item = False
                if len(str(line.item)) > 2:
                    item_string = str(line.item).zfill(3)
                    typee = str(line.exercise_type).lower()
                    if typee not in ['r', 'c', 'd']:
                        typee = 'r'
                    if item_string.isnumeric():
                        item = list(filter(lambda itm: itm['item'] == item_string and itm['exercise_type'] == typee,
                                           item_obj))
                        if not item:
                            item = list(filter(lambda itm: itm['item'] == item_string, item_obj))
                        if item:
                            item = item[0]['id']
                if not item:
                    failed_row += str(line_vals) + \
                        "------>> Invalid Expense Item(PAR) Format\n"
                    failed_line_ids.append(line.id)
                    continue

                if not line.dv:
                    failed_row += str(line_vals) + \
                        "------>> Digito Verificador is not added! \n"
                    failed_line_ids.append(line.id)
                    continue

                origin_resource = False
                if len(str(line.origin_resource)) > 0:
                    origin_resource_str = str(line.origin_resource).replace('.', '').zfill(2)
                    if origin_resource_str.isnumeric():
                        origin_resource = list(
                            filter(lambda ores: ores['key_origin'] == origin_resource_str, origin_obj))
                        origin_resource = origin_resource[0]['id'] if origin_resource else False
                if not origin_resource:
                    failed_row += str(line_vals) + \
                        "------>> Invalid Origin Of Resource(OR) Format\n"
                    failed_line_ids.append(line.id)
                    continue

                # Validation Institutional Activity Number
                institutional_activity = False
                if len(str(line.ai)) > 2:
                    institutional_activity_str = str(line.ai).zfill(5)
                    if institutional_activity_str.isnumeric():
                        institutional_activity = list(
                            filter(lambda inact: inact['number'] == institutional_activity_str, activity_obj))
                        institutional_activity = institutional_activity[0][
                            'id'] if institutional_activity else False
                if not institutional_activity:
                    failed_row += str(line_vals) + \
                        "------>> Invalid Institutional Activity Number(AI) Format\n"
                    failed_line_ids.append(line.id)
                    continue

                # Validation Federal Item
                conversion_item = False
                if len(str(line.departure_conversion)) > 4:
                    conversion_item_str = str(line.departure_conversion).zfill(4)
                    if conversion_item_str.isnumeric():
                        conversion_item = list(filter(lambda coit: coit['federal_part'] == conversion_item_str and coit['item_id'][0]==item, dpc_obj))
                        conversion_item = conversion_item[0]['id'] if conversion_item else False
                if not conversion_item:
                    failed_row += str(line_vals) + \
                        "------>> Invalid SHCP Games(CONPA) Format\n"
                    failed_line_ids.append(line.id)
                    continue

                # Validation Expense Type
                expense_type = False
                if len(str(line.expense_type)) > 1:
                    expense_type_str = str(line.expense_type).zfill(2)
                    if expense_type_str.isnumeric():
                        expense_type = list(
                            filter(lambda exty: exty['key_expenditure_type'] == expense_type_str, expense_type_obj))
                        expense_type = expense_type[0]['id'] if expense_type else False
                if not expense_type:
                    failed_row += str(line_vals) + \
                        "------>> Invalid Expense Type(TG) Format\n"
                    failed_line_ids.append(line.id)
                    continue

                # Validation Geographic Location
                geo_location = False
                if len(str(line.location)) > 1:
                    location_str = str(line.location).zfill(2)
                    if location_str.isnumeric():
                        geo_location = list(filter(lambda geol: geol['state_key'] == location_str, location_obj))
                        geo_location = geo_location[0]['id'] if geo_location else False
                if not geo_location:
                    failed_row += str(line_vals) + \
                        "------>> Invalid Geographic Location (UG) Format\n"
                    failed_line_ids.append(line.id)
                    continue

                # Validation Wallet Key
                wallet_key = False
                if len(str(line.portfolio)) > 3:
                    wallet_key_str = str(line.portfolio).zfill(4)
                    if wallet_key_str.isnumeric():
                        wallet_key = list(
                            filter(lambda wlke: wlke['wallet_password'] == wallet_key_str, wallet_obj))
                        wallet_key = wallet_key[0]['id'] if wallet_key else False
                if not wallet_key:
                    failed_row += str(line_vals) + \
                        "------>> Invalid Wallet Key(CC) Format\n"
                    failed_line_ids.append(line.id)
                    continue

                # Validation Project Type
                project_type = False
                if len(str(line.project_type)) > 1:
                    number = ''
                    if self._context.get('from_adjustment'):
                        number = line.get('No. de Proyecto')
                    else:
                        number = line.project_number
                    project_type_str = str(line.project_type).zfill(2)

                    project_type = list(filter(
                        lambda pt: pt['project_type_identifier'] == project_type_str and pt['number'] == number,
                        project_type_obj))
                    project_type = project_type[0]['id'] if project_type else False
                if not project_type:
                    failed_row += str(project_type) + \
                        "------>> Invalid Project Type(TP) or Project Number Format\n"
                    failed_line_ids.append(line.id)
                    continue

                # Validation Stage
                stage = False
                if len(str(line.stage)) > 1:
                    stage_str = str(line.stage).zfill(2)
                    if stage_str.isnumeric():
                        stage = list(filter(lambda stg: stg['stage_identifier'] == stage_str, stage_obj))
                        stage = stage[0]['id'] if stage else False
                if not stage:
                    failed_row += str(line_vals) + \
                        "------>> Invalid Stage(E) Format\n"
                    failed_line_ids.append(line.id)
                    continue

                # Validation Agreement Type
                agreement_type = False
                if len(str(line.agreement_type)) > 1:
                    agreement_type_str = str(line.agreement_type).zfill(2)
                    agreement_type = list(filter(lambda aty: aty['agreement_type'] == agreement_type_str and aty[
                        'number_agreement'] == line.agreement_number, agreement_type_obj))
                    ('project_id.agreement_type', '=',)
                    agreement_type = agreement_type[0]['id'] if agreement_type else False
                if not agreement_type:
                    failed_row += str(line_vals) + \
                        "------>> Invalid Agreement Type(TC) or Agreement Number Format\n"
                    failed_line_ids.append(line.id)
                    continue


                # Validation Amount
                asigned_amount = 0
                try:
                    asigned_amount = float(line.amount)
                    if asigned_amount < 0:
                        failed_row += str(line_vals) + \
                            "------>> Amount should be greater than 0"
                        failed_line_ids.append(line.id)
                        continue
                except:
                    failed_row += str(line_vals) + \
                        "------>> Invalid Amount Format or Amount should be 0"
                    failed_line_ids.append(line.id)
                    continue
                
                # Validation Folio
                folio = line.folio
                if folio:
                    try:
                        folio = int(float(folio))
                    except:
                        failed_row += str(line_vals) + \
                            "------>> Folio Must Be Numeric"
                        failed_line_ids.append(line.id)    
                        continue
                    line_standardization = self.env['standardization.line'].search(
                        [('folio', '=', str(folio)),('id','!=',line.id)], limit=1)
                    if line_standardization:
                        failed_row += str(line_vals) + \
                            "------>> Folio Must Be Unique"
                        failed_line_ids.append(line.id)
                        continue
                else:
                    failed_row += str(line_vals) + \
                        "------>> Invalid Folio Format"
                    failed_line_ids.append(line.id)
                    continue

                # Validation Budget
                budget_str = line.budget
                budget = budget_obj.search(
                    [('name', '=', budget_str)], limit=1)
                if not budget:
                    failed_row += str(line_vals) + \
                        "------>> Budget Not Found"
                    failed_line_ids.append(line.id)
                    continue

                # Validate Origin
                origin = False
                if line.origin:
                    origin = list(
                                filter(lambda wlke: wlke['name'] == line.origin, quarter_budget_obj))
                    origin = origin[0]['id'] if origin else False
                    
                if not origin:
                    failed_row += str(line_vals) + \
                        "------>> Origin Not Found\n"
                    failed_line_ids.append(line.id)
                    continue
                
                quarter_data = False
                if line.quarter_data:
                    quarter_data = list(
                                filter(lambda wlke: wlke['name'] == line.quarter_data, quarter_budget_obj))
                    quarter_data = quarter_data[0]['id'] if quarter_data else False
                
                if not quarter_data:
                    failed_row += str(line_vals) + \
                        "------>> Quarter Not Found\n"
                    failed_line_ids.append(line.id)
                    continue

                try:
                    program_code = False
                    if stage and origin and budget and year and program and subprogram and dependency and subdependency and item and origin_resource and institutional_activity and shcp and conversion_item and expense_type and geo_location and wallet_key and project_type and stage and agreement_type:
                        search_key_fields = (
                                     year, program, subprogram, dependency, subdependency, item,
                                     origin_resource, institutional_activity, shcp, conversion_item,
                                     expense_type, geo_location, wallet_key, project_type, stage, agreement_type)
                        search_key = ';'.join([str(skey) for skey in search_key_fields])
                        program_code = self.env['program.code'].search([('search_key', '=', search_key)], limit=1)
                        
#                         program_code = self.env['program.code'].sudo().search([
#                             ('year', '=', year.id),
#                             ('program_id', '=', program.id),
#                             ('sub_program_id', '=', subprogram.id),
#                             ('dependency_id', '=', dependency.id),
#                             ('sub_dependency_id', '=', subdependency.id),
#                             ('item_id', '=', item.id),
#                             ('resource_origin_id', '=', origin_resource.id),
#                             ('institutional_activity_id',
#                              '=', institutional_activity.id),
#                             ('budget_program_conversion_id', '=', shcp.id),
#                             ('conversion_item_id', '=', conversion_item.id),
#                             ('expense_type_id', '=', expense_type.id),
#                             ('location_id', '=', geo_location.id),
#                             ('portfolio_id', '=', wallet_key.id),
#                             ('project_type_id', '=', project_type.id),
#                             ('stage_id', '=', stage.id),
#                             ('agreement_type_id', '=', agreement_type.id),
#                             ('state', '=', 'validated'),
#                         ], limit=1)

                        if program_code:
                            self.check_program_item_games(program_code,False)
                            budget_line = self.env['expenditure.budget.line'].sudo().search(
                                [('program_code_id', '=', program_code.id), ('expenditure_budget_id', '=', budget.id)], limit=1)
                            if not budget_line:
                                failed_row += str(line_vals) + \
                                    "------>> Budget line not found for selected program code!"
                                failed_line_ids.append(line.id)
                                continue

                        if program_code:
                            pc = program_code
                            dv_obj = self.env['verifying.digit']
                            if pc.program_id and pc.sub_program_id and pc.dependency_id and \
                                    pc.sub_dependency_id and pc.item_id:
                                vd = dv_obj.check_digit_from_codes(
                                    pc.program_id, pc.sub_program_id, pc.dependency_id, pc.sub_dependency_id,
                                    pc.item_id)
                                if vd and line.dv:
                                    line_dv = line.dv
                                    if len(line.dv) == 1:
                                        line_dv = '0' + line.dv
                                    if vd != line_dv:
                                        failed_row += str(line_vals) + \
                                                      "------>> Digito Verificador is not matched! \n"
                                        failed_line_ids.append(line.id)
                                        continue

                    if not program_code:
                        failed_row += str(line_vals) + \
                            "-------> Program Code is not created. \n"
                        failed_line_ids.append(line.id)
                        continue
                    
                    success_line_ids.append(line.id)

#                     if self._context.get('re_scan_failed'):
#                         failed_row_ids_eval_refill = eval(self.failed_row_ids)
#                         failed_row_ids_eval_refill.remove(pointer)
#                         self.write({'failed_row_ids': str(
#                             list(set(failed_row_ids_eval_refill)))})
                    line.write({
                        #'folio': folio,
                        'code_id': program_code.id,
                        'budget_id': budget.id,
                        #'amount': amount,
                        'origin_id': origin,
                        'quarter': quarter_data,
                        'imported': True,
                    })
#                     if not self.line_ids.filtered(lambda x:x.code_id.id==program_code.id):
#                         self.write({'line_ids': [(0, 0, line_vals)]})
                except:
                    failed_row += str(line_vals) + \
                        "------>> Row Data Are Not Corrected or Validated Program Code Not Found or Program Code not associated with selected budget!"
                    failed_line_ids.append(line.id)


            failed_lines = self.env['standardization.line'].browse(failed_line_ids)
            success_lines = self.env['standardization.line'].browse(success_line_ids)
            success_lines.write({'line_state': 'success'})
            for l in failed_lines.filtered(lambda x:x.line_state=='draft'):
                l.line_state = 'fail'
            if self.failed_rows == 0:
                self.import_status = 'done'
                
            vals = {}
            failed_data = False
            if failed_row != "":
                content = ""
                if self.failed_row_file:
                    file_data = base64.b64decode(self.failed_row_file)
                    content += io.StringIO(file_data.decode("utf-8")).read()
                content += "\n"
                content += "...................Failed Rows " + \
                    str(datetime.today()) + "...............\n"
                content += str(failed_row)
                failed_data = base64.b64encode(content.encode('utf-8'))
                vals['failed_row_file'] = failed_data

            if vals:
                self.write(vals)

    def remove_cron_records(self):
        crons = self.env['ir.cron'].sudo().search([('model_id', '=', self.env.ref('jt_budget_mgmt.model_standardization').id)])
        for cron in crons:
            if cron.standardization_id and not cron.standardization_id.cron_running:
                try:
                    cron.sudo().unlink()
                except:
                    pass

    def send_notification_msg(self, user, failed, successed):
        ch_obj = self.env['mail.channel']
        base_user = self.env.ref('base.user_root')
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url = base_url + '/web#id=%s&view_type=form&model=standardization' % (self.id)
        body = (_("Re-standardization Validation Process is Completed for \
                    <a href='%s' target='new'>%s</a>" % (url, self.folio)))
        body += (_("<ul><li>Total Successed Lines: %s </li>\
            <li>Total Failed Lines: %s </li></ul>") % (str(successed), str(failed)))
        if user:
            ch = ch_obj.sudo().search([('name', '=', str(base_user.name + ', ' + user.name)),
                                       ('channel_type', '=', 'chat')], limit=1)
            if not ch:
                ch = ch_obj.create({
                    'name': 'OdooBot, ' + user.name,
                    'public': 'private',
                    'channel_type': 'chat',
                    'channel_last_seen_partner_ids': [(0, 0, {'partner_id': user.partner_id.id,
                                                              'partner_email': user.partner_id.email}),
                                                      (0, 0, {'partner_id': base_user.partner_id.id,
                                                              'partner_email': base_user.partner_id.email})
                                                      ]
                })
            ch.message_post(attachment_ids=[], body=body, content_subtype='html',
                            message_type='comment', partner_ids=[], subtype='mail.mt_comment',
                            email_from=base_user.partner_id.email, author_id=base_user.partner_id.id)
        return True

    def validate_draft_lines(self):
        
        if self.line_ids.filtered(lambda x:x.line_state in ('draft','fail')):
            self.validate_and_add_budget_line()
        if self.failed_rows ==0:
            self.import_status = 'done'
            # Total CRON to create
#             data = base64.decodestring(self.budget_file)
#             book = open_workbook(file_contents=data or b'')
#             sheet = book.sheet_by_index(0)
#             total_sheet_rows = sheet.nrows - 1
#             total_cron = math.ceil(total_sheet_rows / 5000)
#             msg = (_("Re-standardization Validation Process Started at %s" % datetime.strftime(
#                 datetime.now(), DEFAULT_SERVER_DATETIME_FORMAT)))
#             self.env['mail.message'].create({'model': 'standardization', 'res_id': self.id,
#                                              'body': msg})
#             if total_cron == 1:
#                 self.validate_and_add_budget_line()
#                 msg = (_("Re-standardization Validation Process Ended at %s" % datetime.strftime(
#                     datetime.now(), DEFAULT_SERVER_DATETIME_FORMAT)))
#                 self.env['mail.message'].create({'model': 'standardization', 'res_id': self.id,
#                                                  'body': msg})
#             else:
#                 self.write({'cron_running': True})
#                 prev_cron_id = False
#                 for seq in range(1, total_cron + 1):
#                     # Create CRON JOB
#                     cron_name = str(self.folio).replace(' ', '') + "_" + str(datetime.now()).replace(' ', '')
#                     nextcall = datetime.now()
#                     nextcall = nextcall + timedelta(seconds=10)
# 
#                     cron_vals = {
#                         'name': cron_name,
#                         'state': 'code',
#                         'nextcall': nextcall,
#                         'nextcall_copy': nextcall,
#                         'numbercall': -1,
#                         'code': "model.validate_and_add_budget_line()",
#                         'model_id': self.env.ref('jt_budget_mgmt.model_standardization').id,
#                         'user_id': self.env.user.id,
#                         'standardization_id': self.id
#                     }
# 
#                     # Final process
#                     cron = self.env['ir.cron'].sudo().create(cron_vals)
#                     cron.write({'code': "model.validate_and_add_budget_line(" + str(self.id) + "," + str(cron.id) + ")"})
#                     if prev_cron_id:
#                         cron.write({'prev_cron_id': prev_cron_id, 'active': False})
#                     prev_cron_id = cron.id

        
    def validate_data(self):
        user_lang = self.env.user.lang
        if len(self.line_ids.ids) == 0:
            raise ValidationError(_("Please Add Standardization Lines"))
        if self.failed_rows > 0:
            raise ValidationError("Please correct failed rows!")

        lines = self.line_ids.filtered(lambda l: l.amount == 0)
        if lines:
            raise ValidationError("Row Amount must be greater than 0!")

        if self.total_rows > 0 and self.success_rows != self.total_rows:
            raise ValidationError(
                "Total imported rows not matched with total standardization lines!")

        bugdet_l_obj = self.env['expenditure.budget.line']
        for line in self.line_ids:
            if line.code_id:
                self.check_program_item_games(line.code_id)
                                
            if line.amount and line.origin_id and line.code_id and line.budget_id:
                budget_lines = bugdet_l_obj.search([('expenditure_budget_id', '=', line.budget_id.id),
                                                    ('program_code_id', '=', line.code_id.id)])
                origin_start_date_day = False
                origin_start_date_month = False
                origin_end_date_day = False
                origin_end_date_month = False

                dest_start_date_day = False
                dest_start_date_month = False
                dest_end_date_day = False
                dest_end_date_month = False

                date_start = str(line.origin_id.start_date).split('/')
                if len(date_start) > 1:
                    origin_start_date_day = date_start[0]
                    origin_start_date_month = date_start[1]
                date_end = str(line.origin_id.end_date).split('/')
                if len(date_end) > 1:
                    origin_end_date_day = date_end[0]
                    origin_end_date_month = date_end[1]
                date_start = str(line.quarter.start_date).split('/')
                if len(date_start) > 1:
                    dest_start_date_day = date_start[0]
                    dest_start_date_month = date_start[1]
                date_end = str(line.quarter.end_date).split('/')
                if len(date_end) > 1:
                    dest_end_date_day = date_end[0]
                    dest_end_date_month = date_end[1]
                origin_budget_line = False
                dest_budget_line = False
                for budget_line in budget_lines:
                    if not origin_budget_line:
                        if budget_line.start_date and str(budget_line.start_date.day).zfill(
                                2) == origin_start_date_day and str(budget_line.start_date.month).zfill(
                                2) == origin_start_date_month and budget_line.end_date and str(
                                budget_line.end_date.day).zfill(2) == origin_end_date_day and str(
                                budget_line.end_date.month).zfill(2) == origin_end_date_month:
                            origin_budget_line = budget_line
                    if not dest_budget_line:
                        if budget_line.start_date and str(budget_line.start_date.day).zfill(
                                2) == dest_start_date_day and str(budget_line.start_date.month).zfill(
                                2) == dest_start_date_month and budget_line.end_date and str(
                                budget_line.end_date.day).zfill(2) == dest_end_date_day and str(
                                budget_line.end_date.month).zfill(2) == dest_end_date_month:
                            dest_budget_line = budget_line
                if not dest_budget_line:
                    if user_lang == 'es_MX':
                        raise ValidationError(
                            _("La línea presupuestaria trimestral no se crea para este código de programa: \n %s" %
                              line.code_id.program_code))
                    else:
                        raise ValidationError(_("Quarter budget line is not created for this program code: \n %s" %
                                                line.code_id.program_code))
                if not origin_budget_line:
                    if user_lang == 'es_MX':
                        raise ValidationError(_("La línea presupuestaria Origen no se crea para este código de "
                                                "programa: \n %s" % line.code_id.program_code))
                    raise ValidationError(_("Origin budget line is not created for this program code: \n %s" %
                                            line.code_id.program_code))
                if origin_budget_line and line.amount > origin_budget_line.available:
                    if user_lang == 'es_MX':
                        raise ValidationError(_("El monto es mayor que el asignado en el presupuesto. \n Presupuesto:"
                                                " %s \nCódigo del programa de: %s \nEl monto requerido es de $ %s y el monto disponible es de $ %s " % (
                                                line.budget_id.name, line.code_id.program_code,line.amount,origin_budget_line.available)))
                    else:
                        raise ValidationError(_("The amount is greater than the one assigned in the budget. \n Budget:"
                                                " %s \nProgram Code: %s \nThe required amount is $ %s and the available amount is $ %s" 
                                                % (line.budget_id.name, line.code_id.program_code,line.amount,origin_budget_line.available)))

    def confirm(self):
        self.validate_data()
        self.state = 'confirmed'
        self.line_ids.write({'state': 'draft'})

    def cancel(self):
        self.state = 'cancelled'

    def import_lines(self):
        return {
            'name': _('Import Standardization Lines'),
            'type': 'ir.actions.act_window',
            'res_model': 'import.standardization.line',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(False, 'form')],
            'target': 'new',
        }

    def action_draft(self):
        if self.state != 'confirmed':
            raise ValidationError(_("You can only change the status of the rescheduling lines for confirmed rescheduling"))
        
        lines = self.line_ids.filtered(
            lambda l: l.selected == True and l.state != False and l.state != 'draft')
        if lines:
            if self.env.user.lang == 'es_MX':
                raise ValidationError("No puedes saltar o devolver el estado de una línea de Recalendarización")
            else:
                raise ValidationError("You cannot skip or return the status of a Re-scheduling line")

        
        lines = self.line_ids.filtered(lambda l: l.selected == True and l.state == False)
        for line in lines:
            line.state = 'draft'

    def action_received(self):
        if self.state != 'confirmed':
            raise ValidationError(_("You can only change the status of the rescheduling lines for confirmed rescheduling"))

        lines = self.line_ids.filtered(
            lambda l: l.selected == True and l.state not in ('draft','received'))
        if lines:
            if self.env.user.lang == 'es_MX':
                raise ValidationError("No puedes saltar o devolver el estado de una línea de Recalendarización")
            else:
                raise ValidationError("You cannot skip or return the status of a Re-scheduling line")
                
        lines = self.line_ids.filtered(
            lambda l: l.selected == True and l.state == 'draft')
        
        for line in lines:
            line.state = 'received'

    def action_in_process(self):
        if self.state != 'confirmed':
            raise ValidationError(_("You can only change the status of the rescheduling lines for confirmed rescheduling"))

        lines = self.line_ids.filtered(
            lambda l: l.selected == True and l.state not in ('in_process','received'))
        if lines:
            if self.env.user.lang == 'es_MX':
                raise ValidationError("No puedes saltar o devolver el estado de una línea de Recalendarización")
            else:
                raise ValidationError("You cannot skip or return the status of a Re-scheduling line")
        
        lines = self.line_ids.filtered(
            lambda l: l.selected == True and l.state == 'received')
        for line in lines:
            line.state = 'in_process'

    def action_authorized(self):
        if self.state != 'confirmed':
            raise ValidationError(_("You can only change the status of the rescheduling lines for confirmed rescheduling"))

        lines = self.line_ids.filtered(
            lambda l: l.selected == True and l.state not in ('in_process','authorized'))
        if lines:
            if self.env.user.lang == 'es_MX':
                raise ValidationError("No puedes saltar o devolver el estado de una línea de Recalendarización")
            else:
                raise ValidationError("You cannot skip or return the status of a Re-scheduling line")
        
        lines = self.line_ids.filtered(
            lambda l: l.selected == True and l.state == 'in_process')
        for line in lines:
            line.state = 'authorized'
            
        # if lines and self.journal_id:
        #     move_obj = self.env['account.move']
        #     journal = self.journal_id
        #     today = datetime.today().date()
        #     user = self.env.user
        #     partner_id = user.partner_id.id
        #     amount = sum(lines.mapped('amount'))
        #     company_id = user.company_id.id
        #     if not journal.default_debit_account_id or not journal.default_credit_account_id \
        #             or not journal.conac_debit_account_id or not journal.conac_credit_account_id:
        #         if self.env.user.lang == 'es_MX':
        #             raise ValidationError(_("Por favor configure la cuenta UNAM y CONAC en diario!"))
        #         else:
        #             raise ValidationError(_("Please configure UNAM and CONAC account in budget journal!"))
        #     unam_move_val = {'ref': self.folio, 'budget_standardization_id': self.id, 'conac_move': True,
        #                      'date': today, 'journal_id': journal.id, 'company_id': company_id,
        #                      'line_ids': [(0, 0, {
        #                          'account_id': journal.default_credit_account_id.id,
        #                          'coa_conac_id': journal.conac_credit_account_id.id,
        #                          'credit': amount, 'budget_standardization_id': self.id,
        #                          'partner_id': partner_id
        #                      }), (0, 0, {
        #                          'account_id': journal.default_debit_account_id.id,
        #                          'coa_conac_id': journal.conac_debit_account_id.id,
        #                          'debit': amount, 'budget_standardization_id': self.id,
        #                          'partner_id': partner_id
        #                      })]}
        #     unam_move = move_obj.create(unam_move_val)
        #     unam_move.action_post()
             
    def action_cancelled(self):
        if self.state != 'confirmed':
            raise ValidationError(_("You can only change the status of the rescheduling lines for confirmed rescheduling"))
        
        lines = self.line_ids.filtered(lambda l: l.selected == True and l.state == 'authorized')
        if lines:
            if self.env.user.lang == 'es_MX':
                raise ValidationError("No puede cancelar la línea de Recalendarización autorizada")
            else:
                raise ValidationError("You cannot Canceled the Authorized  Re-scheduling line")
        
        lines = self.line_ids.filtered(lambda l: l.selected == True and l.state != 'authorized')
        
        for line in lines:
            line.state = 'cancelled'
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'reject.standardization.line',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            'context': {'parent_id': self.id, }
        }

    def draft_button(self):
        action = self.env.ref(
            'jt_budget_mgmt.action_standardization_lines').read()[0]
        action['view_mode'] = 'tree'
        action['domain'] = [
            ('standardization_id', '=', self.id), ('state', '=', 'draft')]
        return action

    def received_button(self):
        action = self.env.ref(
            'jt_budget_mgmt.action_standardization_lines').read()[0]
        action['view_mode'] = 'tree'
        action['domain'] = [
            ('standardization_id', '=', self.id), ('state', '=', 'received')]
        return action

    def in_process_button(self):
        action = self.env.ref(
            'jt_budget_mgmt.action_standardization_lines').read()[0]
        action['view_mode'] = 'tree'
        action['domain'] = [
            ('standardization_id', '=', self.id), ('state', '=', 'in_process')]
        return action

    def authorized_button(self):
        action = self.env.ref(
            'jt_budget_mgmt.action_standardization_lines').read()[0]
        action['view_mode'] = 'tree'
        action['domain'] = [
            ('standardization_id', '=', self.id), ('state', '=', 'authorized')]
        return action

    def cancelled_button(self):
        action = self.env.ref(
            'jt_budget_mgmt.action_standardization_lines').read()[0]
        action['view_mode'] = 'tree'
        action['domain'] = [
            ('standardization_id', '=', self.id), ('state', '=', 'cancelled')]
        return action

    def all_lines_button(self):
        action = self.env.ref(
            'jt_budget_mgmt.action_standardization_lines').read()[0]
        action['view_mode'] = 'tree'
        action['domain'] = [
            ('standardization_id', '=', self.id)]
        return action

    def select_deselect_checkbox(self):
        if self.select_box:
            self.select_box = False
        else:
            self.select_box = True

        self.line_ids.write({'selected': self.select_box})

    def unlink(self):
        for budget in self:
            if budget.state != 'draft':
                if self.env.user.lang == 'es_MX':
                    raise ValidationError(
                        'No se puede eliminar una Recalendarización validada!')                    
                else:
                    raise ValidationError(
                        'You can not delete confirmed Re-standardization!')
        return super(Standardization, self).unlink()

    @api.model
    def create(self,vals):
        if not vals.get('name',False):
            name = self.env['ir.sequence'].next_by_code('re.standardization.folio')
            vals.update({'folio':name})
        res = super(Standardization,self).create(vals)
        return res

class StandardizationLine(models.Model):

    _name = 'standardization.line'
    _description = 'Re-standardization Lines'
    _rec_name = 'folio'

    @api.depends('origin_id','origin_id.end_date','origin_id.start_date')
    def get_origin_data(self):
        for line in self:
            if line.origin_id and line.origin_id.end_date:
                date_end = str(line.origin_id.end_date).split('/')
                if len(date_end) > 1:
                    line.origin_id_end_day = int(date_end[0])
                    line.origin_id_end_month = int(date_end[1])
                    
            if line.origin_id and line.origin_id.start_date:
                start_end = str(line.origin_id.start_date).split('/')
                if len(start_end) > 1:
                    line.origin_id_start_day = int(start_end[0])
                    line.origin_id_start_month = int(start_end[1])


    @api.depends('quarter','quarter.end_date','quarter.start_date')
    def get_quarter_data(self):
        for line in self:
            if line.quarter and line.quarter.end_date:
                date_end = str(line.quarter.end_date).split('/')
                if len(date_end) > 1:
                    line.quarter_end_day = int(date_end[0])
                    line.quarter_end_month = int(date_end[1])
                    
            if line.quarter and line.quarter.start_date:
                start_end = str(line.quarter.start_date).split('/')
                if len(start_end) > 1:
                    line.quarter_start_day = int(start_end[0])
                    line.quarter_start_month = int(start_end[1])
                
    folio = fields.Char(string='Folio')
    budget_id = fields.Many2one('expenditure.budget', string='Budget', domain="[('state', '=', 'validate')]")
    code_id = fields.Many2one(
        'program.code', string='Code', domain="[('budget_id', '=', budget_id)]")
    amount = fields.Monetary(string='Amount', currency_field='currency_id')
    origin_id = fields.Many2one('quarter.budget', string='Origin')
    quarter = fields.Many2one('quarter.budget', string='Quarter')
    origin_id_start_month = fields.Integer('Origin Month',compute='get_origin_data',store=True)
    origin_id_start_day = fields.Integer('Origin Day',compute='get_origin_data',store=True)
    origin_id_end_month = fields.Integer('Origin Month',compute='get_origin_data',store=True)
    origin_id_end_day = fields.Integer('Origin Day',compute='get_origin_data',store=True)
    
    quarter_start_month = fields.Integer('quarter Month',compute='get_quarter_data',store=True)
    quarter_start_day = fields.Integer('quarter Day',compute='get_quarter_data',store=True)
    quarter_end_month = fields.Integer('quarter Month',compute='get_quarter_data',store=True)
    quarter_end_day = fields.Integer('quarter Day',compute='get_quarter_data',store=True)
    
    reason = fields.Text(string='Reason for rejection')
    standardization_id = fields.Many2one(
        'standardization', string='Standardization', ondelete="cascade")
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.user.company_id.currency_id)
    imported = fields.Boolean(default=False)
    amount_effected = fields.Boolean(string='Amount Effected?')
    selected = fields.Boolean(default=False)
    state = fields.Selection([('draft', 'Draft'), ('received', 'Received'),
                              ('in_process', 'In process'),
                              ('authorized', 'Authorized'),
                              ('cancelled', 'Cancelled')],
                             string='State')

    # Fields for imported data

    line_state = fields.Selection([('manual', 'Manual'), ('draft', 'Draft'), (
        'fail', 'Fail'), ('success', 'Success')], string='Line Status', default='manual')
        
    year = fields.Char(string='Year')
    program = fields.Char(string='Program')
    subprogram = fields.Char(string='Sub-Program')
    dependency = fields.Char(string='Dependency')
    subdependency = fields.Char(string='Sub-Dependency')
    item = fields.Char(string='Expense Item')
    dv = fields.Char(string='Digit Varification')
    origin_resource = fields.Char(string='Origin Resource')
    ai = fields.Char(string='Institutional Activity')
    conversion_program = fields.Char(string='Conversion Program')
    departure_conversion = fields.Char(string='Federal Item')
    expense_type = fields.Char(string='Expense Type')
    location = fields.Char(string='State Code')
    portfolio = fields.Char(string='Key portfolio')
    project_type = fields.Char(string='Type of Project')
    project_number = fields.Char(string='Project Number')
    stage = fields.Char(string='Stage Identifier')
    agreement_type = fields.Char(string='Type of Agreement')
    agreement_number = fields.Char(string='Agreement number')
    exercise_type = fields.Char(string='Exercise type')
    budget = fields.Char(string='Budget')
    origin = fields.Char(string='Origin')
    quarter_data = fields.Char(string='Quarter')
    
    _sql_constraints = [('uniq_program_per_standardization_id', 'unique(id,code_id,standardization_id)',
                         'The program code must be unique per Standardization'),
                        ('folio_uniq', 'unique(folio)', 'The folio must be unique.')]

    @api.constrains('folio')
    def _check_folio(self):
        for line in self:
            if not str(line.folio).isnumeric():
                if self.env.user.lang == 'es_MX':
                    raise ValidationError('Folio Debe ser un valor numérico!')
                else:
                    raise ValidationError('Folio Must be numeric value!')

    @api.onchange('state')
    def _onchange_state(self):
        state = self._origin.state
        if state and state == 'draft' and self.state not in ['draft', 'received', 'cancelled']:
            if self.env.user.lang == 'es_MX':
                raise ValidationError("No puedes saltar o devolver el estado de una línea de Recalendarización")
            else:
                raise ValidationError(
                "You cannot skip or return the status of a Re-scheduling line")
        if state and state == 'received' and self.state not in ['received', 'in_process', 'cancelled']:
            if self.env.user.lang == 'es_MX':
                raise ValidationError("No puedes saltar o devolver el estado de una línea de Recalendarización")
            else:            
                raise ValidationError(
                    "You cannot skip or return the status of a Re-scheduling line")
        if state and state == 'in_process' and self.state not in ['in_process', 'authorized', 'cancelled']:

            if self.env.user.lang == 'es_MX':
                raise ValidationError("No puedes saltar o devolver el estado de una línea de Recalendarización")
            else:
                raise ValidationError(
                    "You cannot skip or return the status of a Re-scheduling line")
        if state and state == 'authorized' and self.state not in ['authorized']:
            if self.env.user.lang == 'es_MX':
                raise ValidationError("No puedes saltar o devolver el estado de una línea de Recalendarización")
            else:
                raise ValidationError("You cannot skip or return the status of a Re-scheduling line")
        if state and state == 'cancelled' and self.state not in ['cancelled']:
            if self.env.user.lang == 'es_MX':
                raise ValidationError("No puedes saltar o devolver el estado de una línea de Recalendarización")
            else:
                raise ValidationError("You cannot skip or return the status of a Re-scheduling line")
