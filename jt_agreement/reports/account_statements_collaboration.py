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


class AccountStatementsCollaboration(models.AbstractModel):
    _name = "jt_agreement.account.statements.collaboration"
    _inherit = "account.coa.report"
    _description = "Account Statements Collaboration"

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
            AccountStatementsCollaboration, self)._get_templates()
        templates[
            'main_table_header_template'] = 'account_reports.main_table_header'
        templates['main_template'] = 'account_reports.main_template'
        return templates

    def _get_columns_name(self, options):
        return [
            {'name': _('Fecha'),'class': 'text-center'},
            {'name': _('Operación')},
            {'name': _('Depósitos')},
            {'name': _('Retiro')},
            {'name': _('Saldo')},
        ]

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
        start = datetime.strptime(
            str(options['date'].get('date_from')), '%Y-%m-%d').date()
        end = datetime.strptime(
            options['date'].get('date_to'), '%Y-%m-%d').date()
        
        req_lines = self.env['request.open.balance'].search([('bases_collaboration_id','!=',False),('state','=','confirmed'),('request_date', '>=',start),('request_date', '<=',end)])
        base_ids = req_lines.mapped('bases_collaboration_id')
        lang = self.env.user.lang
        total_final = 0
        for base in base_ids:
            base_line_ids = req_lines.filtered(lambda x:x.bases_collaboration_id.id==base.id)
            req_date = base_line_ids.mapped('request_date')
            
            req_date += base.rate_base_ids.filtered(lambda x:x.interest_date >= start and x.interest_date <= end).mapped('interest_date')

            lines.append({
            'id': 'hierarchy_'+str(base.id),
            'name': 'Convenio :   '+str(base.name),
            'columns': [{'name': 'Num.de Convenio :     '+str(base.convention_no)}, 
                        {'name': ''}, 
                        {'name': ''},
                        {'name': ''}, 
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
            })

            if req_date:
                req_date = list(set(req_date))
                req_date =  sorted(req_date)
            final = 0
            for req in req_date:
                opt_lines = base_line_ids.filtered(lambda x:x.state=='confirmed' and x.request_date == req)
                for line in opt_lines:
                    opt = dict(line._fields['type_of_operation'].selection).get(line.type_of_operation)
                    #opt = line.type_of_operation
                    if lang == 'es_MX':
                        if line.type_of_operation=='open_bal':
                            opt = 'Importe de apertura'
                        elif line.type_of_operation=='increase':
                            opt = 'Incremento'
                        elif line.type_of_operation=='retirement':
                            opt = 'Retiro'
                        elif line.type_of_operation=='withdrawal':
                            opt = 'Retiro por liquidación'
                        elif line.type_of_operation=='withdrawal_cancellation':
                            opt = 'Retiro por cancelación'
                        elif line.type_of_operation=='withdrawal_closure':
                            opt = 'Retiro por cierre'
                        elif line.type_of_operation=='increase_by_closing':
                            opt = 'Incremento por cierre'
                    debit = 0
                    credit = 0  
                    if line.type_of_operation in ('open_bal','increase','increase_by_closing'):         
                        final += line.opening_balance
                        total_final += line.opening_balance
                        debit = line.opening_balance
                    elif line.type_of_operation in ('withdrawal','retirement','withdrawal_cancellation','withdrawal_closure'):
                        final -= line.opening_balance
                        total_final -= line.opening_balance
                        credit = line.opening_balance

                    lines.append({
                    'id': 'Date_'+str(base.id),
                    'name': line.request_date,'class': 'text-center',
                    'columns': [{'name': opt}, 
                                self._format({'name': debit},figure_type='float'), 
                                self._format({'name': credit},figure_type='float'),
                                self._format({'name': final},figure_type='float'), 
                                ],
                    'level': 3,
                    'unfoldable': False,
                    'unfolded': True,
                    })
                        
    
                for line in base.rate_base_ids.filtered(lambda x:x.interest_date == req):
                    final += line.interest_rate
                    total_final += line.interest_rate
                    lines.append({
                    'id': 'Date_in'+str(base.id),'class': 'text-center',
                    'name': line.interest_date,
                    'columns': [{'name': 'Intereses' if lang == 'es_MX' else 'Interest',}, 
                                self._format({'name': line.interest_rate},figure_type='float'), 
                                self._format({'name': 0.0},figure_type='float'),
                                self._format({'name': final},figure_type='float'), 
                                ],
                    'level': 3,
                    'unfoldable': False,
                    'unfolded': True,
                    })

        lines.append({
        'id': 'Total',
        'name': 'Total',
        'columns': [{'name': '',}, 
                    {'name': '',}, 
                    {'name': '',},
                    self._format({'name': total_final},figure_type='float'), 
                    ],
        'level': 1,
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
        body_html = body_html.replace(b'<div class="o_account_reports_header">',b'<div style="display:none;text-align:center;">')
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
            header = self.env['ir.actions.report'].render_template("jt_agreement.external_layout_account_statement_collabortion", values=rcontext)
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



    def _get_report_name(self):
        return _("Account Statements")

    @api.model
    def _get_super_columns(self, options):
        date_cols = options.get('date') and [options['date']] or []
        date_cols += (options.get('comparison') or {}).get('periods', [])
        columns = reversed(date_cols)
        return {'columns': columns, 'x_offset': 1, 'merge': 4}

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
