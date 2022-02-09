# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import copy
import ast
from lxml import etree
from lxml.objectify import fromstring
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.tools.misc import formatLang,format_date
from odoo.tools import float_is_zero, ustr
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools.misc import xlsxwriter
from odoo.tools import config, date_utils, get_lang
import io
import base64
from datetime import datetime
from datetime import timedelta
import lxml.html




    
class ReportAccountFinancialReport(models.Model):
    _name = "jt_account_module_design.financial.report"
    _description = "jt Account Report (HTML)"
    _inherit = "account.financial.html.report"


    filter_date = {'mode': 'range', 'filter': 'this_month'}
    filter_journals = True
    filter_program_code_section = True
    filter_comparison = {'date_from': '', 'date_to': '', 'filter': 'no_comparison', 'number_period': 1}

    def open_journal_items(self, options, params):
        result = super(ReportAccountFinancialReport,self).open_journal_items(options,params)
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
        if params:
            account_id = params.get('id', '')
            if account_id:
                account_id = account_id.split('_')
                if account_id:
                    account_id = account_id[-1]
                    options['unfolded_lines'] = ['account_%s' % (account_id,)]
                else:
                    options['unfolded_lines'] = False
            else:
                options['unfolded_lines'] = False
        else:
            options['unfolded_lines'] = False
        options['unfold_all'] = False
        ctx.update({'model': 'jt_account_module_design.account_coa.inherit'})
        action.update({'options': options, 'context': ctx, 'ignore_session': 'read'})
        return action
    
    def _get_templates(self):
        """Get this template for better fit of columns"""
        templates = super(ReportAccountFinancialReport, self)._get_templates()
        templates['main_template'] = 'jt_account_module_design.financial_statement_main_template'
        templates.update({'custom_line_template_right':'jt_account_module_design.custom_line_template_right','custom_line_template_left':'jt_account_module_design.custom_line_template_left'})
        
        return templates

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
        #options['section_program'] =  []
        
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
            value['name'] = str(round(value['name'] * 100, 1)) + '%'
            value['class'] = 'number'
            return value
        value['name'] = round(value['name'], 1)
        return value

    def _get_lines(self, options, line_id=None):
        lines = []
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
            is_add_fiter = True
        if len(options['selected_sub_dependency']) > 0:
            dep_domain.append(('move_id.sub_dependancy_id.sub_dependency', 'in', options['selected_sub_dependency']))
            is_add_dep_fiter = True
            is_add_fiter = True
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
         
        report_id = self.env.ref('account_reports.account_financial_report_balancesheet0')

        move_lines_dep_account_ids = self.env['account.account']
        
        if is_add_dep_fiter:
            move_lines_ids = self.env['account.move.line'].search(dep_domain)
            program_codes_account_ids += move_lines_ids.mapped('account_id').ids
        
        if  report_id:
            #======= Side Data ======#
            line_obj = report_id.line_ids
            if line_id:
                line_obj = self.env['account.financial.html.report.line'].search([('id', '=', line_id)])
            if options.get('comparison') and options.get('comparison').get('periods'):
                line_obj = line_obj.with_context(periods=options['comparison']['periods'])
            if options.get('ir_filters'):
                line_obj = line_obj.with_context(periods=options.get('ir_filters'))
    
            currency_table = report_id._get_currency_table()
            domain, group_by = report_id._get_filter_info(options)
    
            if group_by:
                options['groups'] = {}
                options['groups']['fields'] = group_by
                options['groups']['ids'] = report_id._get_groups(domain, group_by)
    
            amount_of_periods = len((options.get('comparison') or {}).get('periods') or []) + 1
            amount_of_group_ids = len(options.get('groups', {}).get('ids') or []) or 1
            linesDicts = [[{} for _ in range(0, amount_of_group_ids)] for _ in range(0, amount_of_periods)]
            
            left_line_obj = self.env['account.financial.html.report.line']
            right_line_obj = line_obj
            left_line_id = self.env.ref('account_reports.account_financial_report_total_assets0')
            if left_line_id and left_line_id.id in line_obj.ids:
                left_line_obj = left_line_id
                right_line_obj = right_line_obj - left_line_id
            
            if is_add_fiter:
                if is_add_dep_fiter:
                    domain = dep_domain

                lines = left_line_obj.with_context(
                        filter_domain=domain,custom_account_ids=[('account_id','in',program_codes_account_ids)]
                    )._get_lines(self, currency_table, options, linesDicts)
                
                if self.env.context and self.env.context.get('side_lines',False) and self.env.context.get('side_lines',False)=='right':
                    lines = []
                      
                for l in lines:

                    new_col = []
                    for data in l.get('columns'):
                        if data.get('no_format_name',0):
                            balance_pesos = data.get('no_format_name',0)/1000 
                            new_col.append(self._format({'name': balance_pesos},figure_type='float'))
                        elif data.get('name',0) and isinstance(data.get('name',0), float):
                            balance_pesos = data.get('name',0)/1000 
                            new_col.append(self._format({'name': balance_pesos},figure_type='float'))                            
                        else:
                            new_col.append(data)
                    
                    l.update({'side':'left','columns':new_col})

                right_lines = right_line_obj.with_context(
                        filter_domain=domain,custom_account_ids=[('account_id','in',program_codes_account_ids)]
                    )._get_lines(self, currency_table, options, linesDicts)

                if self.env.context and self.env.context.get('side_lines',False) and self.env.context.get('side_lines',False)=='left':
                    right_lines = []
                    
                for l in right_lines:
                    
                    new_col = []
                    for data in l.get('columns'):
                        if data.get('no_format_name',0):
                            balance_pesos = data.get('no_format_name',0)/1000 
                            new_col.append(self._format({'name': balance_pesos},figure_type='float'))
                        elif data.get('name',0) and isinstance(data.get('name',0), float):
                            balance_pesos = data.get('name',0)/1000 
                            new_col.append(self._format({'name': balance_pesos},figure_type='float'))                            
                        else:
                            new_col.append(data)
                    
                    l.update({'side':'right','columns':new_col})
                    
                lines += right_lines
                #lines = report_id.with_context(custom_account_ids=[('account_id','in',program_codes_account_ids)])._get_lines(options, line_id=line_id)
            else:
                lines = left_line_obj.with_context(
                        filter_domain=domain
                    )._get_lines(self, currency_table, options, linesDicts)

                if self.env.context and self.env.context.get('side_lines',False) and self.env.context.get('side_lines',False)=='right':
                    lines = []
                    
                for l in lines:
                    new_col = []
                    for data in l.get('columns'):
                        if data.get('no_format_name',0):
                            balance_pesos = data.get('no_format_name',0)/1000 
                            new_col.append(self._format({'name': balance_pesos},figure_type='float'))
                        elif data.get('name',0) and isinstance(data.get('name',0), float):
                            balance_pesos = data.get('name',0)/1000 
                            new_col.append(self._format({'name': balance_pesos},figure_type='float'))
                        else:
                            new_col.append(data)
                            
                    l.update({'side':'left','columns':new_col})
                    
                right_lines = right_line_obj.with_context(
                        filter_domain=domain
                    )._get_lines(self, currency_table, options, linesDicts)

                if self.env.context and self.env.context.get('side_lines',False) and self.env.context.get('side_lines',False)=='left':
                    right_lines = []
                    
                for l in right_lines:
                    new_col = []
                    for data in l.get('columns'):
                        if data.get('no_format_name',0):
                            balance_pesos = data.get('no_format_name',0)/1000 
                            new_col.append(self._format({'name': balance_pesos},figure_type='float'))
                        elif data.get('name',0) and isinstance(data.get('name',0), float):
                            balance_pesos = data.get('name',0)/1000 
                            new_col.append(self._format({'name': balance_pesos},figure_type='float'))
                        else:
                            new_col.append(data)
                    
                    l.update({'side':'right','columns':new_col})
                
                lines+=right_lines
        return lines
    
    def get_custom_lines(self,lines,side):
        return lines

    def _get_report_name(self):
        return ("Statement Of Financial Position")

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
        body_html = self.with_context(print_mode=True).get_html(options)
        body_html = body_html.replace(b'<div class="o_account_reports_header">',b'<div>')
        #<div class="o_account_reports_header">
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

            header_date = str(start.day).zfill(2) + " " + start_month_name+" DE "+str(start.year)
            header_date += " AL "+str(end.day).zfill(2) + " " + end_month_name +" DE "+str(end.year)
            
            rcontext.update({
                    'css': '',
                    'o': self.env.user,
                    'res_company': self.env.company,
                    'start' : start,
                    'end' : end,
                    'header_date' : header_date,
            })
            header = self.env['ir.actions.report'].render_template("jt_account_module_design.external_layout_fianancial_statement_id", values=rcontext)
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
        start = datetime.strptime(str(options['date'].get('date_from')), '%Y-%m-%d').date()
        end = datetime.strptime(str(options['date'].get('date_to')), '%Y-%m-%d').date()
        start_date = start.strftime('%B %d')
        s_year = start.strftime('%Y')
        end_date = end.strftime('%B %d')
        e_year = end.strftime('%Y')

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
ESTADO DE SITUACIÓN FINANCIERA DEL %s \nCifras en Miles de Pesos''' % (header_date)
        sheet.merge_range(y_offset, col, 5, col + 6,
                          header_title, super_col_style)
        y_offset += 6
        col = 1
        currect_time_msg = "Fecha y hora de impresión: "
        currect_time_msg += datetime.today().strftime('%d/%m/%Y %H:%M')
        sheet.merge_range(y_offset, col, y_offset, col + 6,
                          currect_time_msg, currect_date_style)
        y_offset += 3
        total_col = 2
        for row in self.get_header(options):
            x = 0
            total_col = 0
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
                total_col += colspan
                 
            y_offset += 1
        total_col += 1
        ctx = self._set_context(options)
        ctx.update({'no_format': True, 'print_mode': True,
                    'prefetch_fields': False,})
        
        right_offset = y_offset
        # deactivating the prefetching saves ~35% on get_lines running time
        ctx.update({'side_lines':'left'})
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

        #==============Left======================#
        y_offset = right_offset 
        ctx.update({'side_lines':'right'})
        lines = self.with_context(ctx)._get_lines(options)
        print (lines)
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
                    y + y_offset, total_col, cell_value, date_default_col1_style)
            else:
                sheet.write(y + y_offset, total_col, cell_value, col1_style)
            # write all the remaining cells
            for a in range(1, len(lines[y]['columns']) + 1):
                x=a
                cell_type, cell_value = self._get_cell_type_value(
                    lines[y]['columns'][x - 1])
                x = a+total_col
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

        render_template = templates.get('main_template', 'jt_account_module_design.financial_statement_main_template')
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
    
class AccountFinancialReportLine(models.Model):
    _inherit = "account.financial.html.report.line"
     
    def _get_aml_domain(self):
        domain = super(AccountFinancialReportLine,self)._get_aml_domain()
        if domain:
            domain += (self._context.get('custom_account_ids') or [])
        else:
             domain = (self._context.get('custom_account_ids') or [])
        return domain