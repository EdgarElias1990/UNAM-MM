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


class PaymentDetailsBeneficiaries(models.AbstractModel):
    _name = "jt_agreement.payment_details_beneficiaries"
    _inherit = "account.coa.report"
    _description = "Payment Detail Beneficiaries"

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

    def _get_reports_buttons(self):
        return [
            {'name': _('Export to PDF'), 'sequence': 1,
             'action': 'print_pdf', 'file_export_type': _('PDF')},
            {'name': _('Export (XLSX)'), 'sequence': 2,
             'action': 'print_xlsx', 'file_export_type': _('XLSX')},
        ]

    def _get_templates(self):
        templates = super(
            PaymentDetailsBeneficiaries, self)._get_templates()
        templates[
            'main_table_header_template'] = 'account_reports.main_table_header'
        templates['main_template'] = 'account_reports.main_template'
        return templates

    def _get_columns_name(self, options):
        return [
            {'name': _('Operaciones')},
            {'name': _('FECHA INICIO')},
            {'name': _('FECHa FINAL')},
            {'name': _('ESTATUS')},
            {'name': _('MONTO')},
        ]

    def _get_report_name(self):
        return _("Payment Detail Beneficiaries")

    def _get_lines(self, options, line_id=None):
        lines = []
        record = options['date']
        start = record.get('date_from')
        end = record.get('date_to')

        base_ids = self.env['bases.collaboration'].search([('beneficiary_ids','!=',False)])
        
        for base in base_ids:
            base_no = ''
            state_name = 'Valido'
            if base.convention_no:
                base_no = base.convention_no
                
            lines.append({
                'id': 'hierarchy_base' + str(base.id),
                'name': 'CATEDRA:' + base_no,
                'columns': [{'name': base.name,'class':'text-left'}, 
                            {'name': ''}, 
                            {'name': ''},
                            {'name': ''},
                            ],
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
                'class':'text-center'
            })
            employee_ids =  base.beneficiary_ids.mapped('employee_id')
            for emp in employee_ids:
                lines.append({
                    'id': 'hierarchy_emp' + str(base.id) + str(emp.id),
                    'name': emp.rfc,
                    'columns': [{'name': emp.name}, 
                                {'name': ''}, 
                                {'name': ''},
                                {'name': ''},
                                ],
                    'level': 2,
                    'unfoldable': False,
                    'unfolded': True,
                })
                
                ben_ids =  base.beneficiary_ids.filtered(lambda x:x.employee_id.id==emp.id)
                for ben in ben_ids:
                    operation_ids = base.request_open_balance_ids.filtered(lambda x:x.collaboration_beneficiary_id.id==ben.id and x.state=='confirmed')
#                     partner_id = False
#                     if ben.partner_id:
#                         partner_id = ben.partner_id.id
#                     else: 
#                         partner_id = ben.employee_id and ben.employee_id.user_id and ben.employee_id.user_id.partner_id and ben.employee_id.user_id.partner_id.id or False
#                     
#                     if partner_id:
#                         operation_ids += base.request_open_balance_ids.filtered(lambda x:x.beneficiary_id.id==partner_id and x.opening_balance==ben.amount)
                        
                    if not operation_ids:
                        
                        lines.append({
                            'id': 'hierarchy_ben' + str(ben.id),
                            'name': str(ben.sequence),
                            'columns': [
                                        {'name': ben.validity_start}, 
                                        {'name': ben.validity_final_beneficiary},
                                        {'name': state_name},
                                        {'name': ben.amount},
                                        ],
                            'level': 3,
                            'unfoldable': False,
                            'unfolded': True,
                        })
                    for opt in operation_ids:
                        lines.append({
                            'id': 'hierarchy_ben' + str(opt.id),
                            'name': str(opt.operation_number),
                            'columns': [
                                        {'name': ben.validity_start}, 
                                        {'name': ben.validity_final_beneficiary},
                                        {'name': state_name},
                                        {'name': ben.amount},
                                        ],
                            'level': 3,
                            'unfoldable': False,
                            'unfolded': True,
                        })                        

            partner_ids =  base.beneficiary_ids.mapped('partner_id')
            for partner in partner_ids:
                lines.append({
                    'id': 'hierarchy_partner' + str(base.id) + str(partner.id),
                    'name': partner.vat,
                    'columns': [{'name': partner.name}, 
                                {'name': ''}, 
                                {'name': ''},
                                {'name': ''},
                                ],
                    'level': 2,
                    'unfoldable': False,
                    'unfolded': True,
                })
                
                ben_ids =  base.beneficiary_ids.filtered(lambda x:x.partner_id.id==partner.id)
                for ben in ben_ids:
                    operation_ids = base.request_open_balance_ids.filtered(lambda x:x.collaboration_beneficiary_id.id==ben.id and x.state=='confirmed')
#                     partner_id = False
#                     if ben.partner_id:
#                         partner_id = ben.partner_id.id
#                     else: 
#                         partner_id = ben.employee_id and ben.employee_id.user_id and ben.employee_id.user_id.partner_id and ben.employee_id.user_id.partner_id.id or False
#                     
#                     if partner_id:
#                         operation_ids += base.request_open_balance_ids.filtered(lambda x:x.beneficiary_id.id==partner_id and x.opening_balance==ben.amount)
                        
                    if not operation_ids:
                        
                        lines.append({
                            'id': 'hierarchy_ben' + str(ben.id),
                            'name': str(ben.sequence),
                            'columns': [
                                        {'name': ben.validity_start}, 
                                        {'name': ben.validity_final_beneficiary},
                                        {'name': state_name},
                                        {'name': ben.amount},
                                        ],
                            'level': 3,
                            'unfoldable': False,
                            'unfolded': True,
                        })
                    for opt in operation_ids:
                        lines.append({
                            'id': 'hierarchy_ben' + str(opt.id),
                            'name': str(opt.operation_number),
                            'columns': [
                                        {'name': ben.validity_start}, 
                                        {'name': ben.validity_final_beneficiary},
                                        {'name': state_name},
                                        {'name': ben.amount},
                                        ],
                            'level': 3,
                            'unfoldable': False,
                            'unfolded': True,
                        })                        
                
        return lines

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
            header = self.env['ir.actions.report'].render_template("jt_agreement.external_layout_payment_detail_benificarie", values=rcontext)
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
