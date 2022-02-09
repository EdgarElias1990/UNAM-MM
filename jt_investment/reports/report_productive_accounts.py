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
from datetime import timedelta
from dateutil.relativedelta import relativedelta

class ReportProductiveAccounts(models.AbstractModel):
    _name = "jt_investment.report.productive.accounts"
    _inherit = "account.coa.report"
    _description = "Report Productive Accounts"

    filter_date = {'mode': 'range', 'filter': 'this_month'}
    filter_comparison = {'date_from': '', 'date_to': '', 'filter': 'no_comparison', 'number_period': 1}
    filter_all_entries = True
    filter_journals = True
    filter_analytic = None
    filter_unfold_all = None
    filter_cash_basis = None
    filter_hierarchy = None
    filter_unposted_in_period = None
    MAX_LINES = None

    filter_contract = True
    filter_currency = True
    filter_funds = None

    @api.model
    def _get_filter_funds(self):
        return self.env['agreement.fund'].search([])

    @api.model
    def _init_filter_funds(self, options, previous_options=None):
        if self.filter_funds is None:
            return
        if previous_options and previous_options.get('funds'):
            journal_map = dict((opt['id'], opt['selected']) for opt in previous_options['funds'] if opt['id'] != 'divider' and 'selected' in opt)
        else:
            journal_map = {}
        options['funds'] = []

        default_group_ids = []

        for j in self._get_filter_funds():
            options['funds'].append({
                'id': j.id,
                'name': j.name,
                'code': j.name,
                'selected': journal_map.get(j.id, j.id in default_group_ids),
            })

    @api.model
    def _get_filter_currency(self):
        return self.env['res.currency'].search([])

    @api.model
    def _init_filter_currency(self, options, previous_options=None):
        if self.filter_currency is None:
            return
        if previous_options and previous_options.get('currency'):
            journal_map = dict((opt['id'], opt['selected']) for opt in previous_options['currency'] if opt['id'] != 'divider' and 'selected' in opt)
        else:
            journal_map = {}
        options['currency'] = []

        default_group_ids = []

        for j in self._get_filter_currency():
            options['currency'].append({
                'id': j.id,
                'name': j.name,
                'code': j.name,
                'selected': journal_map.get(j.id, j.id in default_group_ids),
            })

    @api.model
    def _get_filter_contract(self):
        return self.env['investment.contract'].search([])

    @api.model
    def _init_filter_contract(self, options, previous_options=None):
        if self.filter_contract is None:
            return
        if previous_options and previous_options.get('contract'):
            journal_map = dict((opt['id'], opt['selected']) for opt in previous_options['contract'] if opt['id'] != 'divider' and 'selected' in opt)
        else:
            journal_map = {}
        options['contract'] = []

        default_group_ids = []

        for j in self._get_filter_contract():
            options['contract'].append({
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
            ReportProductiveAccounts, self)._get_templates()
        templates[
            'main_table_header_template'] = 'account_reports.main_table_header'
        templates['main_template'] = 'account_reports.main_template'
        return templates

    def _get_columns_name(self, options):
        return [
            {'name': _('Institución financiera')},
            {'name': _('Contrato')},
            {'name':_('moneda')},            
            {'name': _('Capital')},
            {'name': _('Tasa')},
            {'name': _('Plazo Dies')},
            {'name': _('Total')},
            {'name': _('Procentual extra')},
            {'name': _('Procentual extra')},
            {'name': _('Diferencia')},
        ]

    def get_month_name(self,month):
        month_name = ''
        if month==1:
            month_name = 'Enero'
        elif month==2:
            month_name = 'Febrero'
        elif month==3:
            month_name = 'Marzo'
        elif month==4:
            month_name = 'Abril'
        elif month==5:
            month_name = 'Mayo'
        elif month==6:
            month_name = 'Junio'
        elif month==7:
            month_name = 'Julio'
        elif month==8:
            month_name = 'Agosto'
        elif month==9:
            month_name = 'Septiembre'
        elif month==10:
            month_name = 'Octubre'
        elif month==11:
            month_name = 'Noviembre'
        elif month==12:
            month_name = 'Diciembre'
            
        return month_name.upper()

    def _format(self, value,figure_type,digit,is_currency):
        if self.env.context.get('no_format'):
            return value
        value['no_format_name'] = value['name']
        
        if figure_type == 'float':

            if is_currency:
                currency_id = self.env.company.currency_id
            else:
                currency_id = False
            
            if currency_id and currency_id.is_zero(value['name']):
                # don't print -0.0 in reports
                value['name'] = abs(value['name'])
                value['class'] = 'number text-muted'
            value['name'] = formatLang(self.env, value['name'], currency_obj=currency_id,digits=digit)
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
        contract_list = []
        currency_list = []
        fund_list = []
        journal_list = []
        
        comparison = options.get('comparison')
        periods = []
        if comparison and comparison.get('filter') != 'no_comparison':
            period_list = comparison.get('periods')
            period_list.reverse()
            periods = [period for period in period_list]
        periods.append(options.get('date'))

        if options.get('all_entries') is False:
            domain=[('state','in',('confirmed','done'))]
            line_domain=[('investment_id.state','in',('confirmed','done'))]
            
        else:
            domain=[('state','not in',('rejected','canceled'))]
            line_domain=[('investment_id.state','not in',('rejected','canceled'))]

#         journal = self._get_options_journals_domain(options)
#         if journal:
#             domain+=journal

#         for fund in options.get('funds'):
#             if fund.get('selected',False)==True:
#                 fund_list.append(fund.get('id',0))
#         
#         if fund_list:
#             domain.append(('investment_fund_id.fund_id','in',fund_list))

        for select_curreny in options.get('currency'):
            if select_curreny.get('selected',False)==True:
                currency_list.append(select_curreny.get('id',0))

        if currency_list:
            domain.append(('currency_id','in',currency_list))
            line_domain.append(('investment_id.currency_id','in',currency_list))
        
        for contract in options.get('contract'):
            if contract.get('selected',False)==True:
                contract_list.append(contract.get('id',0))
        
        if contract_list:
            domain.append(('contract_id','in',currency_list))
            line_domain.append(('investment_id.contract_id','in',currency_list))

        for journal in options.get('journals'):
            if journal.get('selected',False)==True:
                journal_list.append(journal.get('id',0))

        if journal_list:
            domain += [('journal_id','in',journal_list)]
            line_domain += [('investment_id.journal_id','in',journal_list)]
        
        start = datetime.strptime(
            str(options['date'].get('date_from')), '%Y-%m-%d').date()
        end = datetime.strptime(
            options['date'].get('date_to'), '%Y-%m-%d').date()

        main_domain = domain + [('invesment_date','>=',start),('invesment_date','<=',end)]
        line_main_domain = line_domain + [('date_required','>=',start),('date_required','<=',end)]
        
        #records = self.env['investment.investment'].search([('invesment_date','>=',start),('invesment_date','<=',end)])
        records = self.env['investment.investment'].search(main_domain)
        line_records = self.env['investment.operation'].search(line_main_domain)
        line_records = line_records.mapped('investment_id')
        records += line_records
        if records:
            records = list(set(records.ids))
            records = self.env['investment.investment'].browse(records)
            
        #line_records = line_records - records
        line_records = []
        month_list = {1:[],2:[],3:[],4:[],5:[],6:[],
                      7:[],8:[],9:[],10:[],11:[],12:[]
                      }

        total_month_list = {1:[],2:[],3:[],4:[],5:[],6:[],
                      7:[],8:[],9:[],10:[],11:[],12:[]
                      }
        
        total_days = 0
        total_p_amount = 0
        total_extra_amount = 0
        total_diff_amount = 0
        precision = self.env['decimal.precision'].precision_get('Productive Accounts')
        for rec in records:
            inv_amt = 0
            pro_lines = rec.line_ids.filtered(lambda x: x.line_state == 'done' and x.date_required and x.date_required <= end)
            inv_amt += sum(a.amount for a in pro_lines.filtered(lambda x: x.line_state ==
                                                                  'done' and x.type_of_operation in ('open_bal', 'increase', 'increase_by_closing')))
            inv_amt -= sum(a.amount for a in pro_lines.filtered(lambda x: x.line_state == 'done' and x.type_of_operation in (
                'retirement', 'withdrawal', 'withdrawal_cancellation', 'withdrawal_closure')))
            
            term = 0
            if rec.is_fixed_rate:
                term = rec.term
            if rec.is_variable_rate:
                term = rec.term_variable
            total_rate = rec.extra_percentage + rec.interest_rate
            
            days = ((rec.actual_amount * total_rate)/100)/360*term
            total_days += days
            extra_percentage_value =  ((rec.actual_amount * rec.extra_percentage)/100)/360*term
            diffrence = days - extra_percentage_value
            capital =  self._format({'name': rec.actual_amount},figure_type='float',digit=2,is_currency=True)
            capital = capital.get('name')
            
            total_p_amount += days
            total_extra_amount += extra_percentage_value
            total_diff_amount += diffrence
            
            #resouce_name = rec.investment_fund_id and rec.investment_fund_id.fund_id and rec.investment_fund_id.fund_id.name or ''
             
            lines.append({
                'id': 'hierarchy' + str(rec.id),
                'name': rec.journal_id and rec.journal_id.name or '',
                'columns': [
                            {'name': rec.contract_id and rec.contract_id.name or ''},
                            {'name':rec.currency_id.name},
                            self._format({'name': inv_amt},figure_type='float',digit=2,is_currency=True),
                            self._format({'name': total_rate},figure_type='float',digit=precision,is_currency=False),
                            {'name': term},
                            self._format({'name': days},figure_type='float',digit=2,is_currency=True),
                            self._format({'name': rec.extra_percentage},figure_type='float',digit=precision,is_currency=False),
                            self._format({'name': extra_percentage_value},figure_type='float',digit=2,is_currency=True),
                            self._format({'name': diffrence},figure_type='float',digit=2,is_currency=True),
                            ],
                'level': 3,
                'unfoldable': False,
                'unfolded': True,
            })
            end_date = rec.invesment_date + timedelta(days=term)

            total_month = (end_date.year - rec.invesment_date.year) * 12 +  (end_date.month - rec.invesment_date.month)
             
            current_month_start_date = rec.invesment_date
             
            for month in range(total_month+1):
 
                current_month_start_date = current_month_start_date
                current_month_end_date = current_month_start_date.replace(day=1) + relativedelta(months=1) - timedelta(days=1)
                
                remove_days=0 
                if current_month_end_date > end_date:
                    current_month_end_date = end_date
                    remove_days = 1

                    
                day_diff = current_month_end_date - current_month_start_date 
                day_diff = day_diff.days + 1 - remove_days
                
                total_rate = rec.extra_percentage + rec.interest_rate
                 
                days = ((rec.actual_amount * total_rate)/100)/360*day_diff

                extra_percentage_value =  ((rec.actual_amount * rec.extra_percentage)/100)/360*day_diff
                diffrence = days - extra_percentage_value
 
                month_vals={
                'id': 'hierarchy_' + str(rec.id) + str(current_month_start_date.month),
                'name': rec.journal_id and rec.journal_id.name or '',
                'columns': [
                            {'name': rec.contract_id and rec.contract_id.name or ''},
                            {'name':rec.currency_id.name},
                            self._format({'name': inv_amt},figure_type='float',digit=2,is_currency=True),
                            self._format({'name': total_rate},figure_type='float',digit=precision,is_currency=False),
                            {'name': day_diff},
                            self._format({'name': days},figure_type='float',digit=2,is_currency=True),
                            self._format({'name': rec.extra_percentage},figure_type='float',digit=precision,is_currency=False),
                            self._format({'name': extra_percentage_value},figure_type='float',digit=2,is_currency=True),
                            self._format({'name': diffrence},figure_type='float',digit=2,is_currency=True),
                            ],
                'level': 3,
                'unfoldable': False,
                'unfolded': True,
                }
                month_list.get(current_month_start_date.month,[]).append(month_vals)
                 
                current_month_start_date = current_month_start_date.replace(day=1) + relativedelta(months=1)


        for rec in line_records:
            inv_amt = 0
            pro_lines = rec.line_ids.filtered(lambda x: x.line_state == 'done' and x.date_required and x.date_required <= end)
            inv_amt += sum(a.amount for a in pro_lines.filtered(lambda x: x.line_state ==
                                                                  'done' and x.type_of_operation in ('open_bal', 'increase', 'increase_by_closing')))
            inv_amt -= sum(a.amount for a in pro_lines.filtered(lambda x: x.line_state == 'done' and x.type_of_operation in (
                'retirement', 'withdrawal', 'withdrawal_cancellation', 'withdrawal_closure')))
            
            term = 0
            if rec.is_fixed_rate:
                term = rec.term
            if rec.is_variable_rate:
                term = rec.term_variable
            
            #resouce_name = rec.investment_fund_id and rec.investment_fund_id.fund_id and rec.investment_fund_id.fund_id.name or ''
             
            lines.append({
                'id': 'hierarchy' + str(rec.id),
                'name': rec.journal_id and rec.journal_id.name or '',
                'columns': [
                            {'name': rec.contract_id and rec.contract_id.name or ''},
                            {'name':rec.currency_id.name},
                            self._format({'name': inv_amt},figure_type='float',digit=2,is_currency=True),
                            {'name': ''},
                            {'name': ''},
                            {'name': ''},
                            {'name': ''},
                            {'name': ''},
                            {'name': ''},
                            ],
                'level': 3,
                'unfoldable': False,
                'unfolded': True,
            })                

        lines.append({
            'id': 'hierarchy_total_pro',
            'name': '',
            'columns': [
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        self._format({'name': total_p_amount},figure_type='float',digit=2,is_currency=True),
                        {'name':''},
                        self._format({'name': total_extra_amount},figure_type='float',digit=2,is_currency=True),
                        self._format({'name': total_diff_amount},figure_type='float',digit=2,is_currency=True),
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
        })

        acc_total = 0
        for month in month_list:
            if month_list.get(month):
                lines.append({
                'id': 'hierarchy_month_' + str(current_month_start_date.month),
                'name': '',
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
                            ],
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
                })
                
                lines.append({
                'id': 'hierarchy_month_' + str(current_month_start_date.month),
                'name': 'INVERSION '+self.get_month_name(month),
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
                            ],
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
                })

                total_month_amount =  0
                total_month_extra =  0
                total_month_diff =  0
                
                total_len = len(month_list.get(month))
                count = 0 
                for m_dict in month_list.get(month):
                    count += 1
                    col = m_dict.get('columns')
                    a= col[5]
                    b = col[7]
                    c = col[8]
                    
                    if 'no_format_name' in a:
                        total_month_amount += a.get('no_format_name',0) 
                    elif a.get('name',0):
                        total_month_amount += a.get('name',0) 

                    if 'no_format_name' in b:
                        total_month_extra += b.get('no_format_name',0) 
                    elif b.get('name',0):
                        total_month_extra += b.get('name',0) 

                    if 'no_format_name' in c:
                        total_month_diff += c.get('no_format_name',0) 
                    elif c.get('name',0):
                        total_month_diff += c.get('name',0) 

                    lines.append(m_dict)
                    
                    if count == total_len:
                        acc_total += total_month_amount
                        
                        lines.append({
                        'id': 'hierarchy_month_total_' + str(current_month_start_date.month),
                        'name': '',
                        'columns': [
                                    {'name': ''},
                                    {'name': ''},
                                    {'name': ''},
                                    {'name': ''},
                                    {'name': ''},
                                    self._format({'name': total_month_amount},figure_type='float',digit=2,is_currency=True),
                                    {'name': ''},
                                    self._format({'name': total_month_extra},figure_type='float',digit=2,is_currency=True),
                                    self._format({'name': total_month_diff},figure_type='float',digit=2,is_currency=True),
                                    
                                    ],
                        'level': 1,
                        'unfoldable': False,
                        'unfolded': True,
                        })


        #===================== Currency Data ==========#
        period_name = [{'name': 'Moneda' if self.env.user.lang == 'es_MX' else 'Currency'}]
        for per in periods:
            period_name.append({'name': per.get('string'),'class':'number'})
        r_column = 8 - len(periods)
        if r_column > 0:
            for col in range(r_column):
                period_name.append({'name': ''})
 
        lines.append({
                'id': 'hierarchy_inst',
                'name': '',
                'columns': period_name,
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
            })
 
        currency_ids = self.env['res.currency']
        currency_ids += records.mapped('currency_id')
 
        if currency_ids:
            currencys = list(set(currency_ids.ids))
            currency_ids = self.env['res.currency'].browse(currencys)
 
        amount_total = [{'name': 'Total'}]
        total_dict = {}
        for currency in currency_ids:
            total_ins = 0
            columns = [{'name': currency.name}]
 
            for period in periods:
                date_start = datetime.strptime(str(period.get('date_from')),
                                           DEFAULT_SERVER_DATE_FORMAT).date()
                date_end = datetime.strptime(str(period.get('date_to')),
                                         DEFAULT_SERVER_DATE_FORMAT).date()
 
                records_domain_period = domain + [('currency_id','=',currency.id),('invesment_date','>=',date_start),('invesment_date','<=',date_end)]
                productive_currency_records = self.env['investment.investment'].search(records_domain_period,order='currency_id')
                amount = 0
                #amount += sum(x.amount for x in productive_currency_records.filtered(lambda x:x.type_of_operation in ('increase','increase_by_closing','open_bal')))
                #amount -= sum(x.amount for x in productive_currency_records.filtered(lambda x:x.type_of_operation in ('retirement','withdrawal_cancellation','withdrawal','withdrawal_closure')))                
                amount += sum(x.actual_amount for x in productive_currency_records)
         
                columns.append(self._format({'name': amount},figure_type='float',digit=2,is_currency=True))
                 
                if total_dict.get(period.get('string')):
                    old_amount = total_dict.get(period.get('string',0)) + amount
                    total_dict.update({period.get('string'):old_amount})
                else:
                    total_dict.update({period.get('string'):amount})
                total_ins += amount
            amount_total.append(self._format({'name': total_ins},figure_type='float',digit=2,is_currency=True))
             
            lines.append({
                'id': 'hierarchy_jr' + str(currency.id),
                'name': '',
                'columns': columns,
                'level': 3,
                'unfoldable': False,
                'unfolded': True,
            })
 
        total_name = [{'name': 'Total'}]
        for per in total_dict:
            total_name.append(self._format({'name': total_dict.get(per)},figure_type='float',digit=2,is_currency=True))
             
        r_column = 9 - len(total_name)
        if r_column > 0:
            for col in range(r_column):
                total_name.append({'name': ''})
                 
        lines.append({
                'id': 'total_name_currency',
                'name': '',
                'columns': total_name,
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
            })
                     
                
            #print("=======",month_list.get(month))
        return lines

    def _get_report_name(self):
        return _("Report Productive Accounts")
    
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
        header_title = '''UNIVERSIDAD NACIONAL AUTÓNOMA DE MÉXICO\nPATRONATO UNIVERSITARIO\nDIRECCIÓN GENERAL DE FINANZAS\nSUBDIRECCION DE FINANZAS\nREPORTE DE CUENTAS PRODUCTIVAS'''
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
            period_name = ''
            start_date = datetime.strptime(options.get('date').get('date_from'), DEFAULT_SERVER_DATE_FORMAT)
            end_date = datetime.strptime(options.get('date').get('date_to'), DEFAULT_SERVER_DATE_FORMAT)
            if start_date and end_date:
                period_name += "Del " + str(start_date.day)

                period_name += ' ' + self.get_month_name(start_date.month)
                if start_date.year != end_date.year:
                    period_name += ' ' + str(start_date.year)

                period_name += " al " + str(end_date.day) + " de " + self.get_month_name(end_date.month) + " " \
                               + str(end_date.year)
            rcontext.update({
                'css': '',
                'o': self.env.user,
                'res_company': self.env.company,
                'period_name': period_name,
                'name': 'CUENTAS PRODUCTIVAS',

            })
            header = self.env['ir.actions.report'].with_context(period_name=period_name).render_template(
                "jt_investment.external_layout_report_productive_accounts",
                values=rcontext)
            header = header.decode('utf-8') # Ensure that headers and footer are correctly encoded
            spec_paperformat_args = {'data-report-margin-top': 55, 'data-report-header-spacing': 50}
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

