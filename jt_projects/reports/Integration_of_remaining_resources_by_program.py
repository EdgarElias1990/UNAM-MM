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
from odoo import models, _
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.misc import formatLang
from odoo.tools.misc import xlsxwriter
import io
import base64
from odoo.tools import config, date_utils, get_lang
import lxml.html


class IntegrationOfRemainingResourceByProgram(models.AbstractModel):

    _name = "jt_projects.integration.remaining.resources.program"
    _inherit = "account.coa.report"
    _description = "Integration of remaining resources by program PAPIIT, PAPIME, INFOCAB"

    filter_date = {'mode': 'range', 'filter': 'this_month'}
    filter_comparison = {'date_from': '', 'date_to': '', 'filter': 'no_comparison', 'number_period': 1}
    filter_all_entries = None
    filter_journals = None
    filter_analytic = None
    filter_unfold_all = None
    filter_cash_basis = None
    filter_hierarchy = None
    filter_unposted_in_period = None
    MAX_LINES = None

    def _get_reports_buttons(self):
        return [
            {'name': _('Export to PDF'), 'sequence': 1,
             'action': 'print_pdf', 'file_export_type': _('PDF')},
            {'name': _('Export (XLSX)'), 'sequence': 2,
             'action': 'print_xlsx', 'file_export_type': _('XLSX')},
        ]

    def _get_templates(self):
        templates = super(
            IntegrationOfRemainingResourceByProgram, self)._get_templates()
        templates[
            'main_table_header_template'] = 'account_reports.main_table_header'
        templates['main_template'] = 'account_reports.main_template'
        return templates


#    def get_header(self, options):
# 
#         return[
# 
#             [
#                 {'name': ''},
#                 {'name': _('Cuenta de Pasivo:221.721.027'),
#                  'colspan': 1},
#                 {'name': _('Cuenta de Pasivo:221.006.001.001'),
#                  'colspan': 1},
#                 {'name': _('Cuenta de Pasivo:221.006.002.001'),
#                  'colspan': 1},
#                 {'name': _('Cuenta de Pasivo:221.721.227'),
#                  'colspan': 1},
#                 {'name': _('Cuenta de Pasivo:221.006.003.00'),
#                  'colspan': 1},
# 
#             ],
# 
#             [
#                 {'name': _('RECURSOS')},
#                 {'name': _('PAPIIT ETAPA 27(2016)')},
#                 {'name': _('PAPIIT ETAPA 28(2017)')},
#                 {'name': _('PAPIIT ETAPA 28(2017)')},
#                 {'name': _('INFOCAB ETAPA 28(2016)')},
#                 {'name': _('INFOCAB ETAPA 28(2017)')},
#                 {'name': _('TOTAL DE RECURSOS')},
#             ]
#         ]

    def _format(self, value,figure_type):
        if self.env.context.get('no_format'):
            return value
        value['no_format_name'] = value['name']
        
        if figure_type == 'float':
            currency_id = self.env.company.currency_id
            if currency_id.is_zero(value['name']):
                # don't print -0.0 in reports
                value['name'] = abs(value['name'])
                value['class'] = 'number text-muted'
            value['name'] = formatLang(self.env, value['name'], currency_obj=currency_id)
            value['class'] = 'number'
            return value
        if figure_type == 'percents':
            value['name'] = str(round(value['name'] * 100, 1)) + '%'
            value['class'] = 'number'
            return value
        value['name'] = round(value['name'], 1)
        return value

    def get_month_name(self, month):
        month_name = ''
        if month == 1:
            month_name = 'Enero'
        elif month == 2:
            month_name = 'Febrero'
        elif month == 3:
            month_name = 'Marzo'
        elif month == 4:
            month_name = 'Abril'
        elif month == 5:
            month_name = 'Mayo'
        elif month == 6:
            month_name = 'Junio'
        elif month == 7:
            month_name = 'Julio'
        elif month == 8:
            month_name = 'Agosto'
        elif month == 9:
            month_name = 'Septiembre'
        elif month == 10:
            month_name = 'Octubre'
        elif month == 11:
            month_name = 'Noviembre'
        elif month == 12:
            month_name = 'Diciembre'

        return month_name.upper()

    def _get_columns_name(self, options):

        start = datetime.strptime(
            str(options['date'].get('date_from')), '%Y-%m-%d').date()
        end = datetime.strptime(
            options['date'].get('date_to'), '%Y-%m-%d').date()

        col_span = 2
        
        
        project_type_list = ['papit','papime','infocab']
        p_config_ids = self.env['remaining.resource'].search([('stage_id','!=',False),('year','<=',str(end.year))],order='year')
        if p_config_ids:
            for p in project_type_list:
                p_type_ids =p_config_ids.filtered(lambda x:x.project_type==p)
                for a in p_type_ids:
                    col_span += 1

        col_list = []
        for r in range(col_span):
            col_list.append({'name': ''})
                    
        return col_list

    def _get_lines(self, options, line_id=None):
        lines = []
        start = datetime.strptime(
            str(options['date'].get('date_from')), '%Y-%m-%d').date()
        end = datetime.strptime(
            options['date'].get('date_to'), '%Y-%m-%d').date()

        month_name = self.get_month_name(end.month)
        col_span = 2

        prev = start - timedelta(days=1)
        previous_month = self.get_month_name(prev.month)
                
        col_account = []
        col_stage = []
        open_balance = []
        debit_balance = []
        credit_balance = []
        total_balance = []
        
        total_open_bal = 0
        total_debit = 0
        total_credit = 0
        total = 0
        
        project_type_list = ['papit','papime','infocab']
        p_config_ids = self.env['remaining.resource'].search([('stage_id','!=',False),('year','<=',str(end.year))],order='year')
        if p_config_ids:
            for p in project_type_list:
                p_type_ids =p_config_ids.filtered(lambda x:x.project_type==p).sorted(key='stage_name')
                for a in p_type_ids:
                    col_span += 1
                    account_code = 'Cuenta de Pasivo:'
                    if a.account_id and a.account_id.code:
                        account_code += a.account_id.code
                    col_account.append({'name': account_code})
                    movement = dict(a._fields['project_type'].selection).get(a.project_type)
                    stage_name = ''
                    if movement:
                        stage_name = movement+" " 
                    stage_name += "ETAPA "+str(a.stage_id.name)+"("+str(a.year)+")"
                    col_stage.append({'name': stage_name})
                    o_bal = 0
                    d_bal = 0
                    c_bal = 0
                    
                    if a.account_id:
                        values= self.env['account.move.line'].search([('date','>=',start),('date','<=',end),('account_id', '=', a.account_id.id),('move_id.state', '=', 'posted')])
                        d_bal = sum(x.debit for x in values)
                        c_bal = sum(x.credit for x in values)
                        
                        values= self.env['account.move.line'].search([('date','<',start),('account_id', '=', a.account_id.id),('move_id.state', '=', 'posted')])
                        o_bal = sum(x.credit - x.debit  for x in values)
                    
                    t_bal = o_bal - d_bal + c_bal
                    total_open_bal += o_bal
                    total_debit += d_bal
                    total_credit += c_bal
                    total += t_bal
                    
                    open_balance.append(self._format({'name': o_bal},figure_type='float'))
                    debit_balance.append(self._format({'name': d_bal},figure_type='float'))
                    credit_balance.append(self._format({'name': c_bal},figure_type='float'))
                    total_balance.append(self._format({'name': t_bal},figure_type='float'))
                                                
        col_account.append({'name': ''})
        
        col_stage.append({'name': 'TOTAL DE RECURSOS'})
        open_balance.append(self._format({'name': total_open_bal},figure_type='float'))
        debit_balance.append(self._format({'name': total_debit},figure_type='float'))
        credit_balance.append(self._format({'name': total_credit},figure_type='float'))
        total_balance.append(self._format({'name': total},figure_type='float'))
        
        lines.append({
            'id': 'hierarchy_title',
            'name' : 'INTEGRACIÓN DE RECURSOS REMANENTES POR PROGRAMA PAPIIT,PAPIME,INFOCAB AL '+str(end.day)+" / " +str(month_name) + " / "+str(end.year), 
            'columns': [ 
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-center',
            'colspan':col_span,
        })

        lines.append({
            'id': 'hierarchy_acc_name',
            'name' : '', 
            'columns':col_account,
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
        })

        lines.append({
            'id': 'hierarchy_STAGE',
            'name' : 'RECURSOS', 
            'columns': col_stage,
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
        })

        lines.append({
            'id': 'hierarchy_open_bal',
            'name' : 'DISPONIBLES AL '+str(prev.day)+" / " +str(previous_month) + " / "+str(prev.year), 
            'columns': open_balance,
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
        })

        lines.append({
            'id': 'hierarchy_debit_bal',
            'name' : 'DISTRIBUCION MES DE '+str(month_name), 
            'columns': debit_balance,
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
        })

        lines.append({
            'id': 'hierarchy_credit_bal',
            'name' : 'DEVOLUCION DE RECOURSOS MES DE', 
            'columns': credit_balance,
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
        })

        lines.append({
            'id': 'hierarchy_total_bal',
            'name' : 'DISPONIBLES AL '+str(end.day)+" / " +str(month_name) + " / "+str(end.year), 
            'columns': total_balance,
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
        })

        return lines

    def _get_report_name(self):
        return _("Integration of remaining resources by program PAPIIT, PAPIME, INFOCAB")

    def get_xlsx(self, options, response=None):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(self._get_report_name()[:31])
 
        date_default_col1_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2, 'num_format': 'yyyy-mm-dd'})
        date_default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'num_format': 'yyyy-mm-dd'})
        default_col1_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2})
        default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})
        title_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2})
        super_col_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'align': 'center'})
        level_0_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 6, 'font_color': '#666666'})
        level_1_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 1, 'font_color': '#666666'})
        level_2_col1_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
        level_2_col1_total_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
        level_2_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
        level_3_col1_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2})
        level_3_col1_total_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
        level_3_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})
        currect_date_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'align': 'right'})
        currect_date_style.set_border(0)
        super_col_style.set_border(0)
        #Set the first column width to 50
        sheet.set_column(0, 0,20)
        sheet.set_column(1, 1,17)
        sheet.set_column(2, 2,20)
        sheet.set_column(3, 3,15)
        sheet.set_column(4, 4,10)
        sheet.set_column(5, 5,15)
        sheet.set_column(6, 6,12)
        super_columns = self._get_super_columns(options)
        y_offset = 0
        col = 0
        
        sheet.merge_range(y_offset, col, 16, col, '',super_col_style)
        if self.env.user and self.env.user.company_id and self.env.user.company_id.header_logo:
            filename = 'logo.png'
            image_data = io.BytesIO(base64.standard_b64decode(self.env.user.company_id.header_logo))
            sheet.insert_image(0,0, filename, {'image_data': image_data,'x_offset':8,'y_offset':3,'x_scale':0.6,'y_scale':0.6})
        
        col += 1
        if self.env.user.lang == 'es_MX':
            header_title = _('''PATRONATO UNIVERSITARIO TESORERÍA\nDIRECCIÓN GENERAL DE CONTROL PRESUPUESTAL\nCONTADURÍA GENERAL\nDEPARTAMENTO DE CONTROL DE PROYECTOS DE INVESTIGACIÓN\nINTEGRACIÓN DE RECURSOS REMANENTES POR PROGRAMA PAPIIT, PAPIME, INFOCAB''')
        else:
            header_title = _('''UNIVERSITY BOARD TREASURY\nGENERAL DIRECTORATE OF BUDGETARY CONTROL\nGENERAL ACCOUNTING\nRESEARCH PROJECT CONTROL DEPARTMENT\nINTEGRATION OF REMAINING RESOURCES BY PAPIIT, PAPIME, INFOCAB PROGRAM''')
        sheet.merge_range(y_offset, col, 5, col+6, header_title,super_col_style)
        y_offset += 6
        col=1
        currect_time_msg = "Fecha y hora de impresión: "
        currect_time_msg += datetime.today().strftime('%d/%m/%Y %H:%M')
        sheet.merge_range(y_offset, col, y_offset+10, col+6, currect_time_msg,currect_date_style)
        y_offset += 10
        for row in self.get_header(options):
            x = 0
            for column in row:
                colspan = column.get('colspan', 1)
                header_label = column.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' ')
                if colspan == 1:
                    sheet.write(y_offset, x, header_label, title_style)
                else:
                    sheet.merge_range(y_offset, x, y_offset, x + colspan - 1, header_label, title_style)
                x += colspan
            y_offset += 1
        ctx = self._set_context(options)
        ctx.update({'no_format':True, 'print_mode':True, 'prefetch_fields': False})
        # deactivating the prefetching saves ~35% on get_lines running time
        lines = self.with_context(ctx)._get_lines(options)
 
        if options.get('hierarchy'):
            lines = self._create_hierarchy(lines, options)
        if options.get('selected_column'):
            lines = self._sort_lines(lines, options)
 
        #write all data rows
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
                col1_style = 'total' in lines[y].get('class', '').split(' ') and level_2_col1_total_style or level_2_col1_style
            elif level == 3:
                style = level_3_style
                col1_style = 'total' in lines[y].get('class', '').split(' ') and level_3_col1_total_style or level_3_col1_style
            else:
                style = default_style
                col1_style = default_col1_style
 
            #write the first column, with a specific style to manage the indentation
            cell_type, cell_value = self._get_cell_type_value(lines[y])
            if cell_type == 'date':
                sheet.write_datetime(y + y_offset, 0, cell_value, date_default_col1_style)
            else:
                sheet.write(y + y_offset, 0, cell_value, col1_style)
 
            #write all the remaining cells
            for x in range(1, len(lines[y]['columns']) + 1):
                cell_type, cell_value = self._get_cell_type_value(lines[y]['columns'][x - 1])
                if cell_type == 'date':
                    sheet.write_datetime(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value, date_default_style)
                else:
                    sheet.write(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value, style)
 
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
        body_html = self.with_context(print_mode=True).get_html(options)

        body = body.replace(b'<body class="o_account_reports_body_print">', b'<body class="o_account_reports_body_print">' + body_html)
        if minimal_layout:
            header = ''
            footer = self.env['ir.actions.report'].render_template("web.internal_layout", values=rcontext)
            spec_paperformat_args = {'data-report-margin-top': 10, 'data-report-header-spacing': 10}
            footer = self.env['ir.actions.report'].render_template("web.minimal_layout", values=dict(rcontext, subst=True, body=footer))
        else:
            rcontext.update({
                    'css': '',
                    'o': self.env.user,
                    'res_company': self.env.company,
                })
            header = self.env['ir.actions.report'].render_template("jt_projects.external_integration_of_program_papiit_papime_infocab", values=rcontext)
            header = header.decode('utf-8') # Ensure that headers and footer are correctly encoded
            spec_paperformat_args = {}
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
                'company_name': self.env.company.name,}
        report = {}
        #options.get('date',{}).update({'string':''}) 
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

        render_template = templates.get('main_template', 'account_reports.main_template')
        if line_id is not None:
            render_template = templates.get('line_template', 'account_reports.line_template')
        html = self.env['ir.ui.view'].render_template(
            render_template,
            values=dict(rcontext),
        )
        if self.env.context.get('print_mode', False):
            for k,v in self._replace_class().items():
                html = html.replace(k, v)
            # append footnote as well
            html = html.replace(b'<div class="js_account_report_footnotes"></div>', self.get_html_footnotes(footnotes_to_render))
        return html