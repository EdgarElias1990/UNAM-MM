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


class AccountingOperationWithdraw(models.AbstractModel):
    _name = "jt_agreement.account.operation.withdraw"
    _inherit = "account.coa.report"
    _description = "Report of accounting operations-withdrawals"

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
            AccountingOperationWithdraw, self)._get_templates()
        templates[
            'main_table_header_template'] = 'account_reports.main_table_header'
        templates['main_template'] = 'account_reports.main_template'
        return templates

    def _get_columns_name(self, options):
        return [
            {'name': _('OPERACIONES')},
            {'name': _('FECHA')},
            {'name': _('CONCEPTO')},
            {'name': _('CONVENIO')},
            {'name': _('CUENTA CONTABL')},
            {'name': _('CARGO')},
            {'name': _('ABONO')},

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
        
        
        move_lines = self.env['account.move.line'].search([('request_id.type_of_operation','in',('retirement','withdrawal','withdrawal_cancellation','withdrawal_closure')),('request_id','!=',False),('request_id.bases_collaboration_id','!=',False),('date', '>=', start), ('date', '<=', end)],order='date')
        total_debit = 0
        total_credit = 0
        lang = self.env.user.lang
        for line in move_lines:
            con_no = ''
            if line.request_id and line.request_id.bases_collaboration_id:
                con_no = line.request_id.bases_collaboration_id.convention_no
            opt = ''
            if line.request_id:
                opt = dict(line.request_id._fields['type_of_operation'].selection).get(line.request_id.type_of_operation)
                #opt = line.type_of_operation
                if lang == 'es_MX':
                    if line.request_id.type_of_operation=='open_bal':
                        opt = 'Importe de apertura'
                    elif line.request_id.type_of_operation=='increase':
                        opt = 'Incremento'
                    elif line.request_id.type_of_operation=='retirement':
                        opt = 'Retiro'
                    elif line.request_id.type_of_operation=='withdrawal':
                        opt = 'Retiro por liquidación'
                    elif line.request_id.type_of_operation=='withdrawal_cancellation':
                        opt = 'Retiro por cancelación'
                    elif line.request_id.type_of_operation=='withdrawal_closure':
                        opt = 'Retiro por cierre'
                    elif line.request_id.type_of_operation=='increase_by_closing':
                        opt = 'Incremento por cierre'
                
            total_debit += line.debit
            total_credit += line.credit
            date_format = ''
            if line.date:
                date_format = line.date.strftime("%d-%b-%Y")
                
            lines.append({
                'id': 'line_id_'+str(line.id),
                'name': line.move_id and line.move_id.name or '',
                'columns': [{'name': date_format}, 
                            {'name': opt}, 
                            {'name': con_no},
                            {'name': line.account_id and line.account_id.code or ''}, 
                            self._format({'name': line.debit},figure_type='float'),
                            self._format({'name': line.credit},figure_type='float'),
                            ],
                'level': 3,
                'unfoldable': False,
                'unfolded': True,
            })

        lines.append({
            'id': 'total',
            'name': '',
            'columns': [{'name': ''}, 
                        {'name': ''}, 
                        {'name': ''},
                        {'name': _('GRAN TOTAL:')}, 
                        self._format({'name': total_debit},figure_type='float'),
                        self._format({'name': total_credit},figure_type='float'),
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
        })
            
        return lines


    def _get_report_name(self):
        return _("Report of accounting operations-withdrawals")



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
            sign_data = self.env['agreement.sign'].search([('operation_type','=','withdraw')],limit=1)
            rcontext.update({
                    'css': '',
                    'o': self.env.user,
                    'res_company': self.env.company,
                    'sign' : sign_data
                })
            header = self.env['ir.actions.report'].render_template("jt_agreement.external_layout_accounting_operation_withdraw", values=rcontext)
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
