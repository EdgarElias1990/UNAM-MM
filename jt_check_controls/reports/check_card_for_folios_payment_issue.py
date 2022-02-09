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


class CheckCardFolioPaymentIssue(models.AbstractModel):

    _name = "jt_check_controls.check_card_for_folios_and_issue_payments"
    _inherit = "account.coa.report"
    _description = "Check card for folios and issued payments"

    filter_date = {'mode': 'range'}
    filter_comparison = None
    filter_all_entries = None
    filter_journals = None
    filter_analytic = None
    filter_unfold_all = None
    filter_cash_basis = None
    filter_hierarchy = None
    filter_unposted_in_period = None
    MAX_LINES = None
    filter_fortnight = [
        {'id': '01', 'name': ('01'), 'selected': False},
        {'id': '02', 'name': ('02'), 'selected': False},
        {'id': '03', 'name': ('03'), 'selected': False},
        {'id': '04', 'name': ('04'), 'selected': False},
        {'id': '05', 'name': ('05'), 'selected': False},
        {'id': '06', 'name': ('06'), 'selected': False},
        {'id': '07', 'name': ('07'), 'selected': False},
        {'id': '08', 'name': ('08'), 'selected': False},
        {'id': '09', 'name': ('09'), 'selected': False},
        {'id': '10', 'name': ('10'), 'selected': False},
        {'id': '11', 'name': ('11'), 'selected': False},
        {'id': '12', 'name': ('12'), 'selected': False},
        {'id': '13', 'name': ('13'), 'selected': False},
        {'id': '14', 'name': ('14'), 'selected': False},
        {'id': '15', 'name': ('15'), 'selected': False},
        {'id': '16', 'name': ('16'), 'selected': False},
        {'id': '17', 'name': ('17'), 'selected': False},
        {'id': '18', 'name': ('18'), 'selected': False},
        {'id': '19', 'name': ('19'), 'selected': False},
        {'id': '20', 'name': ('20'), 'selected': False},
        {'id': '21', 'name': ('21'), 'selected': False},
        {'id': '22', 'name': ('22'), 'selected': False},
        {'id': '23', 'name': ('23'), 'selected': False},
        {'id': '24', 'name': ('24'), 'selected': False},
    ]
    
    filter_department = [
        {'id': 'ACATLAN', 'name': _('ACATLAN'), 'selected': False},
        {'id': 'ARAGON', 'name': _('ARAGON'), 'selected': False},
        {'id': 'CUAUTITLAN', 'name': _('CUAUTITLAN'), 'selected': False},
        {'id': 'CUERNAVACA', 'name': _('CUERNAVACA'), 'selected': False},
        {'id': 'COVE', 'name': _('ENSENADA'), 'selected': False},
        {'id': 'IZTACALA', 'name': _('IZTACALA'), 'selected': False},
        {'id': 'JURIQUILLA', 'name': _('JURIQUILLA'), 'selected': False},
        {'id': 'LION', 'name': _('LEON'), 'selected': False},
        {'id': 'MORELIA', 'name': _('MORELIA'), 'selected': False},
        {'id': 'YUCATAN', 'name': _('YUCATAN'), 'selected': False},
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
            CheckCardFolioPaymentIssue, self)._get_templates()
        templates[
            'main_table_header_template'] = 'account_reports.main_table_header'
        templates['main_template'] = 'account_reports.main_template'
        return templates

    def _get_columns_name(self, options):
        return [
            {'name': _('')},
            {'name': _('')},
            {'name': _('')},
        ]

    def _format(self, value,figure_type):
        if self.env.context.get('no_format'):
            return value
        value['no_format_name'] = value['name']
        
        currency_id = self.env.company.currency_id
        if figure_type == 'float':
            
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
        domain = []
        start = datetime.strptime(
            str(options['date'].get('date_from')), '%Y-%m-%d').date()
        end = datetime.strptime(
            options['date'].get('date_to'), '%Y-%m-%d').date()

        fortnight_domain = []
        
        fortnight_select = options.get('fortnight')
        for fortnight in fortnight_select:
            if fortnight.get('selected',False):
                fortnight_domain.append(fortnight.get('id'))
            
        domain = domain + [('payment_date','>=',start),('payment_date','<=',end),('type_of_batch','in',('nominal','pension'))]
        
        payment_issue_ids = self.env['payment.batch.supplier'].search(domain)
        batch_lines_ids = self.env['check.payment.req'].search([('check_status','=','Sent to protection'),
                                                                ('payment_batch_id','in',payment_issue_ids.ids)])
        payment_issue_ids = batch_lines_ids.mapped('payment_batch_id')

        department_domain = []
        
        department_select = options.get('department')
        for department in department_select:
            if department.get('selected',False):
                department_domain.append(department.get('id'))

        if department_domain and payment_issue_ids:
            batch_lines_ids = self.env['check.payment.req'].search([('payment_batch_id','in',payment_issue_ids.ids),
                                                                    ('check_folio_id.module','in',department_domain)])
            payment_issue_ids = batch_lines_ids.mapped('payment_batch_id')

        if fortnight_domain and payment_issue_ids:
            batch_lines_ids = self.env['check.payment.req'].search([('payment_batch_id','in',payment_issue_ids.ids),('payment_req_id.fornight','in',fortnight_domain)])
            payment_issue_ids = batch_lines_ids.mapped('payment_batch_id')
        
        journal_ids = payment_issue_ids.mapped('payment_issuing_bank_id')

        total_amount = 0
        total_check = 0 
        for journal in journal_ids:
            lines.append({
                'id': 'bank_name'+str(journal.id),
                'name' : journal.name, 
                'columns': [ 
                            {'name': ''},
                            {'name': ''},
                            ],
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
            })

            lines.append({
                'id': 'bank_header'+str(journal.id),
                'name' : _('Folio inicial'), 
                'columns': [ 
                            {'name': _('Folio final')},
                            {'name': _('Total')},
                            ],
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
            })
            
            bank_total = 0
            rec_ids = payment_issue_ids.filtered(lambda x:x.payment_issuing_bank_id.id==journal.id and x.type_of_batch == 'nominal')
            for rec in rec_ids:
                    line_payment_ids = rec.payment_req_ids.filtered(lambda r: r.check_status == 'Sent to protection')
                    folio_mapped_ids = line_payment_ids.mapped('check_folio_id').sorted(key='folio')
                    if folio_mapped_ids:
                        amount = 0
                        first_folio_id = False
                        last_folio_id = False
                         
                        for folio in  folio_mapped_ids:
                                
        
                            if last_folio_id and last_folio_id.folio and folio.folio and (last_folio_id.folio+1) != folio.folio: 
                                lines.append({
                                    'id': 'hierarchy_rec' + str(rec.id),
                                    'name': first_folio_id and first_folio_id.folio or '',
                                    'columns': [{'name': last_folio_id and last_folio_id.folio or ''},
                                                {'name': amount,'class':'number'},
                                                
                                                ],
                                    'level': 3,
                                    'unfoldable': False,
                                    'unfolded': True,
                                })
                                first_folio_id = False
                                last_folio_id = False
                                total_amount += amount
                                bank_total += amount
                                
                                amount = 0

                            for line in rec.payment_req_ids.filtered(lambda r: r.check_folio_id.id == folio.id):
                                #amount += line.amount_to_pay
                                amount += 1
                                
                                
                            if not first_folio_id:
                                first_folio_id = folio
                            if first_folio_id:
                                last_folio_id = folio
                        if first_folio_id:
                            lines.append({
                                'id': 'hierarchy_rec' + str(rec.id),
                                'name': first_folio_id and first_folio_id.folio or '',
                                'columns': [{'name': last_folio_id and last_folio_id.folio or ''},
                                            {'name': amount,'class':'number'},
                                            ],
                                'level': 3,
                                'unfoldable': False,
                                'unfolded': True,
                            })
                            first_folio_id = False
                            last_folio_id = False
                            total_amount += amount
                            bank_total += amount
                            
                            amount = 0

            rec_ids = payment_issue_ids.filtered(lambda x:x.payment_issuing_bank_id.id==journal.id and x.type_of_batch == 'pension')
            for rec in rec_ids:
                    line_payment_ids = rec.payment_req_ids.filtered(lambda r: r.check_status == 'Sent to protection')
                    folio_mapped_ids = line_payment_ids.mapped('check_folio_id').sorted(key='folio')
                    if folio_mapped_ids:
                        amount = 0
                        first_folio_id = False
                        last_folio_id = False
                          
                        for folio in  folio_mapped_ids:
                                 
         
                            if last_folio_id and last_folio_id.folio and folio.folio and (last_folio_id.folio+1) != folio.folio:
                                msg_str = 'Incluye los folios' +str(first_folio_id.folio)+" al "+str(last_folio_id.folio)+" que son de Pension Alimenticia" 
                                lines.append({
                                    'id': 'hierarchy_rec' + str(rec.id),
                                    'name': msg_str,
                                    'columns': [
                                                {'name': amount,'class':'number'},
                                                 
                                                ],
                                    'level': 3,
                                    'unfoldable': False,
                                    'unfolded': True,
                                    'colspan':2,
                                })
                                first_folio_id = False
                                last_folio_id = False
                                total_amount += amount
                                bank_total += amount
                                
                                amount = 0
 
                            for line in rec.payment_req_ids.filtered(lambda r: r.check_folio_id.id == folio.id):
                                #amount += line.amount_to_pay
                                amount -= 1
                                 
                                 
                            if not first_folio_id:
                                first_folio_id = folio
                            if first_folio_id:
                                last_folio_id = folio
                        if first_folio_id:
                            first_folio_name = first_folio_id and first_folio_id.folio or ''
                            last_folio_name = last_folio_id and last_folio_id.folio or ''
                            msg_str = 'Incluye los folios' +str(first_folio_name)+" al "+str(last_folio_name)+" que son de Pension Alimenticia"
                            
                            lines.append({
                                'id': 'hierarchy_rec' + str(rec.id),
                                'name': msg_str,
                                'columns': [
                                            {'name': amount,'class':'number'},
                                            ],
                                'level': 3,
                                'unfoldable': False,
                                'unfolded': True,
                                'colspan':2,
                            })
                            first_folio_id = False
                            last_folio_id = False
                            total_amount += amount
                            bank_total += amount
                            
                            amount = 0
                            
            bank_name = 'TOTAL CHEQUES '+str(journal.name)
            lines.append({
                'id': 'total'+str(journal.id),
                'name' : '', 
                'columns': [ 
                            {'name': bank_name},
                            {'name': bank_total,'class':'number'},
                            ],
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
            })

        lines.append({
            'id': 'total',
            'name' : '', 
            'columns': [ 
                        {'name': _('TOTAL CHEQUES BANCOS')},
                        {'name': total_amount,'class':'number'},
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
        })
             
        return lines

    def _get_report_name(self):
        return _("Certificate of verification of folios and payments issued")

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
        body_html = body_html.replace(b'<div class="o_account_reports_header">',b'<div style="display:none;">')

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
            header = self.env['ir.actions.report'].render_template("jt_check_controls.external_layout_check_card_for_folios", values=rcontext)
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

        sheet.merge_range(y_offset, col, 6, col, '', super_col_style)
        if self.env.user and self.env.user.company_id and self.env.user.company_id.header_logo:
            filename = 'logo.png'
            image_data = io.BytesIO(base64.standard_b64decode(
                self.env.user.company_id.header_logo))
            sheet.insert_image(0, 0, filename, {
                               'image_data': image_data, 'x_offset': 8, 'y_offset': 3, 'x_scale': 0.6, 'y_scale': 0.6})

        col += 1
        header_title = '''CEDULA DE COMPROBACIÓN DE FOLIOS Y PAGOS EMITIDOS\nQNA'''
        sheet.merge_range(y_offset, col, 5, col + 6,
                          header_title, super_col_style)
        y_offset += 6
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
