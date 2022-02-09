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
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import re
from odoo.tools.misc import ustr

from odoo.tools.profiler import profile


class ExpenditureBudget(models.Model):
    _name = 'expenditure.budget'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Expenditure Budget'
    _rec_name = 'name'

    @api.depends('success_line_ids', 'success_line_ids.imported', 'success_line_ids.state', 'state')
    def _get_count(self):
        for record in self:
            record.record_number = len(record.success_line_ids)
            record.import_record_number = len(
                record.success_line_ids.filtered(lambda l: l.imported == True))

    # Fields For Header
    name = fields.Text(string='Budget name', required=True, tracking=True,
                       states={'validate': [('readonly', True)]})

    _sql_constraints = [
        ('uniq_budget_name', 'unique(name)',
         'The Budget name must be unique!'),
    ]

    user_id = fields.Many2one('res.users', string='Responsible',
                              default=lambda self: self.env.user, tracking=True,
                              states={'validate': [('readonly', True)]})

    # Date Periods
    from_date = fields.Date(string='From', states={
        'validate': [('readonly', True)]}, tracking=True)
    to_date = fields.Date(string='To', states={
        'validate': [('readonly', True)]}, tracking=True)

    @api.depends('total_budget_validate', 'state', 'success_line_ids', 'success_line_ids.authorized')
    def _compute_total_budget(self):
        for budget in self:
            if budget.state in ('validate', 'done'):
                budget.total_budget = budget.total_budget_validate
            else:
                budget.total_budget = sum(
                    budget.success_line_ids.mapped('authorized'))

    total_budget = fields.Float(
        string='Total budget', tracking=True, compute="_compute_total_budget", store=True)
    total_budget_validate = fields.Float(string='Total budget', copy=False)

    record_number = fields.Integer(
        string='Number of records', compute='_get_count', store=True)
    import_record_number = fields.Integer(
        string='Number of imported records', readonly=True, compute='_get_count', store=True)

    @api.depends('success_line_ids', 'success_line_ids.start_date', 'success_line_ids.end_date',
                 'success_line_ids.assigned', 'success_line_ids.state', 'state')
    def _compute_total_quarter_budget(self):
        for budget in self:
            total_quarter_budget = 0
            for line in budget.success_line_ids:
                if line.start_date and line.start_date.day == 1 and line.start_date.month == 1 and line.end_date and line.end_date.month == 3:
                    total_quarter_budget += line.assigned
            budget.total_quarter_budget = total_quarter_budget

    total_quarter_budget = fields.Float(
        string='Total 1st Quarter', tracking=True, compute="_compute_total_quarter_budget", store=True)
    journal_id = fields.Many2one('account.journal')
    move_line_ids = fields.One2many('account.move.line', 'budget_id', string="Journal Items")

    @api.model
    def fields_get(self, fields=None, attributes=None):
        fields = super(ExpenditureBudget, self).fields_get(fields, attributes=attributes)
        for key, value in fields.items():
            value.update({'searchable': False, 'sortable': False})
        return fields

    @api.model
    def default_get(self, fields):
        res = super(ExpenditureBudget, self).default_get(fields)
        budget_app_jou = self.env.ref('jt_conac.budget_appr_jour')
        if budget_app_jou:
            res.update({'journal_id': budget_app_jou.id})
        return res

    @api.depends('line_ids', 'line_ids.state', 'success_line_ids', 'success_line_ids.state', 'state')
    def _get_imported_lines_count(self):
        for record in self:
            record.imported_lines_count = len(record.line_ids)
            record.success_lines_count = len(record.success_line_ids)

    @api.depends('success_line_ids', 'success_line_ids.assigned', 'success_line_ids.authorized',
                 'success_line_ids.available')
    def _compute_amt_total(self):
        """
        This function will count the total of all success rows
        :return:
        """
        for budget in self:
            assigned_total = 0
            authorised_total = 0
            available_total = 0
            for line in budget.success_line_ids:
                assigned_total += line.assigned
                authorised_total += line.authorized
                available_total += line.available

            budget.assigned_total = assigned_total
            budget.authorised_total = authorised_total
            budget.available_total = available_total

    assigned_total = fields.Float("Assigned Total", tracking=True, compute="_compute_amt_total", store=True)
    authorised_total = fields.Float("Authorised Total", tracking=True, compute="_compute_amt_total", store=True)
    available_total = fields.Float("Available Total", tracking=True, compute="_compute_amt_total", store=True)
    # Budget Lines
    line_ids = fields.One2many(
        'expenditure.budget.line', 'expenditure_budget_id',
        string='Expenditure Budget Lines', states={'validate': [('readonly', True)]},
        domain=[('state', '!=', 'success')])
    success_line_ids = fields.One2many(
        'expenditure.budget.line', 'expenditure_budget_id',
        string='Expenditure Budget Lines', domain=[('state', '=', 'success')])

    state = fields.Selection([
        ('draft', 'Draft'),
        ('previous', 'Previous'),
        ('confirm', 'Confirm'),
        ('validate', 'Validate'),
        ('done', 'Done')], default='draft', required=True, string='State', tracking=True)

    imported_lines_count = fields.Integer(
        string='Imported Lines', compute='_get_imported_lines_count', store=True)
    success_lines_count = fields.Integer(
        string='Success Lines', compute='_get_imported_lines_count', store=True)

    @api.depends('line_ids', 'line_ids.state', 'success_line_ids', 'success_line_ids.state', 'state')
    def _compute_total_rows(self):
        for budget in self:
            budget.draft_rows = self.env['expenditure.budget.line'].search_count(
                [('expenditure_budget_id', '=', budget.id), ('state', 'in', ['draft', 'manual'])])
            budget.failed_rows = self.env['expenditure.budget.line'].search_count(
                [('expenditure_budget_id', '=', budget.id), ('state', '=', 'fail')])
            budget.success_rows = self.env['expenditure.budget.line'].search_count(
                [('expenditure_budget_id', '=', budget.id), ('state', '=', 'success')])
            budget.total_rows = self.env['expenditure.budget.line'].search_count(
                [('expenditure_budget_id', '=', budget.id)])

    # Rows Progress Tracking Details
    cron_running = fields.Boolean(string='Running CRON?')
    import_status = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Completed')], default='draft', copy=False)
    failed_row_file = fields.Binary(string='Failed Rows File')
    fialed_row_filename = fields.Char(
        string='File name', default=lambda self: _("Failed_Rows.txt"))
    draft_rows = fields.Integer(
        string='Failed Rows', compute="_compute_total_rows", store=True)
    failed_rows = fields.Integer(
        string='Failed Rows', compute="_compute_total_rows", store=True)
    success_rows = fields.Integer(
        string='Success Rows', compute="_compute_total_rows", store=True)
    total_rows = fields.Integer(
        string="Total Rows", compute="_compute_total_rows", store=True)

    is_validation_process_start = fields.Boolean(default=False)
    validation_process_start_user = fields.Many2one('res.users', 'Users')

    @api.constrains('from_date', 'to_date')
    def _check_dates(self):
        if self.from_date and self.to_date:
            if self.from_date > self.to_date:
                raise ValidationError("Please select correct date")
            if self.from_date.year != self.to_date.year:
                raise ValidationError("Start date and End date must be related to same year.")

    def import_lines(self):
        ctx = self.env.context.copy()
        if self._context.get('reimport'):
            ctx['reimport'] = True
        return {
            'name': _("Import Budget Lines"),
            'type': 'ir.actions.act_window',
            'res_model': 'import.line',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            'context': ctx,
        }

    def send_notification_msg(self, user, failed, successed):
        ch_obj = self.env['mail.channel']
        base_user = self.env.ref('base.user_root')
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url = base_url + '/web#id=%s&view_type=form&model=expenditure.budget' % (self.id)
        body = (_("Budget Validation Process is Completed for \
                    <a href='%s' target='new'>%s</a>" % (url, self.name)))
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

    def check_year_exist(self, line):

        if len(str(line.year)) > 3:
            year_str = str(line.year)[:4]
            if year_str.isnumeric():
                year_obj = self.env['year.configuration'].search_read([], fields=['id', 'name'])
                if not list(filter(lambda yr: yr['name'] == year_str, year_obj)):
                    self.env['year.configuration'].create({'name': year_str}).id
        else:
            raise ValidationError('Invalid Year Format Of line one!')

    def get_line_vals_list(self, line):
        line_vals = [line.year, line.program, line.subprogram, line.dependency, line.subdependency, line.item,
                     line.dv, line.origin_resource, line.ai, line.conversion_program,
                     line.departure_conversion, line.expense_type, line.location, line.portfolio,
                     line.project_type, line.project_number, line.stage, line.agreement_type,
                     line.agreement_number, line.exercise_type]
        return line_vals

    @profile
    def validate_and_add_budget_line(self):

        if len(self.line_ids.ids) > 0:
            counter = 0
            failed_row = ""
            failed_line_ids = []
            success_line_ids = []
            program_code_model = self.env['program.code'].sudo()
            program_obj = self.env['program'].search_read([('program_key_id', '!=', False)],
                                                          fields=['id', 'key_unam', 'program_key_id'])
            subprogram_obj = self.env['sub.program'].search_read([('dependency_id', '!=', False),
                                                                  ('sub_dependency_id', '!=', False),
                                                                  ('unam_key_id', '!=', False)],
                                                                 fields=['id', 'dependency_id', 'sub_dependency_id',
                                                                         'unam_key_id', 'sub_program'])
            dependancy_obj = self.env['dependency'].search_read([], fields=['id', 'dependency'])
            subdependancy_obj = self.env['sub.dependency'].search_read([],
                                                                       fields=['id', 'dependency_id', 'sub_dependency'])
            item_obj = self.env['expenditure.item'].search_read([], fields=['id', 'item', 'exercise_type'])
            origin_obj = self.env['resource.origin'].search_read([], fields=['id', 'key_origin'])
            activity_obj = self.env['institutional.activity'].search_read([], fields=['id', 'number'])
            shcp_obj = self.env['budget.program.conversion'].search_read([('shcp_name', '!=', False),
                                                                          ('program_key_id', '!=', False),
                                                                          ('conversion_key_id', '!=', False)],
                                                                         fields=['id', 'program_key_id', 'shcp_name',
                                                                                 'conversion_key_id', 'federal_part'])
            dpc_obj = self.env['departure.conversion'].search_read([('item_id', '!=', False)],
                                                                   fields=['id', 'federal_part', 'item_id'])
            expense_type_obj = self.env['expense.type'].search_read([], fields=['id', 'key_expenditure_type'])
            location_obj = self.env['geographic.location'].search_read([], fields=['id', 'state_key'])
            wallet_obj = self.env['key.wallet'].search_read([], fields=['id', 'wallet_password'])
            project_type_obj = self.env['project.type'].search_read([],
                                                                    fields=['id', 'project_type_identifier', 'number'])
            stage_obj = self.env['stage'].search_read([], fields=['id', 'stage_identifier'])
            agreement_type_obj = self.env['agreement.type'].search_read([], fields=['id', 'agreement_type',
                                                                                    'number_agreement'])
            year_obj = self.env['year.configuration'].search_read([], fields=['id', 'name'])

            lines_to_execute = self.line_ids
            for line in lines_to_execute:
                counter += 1
                if line.state == 'manual' or line.program_code_id:
                    # Validation Importe 1a Asignacion
                    try:
                        asigned_amount = float(line.assigned)
                        if asigned_amount < 0:
                            failed_row += str(self.get_line_vals_list(line)) + \
                                          "------>> Assigned Amount should be greater than or 0!"
                            failed_line_ids.append(line.id)
                            continue
                    except:
                        failed_row += str(self.get_line_vals_list(line)) + \
                                      "------>> Invalid Asigned Amount Format"
                        failed_line_ids.append(line.id)
                        continue

                    # Validation Authorized Amount
                    try:
                        authorized_amount = float(line.authorized)
                        if authorized_amount < 0:
                            failed_row += str(self.get_line_vals_list(line)) + \
                                          "------>> Authorized Amount should be greater than 0!"
                            failed_line_ids.append(line.id)
                            continue
                    except:
                        failed_row += str(self.get_line_vals_list(line)) + \
                                      "------>> Invalid Authorized Amount Format"
                        failed_line_ids.append(line.id)
                        continue
                    line.state = 'success'

                if line.state in ['fail', 'draft']:

                    # Check Start and End Date
                    if not line.start_date:
                        failed_row += str(self.get_line_vals_list(line)) + \
                                      "------>> Please Add Start Date\n"
                        failed_line_ids.append(line.id)
                        continue

                    if not line.end_date:
                        failed_row += str(self.get_line_vals_list(line)) + \
                                      "------>> Please Add End Date\n"
                        failed_line_ids.append(line.id)
                        continue

                    if line.start_date and line.end_date \
                            and self.from_date.year != line.start_date.year \
                            or self.to_date.year != line.end_date.year:
                        failed_row += str(self.get_line_vals_list(line)) + \
                                      "------>> Start date and End date must be related to same year of budget date.\n"
                        failed_line_ids.append(line.id)
                        continue

                    # Validate year format
                    year = False
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
                        failed_row += str(self.get_line_vals_list(line)) + \
                                      "------>> Invalid Year Format\n"
                        failed_line_ids.append(line.id)
                        continue

                    # Validate Program(PR)
                    program = False
                    program_key_id = False
                    if len(str(line.program)) > 1:
                        program_str = line.program
                        if program_str.isnumeric():
                            program = list(filter(lambda prog: prog['key_unam'] == program_str, program_obj))
                            program_key_id = program[0]['program_key_id'][0] if program else False
                            program = program[0]['id'] if program else False
                    if not program:
                        failed_row += str(self.get_line_vals_list(line)) + \
                                      "------>> Invalid Program(PR) Format\n"
                        failed_line_ids.append(line.id)
                        continue

                    # Validation Conversion Program SHCP
                    shcp = False
                    # program = False

                    departure_conversion_str = False
                    if len(str(line.departure_conversion)) > 4:
                        departure_conversion_str = line.departure_conversion

                    program_str = False
                    if len(str(line.program)) > 1:
                        program_str = line.program

                    if len(str(line.conversion_program)) > 3:
                        shcp_str = str(line.conversion_program)
                        if len(shcp_str) == 4 and (re.match("[A-Z]{1}\d{3}", str(shcp_str).upper())):
                            shcp = list(
                                filter(lambda tmp: tmp['shcp_name'] == shcp_str and \
                                                   tmp['program_key_id'][0] == program_key_id and \
                                                   tmp['federal_part'] == departure_conversion_str,
                                       shcp_obj))

                            shcp = shcp[0]['id'] if shcp else False

                    if not shcp:
                        failed_row += str(self.get_line_vals_list(line)) + \
                                      "------>> Invalid Conversion Program SHCP(CONPP) Format\n"
                        failed_line_ids.append(line.id)
                        continue
                    # Validate Dependency
                    dependency = False
                    if len(str(line.dependency)) > 2:
                        dependency_str = line.dependency
                        if dependency_str.isnumeric():
                            dependency = list(filter(lambda dep: dep['dependency'] == dependency_str, dependancy_obj))
                            dependency = dependency[0]['id'] if dependency else False
                    if not dependency:
                        failed_row += str(self.get_line_vals_list(line)) + \
                                      "------>> Invalid Dependency(DEP) Format\n"
                        failed_line_ids.append(line.id)
                        continue

                    if not subdependancy_obj:
                        subdependancy_obj = []
                    # Validate Sub-Dependency
                    subdependency = False
                    subdependency_str = line.subdependency
                    if subdependency_str.isnumeric():
                        subdependency = list(filter(
                            lambda sdo: sdo['sub_dependency'] == subdependency_str and sdo['dependency_id'][
                                0] == dependency, subdependancy_obj))
                        subdependency = subdependency[0]['id'] if subdependency else False

                    if not subdependency:
                        failed_row += str(self.get_line_vals_list(line)) + \
                                      "------>> Invalid Sub Dependency(DEP) Format\n"
                        failed_line_ids.append(line.id)
                        continue

                    # Validate Sub-Program
                    subprogram = False
                    if len(str(line.subprogram)) > 1:

                        subprogram_str = line.subprogram
                        if subprogram_str.isnumeric():
                            subprogram = list(filter(
                                lambda subp: subp['sub_program'] == subprogram_str and subp['unam_key_id'][0] == program \
                                             and subp['dependency_id'][0] == dependency and
                                             subp['sub_dependency_id'][0] == subdependency, subprogram_obj))
                            subprogram = subprogram[0]['id'] if subprogram else False
                    if not subprogram:
                        failed_row += str(self.get_line_vals_list(line)) + \
                                      "------>> Invalid SubProgram(SP) Format\n"
                        failed_line_ids.append(line.id)
                        continue

                    # Validate Item
                    item = False
                    if len(str(line.item)) > 2:
                        item_string = line.item
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
                        failed_row += str(self.get_line_vals_list(line)) + \
                                      "------>> Invalid Expense Item(PAR) Format\n"
                        failed_line_ids.append(line.id)
                        continue

                    # Validate Origin Of Resource
                    origin_resource = False
                    if len(str(line.origin_resource)) > 0:
                        origin_resource_str = line.origin_resource.replace('.', '')
                        if origin_resource_str.isnumeric():
                            origin_resource = list(
                                filter(lambda ores: ores['key_origin'] == origin_resource_str, origin_obj))
                            origin_resource = origin_resource[0]['id'] if origin_resource else False

                    if not origin_resource:
                        failed_row += str(self.get_line_vals_list(line)) + \
                                      "------>> Invalid Origin Of Resource(OR) Format\n"
                        failed_line_ids.append(line.id)
                        continue

                    # Validation Institutional Activity Number
                    institutional_activity = False
                    if len(str(line.ai)) > 2:
                        institutional_activity_str = line.ai
                        if institutional_activity_str.isnumeric():
                            institutional_activity = list(
                                filter(lambda inact: inact['number'] == institutional_activity_str, activity_obj))
                            institutional_activity = institutional_activity[0][
                                'id'] if institutional_activity else False
                    if not institutional_activity:
                        failed_row += str(self.get_line_vals_list(line)) + \
                                      "------>> Invalid Institutional Activity Number(AI) Format\n"
                        failed_line_ids.append(line.id)
                        continue

                    # Validation Federal Item
                    conversion_item = False
                    if len(str(line.departure_conversion)) > 4:
                        conversion_item_str = line.departure_conversion
                        if conversion_item_str.isnumeric():
                            conversion_item = list(filter(
                                lambda coit: coit['federal_part'] == conversion_item_str and coit['item_id'][0] == item,
                                dpc_obj))
                            conversion_item = conversion_item[0]['id'] if conversion_item else False
                    if not conversion_item:
                        failed_row += str(self.get_line_vals_list(line)) + \
                                      "------>> Invalid SHCP Games(CONPA) Format\n"
                        failed_line_ids.append(line.id)
                        continue

                    # Validation Expense Type
                    expense_type = False
                    if len(str(line.expense_type)) > 1:
                        expense_type_str = line.expense_type
                        if expense_type_str.isnumeric():
                            expense_type = list(
                                filter(lambda exty: exty['key_expenditure_type'] == expense_type_str, expense_type_obj))
                            expense_type = expense_type[0]['id'] if expense_type else False
                    if not expense_type:
                        failed_row += str(self.get_line_vals_list(line)) + \
                                      "------>> Invalid Expense Type(TG) Format\n"
                        failed_line_ids.append(line.id)
                        continue

                    # Validation Expense Type
                    geo_location = False
                    if len(str(line.location)) > 1:
                        location_str = line.location
                        if location_str.isnumeric():
                            geo_location = list(filter(lambda geol: geol['state_key'] == location_str, location_obj))
                            geo_location = geo_location[0]['id'] if geo_location else False

                    if not geo_location:
                        failed_row += str(self.get_line_vals_list(line)) + \
                                      "------>> Invalid Geographic Location (UG) Format\n"
                        failed_line_ids.append(line.id)
                        continue

                    # Validation Wallet Key
                    wallet_key = False
                    if len(str(line.portfolio)) > 3:
                        wallet_key_str = line.portfolio
                        if wallet_key_str.isnumeric():
                            wallet_key = list(
                                filter(lambda wlke: wlke['wallet_password'] == wallet_key_str, wallet_obj))
                            wallet_key = wallet_key[0]['id'] if wallet_key else False

                    if not wallet_key:
                        failed_row += str(self.get_line_vals_list(line)) + \
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
                        project_type_str = line.project_type

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
                        stage_str = line.stage
                        if stage_str.isnumeric():
                            stage = list(filter(lambda stg: stg['stage_identifier'] == stage_str, stage_obj))
                            stage = stage[0]['id'] if stage else False

                    if not stage:
                        failed_row += str(self.get_line_vals_list(line)) + \
                                      "------>> Invalid Stage(E) Format\n"
                        failed_line_ids.append(line.id)
                        continue

                    # Validation Agreement Type
                    agreement_type = False
                    if len(str(line.agreement_type)) > 1:
                        agreement_type_str = line.agreement_type
                        agreement_type = list(filter(lambda aty: aty['agreement_type'] == agreement_type_str and
                                                                 aty['number_agreement'] == line.agreement_number,
                                                     agreement_type_obj))
                        agreement_type = agreement_type[0]['id'] if agreement_type else False

                    if not agreement_type:
                        failed_row += str(self.get_line_vals_list(line)) + \
                                      "------>> Invalid Agreement Type(TC) or Agreement Number Format\n"
                        failed_line_ids.append(line.id)
                        continue

                    if not line.dv:
                        failed_row += str(self.get_line_vals_list(line)) + \
                                      "------>> Digito Verificador is not added! \n"
                        failed_line_ids.append(line.id)
                        continue
                    try:
                        program_code = False
                        if year and program and subprogram and dependency and subdependency and item and origin_resource \
                                and institutional_activity and shcp and conversion_item and expense_type and geo_location and \
                                wallet_key and project_type and stage and agreement_type:
                            # preppare search key to get the match.
                            search_key_fields = (
                                year, program, subprogram, dependency, subdependency, item,
                                origin_resource, institutional_activity, shcp, conversion_item,
                                expense_type, geo_location, wallet_key, project_type, stage, agreement_type)
                            search_key = ';'.join([str(skey) for skey in search_key_fields])
                            program_code = program_code_model.search([('search_key', '=', search_key)], limit=1)

                            if program_code and program_code.state == 'validated':
                                failed_row += str(self.get_line_vals_list(line)) + \
                                              "------>> Duplicated Program Code Found! \n"
                                failed_line_ids.append(line.id)
                                continue
                            if program_code and program_code.state == 'draft':
                                budget_line = self.env['expenditure.budget.line'].search(
                                    [('program_code_id', '=', program_code.id), (
                                        'start_date', '=', line.start_date), ('end_date', '=', line.end_date)], limit=1)
                                if budget_line:
                                    failed_row += str(self.get_line_vals_list(line)) + \
                                                  "------>> Program Code Already Linked With Budget Line With Selected Start/End Date! \n"
                                    failed_line_ids.append(line.id)
                                    continue

                        if not program_code:
                            program_vals = {
                                'year': year,
                                'program_id': program,
                                'sub_program_id': subprogram,
                                'dependency_id': dependency,
                                'sub_dependency_id': subdependency,
                                'item_id': item,
                                'resource_origin_id': origin_resource,
                                'institutional_activity_id': institutional_activity,
                                'budget_program_conversion_id': shcp,
                                'conversion_item_id': conversion_item,
                                'expense_type_id': expense_type,
                                'location_id': geo_location,
                                'portfolio_id': wallet_key,
                                'project_type_id': project_type,
                                'stage_id': stage,
                                'agreement_type_id': agreement_type,
                            }
                            program_code = program_code_model.with_context().create(
                                program_vals)

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
                                        failed_row += str(self.get_line_vals_list(line)) + \
                                                      "------>> Digito Verificador is not matched! \n"
                                        failed_line_ids.append(line.id)
                                        continue

                        if program_code:
                            line.program_code_id = program_code.id
                            success_line_ids.append(line.id)
                            line.available = line.assigned
                    except:
                        failed_row += str(self.get_line_vals_list(line)) + \
                                      "------>> Row Data Are Not Corrected or Duplicated Program Code Found! \n"
                        failed_line_ids.append(line.id)
                        continue

            failed_lines = self.env['expenditure.budget.line'].search(
                [('expenditure_budget_id', '=', self.id), ('id', 'in', failed_line_ids)])
            success_lines = self.env['expenditure.budget.line'].search(
                [('expenditure_budget_id', '=', self.id), ('id', 'in', success_line_ids)])
            success_lines.write({'state': 'success'})
            for l in failed_lines:
                if l.state == 'draft':
                    l.state = 'fail'

            vals = {}
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
            if len(self.line_ids.ids) == 0:
                self.write({'state': 'previous'})
            msg = (_("Budget Validation Process Ended at %s" % datetime.strftime(
                datetime.now(), DEFAULT_SERVER_DATETIME_FORMAT)))
            self.env['mail.message'].create({'model': 'expenditure.budget', 'res_id': self.id,
                                             'body': msg})

            if vals.get('failed_row_file'):
                self.write(vals)

    def remove_cron_records(self):
        crons = self.env['ir.cron'].sudo().search(
            [('model_id', '=', self.env.ref('jt_budget_mgmt.model_expenditure_budget').id)])
        for cron in crons:
            if cron.budget_id and not cron.budget_id.cron_running:
                try:
                    cron.sudo().unlink()
                except:
                    pass

    def verify_data(self):
        total = sum(self.success_line_ids.mapped('authorized'))
        if total <= 0:
            raise ValidationError("Budget amount should be greater than 0")
        if len(self.success_line_ids.ids) == 0:
            raise ValidationError("Please correct failed rows")
        # if self.total_rows > 0 and self.success_rows != self.total_rows:
        #     raise ValidationError("Please correct failed rows")
        return True

    def start_again_previous_budget(self):
        if self.validation_process_start_user and self.validation_process_start_user.id != self.env.user.id:
            raise ValidationError("Budget Validation Process Is Started By Other Users!")
        self.is_validation_process_start = False
        self.validation_process_start_user = False
        self.previous_budget()

    def previous_budget(self):
        # Total CRON to create
        if self.state == 'previous':
            raise ValidationError("Budget already validated.Please reload the page!")
        if self.is_validation_process_start:
            raise ValidationError("Budget Validation Process Is Started By Other Users!")
        self.is_validation_process_start = True
        self.validation_process_start_user = self.env.user.id
        self.env.cr.commit()

        try:
            msg = (_("Budget Validation Process Started at %s" % datetime.strftime(
                datetime.now(), DEFAULT_SERVER_DATETIME_FORMAT)))
            self.env['mail.message'].create({'model': 'expenditure.budget', 'res_id': self.id,
                                             'body': msg})
            if self.success_rows != self.total_rows:
                self.validate_and_add_budget_line()
                total_lines = len(self.success_line_ids.filtered(
                    lambda l: l.state == 'success'))

                if total_lines == self.total_rows:
                    self.state = 'previous'
                    msg = (_("Budget Validation Process Ended at %s" % datetime.strftime(
                        datetime.now(), DEFAULT_SERVER_DATETIME_FORMAT)))

        except ValueError as e:
            self.is_validation_process_start = False
            self.validation_process_start_user = False
            self.env.cr.commit()
            raise ValidationError(_("%s") % (ustr(e)))

        except ValidationError as e:
            self.is_validation_process_start = False
            self.validation_process_start_user = False
            self.env.cr.commit()
            raise ValidationError(_("%s") % (ustr(e)))

        except UserError as e:
            self.is_validation_process_start = False
            self.validation_process_start_user = False
            self.env.cr.commit()
            raise ValidationError(_("%s") % (ustr(e)))

        self.is_validation_process_start = False
        self.validation_process_start_user = False

    def confirm(self):
        self.verify_data()
        self.write({'state': 'confirm'})

    def approve(self):
        if self.state == 'validate':
            raise ValidationError("Budget already validated.Please reload the page!")
        self.write({'state': 'validate'})
        self.total_budget_validate = sum(self.success_line_ids.mapped('authorized'))

        self.verify_data()
        if self.journal_id:
            move_obj = self.env['account.move']
            journal = self.journal_id
            today = datetime.today().date()
            budget_id = self.id
            user = self.env.user
            partner_id = user.partner_id.id
            amount = sum(self.success_line_ids.mapped('authorized'))
            company_id = user.company_id.id
            if not journal.default_debit_account_id or not journal.default_credit_account_id \
                    or not journal.conac_debit_account_id or not journal.conac_credit_account_id:
                if self.env.user.lang == 'es_MX':
                    raise ValidationError(_("Por favor configure la cuenta UNAM y CONAC en diario!"))
                else:
                    raise ValidationError(_("Please configure UNAM and CONAC account in budget journal!"))
            unam_move_val = {'ref': self.name, 'budget_id': budget_id, 'conac_move': True,
                             'date': today, 'journal_id': journal.id, 'company_id': company_id,
                             'line_ids': [(0, 0, {
                                 'account_id': journal.default_credit_account_id.id,
                                 'coa_conac_id': journal.conac_credit_account_id.id,
                                 'credit': amount, 'budget_id': budget_id,
                                 'partner_id': partner_id
                             }), (0, 0, {
                                 'account_id': journal.default_debit_account_id.id,
                                 'coa_conac_id': journal.conac_debit_account_id.id,
                                 'debit': amount, 'budget_id': budget_id,
                                 'partner_id': partner_id
                             })]}
            unam_move = move_obj.create(unam_move_val)
            unam_move.action_post()
        self.success_line_ids.mapped('program_code_id').write(
            {'state': 'validated', 'budget_id': self.id})

    def reject(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'reject',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(False, 'form')],
            'target': 'new',
        }

    def unlink(self):
        program_codes = self.env['program.code']
        for rec in self:
            program_codes += rec.success_line_ids.mapped('program_code_id')
            program_codes += rec.line_ids.mapped('program_code_id')

        if not self._context.get('from_wizard'):
            for budget in self:
                if budget.state not in ('draft', 'previous'):
                    if self.env.user.lang == 'es_MX':
                        raise ValidationError(
                            'No se puede borrar el presupuesto procesado!')
                    else:
                        raise ValidationError(
                            'You can not delete processed budget!')
        res = super(ExpenditureBudget, self).unlink()
        if program_codes:
            program_codes.filtered(lambda x: x.state != 'validated').unlink()
        return res

    def show_imported_lines(self):
        action = self.env.ref(
            'jt_budget_mgmt.action_expenditure_budget_imported_line').read()[0]
        action['limit'] = 1000
        action['domain'] = [('id', 'in', self.line_ids.ids)]
        action['search_view_id'] = (self.env.ref(
            'jt_budget_mgmt.expenditure_budget_imported_line_search_view').id,)
        return action

    def show_success_lines(self):
        action = self.env.ref(
            'jt_budget_mgmt.action_expenditure_budget_success_line').read()[0]
        action['limit'] = 1000
        action['domain'] = [('id', 'in', self.success_line_ids.ids)]
        action['search_view_id'] = (self.env.ref(
            'jt_budget_mgmt.expenditure_budget_success_line_search_view').id,)
        return action


class ExpenditureBudgetLine(models.Model):
    _name = 'expenditure.budget.line'
    _description = 'Expenditure Budget Line'
    _rec_name = 'program_code_id'

    expenditure_budget_id = fields.Many2one(
        'expenditure.budget', string='Expenditure Budget', ondelete="cascade")

    start_date = fields.Date(
        string='Start date')
    end_date = fields.Date(
        string='End date')

    authorized = fields.Float(
        string='Authorized')
    assigned = fields.Float(
        string='Assigned')
    available = fields.Float(
        string='Available')
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id)

    program_code_id = fields.Many2one('program.code', string='Program code')
    program_id = fields.Many2one(
        'program', string='Program', related="program_code_id.program_id")
    dependency_id = fields.Many2one(
        'dependency', string='Dependency', related="program_code_id.dependency_id")
    sub_dependency_id = fields.Many2one(
        'sub.dependency', string='Sub-Dependency', related="program_code_id.sub_dependency_id")
    item_id = fields.Many2one(
        'expenditure.item', string='Item', related="program_code_id.item_id")

    imported = fields.Boolean()
    state = fields.Selection([('manual', 'Manual'), ('draft', 'Draft'), (
        'fail', 'Fail'), ('success', 'Success')], string='Status', default='manual')
    imported_sessional = fields.Boolean()

    # Fields for imported data
    year = fields.Char(string='Year')
    program = fields.Char(string='Program')
    subprogram = fields.Char(string='Sub-Program')
    dependency = fields.Char(string='Dependency')
    subdependency = fields.Char(string='Sub-Dependency')
    item = fields.Char(string='Expense Item')
    dv = fields.Char(string='Digit Verification')
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
    cron_id = fields.Many2one('ir.cron', string="CRON ID")
    is_create_from_adequacies = fields.Boolean(string="Line Create From Adequacies", default=False, copy=False)
    new_adequacies_id = fields.Many2one('adequacies', copy=False)

    _sql_constraints = [
        ('uniq_quarter', 'unique(program_code_id,start_date,end_date)',
         'The Program code must be unique per quarter!'),
    ]

    @api.onchange('assigned')
    def onchange_assigned(self):
        if self.assigned:
            self.available = self.assigned

    def write(self, vals):
        if 'assigned' in vals:
            for line in self:
                line.available = vals.get('assigned', 0)
        return super(ExpenditureBudgetLine, self).write(vals)

    @api.model
    def create(self, vals):

        res = super(ExpenditureBudgetLine, self).create(vals)
        if res and res.assigned:
            res.available = res.assigned
        return res

    # ALTER TABLE expenditure_budget_line DROP CONSTRAINT expenditure_budget_line_uniq_program_code_id;
