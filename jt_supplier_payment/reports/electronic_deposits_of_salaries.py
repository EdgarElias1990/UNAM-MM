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
from odoo.tools.misc import xlsxwriter
import io
import base64
from odoo.tools import config, date_utils, get_lang
import lxml.html


class ElectronicDepositsOfSalaries(models.AbstractModel):
    _name = "jt_supplier_payment.electronic.deposits.of.salaries"
    _inherit = "account.coa.report"
    _description = "Electronic Deposits Of Salaries"

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

    filter_payment_method = True
    
    @api.model
    def _get_filter_payment_method(self):
        return self.env['l10n_mx_edi.payment.method'].search([])

    @api.model
    def _init_filter_payment_method(self, options, previous_options=None):
        if self.filter_payment_method is None:
            return
        if previous_options and previous_options.get('payment_method'):
            journal_map = dict((opt['id'], opt['selected']) for opt in previous_options['payment_method'] if opt['id'] != 'divider' and 'selected' in opt)
        else:
            journal_map = {}
        options['payment_method'] = []

        default_group_ids = []

        for j in self._get_filter_payment_method():
            options['payment_method'].append({
                'id': j.id,
                'name': j.name,
                'code': j.name,
                'selected': journal_map.get(j.id, j.id in default_group_ids),
            })

    def _get_reports_buttons(self):
        return [
            {'name': _('Export to PDF'), 'sequence': 1, 'action': 'print_pdf', 'file_export_type': _('PDF')},
            {'name': _('Export (XLSX)'), 'sequence': 2, 'action': 'print_xlsx', 'file_export_type': _('XLSX')},
        ]

    def _get_templates(self):
        templates = super(
            ElectronicDepositsOfSalaries, self)._get_templates()
        templates[
            'main_table_header_template'] = 'account_reports.main_table_header'
        templates['main_template'] = 'account_reports.main_template'
        return templates

    def _get_columns_name(self, options):
        return [
            {'name': _('Tipo de solicitud de pago de nómina')},
            {'name': _('Cuenta bancaria de emisión de pago')},
            {'name': _('Cantidad a pagar')},
        ]

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

    def _get_lines(self, options, line_id=None):
        lines = []
        payment_method_list = []
        for select_curreny in options.get('payment_method'):
            if select_curreny.get('selected',False)==True:
                payment_method_list.append(select_curreny.get('id',0))

        start = datetime.strptime(
            str(options['date'].get('date_from')), '%Y-%m-%d').date()
        end = datetime.strptime(
            options['date'].get('date_to'), '%Y-%m-%d').date()
        
#         if not payment_method_list:
#             method_ids = self._get_filter_payment_method()
#             payment_method_list = method_ids.ids
#         
#         if not payment_method_list:
#             payment_method_list = [0]
        
        datas = []
#         if payment_method_list:
#             self.env.cr.execute('''select ap.journal_id as id,ap.payroll_request_type as payment_method,
#                                     COALESCE(sum(amount),0) as amount
#                                     from account_payment ap,account_journal aj
#                                     where ap.payment_state in ('for_payment_procedure')
#                                     and ap.payment_request_type = 'payroll_payment'
#                                     and ap.journal_id IS NOT NULL
#                                     and ap.payroll_request_type IS NOT NULL 
#                                     and ap.journal_id = aj.id
#                                     and ap.l10n_mx_edi_payment_method_id in %s
#                                     group by ap.journal_id,ap.payroll_request_type
#                 ''',(tuple(payment_method_list),))
#             datas = self.env.cr.fetchall()
#         else:
#             self.env.cr.execute('''select ap.journal_id as id,ap.payroll_request_type as payment_method,
#                                     COALESCE(sum(amount),0) as amount
#                                     from account_payment ap,account_journal aj
#                                     where ap.payment_state in ('for_payment_procedure')
#                                     and ap.payment_request_type = 'payroll_payment'
#                                     and ap.journal_id IS NOT NULL
#                                     and ap.payroll_request_type IS NOT NULL 
#                                     and ap.journal_id = aj.id
#                                     group by ap.journal_id,ap.payroll_request_type
#                 ''')
#             datas = self.env.cr.fetchall()

        if payment_method_list:
            self.env.cr.execute('''select ap.payment_bank_account_id as id,ap.payroll_request_type as payment_method,
                                    COALESCE(sum(amount_total),0) as amount
                                    from account_move ap,res_partner_bank aj
                                    where ap.payment_state in ('approved_payment')
                                    and ap.is_payroll_payment_request = True
                                    and ap.payment_bank_account_id IS NOT NULL
                                    and ap.payroll_request_type IS NOT NULL 
                                    and ap.payment_bank_account_id = aj.id
                                    and ap.l10n_mx_edi_payment_method_id in %s
                                    and ap.invoice_date >= %s and ap.invoice_date <= %s
                                    group by ap.payment_bank_account_id,ap.payroll_request_type
                ''',(tuple(payment_method_list),start,end))
            datas = self.env.cr.fetchall()
        else:
            self.env.cr.execute('''select ap.payment_bank_account_id as id,ap.payroll_request_type as payment_method,
                                    COALESCE(sum(amount_total),0) as amount
                                    from account_move ap,res_partner_bank aj
                                    where ap.payment_state in ('approved_payment')
                                    and ap.is_payroll_payment_request = True
                                    and ap.payment_bank_account_id IS NOT NULL
                                    and ap.payroll_request_type IS NOT NULL 
                                    and ap.payment_bank_account_id = aj.id
                                    and ap.invoice_date >= %s and ap.invoice_date <= %s
                                    group by ap.payment_bank_account_id,ap.payroll_request_type
                ''',(start,end))
            datas = self.env.cr.fetchall()
            
        total_amount = 0
        total_journal_amount=0
        pre_journal = 0
        payment_method_line = []
        list_payment_method = {}
        total_payment_amount=0
        
        for data in datas:
            #payment_method_id = self.env['l10n_mx_edi.payment.method'].browse(data[1])
            if pre_journal != 0 and pre_journal != data[0]:
                journal_id = self.env['res.partner.bank'].browse(pre_journal)
                lines.append({
                    'id': 'hierarchy1_' + str(pre_journal),
                    'name': journal_id.bank_id and journal_id.bank_id.name or '',
                    'columns': [
                                {'name': journal_id.acc_number or ''},
                                self._format({'name': total_journal_amount},figure_type='float'),
                                ],
                    'level': 1,
                    'unfoldable': False,
                    'unfolded': True,
                })
                lines += payment_method_line
                payment_method_line = []
                total_journal_amount = 0
                
            pre_journal = data[0]   
            total_amount += data[2]
            total_journal_amount += data[2]
            
            payroll_name = dict(self.env['account.move']._fields['payroll_request_type'].selection).get(data[1]) 
            payment_method_line.append({
                'id': 'hierarchy2_' + str(data[0])+str(data[1]),
                'name': payroll_name,
                'columns': [
                            {'name': ''},
                            self._format({'name': data[2]},figure_type='float'),
                            ],
                'level': 3,
                'unfoldable': False,
                'unfolded': True,
            })
            if list_payment_method.get(data[1],False):
                p_dict = list_payment_method.get(data[1],{})
                p_dict.update({'amount':data[2]+p_dict.get('amount',0)})
            else:
                list_payment_method.update({data[1]:{'name':payroll_name,'amount':data[2]}})
             
        if payment_method_line and pre_journal:
            journal_id = self.env['res.partner.bank'].browse(pre_journal)
            lines.append({
                'id': 'hierarchy1_' + str(pre_journal),
                'name': journal_id.bank_id and journal_id.bank_id.name or '',
                'columns': [
                            {'name': journal_id.acc_number or ''},
                            self._format({'name': total_journal_amount},figure_type='float'),
                            ],
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
            })
            lines += payment_method_line
            payment_method_line = []
            total_journal_amount = 0
            
        if lines:
            lines.append({
                'id': 'hierarchy1_total',
                'name': '',
                'columns': [
                            {'name': 'SUMAS'},
                            self._format({'name': total_amount},figure_type='float'),
                            ],
                'level': 2,
                'unfoldable': False,
                'unfolded': True,
            })
        
        for method in list_payment_method:
            method_dict = list_payment_method.get(method,{})
            
            lines.append({
                'id': 'hierarchy1_method'+str(method_dict.get('name','')),
                'name': method_dict.get('name',''),
                'columns': [
                            {'name': ''},
                            self._format({'name': method_dict.get('amount',0)},figure_type='float'),
                            ],
                'level': 2,
                'unfoldable': False,
                'unfolded': True,
            })
            total_payment_amount += method_dict.get('amount',0)
        
        if total_payment_amount:
            lines.append({
                'id': 'hierarchy1_method_total',
                'name': '',
                'columns': [
                            {'name': 'SUMAS'},
                            self._format({'name': total_payment_amount},figure_type='float'),
                            ],
                'level': 2,
                'unfoldable': False,
                'unfolded': True,
            })
            
        return lines

    def _get_report_name(self):
        return _("Electronic Deposits Of Salaries")
    
    @api.model
    def _get_super_columns(self, options):
        date_cols = options.get('date') and [options['date']] or []
        date_cols += (options.get('comparison') or {}).get('periods', [])
        columns = reversed(date_cols)
        return {'columns': columns, 'x_offset': 1, 'merge': 5}

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
        sheet.set_column(0, 0,35)
        sheet.set_column(0, 1,35)
        sheet.set_column(0, 2,35)
        super_columns = self._get_super_columns(options)
        y_offset = 0
        col = 0
        
        sheet.merge_range(y_offset, col, 6, col, '',super_col_style)
        if self.env.user and self.env.user.company_id and self.env.user.company_id.header_logo:
            filename = 'logo.png'
            image_data = io.BytesIO(base64.standard_b64decode(self.env.user.company_id.header_logo))
            sheet.insert_image(0,0, filename, {'image_data': image_data,'x_offset':8,'y_offset':3,'x_scale':0.6,'y_scale':0.6})
        
        col += 1
        header_title = '''REPORTE DE LOS IMPORTES DE LOS DEPOSITOS ELECTRONICOS'''
        sheet.merge_range(y_offset, col, 6, col+1, header_title,super_col_style)
        y_offset += 8
#         col=1
#         currect_time_msg = "Fecha y hora de impresión: "
#         currect_time_msg += datetime.today().strftime('%d/%m/%Y %H:%M')
#         sheet.merge_range(y_offset, col, y_offset, col+3, currect_time_msg,currect_date_style)
#         y_offset += 1
#         sheet.merge_range(y_offset, 1, y_offset, 2, "PERIODO",super_col_style)
#         y_offset += 1
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
            header = self.env['ir.actions.report'].render_template("jt_supplier_payment.external_layout_electronic_deposits_of_salaries", values=rcontext)
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
    