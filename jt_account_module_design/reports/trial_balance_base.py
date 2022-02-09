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

from lxml import etree
from lxml.objectify import fromstring

from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval
from odoo.tools.xml_utils import _check_with_xsd


from odoo import models, api, _, fields, tools
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.misc import formatLang
from odoo.tools.misc import xlsxwriter
import io
import base64
from odoo.tools import config, date_utils, get_lang
import lxml.html

class StatusProgramReport(models.AbstractModel):

    _name = "jt_account_module_design.trial.balance.base"
    _inherit = "account.report"
    _description = "Trial Balance Base"

    filter_program_code_section = True
    filter_date = {'mode': 'range', 'filter': 'this_month'}
    filter_comparison = {'date_from': '', 'date_to': '', 'filter': 'no_comparison', 'number_period': 1}
    filter_all_entries = False
    filter_journals = True
    #filter_analytic = True
    filter_unfold_all = False
    filter_cash_basis = None
    filter_hierarchy = False
    MAX_LINES = None

    def open_journal_items(self, options, params):
        result = super(StatusProgramReport,self).open_journal_items(options,params)
        if result.get('domain'):
            domain = result.get('domain',[])
        else:
            domain = result.get('domain',[])

        if len(options['selected_dependency']) > 0:
            domain.append(('move_id.dependancy_id.dependency', 'in', options['selected_dependency']))
        if len(options['selected_sub_dependency']) > 0:
            domain.append(('move_id.sub_dependancy_id.sub_dependency', 'in', options['selected_sub_dependency']))
        result['domain'] = domain
        return result
    
    def open_general_ledger(self, options, params=None):
        if not params:
            params = {}
        ctx = self.env.context.copy()
        ctx.pop('id', '')
        action = self.env.ref('jt_account_module_design.action_general_accounting').read()[0]
        options['unfolded_lines'] = ['account_%s' % (params.get('id', ''),)]
        options['unfold_all'] = False
        ctx.update({'model': 'jt_account_module_design.account_coa.inherit'})
        action.update({'options': options, 'context': ctx, 'ignore_session': 'read'})
        return action
    
    @api.model
    def _init_filter_program_code_section(self, options, previous_options=None):
        options['is_code_sections'] = True
        options['code_sections'] = previous_options and previous_options.get(
            'code_sections') or []
        program_fields_ids = [int(acc) for acc in options['code_sections']]
        program_fields_ids = self.env['report.program.fields']
        selected_program_fields = program_fields_ids \
                                  and self.env['report.program.fields'].browse(program_fields_ids) \
                                  or self.env['report.program.fields']
        options['selected_program_fields'] = selected_program_fields.mapped(
            'name')

        # Program Section filter
        options['section_program'] = previous_options and previous_options.get(
            'section_program') or []
        program_ids = [int(acc) for acc in options['section_program']]
        selected_programs = program_ids \
                            and self.env['program'].browse(program_ids) \
                            or self.env['program']
        options['selected_programs'] = selected_programs.mapped('key_unam')

        # Sub Program Section filter
        options['section_sub_program'] = previous_options and previous_options.get(
            'section_sub_program') or []
        sub_program_ids = [int(acc) for acc in options['section_sub_program']]
        selected_sub_programs = sub_program_ids \
                                and self.env['sub.program'].browse(sub_program_ids) \
                                or self.env['sub.program']
        options['selected_sub_programs'] = selected_sub_programs.mapped(
            'sub_program')

        # Dependency Section filter
        options['section_dependency'] = previous_options and previous_options.get(
            'section_dependency') or []
        dependency_ids = [int(acc) for acc in options['section_dependency']]
        selected_dependency = dependency_ids \
                              and self.env['dependency'].browse(dependency_ids) \
                              or self.env['dependency']
        options['selected_dependency'] = selected_dependency.mapped(
            'dependency')

        # Sub Dependency Section filter
        options['section_sub_dependency'] = previous_options and previous_options.get(
            'section_sub_dependency') or []
        sub_dependency_ids = [int(acc)
                              for acc in options['section_sub_dependency']]
        selected_sub_dependency = sub_dependency_ids \
                                  and self.env['sub.dependency'].browse(sub_dependency_ids) \
                                  or self.env['sub.dependency']
        options['selected_sub_dependency'] = selected_sub_dependency.mapped(
            'sub_dependency')

        # Expense Item filter
        options['section_expense_item'] = previous_options and previous_options.get(
            'section_expense_item') or []
        item_ids = [int(acc) for acc in options['section_expense_item']]
        selected_items = item_ids \
                         and self.env['expenditure.item'].browse(item_ids) \
                         or self.env['expenditure.item']
        options['selected_items'] = selected_items.mapped('item')

        # Origin Resource filter
        options['section_or'] = previous_options and previous_options.get(
            'section_or') or []
        or_ids = [int(acc) for acc in options['section_or']]
        selected_origins = or_ids \
                           and self.env['resource.origin'].browse(or_ids) \
                           or self.env['resource.origin']
        options['selected_or'] = selected_origins.mapped('key_origin')


    @api.model
    def _get_columns_name(self, options):
        columns = [
            {'name': '', 'style': 'width:40%'},
            {'name': _('Debit'), 'class': 'text-center'},
            {'name': _('Credit'), 'class': 'text-center'},
        ]
        if options.get('comparison') and options['comparison'].get('periods'):
            columns += [
                {'name': _('Debit'), 'class': 'text-center'},
                {'name': _('Credit'), 'class': 'text-center'},
            ] * len(options['comparison']['periods'])
        return columns + [
            {'name': _('Debit'), 'class': 'text-center'},
            {'name': _('Credit'), 'class': 'text-center'},
            {'name': _('Debit'), 'class': 'text-center'},
            {'name': _('Credit'), 'class': 'text-center'},
        ]

    @api.model
    def _get_super_columns(self, options):
        date_cols = options.get('date') and [options['date']] or []
        date_cols += (options.get('comparison') or {}).get('periods', [])

        columns = [{'string': _('Initial Balance')}]
        columns += reversed(date_cols)
        columns += [{'string': _('Total')}]

        return {'columns': columns, 'x_offset': 1, 'merge': 2}

    @api.model
    def _get_lines(self, options, line_id=None):
        # Create new options with 'unfold_all' to compute the initial balances.
        # Then, the '_do_query' will compute all sums/unaffected earnings/initial balances for all comparisons.

        domain = []
        dep_domain = []
        is_add_fiter = False
        is_add_dep_fiter = False
        if len(options['selected_programs']) > 0:
            domain.append(('program_id.key_unam', 'in', options['selected_programs']))
            is_add_fiter = True
        if len(options['selected_sub_programs']) > 0:
            domain.append(('sub_program_id.sub_program', 'in', options['selected_sub_programs']))
            is_add_fiter = True
        if len(options['selected_dependency']) > 0:
            dep_domain.append(('move_id.dependancy_id.dependency', 'in', options['selected_dependency']))
            is_add_dep_fiter = True
        if len(options['selected_sub_dependency']) > 0:
            dep_domain.append(('move_id.sub_dependancy_id.sub_dependency', 'in', options['selected_sub_dependency']))
            is_add_dep_fiter = True
        if len(options['selected_items']) > 0:
            domain.append(('item_id.item', 'in', options['selected_items']))
            is_add_fiter = True
        if len(options['selected_or']) > 0:
            domain.append(('resource_origin_id.key_origin', 'in', options['selected_or']))
            is_add_fiter = True
            
        program_code_obj = self.env['program.code']
        program_codes = program_code_obj.search(domain)
        
        program_codes_account_ids = program_codes.mapped('item_id.unam_account_id')
        program_codes_account_ids = program_codes_account_ids.ids
        
        new_options = options.copy()
        new_options['unfold_all'] = True
        options_list = self._get_options_periods_list(new_options)
        accounts_results, taxes_results = self.env['account.general.ledger']._do_query(options_list, fetch_lines=False)

        lines = []
        totals = [0.0] * (2 * (len(options_list) + 2))

        move_lines_dep_account_ids = self.env['account.account']
        
        if is_add_dep_fiter:
            move_lines_ids = self.env['account.move.line'].search(dep_domain)
            move_lines_dep_account_ids = move_lines_ids.mapped('account_id')

        # Add lines, one per account.account record.
        for account, periods_results in accounts_results:

            if is_add_fiter and not account.id in program_codes_account_ids:
                continue

            if is_add_dep_fiter  and not account.id in move_lines_dep_account_ids.ids:
                continue
            
            sums = []
            account_balance = 0.0
            for i, period_values in enumerate(reversed(periods_results)):
                account_sum = period_values.get('sum', {})
                account_un_earn = period_values.get('unaffected_earnings', {})
                account_init_bal = period_values.get('initial_balance', {})

                if i == 0:
                    # Append the initial balances.
                    initial_balance = account_init_bal.get('balance', 0.0) + account_un_earn.get('balance', 0.0)
                    sums += [
                        initial_balance > 0 and initial_balance or 0.0,
                        initial_balance < 0 and -initial_balance or 0.0,
                    ]
                    account_balance += initial_balance

                # Append the debit/credit columns.
                sums += [
                    account_sum.get('debit', 0.0) - account_init_bal.get('debit', 0.0),
                    account_sum.get('credit', 0.0) - account_init_bal.get('credit', 0.0),
                ]
                account_balance += sums[-2] - sums[-1]

            # Append the totals.
            sums += [
                account_balance > 0 and account_balance or 0.0,
                account_balance < 0 and -account_balance or 0.0,
            ]

            # account.account report line.
            columns = []
            for i, value in enumerate(sums):
                # Update totals.
                totals[i] += value

                # Create columns.
                columns.append({'name': self.format_value(value, blank_if_zero=True), 'class': 'number', 'no_format_name': value})

            name = account.name_get()[0][1]
            if len(name) > 40 and not self._context.get('print_mode'):
                name = name[:40]+'...'

            lines.append({
                'id': account.id,
                'name': name,
                'title_hover': name,
                'columns': columns,
                'unfoldable': False,
                'caret_options': 'account.account',
            })

        # Total report line.
        lines.append({
             'id': 'grouped_accounts_total',
             'name': _('Total'),
             'class': 'total',
             'columns': [{'name': self.format_value(total), 'class': 'number'} for total in totals],
             'level': 1,
        })

        return lines

    @api.model
    def _get_report_name(self):
        return _("Trial Balance")

    def get_pdf(self, options, minimal_layout=True,line_id=None):
        # As the assets are generated during the same transaction as the rendering of the
        # templates calling them, there is a scenario where the assets are unreachable: when
        # you make a request to read the assets while the transaction creating them is not done.
        # Indeed, when you make an asset request, the controller has to read the `ir.attachment`
        # table.
        # This scenario happens when you want to print a PDF report for the first time, as the
        # assets are not in cache and must be generated. To workaround this issue, we manually
        # commit the writes in the `ir.attachment` table. It is done thanks to a key in the context.
        minimal_layout = False
        if not config['test_enable']:
            self = self.with_context(commit_assetsbundle=True)

        base_url = self.env['ir.config_parameter'].sudo().get_param('report.url') or self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        rcontext = {
            'mode': 'print',
            'base_url': base_url,
            'company': self.env.company,
        }

        body = self.env['ir.ui.view'].render_template(
            "account_reports.print_template",
            values=dict(rcontext),
        )

        start = datetime.strptime(
        str(options['date'].get('date_from')), '%Y-%m-%d').date()
        end = datetime.strptime(
        options['date'].get('date_to'), '%Y-%m-%d').date()
        start_month_name = start.strftime("%B")
        end_month_name = end.strftime("%B")
        
        if self.env.user.lang == 'es_MX':
            start_month_name = self.get_month_name(start.month)
            end_month_name = self.get_month_name(end.month)

        header_date = str(start.day).zfill(2) + " " + start_month_name+" DE "+str(start.year)
        header_date += " AL "+str(end.day).zfill(2) + " " + end_month_name +" DE "+str(end.year)
        

        rcontext_test = {
                'mode': 'print',
                'base_url': base_url,
                'company': self.env.company,
            } 
        rcontext_test.update({
                'css': '',
                'o': self.env.user,
                'res_company': self.env.company,
                'start' : start,
                'end' : end,
                'header_date' : header_date,
        })
        
        body_html = self.with_context(print_mode=True).get_html(options)

        body_header =  self.env['ir.actions.report'].render_template("jt_account_module_design.external_layout_trial_balance", values=rcontext_test)
        body_html = body_header+body_html
        
        body_html = body_html.replace(b'<div class="o_account_reports_header">',b'<div style="font-size:1px;text-align:center;">')
        body = body.replace(b'<body class="o_account_reports_body_print">', b'<body class="o_account_reports_body_print">' + body_html)
        if minimal_layout:
            header = ''
            footer = self.env['ir.actions.report'].render_template("web.internal_layout", values=rcontext)
            spec_paperformat_args = {'data-report-margin-top': 10, 'data-report-header-spacing': 20}
            footer = self.env['ir.actions.report'].render_template("web.minimal_layout", values=dict(rcontext, subst=True, body=footer))
        else:
            lines = self._get_lines(options, line_id=line_id)
            start = datetime.strptime(
            str(options['date'].get('date_from')), '%Y-%m-%d').date()
            end = datetime.strptime(
            options['date'].get('date_to'), '%Y-%m-%d').date()

            start_month_name = start.strftime("%B")
            end_month_name = end.strftime("%B")
            
            if self.env.user.lang == 'es_MX':
                start_month_name = self.get_month_name(start.month)
                end_month_name = self.get_month_name(end.month)

            header_date = str(start.day).zfill(2) + " " + start_month_name+" OF "+str(start.year)
            header_date += " AND "+str(end.day).zfill(2) + " " + end_month_name +" OF "+str(end.year)
            
            rcontext.update({
                    'css': '',
                    'o': self.env.user,
                    'res_company': self.env.company,
                    'start' : start,
                    'end' : end,
                    'header_date' : header_date,
            })
            header = b'<p></p>'
            # header = self.env['ir.actions.report'].render_template("jt_account_module_design.external_layout_trial_balance", values=rcontext)
            header = header.decode('utf-8') # Ensure that headers and footer are correctly encoded
            spec_paperformat_args = {'data-report-margin-top': 4, 'data-report-header-spacing': 4}
            # Default header and footer in case the user customized web.external_layout and removed the header/footer
            headers = header.encode()
            footer = b''
            # parse header as new header contains header, body and footer
            try:
                root = lxml.html.fromstring(header)
                match_klass = "//div[contains(concat(' ', normalize-space(@class), ' '), ' {} ')]"

                for node in root.xpath(match_klass.format('header')):
                    headers = lxml.html.tostring(node)
                    headers = self.env['ir.actions.report'].render_template("web.minimal_layout", values=dict(rcontext, subst=True, body=headers))

                for node in root.xpath(match_klass.format('footer')):
                    footer = lxml.html.tostring(node)
                    footer = self.env['ir.actions.report'].render_template("web.minimal_layout", values=dict(rcontext, subst=True, body=footer))

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
        start = datetime.strptime(
        str(options['date'].get('date_from')), '%Y-%m-%d').date()
        end = datetime.strptime(
        options['date'].get('date_to'), '%Y-%m-%d').date()
        start_month_name = start.strftime("%B")
        end_month_name = end.strftime("%B")
        
        if self.env.user.lang == 'es_MX':
            start_month_name = self.get_month_name(start.month)
            end_month_name = self.get_month_name(end.month)

        header_date = str(start.day).zfill(2) + " " + start_month_name+" DE "+str(start.year)
        header_date += " AL "+str(end.day).zfill(2) + " " + end_month_name +" DE "+str(end.year)
        

        sheet.merge_range(y_offset, col, 6, col, '', super_col_style)
        if self.env.user and self.env.user.company_id and self.env.user.company_id.header_logo:
            filename = 'logo.png'
            image_data = io.BytesIO(base64.standard_b64decode(
                self.env.user.company_id.header_logo))
            sheet.insert_image(0, 0, filename, {
                               'image_data': image_data, 'x_offset': 8, 'y_offset': 3, 'x_scale': 0.6, 'y_scale': 0.6})
        col += 1
        header_title = '''UNIVERSIDAD NACIONAL AUTÓNOMA DE MÉXICO\nDIRECCIÓN GENERAL DE CONTROL PRESUPUESTAL-CONTADURÍA GENERAL
        \nBALANZA DE COMPROBACIÓN DEL %s \nCifras en Pesos''' % (header_date)

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
