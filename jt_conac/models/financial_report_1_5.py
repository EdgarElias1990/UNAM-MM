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
from odoo import models, _, fields,api
from odoo.tools.misc import xlsxwriter
import io
import base64
import lxml.html
from datetime import datetime


class MXReportAccountCoaCONAC(models.AbstractModel):
    _name = "jt_conac.coa.conac.report"
    _inherit = "account.coa.report"
    _description = "Mexican CONAC Chart of Account Report"

    filter_journals = None
    filter_multi_company = None
    filter_date = None
    filter_all_entries = None
    filter_comparison = None
    filter_journals = None
    filter_analytic = None
    filter_unfold_all = None
    filter_hierarchy = None
    filter_partner = None

    def _get_templates(self):
        templates = super(MXReportAccountCoaCONAC, self)._get_templates()
        templates[
            'main_table_header_template'] = 'account_reports.main_table_header'
        templates['main_template'] = 'account_reports.main_template'
        return templates

    def _get_columns_name(self, options):
        return [
            {'name': _('Account Name')},
            {'name': _('Nature')},
            {'name': _('Account Type')},
            {'name': _('Gender')},
            {'name': _('Group')},
            {'name': _('Item')},
        ]

    def _get_lines(self, options, line_id=None):
        conac_obj = self.env['coa.conac']
        lines = []
        hierarchy_lines = conac_obj.sudo().search(
            [('parent_id', '=', False)], order='code')
        for line in hierarchy_lines:

            # Root Level
            line_code = ''
            if line.code:
                line_code = line.code 
            lines.append({
                'id': 'hierarchy_' + line_code,
                'name': line.display_name,
                'columns': [{'name': ''}, {'name': ''}, {'name': ''}, {'name': ''}, {'name': ''}],
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
            })
            
            accounts = self.env['account.account'].search([('coa_conac_id', '=', line.id)])
            for account in accounts:
                lines.append({
                    'id': 'level_four_%s' % account.id,
                    'name': account.display_name,
                    'columns': [{'name': ''}, {'name': account.user_type_id and account.user_type_id.name or ''}, {'name': line.gender}, {'name': account.group_id and account.group_id.name or ''}, {'name': line.item}],
                    'level': 3,
                    'parent_id': 'level_three_%s' % line.id,
                })

            # Level-1 lines
            level_1_lines = conac_obj.search([('parent_id', '=', line.id)])
            for level_1_line in level_1_lines:
                lines.append({
                    'id': 'level_one_%s' % level_1_line.id,
                    'name': level_1_line.display_name,
                    'columns': [{'name': ''}, {'name': ''}, {'name': ''}, {'name': ''}, {'name': ''}],
                    'level': 2,
                    'unfoldable': True,
                    'unfolded': True,
                    'parent_id': 'hierarchy_' + line_code,
                })
                accounts = self.env['account.account'].search([('coa_conac_id', '=', level_1_line.id)])
                for account in accounts:
                    lines.append({
                        'id': 'level_four_%s' % account.id,
                        'name': account.display_name,
                        'columns': [{'name': ''}, {'name': account.user_type_id and account.user_type_id.name or ''}, {'name': level_1_line.gender}, {'name': account.group_id and account.group_id.name or ''}, {'name': level_1_line.item}],
                        'level': 3,
                        'parent_id': 'level_three_%s' % level_1_line.id,
                    })

                # Level-2 Lines
                level_2_lines = conac_obj.search(
                    [('parent_id', '=', level_1_line.id)])
                for level_2_line in level_2_lines:
                    lines.append({
                        'id': 'level_two_%s' % level_2_line.id,
                        'name': level_2_line.display_name,
                        'columns': [{'name': ''}, {'name': ''}, {'name': ''}, {'name': ''}, {'name': ''}],
                        'level': 3,
                        'unfoldable': True,
                        'unfolded': True,
                        'parent_id': 'level_one_%s' % level_1_line.id,
                    })
                    accounts = self.env['account.account'].search([('coa_conac_id', '=', level_2_line.id)])
                    for account in accounts:
                        lines.append({
                            'id': 'level_four_%s' % account.id,
                            'name': account.display_name,
                            'columns': [{'name': ''}, {'name': account.user_type_id and account.user_type_id.name or ''}, {'name': level_2_line.gender}, {'name': account.group_id and account.group_id.name or ''}, {'name': level_2_line.item}],
                            'level': 4,
                            'parent_id': 'level_three_%s' % level_2_line.id,
                        })

                    # Level-3 Lines
                    level_3_lines = conac_obj.search(
                        [('parent_id', '=', level_2_line.id)])
                    for level_3_line in level_3_lines:
                        nature = ''
                        acc_type = ''
                        if level_3_line.applicability == 'debtor':
                            nature = 'Debitable account'
                            acc_type = 'Debtor'
                        elif level_3_line.applicability == 'creditor':
                            nature = 'Creditable account'
                            acc_type = 'Creditor'
                        elif level_3_line.applicability == 'debtor_creditor':
                            nature = 'Debitable/Creditable account'
                            acc_type = 'Debtoror/Creditor'
                        lines.append({
                            'id': 'level_three_%s' % level_3_line.id,
                            'name': level_3_line.display_name,
                            'columns': [{'name': nature}, {'name': acc_type}, {'name': level_3_line.gender}, {'name': level_3_line.group}, {'name': level_3_line.item}],
                            'level': 4,
                            'unfoldable': True,
                            'unfolded': True,
                            'parent_id': 'level_two_%s' % level_2_line.id,
                        })

                        accounts = self.env['account.account'].search([('coa_conac_id', '=', level_3_line.id)])
                        for account in accounts:
                            lines.append({
                                'id': 'level_four_%s' % account.id,
                                'name': account.display_name,
                                'columns': [{'name': ''}, {'name': account.user_type_id and account.user_type_id.name or ''}, {'name': level_3_line.gender}, {'name': account.group_id and account.group_id.name or ''}, {'name': level_3_line.item}],
                                'level': 5,
                                'parent_id': 'level_three_%s' % level_3_line.id,
                            })
        return lines

    def _get_report_name(self):
        """The structure to name the CoA CONAC reports is:
        YEAR_MONTH_COA_CONAC"""
        context = self.env.context
        date_report = fields.Date.from_string(context['date_from']) if context.get(
            'date_from') else fields.date.today()
        return '%s_%s_COA_CONAC' % (
            date_report.year,
            str(date_report.month).zfill(2))

    @api.model
    def _get_super_columns(self, options):
        return {'columns': {}, 'x_offset': 1, 'merge': 1}

    def get_pdf(self, options, minimal_layout=True):
        print('pdfmm')
        # As the assets are generated during the same transaction as the rendering of the
        # templates calling them, there is a scenario where the assets are unreachable: when
        # you make a request to read the assets while the transaction creating them is not done.
        # Indeed, when you make an asset request, the controller has to read the `ir.attachment`
        # table.
        # This scenario happens when you want to print a PDF report for the first time, as the
        # assets are not in cache and must be generated. To workaround this issue, we manually
        # commit the writes in the `ir.attachment` table. It is done thanks to a key in the context.
        minimal_layout = False
        # if not config['test_enable']:
        #     self = self.with_context(commit_assetsbundle=True)

        base_url = self.env['ir.config_parameter'].sudo().get_param('report.url') or self.env[
            'ir.config_parameter'].sudo().get_param('web.base.url')
        rcontext = {
            'mode': 'print',
            'base_url': base_url,
            'company': self.env.company,
        }

        body = self.env['ir.ui.view'].render_template(
            "account_reports.print_template",
            values=dict(rcontext),
        )
        current_date = datetime.now()
        header_date = str(current_date.day).zfill(2) + '/' + str(current_date.month) + '/' + str(
            current_date.year) + ' ' + str(current_date.strftime("%H:%M"))

        rcontext.update({
            'css': '',
            'o': self.env.user,
            'res_company': self.env.company,
            'header_date': header_date,
        })

        
        body_html = self.with_context(print_mode=True, get_sign_col=True).get_html(options)
        body_html = body_html.replace(b'<div class="o_account_reports_header">', b'<div style="display:none;">')

        body_header =  self.env['ir.actions.report'].render_template("jt_conac.external_layout_mm_custom", values=rcontext)
        body_html = body_header+body_html

        body = body.replace(b'<body class="o_account_reports_body_print">',
                            b'<body class="o_account_reports_body_print">' + body_html)
        if minimal_layout:
            header = ''
            footer = self.env['ir.actions.report'].render_template("web.internal_layout", values=rcontext)
            spec_paperformat_args = {'data-report-margin-top': 10, 'data-report-header-spacing': 10}
            footer = self.env['ir.actions.report'].render_template("web.minimal_layout",
                                                                   values=dict(rcontext, subst=True, body=footer))
        else:
            # start = datetime.strptime(
            #     str(options['date'].get('date_from')), '%Y-%m-%d').date()
            # end = datetime.strptime(
            #     options['date'].get('date_to'), '%Y-%m-%d').date()
            # start_month_name = start.strftime("%B")
            # end_month_name = end.strftime("%B")

            # if self.env.user.lang == 'es_MX':
            #     start_month_name = self.get_month_name(start.month)
            #     end_month_name = self.get_month_name(end.month)
            #
            # header_date = str(start.day).zfill(2) + " " + start_month_name + " DE " + str(start.year)
            current_date = datetime.now()
            # print('fechas: ', current_date.day, '/', current_date.month, '/', current_date.year)
            header_date = str(current_date.day).zfill(2) + '/' + str(current_date.month) + '/' + str(
                current_date.year) + ' ' + str(current_date.strftime("%H:%M"))

            rcontext.update({
                'css': '',
                'o': self.env.user,
                'res_company': self.env.company,
                'header_date': header_date,
            })
            header = b'<p></p>'
#             header = self.env['ir.actions.report'].render_template(
#                 "jt_conac.external_layout_mm_custom", values=rcontext)
            header = header.decode('utf-8')  # Ensure that headers and footer are correctly encoded
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
                    headers = self.env['ir.actions.report'].render_template("web.minimal_layout",
                                                                            values=dict(rcontext, subst=True,
                                                                                        body=headers))

                for node in root.xpath(match_klass.format('footer')):
                    footer = lxml.html.tostring(node)
                    footer = self.env['ir.actions.report'].render_template("web.minimal_layout",
                                                                           values=dict(rcontext, subst=True,
                                                                                       body=footer))

            except lxml.etree.XMLSyntaxError:
                print('exept')
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

        sheet.merge_range(y_offset, col, 6, col, '', super_col_style)
        if self.env.user and self.env.user.company_id and self.env.user.company_id.header_logo:
            filename = 'logo.png'
            image_data = io.BytesIO(base64.standard_b64decode(
                self.env.user.company_id.header_logo))
            sheet.insert_image(0, 0, filename, {
                'image_data': image_data, 'x_offset': 8, 'y_offset': 3, 'x_scale': 0.4, 'y_scale': 0.4})

        col += 1
        # start = datetime.strptime(
        #     str(options['date'].get('date_from')), '%Y-%m-%d').date()
        # end = datetime.strptime(
        #     options['date'].get('date_to'), '%Y-%m-%d').date()
        # start_month_name = start.strftime("%B")
        # end_month_name = end.strftime("%B")
        #
        # if self.env.user.lang == 'es_MX':
        #     start_month_name = self.get_month_name(start.month)
        #     end_month_name = self.get_month_name(end.month)
        #
        # header_date = str(start.day).zfill(2) + " " + start_month_name + " DE " + str(start.year)
        # header_date += " AL " + str(end.day).zfill(2) + " " + end_month_name + " DE " + str(end.year)

        header_title = _('''UNIVERSIDAD NACIONAL AUTÓNOMA DE MÉXICO\n REPORTE COA CONAC''')
        header_title += "\n"
        # header_title += str(header_date)
        sheet.merge_range(y_offset, col, 5, col + 6,
                          header_title, super_col_style)
        y_offset += 6
        col = 1
        currect_time_msg = "Fecha de impresión: "
        currect_time_msg += datetime.today().strftime('%d/%m/%Y')
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

    def get_html(self, options, line_id=None, additional_context=None):
        '''
        return the html value of report, or html value of unfolded line
        * if line_id is set, the template used will be the line_template
        otherwise it uses the main_template. Reason is for efficiency, when unfolding a line in the report
        we don't want to reload all lines, just get the one we unfolded.
        '''
        # Check the security before updating the context to make sure the options are safe.
        self._check_report_security(options)

        # Prevent inconsistency between options and context.
        self = self.with_context(self._set_context(options))

        templates = self._get_templates()
        report_manager = self._get_report_manager(options)
        report = {'name': self._get_report_name(),
                  'summary': report_manager.summary,
                  'company_name': self.env.company.name, }
        report = {}
        lines = self._get_lines(options, line_id=line_id)

        if options.get('hierarchy'):
            lines = self._create_hierarchy(lines, options)
        if options.get('selected_column'):
            lines = self._sort_lines(lines, options)

        footnotes_to_render = []
        if self.env.context.get('print_mode', False):
            # we are in print mode, so compute footnote number and include them in lines values, otherwise, let the js compute the number correctly as
            # we don't know all the visible lines.
            footnotes = dict([(str(f.line), f) for f in report_manager.footnotes_ids])
            number = 0
            for line in lines:
                f = footnotes.get(str(line.get('id')))
                if f:
                    number += 1
                    line['footnote'] = str(number)
                    footnotes_to_render.append({'id': f.id, 'number': number, 'text': f.text})

        rcontext = {'report': report,
                    'lines': {'columns_header': self.get_header(options), 'lines': lines},
                    'options': options,
                    'context': self.env.context,
                    'model': self,
                    }
        if additional_context and type(additional_context) == dict:
            rcontext.update(additional_context)
        if self.env.context.get('analytic_account_ids'):
            rcontext['options']['analytic_account_ids'] = [
                {'id': acc.id, 'name': acc.name} for acc in self.env.context['analytic_account_ids']
            ]

        render_template = templates.get('main_template', 'account_reports.main_template')
        if line_id is not None:
            render_template = templates.get('line_template', 'account_reports.line_template')
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
