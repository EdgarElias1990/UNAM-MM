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
# You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, api, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.misc import formatLang
from odoo.tools.misc import xlsxwriter
import io
import base64
from odoo.tools import config, date_utils, get_lang
import lxml.html


class CumulativeComparison(models.AbstractModel):

    _name = "jt_projects.cumulative.comparison"
    _inherit = "account.coa.report"
    _description = "ACCUMULATED CHECKS"

    filter_date = {'mode': 'range', 'filter': 'this_month'}
    filter_comparison = None
    filter_all_entries = None
    filter_journals = None
    filter_analytic = None
    filter_unfold_all = None
    filter_cash_basis = None
    filter_hierarchy = None
    filter_unposted_in_period = None
    MAX_LINES = None

    filter_project_type = [
        {'id': 'conacyt', 'name': ('CONACYT'), 'selected': False},
        {'id': 'concurrent', 'name': ('Concurrente'), 'selected': False},
        {'id': 'other', 'name': ('Otro'), 'selected': False},
    ]

    def _get_reports_buttons(self):
        return [
            {'name': _('Export to PDF'), 'sequence': 1,
             'action': 'print_pdf', 'file_export_type': _('PDF')},
            {'name': _('Export (XLSX)'), 'sequence': 2,
             'action': 'print_xlsx', 'file_export_type': _('XLSX')},
        ]

    def _get_templates(self):
        templates = super(
            CumulativeComparison, self)._get_templates()
        templates[
            'main_table_header_template'] = 'account_reports.main_table_header'
        templates['main_template'] = 'account_reports.main_template'
        return templates

    def _format(self, value, figure_type):
        if self.env.context.get('no_format'):
            return value
        value['no_format_name'] = value['name']

        if figure_type == 'float':
            currency_id = self.env.company.currency_id
            if currency_id.is_zero(value['name']):
                # don't print -0.0 in reports
                value['name'] = abs(value['name'])
                value['class'] = 'number text-muted'
            value['name'] = formatLang(
                self.env, value['name'], currency_obj=currency_id)
            value['class'] = 'number'
            return value
        if figure_type == 'percents':
            value['name'] = str(round(value['name'], 2)) + '%'
            value['class'] = 'number'
            return value
        value['name'] = round(value['name'], 1)
        return value

    def _get_columns_name(self, options):
        return [

            {'name': _('')},
            {'name': _('')},
            {'name': _('')},
            {'name': _('')},
            {'name': _('')},
            {'name': _('')},
            {'name': _('')},
            {'name': _('')},
            {'name': _('')},
            {'name': _('')},
            {'name': _('')},

        ]

    def _get_lines(self, options, line_id=None):
        lines = []
        project_type_domain = []
        project_domain = []

        start = datetime.strptime(
            str(options['date'].get('date_from')), '%Y-%m-%d').date()
        end = datetime.strptime(
            options['date'].get('date_to'), '%Y-%m-%d').date()

        project_type_select = options.get('project_type')
        for p_type in project_type_select:
            if p_type.get('selected', False):
                project_type_domain.append(p_type.get('id'))

        if project_type_domain:
            project_domain += [('project_type', 'in',
                                tuple(project_type_domain))]
        else:
            project_domain += [('project_type', 'in',
                                ('conacyt', 'concurrent', 'other'))]

        project_domain += [('status', '=', 'open'), ('proj_start_date',
                                                     '>=', start), ('proj_end_date', '<=', end)]

        #============ Header Part ====================#
        project_records = self.env['project.project'].search(project_domain)

        year_list_tuple = range(start.year, end.year + 1)
        year_list = []

        for y in year_list_tuple:
            year_list.append(str(y))

        lines.append({
            'id': 'hierarchy_col_header',
            'name': 'ETAPA/ANO',
            'columns': [{'name': 'PROYECTOS CONACTY', 'class': 'number'},
                        {'name': 'PROYECTOS ESPECIALES'},
                        {'name': 'TOTAL'},
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
            'colspan': 2,
        })

        stage_ids = project_records.mapped('custom_stage_id')
        for stage in stage_ids:
            for year in year_list:
                current_project_ids = project_records.filtered(
                    lambda x: x.custom_stage_id.id == stage.id and str(x.proj_start_date.year) == year)

                con_project_ids = current_project_ids.filtered(
                    lambda x: x.project_type != 'other')
                other_project_ids = current_project_ids.filtered(
                    lambda x: x.project_type == 'other')

                con_amount = 0
                other_amount = 0

                for c in con_project_ids:
                    con_amount += sum(x.ministering_amount for x in c.project_ministrations_ids)
                    verification_ids = self.env['expense.verification'].search(
                        [('status', '=', 'approve'), ('project_id', '=', c.id)])
                    con_amount -= sum(x.amount_total for x in verification_ids)

                for c in other_project_ids:
                    other_amount += sum(
                        x.ministering_amount for x in c.project_ministrations_ids)
                    verification_ids = self.env['expense.verification'].search(
                        [('status', '=', 'approve'), ('project_id', '=', c.id)])
                    other_amount -= sum(x.amount_total for x in verification_ids)

                lines.append({
                    'id': 'hierarchy_' + str(stage.id) + str(year),
                    'name': stage.name + "/" + year,
                    'columns': [self._format({'name': con_amount}, figure_type='float'),
                                self._format({'name': other_amount},
                                             figure_type='float'),
                                self._format(
                                    {'name': other_amount + con_amount}, figure_type='float'),
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                ],
                    'level': 3,
                    'unfoldable': False,
                    'unfolded': True,
                    'colspan': 2,
                })

        #================= First Part =====================#
        total_cont_amount = 0

        project_type_all = ['conacyt', 'concurrent', 'other']

        for t in project_type_all:
            con_project_domain = project_domain + [('project_type', '=', t)]
            project_records = self.env[
                'project.project'].search(con_project_domain)
            if project_records:
                total_current_due_project = 0
                total_account_bal = 0
                total_bank_bal = 0
                type_name = ''
                if t == 'conacyt':
                    type_name = 'CONACYT projects'
                elif t == 'concurrent':
                    type_name = 'CONCURRENT projects'
                elif t == 'other':
                    type_name = 'OTHER projects'

                lines.append({
                    'id': 'hierarchy_1_col',
                    'name': 'NUM PROYS',
                    'columns': [{'name': type_name},
                                {'name': 'SALDO CONT.'},
                                {'name': 'SALDO BANC.'},
                                {'name': '%'},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                ],
                    'level': 1,
                    'unfoldable': False,
                    'unfolded': True,
                    'colspan': 2,
                })

                #==== Overdue Projects===========#
                overdue_project = project_records.filtered(
                    lambda x: x.check_project_due)
                overdue_account_balance = 0

                for p in overdue_project:
                    overdue_account_balance += sum(
                        x.ministering_amount for x in p.project_ministrations_ids)
                    verification_ids = self.env['expense.verification'].search(
                        [('status', '=', 'approve'), ('project_id', '=', p.id)])
                    overdue_account_balance -= sum(
                        x.amount_total for x in verification_ids)

                bank_account_ids = overdue_project.mapped(
                    'bank_account_id.default_debit_account_id')
                values = self.env['account.move.line'].search([('date', '<=', end), (
                    'account_id', 'in', bank_account_ids.ids), ('move_id.state', '=', 'posted')])
                overdue_bank_balance = sum(x.debit - x.credit for x in values)

                total_current_due_project += len(overdue_project)
                total_account_bal += overdue_account_balance
                total_bank_bal += overdue_bank_balance

                #==== Current Projects===========#
                current_project = project_records.filtered(
                    lambda x: not x.check_project_due)
                current_account_balance = 0

                for p in current_project:
                    current_account_balance += sum(
                        x.ministering_amount for x in p.project_ministrations_ids)
                    verification_ids = self.env['expense.verification'].search(
                        [('status', '=', 'approve'), ('project_id', '=', p.id)])
                    current_account_balance -= sum(
                        x.amount_total for x in verification_ids)

                bank_account_ids = current_project.mapped(
                    'bank_account_id.default_debit_account_id')
                values = self.env['account.move.line'].search([('date', '<=', end), (
                    'account_id', 'in', bank_account_ids.ids), ('move_id.state', '=', 'posted')])
                current_bank_balance = sum(x.debit - x.credit for x in values)

                total_current_due_project += len(current_project)
                total_account_bal += current_account_balance
                total_bank_bal += current_bank_balance

                overdue_per = 0
                if total_account_bal:
                    overdue_per = (overdue_account_balance *
                                   100) / total_account_bal

                lines.append({
                    'id': 'hierarchy_1_col_overdue',
                    'name': len(overdue_project),
                    'columns': [{'name': 'PROYECTOS VENCIDOS'},
                                self._format(
                                    {'name': overdue_account_balance}, figure_type='float'),
                                self._format(
                                    {'name': overdue_bank_balance}, figure_type='float'),
                                self._format({'name': overdue_per},
                                             figure_type='percents'),
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                ],
                    'level': 3,
                    'unfoldable': False,
                    'unfolded': True,
                    'colspan': 2,
                })

                current_per = 0
                if total_account_bal:
                    current_per = (current_account_balance *
                                   100) / total_account_bal

                lines.append({
                    'id': 'hierarchy_1_col_current',
                    'name': len(current_project),
                    'columns': [{'name': 'PROYECTOS VIGENTES'},
                                self._format(
                                    {'name': current_account_balance}, figure_type='float'),
                                self._format(
                                    {'name': current_bank_balance}, figure_type='float'),
                                self._format({'name': current_per},
                                             figure_type='percents'),
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                ],
                    'level': 3,
                    'unfoldable': False,
                    'unfolded': True,
                    'colspan': 2,
                })

                lines.append({
                    'id': 'hierarchy_1_col_curr',
                    'name': total_current_due_project,
                    'columns': [{'name': 'SUBTOTAL'},
                                self._format(
                                    {'name': total_account_bal}, figure_type='float'),
                                self._format(
                                    {'name': total_bank_bal}, figure_type='float'),
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                ],
                    'level': 1,
                    'unfoldable': False,
                    'unfolded': True,
                    'colspan': 2,
                })
                total_cont_amount += total_account_bal

                #==== Zero Bank Balance Projects===========#
                zero_balance_project = self.env['project.project']
                total_zero_project = 0
                total_zero_account_bal = 0
                total_zero_bank_bal = 0

                for pr in project_records:
                    if pr.bank_account_id and pr.bank_account_id.default_debit_account_id:
                        values = self.env['account.move.line'].search(
                            [('account_id', '=', pr.bank_account_id.default_debit_account_id.id), ('move_id.state', '=', 'posted')])
                        account_amount = sum(
                            x.debit - x.credit for x in values)
                        if account_amount == 0:
                            zero_balance_project += pr

                zero_account_balance = 0
                zero_bank_balance = 0

                for p in zero_balance_project:
                    zero_account_balance += sum(
                        x.ministering_amount for x in p.project_ministrations_ids)
                    verification_ids = self.env['expense.verification'].search(
                        [('status', '=', 'approve'), ('project_id', '=', p.id)])
                    zero_account_balance -= sum(
                        x.amount_total for x in verification_ids)

                total_zero_account_bal += zero_account_balance
                total_zero_bank_bal += zero_bank_balance
                total_zero_project += len(zero_balance_project)

                lines.append({
                    'id': 'hierarchy_1_col_current',
                    'name': len(zero_balance_project),
                    'columns': [{'name': 'PROYECTOS COMPROBADOS CON SALIDO BANCARIO EN CERO'},
                                self._format(
                                    {'name': zero_account_balance}, figure_type='float'),
                                self._format(
                                    {'name': zero_bank_balance}, figure_type='float'),
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                ],
                    'level': 3,
                    'unfoldable': False,
                    'unfolded': True,
                    'colspan': 2,
                })
                total_cont_amount += zero_account_balance

        lines.append({
            'id': 'hierarchy_1_col_total',
            'name': 'TOTAL',
            'columns': [{'name': ''},
                        self._format({'name': total_cont_amount},
                                     figure_type='float'),
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
            'colspan': 2,
        })

        #================ 2nd Part ====================#
        project_records = self.env['project.project'].search(project_domain)

        lines.append({
            'id': 'hierarchy_2_col',
            'name': 'No.',
            'columns': [{'name': 'Entidad'},
                        {'name': 'Nombre'},
                        {'name': 'Cuenta Bancaria'},
                        {'name': 'Proyecto'},
                        {'name': 'Del'},
                        {'name': 'Al'},
                        {'name': 'ETAPA/ANO'},
                        {'name': 'Total General'},
                        {'name': 'Saldo bancario'},
                        {'name': 'Diferencia'},
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
        })

        count = 0
        total_account_balance = 0
        total_minis_amount = 0
        total_diff = 0

        #project_records = project_records.search([('id','in',project_records.ids)],order='sub_dependency_name,dependency_name')

        dep_ids = project_records.mapped(
            'dependency_id').sorted(key='dependency')

        for dep in dep_ids:
            dp_rec_ids = project_records.filtered(
                lambda x: x.dependency_id.id == dep.id)
            sub_dep_ids = dp_rec_ids.mapped(
                'subdependency_id').sorted(key='sub_dependency')

            for sub in sub_dep_ids:
                sp_rec_ids = dp_rec_ids.filtered(
                    lambda x: x.subdependency_id.id == sub.id)
                for project in sp_rec_ids:
                    count += 1
                    entity = ''
                    if project.dependency_id and project.dependency_id.dependency:
                        entity = project.dependency_id.dependency
                    if project.subdependency_id and project.subdependency_id.sub_dependency:
                        entity += project.subdependency_id.sub_dependency
                    stage_name = ''
                    if project.custom_stage_id and project.custom_stage_id.name:
                        stage_name = project.custom_stage_id.name
                    if project.proj_start_date:
                        stage_name += "/" + str(project.proj_start_date.year)

                    account_balance = 0
                    if project.bank_account_id and project.bank_account_id.default_debit_account_id:
                        values = self.env['account.move.line'].search([('date', '<=', end), (
                            'account_id', '=', project.bank_account_id.default_debit_account_id.id), ('move_id.state', '=', 'posted')])
                        account_balance = sum(
                            x.debit - x.credit for x in values)

                    minis_amount = sum(
                        x.ministering_amount for x in project.project_ministrations_ids)
                    verification_ids = self.env['expense.verification'].search(
                        [('status', '=', 'approve'), ('project_id', '=', project.id)])
                    minis_amount -= sum(x.amount_total for x in verification_ids)

                    diff = minis_amount - account_balance

                    total_account_balance += account_balance
                    total_minis_amount += minis_amount
                    total_diff += diff

                    lines.append({
                        'id': 'hierarchy_2_col' + str(project.id),
                        'name': count,
                        'columns': [{'name': entity},
                                    {'name': project.dependency_id and project.dependency_id.description or ''},
                                    {'name': project.bank_acc_number_id and project.bank_acc_number_id.acc_number or ''},
                                    {'name': project.number},
                                    {'name': project.proj_start_date},
                                    {'name': project.proj_end_date},
                                    {'name': stage_name},
                                    self._format(
                                        {'name': minis_amount}, figure_type='float'),
                                    self._format(
                                        {'name': account_balance}, figure_type='float'),
                                    self._format({'name': diff},
                                                 figure_type='float'),
                                    ],
                        'level': 3,
                        'unfoldable': False,
                        'unfolded': True,
                    })

        lines.append({
            'id': 'hierarchy_2_total',
            'name': '',
            'columns': [{'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name': 'Total'},
                        self._format({'name': total_minis_amount},
                                     figure_type='float'),
                        self._format(
                            {'name': total_account_balance}, figure_type='float'),
                        self._format({'name': total_diff},
                                     figure_type='float'),
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
        })

        return lines

    def _get_report_name(self):
        return _("ACCUMULATED CHECKS")

    def get_xlsx(self, options, response=None):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(self._get_report_name()[:31])

        date_default_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2, 'num_format': 'yyyy-mm-dd'})
        date_default_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'num_format': 'yyyy-mm-dd'})
        default_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2})
        default_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})
        title_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'bottom': 2})
        super_col_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'align': 'center'})
        level_0_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 6, 'font_color': '#666666'})
        level_1_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 1, 'font_color': '#666666'})
        level_2_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
        level_2_col1_total_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
        level_2_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
        level_3_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2})
        level_3_col1_total_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
        level_3_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})
        currect_date_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'align': 'right'})
        currect_date_style.set_border(0)
        super_col_style.set_border(0)
        # Set the first column width to 50
        sheet.set_column(0, 0, 20)
        sheet.set_column(1, 1, 17)
        sheet.set_column(2, 2, 20)
        sheet.set_column(3, 3, 15)
        sheet.set_column(4, 4, 10)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 6, 12)
        super_columns = self._get_super_columns(options)
        y_offset = 0
        col = 0

        sheet.merge_range(y_offset, col, 6, col, '', super_col_style)
        if self.env.user and self.env.user.company_id and self.env.user.company_id.header_logo:
            filename = 'logo.png'
            image_data = io.BytesIO(base64.standard_b64decode(
                self.env.user.company_id.header_logo))
            sheet.insert_image(0, 0, filename, {
                               'image_data': image_data, 'x_offset': 8, 'y_offset': 3, 'x_scale': 0.6, 'y_scale': 0.6})

        col += 1
        header_title = '''UNIVERSIDAD NACIONAL AUTÓNOMA DE MÉXICOO\nUNIVERSITY BOARD\nDIRECCIÓN GENERAL DE FINANZAS\nSUBDIRECCION DE FINANZAS\nRESUMEN DE OPERACIÓN - SALDOS DE FONDOS DE INVERSIÓN'''
        sheet.merge_range(y_offset, col, 5, col + 6,
                          header_title, super_col_style)
        y_offset += 6
        col = 1
        currect_time_msg = "Fecha y hora de impresión: "
        currect_time_msg += datetime.today().strftime('%d/%m/%Y %H:%M')
        sheet.merge_range(y_offset, col, y_offset, col + 6,
                          currect_time_msg, currect_date_style)
        y_offset += 1
        for row in self.get_header(options):
            x = 0
            for column in row:
                colspan = column.get('colspan', 1)
                header_label = column.get('name', '').replace(
                    '<br/>', ' ').replace('&nbsp;', ' ')
                if colspan == 1:
                    sheet.write(y_offset, x, header_label, title_style)
                else:
                    sheet.merge_range(y_offset, x, y_offset,
                                      x + colspan - 1, header_label, title_style)
                x += colspan
            y_offset += 1
        ctx = self._set_context(options)
        ctx.update({'no_format': True, 'print_mode': True,
                    'prefetch_fields': False})
        # deactivating the prefetching saves ~35% on get_lines running time
        lines = self.with_context(ctx)._get_lines(options)

        if options.get('hierarchy'):
            lines = self._create_hierarchy(lines, options)
        if options.get('selected_column'):
            lines = self._sort_lines(lines, options)

        # write all data rows
        for y in range(0, len(lines)):
            level = lines[y].get('level')
            if lines[y].get('caret_options'):
                style = level_3_style
                col1_style = level_3_col1_style
            elif level == 0:
                y_offset += 1
                style = level_0_style
                col1_style = style
            elif level == 1:
                style = level_1_style
                col1_style = style
            elif level == 2:
                style = level_2_style
                col1_style = 'total' in lines[y].get('class', '').split(
                    ' ') and level_2_col1_total_style or level_2_col1_style
            elif level == 3:
                style = level_3_style
                col1_style = 'total' in lines[y].get('class', '').split(
                    ' ') and level_3_col1_total_style or level_3_col1_style
            else:
                style = default_style
                col1_style = default_col1_style

            # write the first column, with a specific style to manage the
            # indentation
            cell_type, cell_value = self._get_cell_type_value(lines[y])
            if cell_type == 'date':
                sheet.write_datetime(
                    y + y_offset, 0, cell_value, date_default_col1_style)
            else:
                sheet.write(y + y_offset, 0, cell_value, col1_style)

            # write all the remaining cells
            for x in range(1, len(lines[y]['columns']) + 1):
                cell_type, cell_value = self._get_cell_type_value(
                    lines[y]['columns'][x - 1])
                if cell_type == 'date':
                    sheet.write_datetime(
                        y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value, date_default_style)
                else:
                    sheet.write(
                        y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value, style)

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()
        return generated_file

    def get_pdf(self, options, minimal_layout=True):
        # As the assets are generated during the same transaction as the rendering of the
        # templates calling them, there is a scenario where the assets are unreachable: when
        # you make a request to read the assets while the transaction creating them is not done.
        # Indeed, when you make an asset request, the controller has to read the `ir.attachment`
        # table.
        # This scenario happens when you want to print a PDF report for the first time, as the
        # assets are not in cache and must be generated. To workaround this issue, we manually
        # commit the writes in the `ir.attachment` table. It is done thanks to
        # a key in the context.
        minimal_layout = False
        if not config['test_enable']:
            self = self.with_context(commit_assetsbundle=True)

        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'report.url') or self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        rcontext = {
            'mode': 'print',
            'base_url': base_url,
            'company': self.env.company,
        }

        body = self.env['ir.ui.view'].render_template(
            "account_reports.print_template",
            values=dict(rcontext),
        )
        body_html = self.with_context(print_mode=True).get_html(options)

        body = body.replace(b'<body class="o_account_reports_body_print">',
                            b'<body class="o_account_reports_body_print">' + body_html)
        if minimal_layout:
            header = ''
            footer = self.env['ir.actions.report'].render_template(
                "web.internal_layout", values=rcontext)
            spec_paperformat_args = {
                'data-report-margin-top': 10, 'data-report-header-spacing': 10}
            footer = self.env['ir.actions.report'].render_template(
                "web.minimal_layout", values=dict(rcontext, subst=True, body=footer))
        else:
            rcontext.update({
                'css': '',
                'o': self.env.user,
                'res_company': self.env.company,
            })
            header = self.env['ir.actions.report'].render_template(
                "jt_investment.external_layout_investment_funds_balances", values=rcontext)
            # Ensure that headers and footer are correctly encoded
            header = header.decode('utf-8')
            spec_paperformat_args = {
                'data-report-margin-top': 40, 'data-report-header-spacing': 40}
            # Default header and footer in case the user customiz
            # web.external_layout and removed the header/footer
            headers = header.encode()
            footer = b''
            # parse header as new header contains header, body and footer
            try:
                root = lxml.html.fromstring(header)
                match_klass = "//div[contains(concat(' ', normalize-space(@class), ' '), ' {} ')]"

                for node in root.xpath(match_klass.format('header')):
                    headers = lxml.html.tostring(node)
                    headers = self.env['ir.actions.report'].render_template(
                        "web.minimal_layout", values=dict(rcontext, subst=True, body=headers))

                for node in root.xpath(match_klass.format('footer')):
                    footer = lxml.html.tostring(node)
                    footer = self.env['ir.actions.report'].render_template(
                        "web.minimal_layout", values=dict(rcontext, subst=True, body=footer))

            except lxml.etree.XMLSyntaxError:
                headers = header.encode()
                footer = b''
            header = headers

        landscape = False
        if len(self.with_context(print_mode=True).get_header(options)[-1]) > 5:
            landscape = True

        return self.env['ir.actions.report']._run_wkhtmltopdf(
            [body],
            header=header, footer=footer,
            landscape=landscape,
            specific_paperformat_args=spec_paperformat_args
        )

    def get_html(self, options, line_id=None, additional_context=None):
        '''
        return the html value of report, or html value of unfolded line
        * if line_id is set, the template used will be the line_template
        otherwise it uses the main_template. Reason is for efficiency, when unfolding a line in the report
        we don't want to reload all lines, just get the one we unfolded.
        '''
        # Check the security before updating the context to make sure the
        # options are safe.
        self._check_report_security(options)

        # Prevent inconsistency between options and context.
        self = self.with_context(self._set_context(options))

        templates = self._get_templates()
        report_manager = self._get_report_manager(options)
        report = {'name': self._get_report_name(),
                  'summary': report_manager.summary,
                  'company_name': self.env.company.name, }
        report = {}
        # options.get('date',{}).update({'string':''})
        lines = self._get_lines(options, line_id=line_id)

        if options.get('hierarchy'):
            lines = self._create_hierarchy(lines, options)
        if options.get('selected_column'):
            lines = self._sort_lines(lines, options)

        footnotes_to_render = []
        if self.env.context.get('print_mode', False):
            # we are in print mode, so compute footnote number and include them in lines values, otherwise, let the js compute the number correctly as
            # we don't know all the visible lines.
            footnotes = dict([(str(f.line), f)
                              for f in report_manager.footnotes_ids])
            number = 0
            for line in lines:
                f = footnotes.get(str(line.get('id')))
                if f:
                    number += 1
                    line['footnote'] = str(number)
                    footnotes_to_render.append(
                        {'id': f.id, 'number': number, 'text': f.text})

        rcontext = {'report': report,
                    'lines': {'columns_header': self.get_header(options), 'lines': lines},
                    'options': {},
                    'context': self.env.context,
                    'model': self,
                    }
        if additional_context and type(additional_context) == dict:
            rcontext.update(additional_context)
        if self.env.context.get('analytic_account_ids'):
            rcontext['options']['analytic_account_ids'] = [
                {'id': acc.id, 'name': acc.name} for acc in self.env.context['analytic_account_ids']
            ]

        render_template = templates.get(
            'main_template', 'account_reports.main_template')
        if line_id is not None:
            render_template = templates.get(
                'line_template', 'account_reports.line_template')
        html = self.env['ir.ui.view'].render_template(
            render_template,
            values=dict(rcontext),
        )
        if self.env.context.get('print_mode', False):
            for k, v in self._replace_class().items():
                html = html.replace(k, v)
            # append footnote as well
            html = html.replace(b'<div class="js_account_report_footnotes"></div>',
                                self.get_html_footnotes(footnotes_to_render))
        return html
