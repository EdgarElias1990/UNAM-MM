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


class TypeofOperation(models.AbstractModel):
    _name = "jt_finance.type.of.operation"
    _inherit = "account.coa.report"
    _description = "Type of Operation"

    filter_date = {'mode': 'range', 'filter': 'this_month'}
    filter_comparison = None
    filter_all_entries = True
    filter_journals = None
    filter_analytic = None
    filter_unfold_all = None
    filter_cash_basis = None
    filter_hierarchy = None
    filter_unposted_in_period = None
    MAX_LINES = None

    def _get_reports_buttons(self):
        return [
            {'name': _('Export to PDF'), 'sequence': 1, 'action': 'print_pdf', 'file_export_type': _('PDF')},
            {'name': _('Export (XLSX)'), 'sequence': 2, 'action': 'print_xlsx', 'file_export_type': _('XLSX')},
        ]

    def _get_templates(self):
        templates = super(
            TypeofOperation, self)._get_templates()
        templates[
            'main_table_header_template'] = 'account_reports.main_table_header'
        templates['main_template'] = 'account_reports.main_template'
        return templates

    def _get_columns_name(self, options):
        return [
            {'name': _('Cuenta Bancaria')},
            {'name': _('Descripción')},
            {'name': _('Nómina')},
            {'name': _('Proveedores')},
            {'name': _('Diferentes a nómina')},
            {'name': _('ISSSTE')},
            {'name': _('FOVISSSTE')},
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
        start = datetime.strptime(
            str(options['date'].get('date_from')), '%Y-%m-%d').date()
        end = datetime.strptime(
            options['date'].get('date_to'), '%Y-%m-%d').date()

        if options.get('all_entries') == True:
            account_payment = self.env['account.payment'].search([('payment_date', '>=', start),
                                                                  ('payment_date', '<=', end),
                                                                  ('payment_request_type','!=',False),
                                               ('payment_state', '=',   ('for_payment_procedure'))],order="journal_id")
        else:
            account_payment = self.env['account.payment'].search([('payment_date', '>=', start),
                                                                  ('payment_date', '<=', end),
                                                                  ('payment_request_type', '!=', False),
                                                                  ('payment_state', 'in', ('posted', 'reconciled'))],
                                                                 order="journal_id")
        master_total_amount_supplier = 0
        master_total_amount_payroll = 0
        master_total_amount_different_payroll = 0
        master_total_amount_ISSSTE = 0
        master_total_amount_FOVISSSTE = 0

        for journal in account_payment.mapped("journal_id"):
            total_amount_supplier = 0
            total_amount_payroll = 0
            total_amount_different_payroll = 0
            total_amount_ISSSTE = 0
            total_amount_FOVISSSTE = 0
            
            lines.append({
                'id': 'hierarchy1_' + str(journal.id),
                'name': journal.name,
                'columns': [{'name': ''}, {'name': ''}, {'name': ''}, {'name': ''}, {'name': ''}, {'name': ''}],
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
            })
            payment_accounts = account_payment.filtered(lambda x:x.journal_id.id==journal.id).mapped('payment_issuing_bank_acc_id')
            for payment_account in payment_accounts:
                payment_type_records = account_payment.filtered(lambda x:x.journal_id.id==journal.id and x.payment_issuing_bank_acc_id.id==payment_account.id)
                supplier = sum(x.amount for x in payment_type_records.filtered(lambda x:x.payment_request_type == 'supplier_payment'))
                payroll = sum(x.amount for x in payment_type_records.filtered(lambda x:x.payment_request_type == 'payroll_payment'))
                payroll_diff = sum(x.amount for x in payment_type_records.filtered(lambda x:x.payment_request_type == 'different_to_payroll' and not x.partner_id.is_ISSSTE_supplier and not x.partner_id.is_FOVISSSTE_supplier))
                
                ISSSTE_supplier = sum(x.amount for x in payment_type_records.filtered(lambda x:x.payment_request_type == 'supplier_payment' and x.partner_id.is_ISSSTE_supplier))
                FOVISSSTE_supplier = sum(x.amount for x in payment_type_records.filtered(lambda x:x.payment_request_type == 'supplier_payment' and x.partner_id.is_FOVISSSTE_supplier))
                ISSSTE_payroll = sum(x.amount for x in payment_type_records.filtered(lambda x:x.payment_request_type == 'payroll_payment' and x.partner_id.is_ISSSTE_supplier))
                FOVISSSTE_payroll = sum(x.amount for x in payment_type_records.filtered(lambda x:x.payment_request_type == 'payroll_payment' and x.partner_id.is_FOVISSSTE_supplier))
                ISSSTE_diff_payroll = sum(x.amount for x in payment_type_records.filtered(lambda x:x.payment_request_type == 'different_to_payroll' and x.partner_id.is_ISSSTE_supplier))
                FOVISSSTE_diff_payroll = sum(x.amount for x in payment_type_records.filtered(lambda x:x.payment_request_type == 'different_to_payroll' and x.partner_id.is_FOVISSSTE_supplier))

                
                payment_type_name= ''
                total_amount_supplier += supplier
                master_total_amount_supplier += supplier

                total_amount_payroll += payroll
                master_total_amount_payroll += payroll

                total_amount_different_payroll += payroll_diff
                master_total_amount_different_payroll += payroll_diff
                
                total_amount_ISSSTE += ISSSTE_supplier + ISSSTE_payroll+ISSSTE_diff_payroll
                total_amount_FOVISSSTE += FOVISSSTE_supplier + FOVISSSTE_payroll+FOVISSSTE_diff_payroll

                master_total_amount_ISSSTE += ISSSTE_supplier + ISSSTE_payroll+ISSSTE_diff_payroll
                master_total_amount_FOVISSSTE += FOVISSSTE_supplier + FOVISSSTE_payroll+FOVISSSTE_diff_payroll
                
                if payroll:
                    payment_type_name = 'Nómina'
                    lines.append({
                        'id': 'hierarchy2_' + str(journal.id) + str(payment_account.id)+'Nómina',
                        'name': payment_account.acc_number,
                        'columns': [{'name': payment_type_name},
                                    self._format({'name': payroll},figure_type='float'), 
                                    self._format({'name': 0.0},figure_type='float'),
                                    self._format({'name': 0.0},figure_type='float'),
                                    self._format({'name': ISSSTE_payroll},figure_type='float'),
                                    self._format({'name': FOVISSSTE_payroll},figure_type='float'), 
                                    ],
                        'level': 3,
                        'parent_id': 'hierarchy1_' + str(journal.id),
                    })
                
                if supplier:
                    payment_type_name = 'Proveedores'
                    lines.append({
                        'id': 'hierarchy2_' + str(journal.id) + str(payment_account.id)+'Proveedores',
                        'name': payment_account.acc_number,
                        'columns': [{'name': payment_type_name},
                                    self._format({'name': 0.0},figure_type='float'), 
                                    self._format({'name': supplier},figure_type='float'),
                                    self._format({'name': 0.0},figure_type='float'),
                                    self._format({'name': ISSSTE_supplier},figure_type='float'),
                                    self._format({'name': FOVISSSTE_supplier},figure_type='float'), 
                                    ],
                        'level': 3,
                        'parent_id': 'hierarchy1_' + str(journal.id),
                    })

                if payroll_diff or ISSSTE_diff_payroll or FOVISSSTE_diff_payroll:
                    payment_type_name = 'Diferentes a nómina'
                    lines.append({
                        'id': 'hierarchy2_' + str(journal.id) + str(payment_account.id)+'Diferentes_nómina',
                        'name': payment_account.acc_number,
                        'columns': [{'name': payment_type_name},
                                    self._format({'name': 0.0},figure_type='float'), 
                                    self._format({'name': 0.0},figure_type='float'),
                                    self._format({'name': payroll_diff},figure_type='float'),
                                    self._format({'name': ISSSTE_diff_payroll},figure_type='float'),
                                    self._format({'name': FOVISSSTE_diff_payroll},figure_type='float'), 
                                    ],
                        'level': 3,
                        'parent_id': 'hierarchy1_' + str(journal.id),
                    })

            lines.append({
                'id': 'hierarchy1total_' + str(journal.id),
                'name': "TOTAL",
                'columns': [{'name': ''}, 
                            self._format({'name': total_amount_payroll},figure_type='float'),
                            self._format({'name': total_amount_supplier},figure_type='float'),
                            self._format({'name': total_amount_different_payroll},figure_type='float'),
                            self._format({'name': total_amount_ISSSTE},figure_type='float'),
                            self._format({'name': total_amount_FOVISSSTE},figure_type='float'), 
                            ],
                'level': 2,
                'parent_id': 'hierarchy1_' + str(journal.id),
            })

        lines.append({
            'id': 'hierarchy1mastertotal',
            'name': "Suma Total",
            'columns': [{'name': ''}, 
                        self._format({'name': master_total_amount_payroll},figure_type='float'),
                        self._format({'name': master_total_amount_supplier},figure_type='float'),
                        self._format({'name': master_total_amount_different_payroll},figure_type='float'),
                        self._format({'name': master_total_amount_ISSSTE},figure_type='float'),
                        self._format({'name': master_total_amount_FOVISSSTE},figure_type='float'), 
 
                        ],
            'level': 2,
            # 'parent_id': 'hierarchy1_' + str(journal.id),
        })
            
        return lines

    def _get_report_name(self):
        return _("Type of Operation")
    
    @api.model
    def _get_super_columns(self, options):
        date_cols = options.get('date') and [options['date']] or []
        date_cols += (options.get('comparison') or {}).get('periods', [])
        columns = reversed(date_cols)
        return {'columns': columns, 'x_offset': 1, 'merge': 4}

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
        sheet.set_column(0, 1,20)
        sheet.set_column(0, 2,15)
        sheet.set_column(0, 3,15)
        sheet.set_column(0, 4,15)
        sheet.set_column(0, 5,15)
        sheet.set_column(0, 6,15)
        super_columns = self._get_super_columns(options)
        y_offset = 0
        col = 0
        
        sheet.merge_range(y_offset, col, 6, col, '',super_col_style)
        if self.env.user and self.env.user.company_id and self.env.user.company_id.header_logo:
            filename = 'logo.png'
            image_data = io.BytesIO(base64.standard_b64decode(self.env.user.company_id.header_logo))
            sheet.insert_image(0,0, filename, {'image_data': image_data,'x_offset':5,'y_offset':3,'x_scale':0.46,'y_scale':0.6})
        
        col += 1
        header_title = '''UNIVERSIDAD NACIONAL AUTÓNOMA DE MÉXICO\nPATRONATO UNIVERSITARIO\nDIRECCIÓN GENERAL DE FINANZAS\nSUBDIRECCION DE FINANZAS\nDepartamento de Control Financiero\n%s'''%self._get_report_name()
        sheet.merge_range(y_offset, col, 5, col+5, header_title,super_col_style)
        y_offset += 6
        col=1
        currect_time_msg = "Fecha y hora de impresión: "
        currect_time_msg += datetime.today().strftime('%d/%m/%Y %H:%M')
        sheet.merge_range(y_offset, col, y_offset, col+5, currect_time_msg,currect_date_style)
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
            header = self.env['ir.actions.report'].render_template("jt_finance.external_layout_payment_expense", values=rcontext)
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
