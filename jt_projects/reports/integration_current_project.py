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
from odoo import models, api, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.misc import formatLang
from odoo.tools import format_date
from odoo.tools.misc import xlsxwriter
import io
import base64
from odoo.tools import config, date_utils, get_lang
import lxml.html


class IntegrationOfCurrentResearchProjects(models.AbstractModel):

    _name = "jt_projects.integration.of.curr.resarch.project"
    _inherit = "account.coa.report"
    _description = "Integration of current research projects"

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
        {'id': 'conacyt', 'name': ('CONACYT'), 'selected': True},
        {'id': 'concurrent', 'name': ('Concurrente'), 'selected': True},
        {'id': 'other', 'name': ('Otro'), 'selected': True},
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
            IntegrationOfCurrentResearchProjects, self)._get_templates()
        templates[
            'main_table_header_template'] = 'account_reports.main_table_header'
        templates['main_template'] = 'account_reports.main_template'
        return templates

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

    def get_header(self, options):

        start_date = datetime.strptime(
            str(options['date'].get('date_from')), '%Y-%m-%d').date()
        today = datetime.today().date() 
        return[

            [
                {'name': _('Stage / Year'),'class':'align-center'},
                {'name': _('Active project control system balances'),
                 'colspan': 3},
                {'name': _('Accounting Balance at') + ' ' +
                 str(today), 'class': 'number'},

            ],

            [
                {'name': ''},
                {'name': _('Ministered')},
                {'name': _('Checked')},
                {'name': _('To check')},
                {'name': _('Countable balance')},
                {'name': _('Accounting account of various debtors')},
                {'name': _('Total of (Number of projects)')},
            ]
        ]

    def _get_lines(self, options, line_id=None):
        lines = []
        project_domain = []
        project_type_domain = []
        
        start = datetime.strptime(
            str(options['date'].get('date_from')), '%Y-%m-%d').date()
        end = datetime.strptime(
            options['date'].get('date_to'), '%Y-%m-%d').date()

        project_type_select = options.get('project_type')
        for p_type in project_type_select:
            if p_type.get('selected',False):
                project_type_domain.append(p_type.get('id'))
        
        if project_type_domain:
            project_domain += [('project_type','in',tuple(project_type_domain))]
        else:
            project_domain += [('project_type','in',('conacyt','concurrent','other'))]
            
        project_domain += [('proj_start_date', '>=', start), ('proj_end_date', '<=', end)]
          
        project_records = self.env['project.project'].search(project_domain)

        stage_ids = project_records.mapped('custom_stage_id')
        
        total_project = 0
        total_ministering_amount = 0
        total_checked_amount = 0
        total_to_checked_amount = 0
                
        for stage in stage_ids:
            stage_project_records = project_records.filtered(lambda x:x.custom_stage_id.id==stage.id)
             
            ministering_amount = 0.0
            checked_amount = 0.0
            
            name = ''
            if stage:
                name = stage.name or ''
                if stage.description:
                    name += '/'+stage.description
                    
#             name = str(record.stage_identifier_id.id or '') + \
#                 '/' + str(record.proj_start_date)
            for record in stage_project_records:
                for rec in record.project_ministrations_ids:
                    ministering_amount += rec.ministering_amount
            
            exp_records = self.env['expense.verification'].search([('project_id','in',stage_project_records.ids),('status','=','approve')])
            checked_amount = sum(x.amount_total for x in exp_records)
            
            total_project += len(stage_project_records)
            total_ministering_amount += ministering_amount
            total_checked_amount += checked_amount
            total_to_checked_amount += ministering_amount - checked_amount
                       
            lines.append({
                'id': 'projects' + str(record.id),
                'name': name,
                'columns': [
                            self._format({'name': ministering_amount},figure_type='float'),
                            self._format({'name': checked_amount},figure_type='float'),
                            self._format({'name': ministering_amount - checked_amount},figure_type='float'),
                            self._format({'name': ministering_amount - checked_amount},figure_type='float'),
                            {'name': '121,003 MINISTRATIONS FOR VERIFYING CONACYT PROJECTS'},
                            {'name': len(stage_project_records)},
                            ],
                'level': 3,
                'unfoldable': False,
                'unfolded': True,
            })
        
        lines.append({
            'id': 'projects_total',
            'name': 'TOTAL DE '+str(total_project)+' PROYECTOS',
            'columns': [
                        self._format({'name': total_ministering_amount},figure_type='float'),
                        self._format({'name': total_checked_amount},figure_type='float'),
                        self._format({'name': total_to_checked_amount},figure_type='float'),
                        self._format({'name': total_to_checked_amount},figure_type='float'),
                        {'name': ''},
                        {'name': ''},
                        ],
            'level': 2,
            'unfoldable': False,
            'unfolded': True,
        })
        account_amount = 0
        
        project_account_ids = project_records.mapped('bank_account_id.default_debit_account_id')
        if project_account_ids:
            values= self.env['account.move.line'].search([('date', '<=', end),('account_id', '=', project_account_ids.ids),('move_id.state', '=', 'posted')])
            account_amount = sum(x.debit-x.credit for x in values)
        
        total_account = len(project_account_ids)
        lines.append({
            'id': 'projects_saldo_total',
            'name': 'TOTAL DE CUENTAS BANCARIAS '+str(total_account),
            'columns': [
                         
                         {'name': ''},
                         {'name': ''},
                        {'name': 'SALDO EN CUENTA & BANCARIA & CONACTY','colspan' :3},
                        self._format({'name': account_amount},figure_type='float'),
                        {'name': ''},
                        {'name': ''},
                        ],
            'level': 2,
            'unfoldable': False,
            'unfolded': True,
            #'colspan' :3,
            'class': 'o_account_reports_load_more text-right',
        })

        lines.append({
            'id': 'projects_diff_total',
            'name': 'DIFERENCIA GASTO & PENDIENTE & DE COMP ROBARA LA CONTADURA GENERAL',
            'columns': [
#                        {'name': _('DIFERENCIA GASTO & PENDIENTE & DE COMP ROBARA LA CONTADURA GENERAL')},
#                         {'name': ''},
#                         {'name': ''},

                        #{'name': 'DIFERENCIA GASTO & PENDIENTE & DE COMP ROBARA LA CONTADURA GENERAL'},
                        self._format({'name': total_to_checked_amount-account_amount},figure_type='float'),
                        {'name': ''},
                        {'name': ''},
                        ],
            'level': 2,
            'unfoldable': False,
            'unfolded': True,
            'colspan' :4,
            'class': 'o_account_reports_load_more text-right',
        })
    
        #=================== Second Part =================#
        return lines
    
        lines.append({
            'id': 'projects_2_01',
            'name': '',
            'columns': [
                        {'name': '','colspan': 6},
                        ],
            'level': 2,
            'unfoldable': False,
            'unfolded': True,
        })

        lines.append({
            'id': 'projects_2_1',
            'name': 'PROYECTOS DE INVESTIGACION CONACYT POR NUMERO DE CUENTAS BANCARIAS',
#             'columns': [
#                         {'name': ''},
#                         {'name': ''},
#                         {'name': 'PROYECTOS DE INVESTIGACION CONACYT POR NUMERO DE CUENTAS BANCARIAS'},
#                         {'name': ''},
#                         {'name': ''},
#                         {'name': ''},
#                         ],
            'level': 2,
            'unfoldable': False,
            'unfolded': True,
            'colspan':7,
            'class': 'o_account_reports_load_more text-center',
        })
        
        

#         lines.append({
#             'id': 'project_id',
#             'name': 'CONCEPTO',
#             'columns': [
#                         {'name':'PROYECTOS CON CUENTAS BANCARIAS SEGUN CONTADURIA GENERAL','style': 'word-wrap: break-word;'},
#                         {'name': 'SALDO CONTABLE'},
#                         {'name':'N*,CTAS,BANCARIAS'},
#                         {'name': 'SALDO EN CUENTAS BANCARIAS SEGUN DIRECCION GENERAL DE FINANZAS '},
#                         {'name': 'DIFERENCIA GASTOS PENDIENTES DE COMPROBAR A LA CONTADURIA GENERAL'},
#                         {'name': ''},
#  
#                         ],
#             'level': 2,
#             'unfoldable': False,
#             'unfolded': True,
#             'class': 'o_account_reports_load_more text-center',
#             })
    
        lines.append({
            'id': 'project_id',
            'name': 'CONCEPTO',
            'columns': [
                        {'name':'PROYECTOS CON CUENTAS BANCARIAS','style': 'word-wrap: break-word;'},
                        {'name': 'SALDO CONTABLE'},
                        {'name':'N*,CTAS,BANCARIAS'},
                        {'name': 'SALDO EN CUENTAS BANCARIAS '},
                        {'name': 'DIFERENCIA '},
 
                        ],
            'level': 2,
            'unfoldable': False,
            'unfolded': True,
            'colspan':2,
            'class':'height:100px;'
            })
        
        
        
        active_project = self.env['request.accounts'].search([('status','=','confirmed'),('project_id','in',project_records.ids),('move_type','=','account open')])
        cancel_project = self.env['request.accounts'].search([('status','=','confirmed'),('project_id','in',project_records.ids),('move_type','=','account cancel')])
        
        active_project_total = sum(x.ministrations_amount for x in active_project)
        cancel_project_total = sum(x.ministrations_amount for x in cancel_project)
        
        active_bank_ids = active_project.mapped('bank_account_id')
        active_no_bank_account = len(active_bank_ids)

        cancel_bank_ids = cancel_project.mapped('bank_account_id')
        cancel_no_bank_account = len(cancel_bank_ids)
         
         
        active_len = len(active_project) - len(cancel_project)
        cancel_len = len(cancel_project)
        
        active_total = 0.0
        cancel_total = 0.0
        
        active_diff = active_project_total - active_total
        cancel_diff = cancel_project_total - cancel_total
        
         

        lines.append({
            'id': 'projects_2_active',
            'name': 'PROYECTOS ACTIVOS CON UNA CUENTA BANCARIA ACTIVA',
            'columns': [
                        {'name': active_len,'class':'number'},
                        self._format({'name': active_project_total},figure_type='float'),
                        {'name': active_no_bank_account,'class':'number'},
                        self._format({'name': active_total},figure_type='float'),
                        self._format({'name': active_diff},figure_type='float'),
                        ],
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
            'colspan':2,
        })

        lines.append({
            'id': 'projects_2_active',
            'name': 'PROYECTOS ACTIVOS CON UNA CUENTA BANCARIA CANCELADA',
            'columns': [
                        {'name': cancel_len,'class':'number'},
                        self._format({'name': cancel_project_total},figure_type='float'),
                        {'name': cancel_no_bank_account,'class':'number'},
                        self._format({'name': cancel_total},figure_type='float'),
                        self._format({'name': cancel_diff},figure_type='float'),
                        ],
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
            'colspan':2,
        })
        

        return lines


    def _get_report_name(self):
        return _("Integration of current research projects")

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
        
        sheet.merge_range(y_offset, col, 6, col, '',super_col_style)
        if self.env.user and self.env.user.company_id and self.env.user.company_id.header_logo:
            filename = 'logo.png'
            image_data = io.BytesIO(base64.standard_b64decode(self.env.user.company_id.header_logo))
            sheet.insert_image(0,0, filename, {'image_data': image_data,'x_offset':8,'y_offset':3,'x_scale':0.6,'y_scale':0.6})
        
        col += 1
        header_title = '''UNIVERSIDAD NACIONAL AUTÓNOMA DE MÉXICOO\nUNIVERSITY BOARD\nDIRECCIÓN GENERAL DE FINANZAS\nSUBDIRECCION DE FINANZAS\nRESUMEN DE OPERACIÓN - SALDOS DE FONDOS DE INVERSIÓN'''
        sheet.merge_range(y_offset, col, 5, col+6, header_title,super_col_style)
        y_offset += 6
        col=1
        currect_time_msg = "Fecha y hora de impresión: "
        currect_time_msg += datetime.today().strftime('%d/%m/%Y %H:%M')
        sheet.merge_range(y_offset, col, y_offset, col+6, currect_time_msg,currect_date_style)
        y_offset += 1
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
            header = self.env['ir.actions.report'].render_template("jt_projects.external_integration_of_current_research_projects", values=rcontext)
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
