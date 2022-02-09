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

class DetailStatementOfIncomeExpensesandInvestment(models.AbstractModel):

    _name = "jt_account_module_design.stat.inc.exp.inv.report"
    _inherit = "account.coa.report"
    _description = "Detail Statements of Income,expenses and investments"

    filter_date = {'mode': 'range', 'filter': 'this_month'}
    filter_comparison = None
    filter_all_entries = True
    filter_journals = True
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
            DetailStatementOfIncomeExpensesandInvestment, self)._get_templates()
        templates[
            'main_table_header_template'] = 'account_reports.main_table_header'
        templates['main_template'] = 'account_reports.main_template'
        return templates

    def _get_columns_name(self, options):
        return [
            {'name': _('Concepto')},
            {'name': _('ASSIGNED ADVICE')},
            {'name': _('Transfers')},
            {'name': _('Assigned')},
            {'name': _('TIENDA')},
            {'name': _('CONTABLE EXERCISE')},
            {'name': _('EXTRAORDINARY INCOMES')},
            {'name': _('EXTRA BOOKS')},
            {'name': _('Exercised')},
            {'name': _('Percentage')},
            {'name': _('EXERCISE PENDANT')},

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

        if options.get('all_entries') is False:
            move_state_domain = ('move_id.state', '=', 'posted')
        else:
            move_state_domain = ('move_id.state', '!=', 'cancel')

        #domain = [('date', '>=', start),('date', '<=', end),move_state_domain]
        domain = [('date', '<=', end),move_state_domain]
        
        concept_ids = self.env['detailed.statement.income'].search([('inc_exp_type','!=',False)])
        
        
        list_data = ['income','expenses','investments','other expenses']
        
        remant_authorized = 0
        remant_transfers = 0
        remant_assign = 0
        remant_contable_exercised = 0
        remant_e_income = 0
        remant_extra_book = 0
        remant_exercised = 0
        remant_to_exercised = 0

        expenses_authorized = 0
        expenses_transfers = 0
        expenses_assign = 0
        expenses_contable_exercised = 0
        expenses_e_income = 0
        expenses_extra_book = 0
        expenses_exercised = 0
        expenses_to_exercised = 0

        year_authorized = 0
        year_transfers = 0
        year_assign = 0
        year_contable_exercised = 0
        year_e_income = 0
        year_extra_book = 0
        year_exercised = 0
        year_to_exercised = 0
        
        for type in list_data:
            type_concept_ids = concept_ids.filtered(lambda x:x.inc_exp_type == type)
            major_ids = type_concept_ids.mapped('major_id')

            if type_concept_ids:
                name = type.upper()
                if self.env.lang == 'es_MX' and type == 'income':
                    str1 = 'INGRESOS'
                    name = str1.upper()
                if self.env.lang == 'es_MX' and type == 'expenses':
                    str2 = 'GASTOS'
                    name = str2.upper()
                if self.env.lang == 'es_MX' and type == 'investments':
                    str3 = 'INVERSIONES'
                    name = str3.upper()
                if self.env.lang == 'es_MX' and type == 'other expenses':
                    str4 = 'OTROS GASTOS'
                    name = str4.upper()

                lines.append({
                    'id': type,
                    'name': name,
                    'columns': [
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                ],
    
                    'level': 1,
                    'unfoldable': False,
                    'unfolded': True,
                })
            
            for major in major_ids:  
                                
                total_per = 100
                lines.append({
                    'id': 'major' + str(major.id),
                    'name': major.name,
                    'columns': [
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                {'name': ''},
                                ],
    
                    'level': 1,
                    'unfoldable': False,
                    'unfolded': True,
                    'class':'text-left'
                })
                
                for con in type_concept_ids.filtered(lambda x:x.major_id.id == major.id):
                    account_lines = []
                    total_authorized = 0
                    total_transfers = 0
                    total_assign = 0
                    total_contable_exercised = 0
                    total_e_income = 0
                    total_extra_book = 0
                    total_exercised = 0
                    total_to_exercised = 0
                    
                    account_ids = con.account_ids
                    

                    for acc in account_ids:
#                         values= self.env['account.move.line'].search(domain + [('budget_id','!=',False),('account_id', 'in', acc.ids)])
#                         authorized = sum(x.debit-x.credit for x in values)
#                         authorized = authorized/1000
                        authorized = 0
                        assign = 0
                        transfers = 0
                        # ======Budget Data ======#
                        if con.item_ids:
                            acc_item_ids = con.item_ids.filtered(lambda x:x.unam_account_id.id==acc.id)
                            if acc_item_ids:
                                program_code_ids = self.env['program.code'].search([('item_id','in',acc_item_ids.ids)])
                                if program_code_ids:
                                    #self.env.cr.execute("select coalesce(sum(ebl.authorized),0) from expenditure_budget_line ebl where ebl.program_code_id in %s and ebl.imported_sessional IS NULL and start_date >= %s and end_date <= %s", (tuple(program_code_ids.ids),start,end))
                                    self.env.cr.execute("select coalesce(sum(ebl.authorized),0) from expenditure_budget_line ebl where ebl.program_code_id in %s and ebl.imported_sessional IS NULL and end_date <= %s", (tuple(program_code_ids.ids),end))
                                    my_datas = self.env.cr.fetchone()
                                    if my_datas:
                                        authorized = my_datas[0]
        
                                    self.env.cr.execute("select coalesce(SUM(CASE WHEN al.line_type = %s THEN al.amount ELSE -al.amount END),0) from adequacies_lines al,adequacies a where a.state=%s and al.program in %s and a.id=al.adequacies_id", ('increase','accepted',tuple(program_code_ids.ids)))
                                    my_datas = self.env.cr.fetchone()
                                    if my_datas:
                                        assign = my_datas[0]
                                
                            transfers = assign
                            assign += authorized
                            
                            authorized = authorized/1000
                            assign = assign/1000
                            transfers = transfers/1000
                            
                        total_authorized += authorized
                        
                        total_transfers += transfers

#                         values= self.env['account.move.line'].search(domain + [('adequacy_id','!=',False),('account_id', 'in', acc.ids)])
#                         assign = sum(x.debit-x.credit for x in values)
#                         assign = assign/1000
                        total_assign += assign

                        values= self.env['account.move.line'].search(domain + [('account_id', 'in', acc.ids)])
                        contable_exercised = sum(x.credit - x.debit for x in values)
                        contable_exercised = abs(contable_exercised)
                        contable_exercised = contable_exercised/1000
                        
                        #contable_exercised = 0
                        total_contable_exercised += contable_exercised

                        e_income = 0
                        total_e_income += e_income
                        
                        extra_book = 0
                        total_extra_book += extra_book
                        
                        values= self.env['account.move.line'].search(domain + [('move_id.payment_state','in',('for_payment_procedure','payment_not_applied')),('account_id', 'in', acc.ids)])
                        exercised = sum(x.debit-x.credit for x in values)
                        exercised = exercised/1000
                        total_exercised += exercised

                        values= self.env['account.move.line'].search(domain + [('budget_id','!=',False),('account_id', 'in', acc.ids)])
                        to_exercised = sum(x.debit-x.credit for x in values)
                        to_exercised = to_exercised/1000
                        
                        total_to_exercised += to_exercised
                         
                            
                        per = 0.00
                        if exercised:
                            per = 100.00
                        if assign > 0:
                            per = (exercised/assign)*100
                            
                        account_lines.append({
                            'id': 'account' + str(acc.id),
                            'name': str(acc.code) +" "+ str(acc.name),
                            'columns': [
                                        self._format({'name': authorized},figure_type='float'),
                                        self._format({'name': transfers},figure_type='float'),
                                        self._format({'name': assign},figure_type='float'),
                                        {'name': ''},
                                        self._format({'name': contable_exercised},figure_type='float'),
                                        self._format({'name': e_income},figure_type='float'),
                                        self._format({'name': extra_book},figure_type='float'),
                                        self._format({'name': exercised},figure_type='float'),
                                        {'name': per,'class':'number'},
                                        self._format({'name': to_exercised},figure_type='float'),
                                        ],
            
                            'level': 3,
                            'unfoldable': False,
                            'unfolded': True,
                            'parent_id': 'con' + str(con.id),
                        })

                    if type == 'income':
                        # if self.env.user.lang == 'es_MX':
                        #         type.update({'name':'INGRESOS'})
                        remant_authorized += total_authorized
                        remant_transfers += total_transfers
                        remant_assign += total_assign
                        remant_contable_exercised += total_contable_exercised
                        remant_e_income += total_e_income
                        remant_extra_book += total_extra_book
                        remant_exercised += total_exercised
                        remant_to_exercised += total_to_exercised

                        year_authorized += total_authorized
                        year_transfers += total_transfers
                        year_assign += total_assign
                        year_contable_exercised += total_contable_exercised
                        year_e_income += total_e_income
                        year_extra_book += total_extra_book
                        year_exercised += total_exercised
                        year_to_exercised += total_to_exercised
                        
                    elif type == 'expenses':
                        remant_authorized -= total_authorized
                        remant_transfers -= total_transfers
                        remant_assign -= total_assign
                        remant_contable_exercised -= total_contable_exercised
                        remant_e_income -= total_e_income
                        remant_extra_book -= total_extra_book
                        remant_exercised -= total_exercised
                        remant_to_exercised -= total_to_exercised
                        
                    if type != 'income':
                        expenses_authorized += total_authorized
                        expenses_transfers += total_transfers
                        expenses_assign += total_assign
                        expenses_contable_exercised += total_contable_exercised
                        expenses_e_income += total_e_income
                        expenses_extra_book += total_extra_book
                        expenses_exercised += total_exercised
                        expenses_to_exercised += total_to_exercised

                        year_authorized -= total_authorized
                        year_transfers -= total_transfers
                        year_assign -= total_assign
                        year_contable_exercised -= total_contable_exercised
                        year_e_income -= total_e_income
                        year_extra_book -= total_extra_book
                        year_exercised -= total_exercised
                        year_to_exercised -= total_to_exercised

                    total_per = 0.00
                    if total_exercised:
                        total_per = 100.00
                    if total_assign > 0:
                        total_per = (total_exercised/total_assign)*100

                    lines.append({
                        'id': 'con' + str(con.id),
                        'name': con.concept,
                        'columns': [
                                    self._format({'name': total_authorized},figure_type='float'),
                                    self._format({'name': total_transfers},figure_type='float'),
                                    self._format({'name': total_assign},figure_type='float'),
                                    {'name': ''},
                                    self._format({'name': total_contable_exercised},figure_type='float'),
                                    self._format({'name': total_e_income},figure_type='float'),
                                    self._format({'name': total_extra_book},figure_type='float'),
                                    self._format({'name': total_exercised},figure_type='float'),
                                    {'name': total_per,'class':'number'},
                                    self._format({'name': total_to_exercised},figure_type='float'),
                                    ],
        
                        'level': 2,
                        'unfoldable': True,
                        'unfolded': False,
                        'class':'text-left'
                    })
                    lines += account_lines
                    lines.append({
                        'id': 'group_total',
                        'name': 'SUMA',
                        'columns': [
                                    self._format({'name': total_authorized},figure_type='float'),
                                    self._format({'name': total_transfers},figure_type='float'),
                                    self._format({'name': total_assign},figure_type='float'),
                                    {'name': ''},
                                    self._format({'name': total_contable_exercised},figure_type='float'),
                                    self._format({'name': total_e_income},figure_type='float'),
                                    self._format({'name': total_extra_book},figure_type='float'),
                                    self._format({'name': total_exercised},figure_type='float'),
                                    {'name': total_per,'class':'number'},
                                    self._format({'name': total_to_exercised},figure_type='float'),
                                    ],
                        
                        'level': 1,
                        'unfoldable': False,
                        'unfolded': True,
                        'class':'text-right',
                        'parent_id': 'con' + str(con.id),
                    })
            if type=="expenses":

                remant_per = 0.00
                if remant_exercised:
                    remant_per = 100.00
                if remant_assign > 0:
                    remant_per = (remant_exercised/remant_assign)*100
                
                lines.append({
                    'id': 'REMNANT',
                    'name': _('REMAINING BEFORE INVESTMENTS'),
                    'columns': [
                            self._format({'name': remant_authorized},figure_type='float'),
                            self._format({'name': remant_transfers},figure_type='float'),
                            self._format({'name': remant_assign},figure_type='float'),
                            {'name': ''},
                            self._format({'name': remant_contable_exercised},figure_type='float'),
                            self._format({'name': remant_e_income},figure_type='float'),
                            self._format({'name': remant_extra_book},figure_type='float'),
                            self._format({'name': remant_exercised},figure_type='float'),
                            {'name': remant_per,'class':'number'},
                            self._format({'name': remant_to_exercised},figure_type='float'),
                            ],
                
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
                'class':'text-right'
            })

        expenses_per = 0.00
        if expenses_exercised:
            expenses_per = 100.00
        if expenses_assign > 0:
            expenses_per = (expenses_exercised/expenses_assign)*100

        lines.append({
            'id': 'Total EXPENSES',
            'name': _('TOTAL EXPENSES, INVESTMENTS AND OTHER EXPENSES'),
            'columns': [
                    self._format({'name': expenses_authorized},figure_type='float'),
                    self._format({'name': expenses_transfers},figure_type='float'),
                    self._format({'name': expenses_assign},figure_type='float'),
                    {'name': ''},
                    self._format({'name': expenses_contable_exercised},figure_type='float'),
                    self._format({'name': expenses_e_income},figure_type='float'),
                    self._format({'name': expenses_extra_book},figure_type='float'),
                    self._format({'name': expenses_exercised},figure_type='float'),
                    {'name': expenses_per,'class':'number'},
                    self._format({'name': expenses_to_exercised},figure_type='float'),
                    ],
        
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-right'
        })

        year_per = 0.00
        if year_exercised:
            year_per = 100.00
        if year_assign > 0:
            year_per = (year_exercised/year_assign)*100

        lines.append({
            'id': 'Total Year',
            'name': _('REMAINING OF THE YEAR'),
            'columns': [
                    self._format({'name': year_authorized},figure_type='float'),
                    self._format({'name': year_transfers},figure_type='float'),
                    self._format({'name': year_assign},figure_type='float'),
                    {'name': ''},
                    self._format({'name': year_contable_exercised},figure_type='float'),
                    self._format({'name': year_e_income},figure_type='float'),
                    self._format({'name': year_extra_book},figure_type='float'),
                    self._format({'name': year_exercised},figure_type='float'),
                    {'name': year_per,'class':'number'},
                    self._format({'name': year_to_exercised},figure_type='float'),
                    ],
        
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-right'
        })
                
        return lines
    def _get_report_name(self):
        return _("Detail Statement of Income,Expenses and Investments Report")

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
            header = self.env['ir.actions.report'].render_template("jt_account_module_design.external_layout_income_exp_and_invest", values=rcontext)
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
        

        header_title = "UNIVERSIDAD NACIONAL AUTÓNOMA DE MÉXICO"
        header_title += "\n"
        header_title += "DIRECCIÓN GENERAL DE CONTROL PRESUPUESTAL-CONTADURÍA GENERAL "
        header_title += "\n"
        header_title += "ESTADO DE INGRESOS, GASTOS E INVERSIONES DETALLADOS DEL "
        header_title += str(header_date)
        header_title += "\n"
        header_title += "Cifras en Miles de Pesos"
    
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

