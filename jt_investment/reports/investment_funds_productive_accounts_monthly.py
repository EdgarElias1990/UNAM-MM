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
from datetime import datetime ,timedelta,date
import json

class InvestmentFundsinProductiveAccountsMonthly(models.AbstractModel):
    _name = "jt_investment.investment.funds.productive.monthly.accounts"
    _inherit = "account.coa.report"
    _description = "Report of Investment Funds in Monthly Productive Accounts"

    filter_date = {'mode': 'range', 'filter': 'this_month'}
    filter_comparison = {'date_from': '', 'date_to': '', 'filter': 'no_comparison', 'number_period': 1}
    filter_all_entries = True
    filter_bank = True
    filter_journals = None
    filter_analytic = None
    filter_unfold_all = None
    filter_cash_basis = None
    filter_hierarchy = None
    filter_unposted_in_period = None
    MAX_LINES = None
    filter_funds = True


    @api.model
    def _get_filter_bank(self):
        return self.env['res.bank'].search([])

    @api.model
    def _init_filter_bank(self, options, previous_options=None):
        if self.filter_bank is None:
            return
        if previous_options and previous_options.get('bank'):
            journal_map = dict((opt['id'], opt['selected']) for opt in previous_options[
                               'bank'] if opt['id'] != 'divider' and 'selected' in opt)
        else:
            journal_map = {}
        options['bank'] = []

        default_group_ids = []

        for j in self._get_filter_bank():
            options['bank'].append({
                'id': j.id,
                'name': j.name,
                'code': j.name,
                'selected': journal_map.get(j.id, j.id in default_group_ids),
            })

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

    # Set columns based on dynamic options
    def print_xlsx(self, options,test):
        return {
                'type': 'ir_actions_account_report_download',
                'data': {'model': self.env.context.get('model'),
                         'options': json.dumps(options),
                         'output_format': 'xlsx',
                         'financial_id': self.env.context.get('id'),
                         }
                }

    def _get_reports_buttons(self):
        return [
            {'name': _('Export (XLSX)'), 'sequence': 2, 'action': 'print_xlsx', 'file_export_type': _('XLSX')},
        ]

    def _get_templates(self):
        templates = super(
            InvestmentFundsinProductiveAccountsMonthly, self)._get_templates()
        templates[
            'main_table_header_template'] = 'account_reports.main_table_header'
        templates['main_template'] = 'account_reports.main_template'
        return templates
    
    def get_total_fund_data(self,options):

        lines = []
        fund_list = []
        bank_list = []        
        domain =[]

        comparison = options.get('comparison')
        periods = []
        if comparison and comparison.get('filter') != 'no_comparison':
            period_list = comparison.get('periods')
            period_list.reverse()
            periods = [period for period in period_list]
        periods.append(options.get('date'))

        for bank in options.get('bank'):
            if bank.get('selected',False)==True:
                bank_list.append(bank.get('id',0))

        if not bank_list:
            bank_ids = self._get_filter_bank()
            bank_list = bank_ids.ids
        
        if not bank_list:
            bank_list = [0]

        if bank_list :
            domain.append(('journal_id.bank_id','in',bank_list))

        for fund in options.get('funds'):
            if fund.get('selected',False)==True:
                fund_list.append(fund.get('id',0))
        
        
        if fund_list:
            domain.append(('investment_fund_id.fund_id','in',fund_list))
            
        if options.get('all_entries') is False:
            domain+=[('line_state','in',('confirmed','done'))]
        else:
            domain+=[('line_state','not in',('rejected','canceled'))]
            
        start = datetime.strptime(
            str(options['date'].get('date_from')), '%Y-%m-%d').date()
        end = datetime.strptime(
            options['date'].get('date_to'), '%Y-%m-%d').date()
        
        previous_domain = domain + [('date_required','<',start)]
        
        main_domain = domain + [('date_required','>=',start),('date_required','<=',end)]
        records = self.env['investment.operation'].search(main_domain)

        origin_ids = self.env['agreement.fund']
        origin_ids += records.mapped('investment_fund_id.fund_id')        

        if origin_ids:
            origins = list(set(origin_ids.ids))
            origin_ids = self.env['agreement.fund'].browse(origins)
        
        return len(origin_ids),origin_ids
    
    def _get_columns_name(self, options):
        list_column = [
            {'name': _('Dias')},
            {'name': _('Mes')},
            {'name': _('Fecha')},
            {'name': _('Bank')},
            {'name': _('TIIE 28')},
            {'name': _('Capital')},
            {'name': _('Entradas')},
            ]
        origin_ids_len,origin_ids = self.get_total_fund_data(options)
        for fund in origin_ids:
            list_column.append({'name':fund.name})
            
        
        list_column += [{'name': _('Salidas')},
            {'name': _('Saldo Final')},
            {'name': _('Promedio Diario')},
        ]
        
        return list_column
    
#         return [
#             {'name': _('Dias')},
#             {'name': _('Mes')},
#             {'name': _('Fecha')},
#             {'name': _('Bank')},
#             {'name': _('TIIE 28')},
#             {'name': _('Capital')},
#             {'name': _('Entradas')},
#             {'name':_('Fondos Ligados a Convenios')},
#             {'name':_('Fondos de Recursos Patrimoniales')},
#             {'name':_('Fondo Institucional de Fortalecimiento')},
#             {'name':_('Fondo de Mantenimiento Mayor')},
#             {'name': _('Salidas')},
#             {'name': _('Saldo Final')},
#             {'name': _('Promedio Diario')},
#         ]

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

    def get_fund_amount(self,origin,bank,domain,date_start,date_end):
        domain_fund = domain + [('date_required','>=',date_start),('date_required','<=',date_end)]
        records_fund = self.env['investment.operation'].search(domain_fund)

        inc_domain_fund = domain + [('date_required','<',date_start)]
        inc_records_fund = self.env['investment.operation'].search(inc_domain_fund)

        amount = 0
        amount += sum(x.amount for x in inc_records_fund.filtered(lambda x:x.type_of_operation in ('increase','increase_by_closing','open_bal') and x.investment_fund_id.fund_id.id==origin.id and x.investment_id.journal_id.id==bank.id))
        amount -= sum(x.amount for x in inc_records_fund.filtered(lambda x:x.type_of_operation in ('retirement','withdrawal_cancellation','withdrawal','withdrawal_closure') and x.investment_fund_id.fund_id.id==origin.id and x.investment_id.journal_id.id==bank.id))
        
    
        amount += sum(x.amount for x in records_fund.filtered(lambda x:x.type_of_operation in ('increase','increase_by_closing','open_bal') and x.investment_fund_id.fund_id.id==origin.id and x.investment_id.journal_id.id==bank.id))
        amount -= sum(x.amount for x in records_fund.filtered(lambda x:x.type_of_operation in ('retirement','withdrawal_cancellation','withdrawal','withdrawal_closure') and x.investment_fund_id.fund_id.id==origin.id and x.investment_id.journal_id.id==bank.id))

        return amount
            
    def _get_lines(self, options, line_id=None):
        lines = []
        fund_list = []
        bank_list = []        
        domain =[]
        comparison = options.get('comparison')
        periods = []
        if comparison and comparison.get('filter') != 'no_comparison':
            period_list = comparison.get('periods')
            period_list.reverse()
            periods = [period for period in period_list]
        periods.append(options.get('date'))

        for bank in options.get('bank'):
            if bank.get('selected',False)==True:
                bank_list.append(bank.get('id',0))

        if not bank_list:
            bank_ids = self._get_filter_bank()
            bank_list = bank_ids.ids
        
        if not bank_list:
            bank_list = [0]

        if bank_list :
            domain.append(('journal_id.bank_id','in',bank_list))

        for fund in options.get('funds'):
            if fund.get('selected',False)==True:
                fund_list.append(fund.get('id',0))
        
        
        if fund_list:
            domain.append(('investment_fund_id.fund_id','in',fund_list))
            
        if options.get('all_entries') is False:
            domain+=[('line_state','in',('confirmed','done'))]
        else:
            domain+=[('line_state','not in',('rejected','canceled'))]
            
        start = datetime.strptime(
            str(options['date'].get('date_from')), '%Y-%m-%d').date()
        end = datetime.strptime(
            options['date'].get('date_to'), '%Y-%m-%d').date()
        
        previous_domain = domain + [('date_required','<',start)]
        
        main_domain = domain + [('date_required','>=',start),('date_required','<=',end)]
        records = self.env['investment.operation'].search(main_domain)
        previous_records = self.env['investment.operation'].search(previous_domain)
        
        
        opt_lines = self.env['investment.operation']
        opt_lines += records.filtered(lambda x:x.type_of_operation == 'open_bal')
        opt_lines += records.filtered(lambda x:x.type_of_operation == 'increase')
        opt_lines += records.filtered(lambda x:x.type_of_operation == 'increase_by_closing')
        opt_lines += records.filtered(lambda x:x.type_of_operation == 'retirement')
        opt_lines += records.filtered(lambda x:x.type_of_operation == 'withdrawal')
        opt_lines += records.filtered(lambda x:x.type_of_operation == 'withdrawal_cancellation')
        opt_lines += records.filtered(lambda x:x.type_of_operation == 'withdrawal_closure')
         
        opt_lines.sorted('date_required')
        total_capital = 0
        final_amount = 0
        total_entradas = 0
        total_salidas  = 0
        
        origin_ids_len,origin_ids_data = self.get_total_fund_data(options)
        bank_account_ids = opt_lines.mapped('investment_id.journal_id')
        bank_account_ids += previous_records.mapped('investment_id.journal_id')
        bank_account_ids = self.env['account.journal'].search([('id','in',bank_account_ids.ids)])
        for bank in bank_account_ids:
            total_avg_final = 0
            record_date_day = 1
            total_capital = 0
            final_amount = 0
            total_entradas = 0
            total_salidas  = 0
            columns = [{'name': ''}, 
                            {'name': ''},
                            {'name': ''},
                            {'name': ''},
                            {'name': ''},
                            {'name': ''},
                            {'name': ''},
                            {'name': ''},
                            {'name': ''},
                            ]
            columns += [{'name':''}]*origin_ids_len
            
            lines.append({
                'id': 'hierarchy_total',
                'name': bank.name,
                'columns': columns,
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
            })
            header_intial = 0
            for rec in previous_records.filtered(lambda x:x.investment_id.journal_id.id == bank.id):
                if rec.type_of_operation in ('increase', 'increase_by_closing', 'open_bal'):
                    header_intial += rec.amount
                elif rec.type_of_operation in ('retirement', 'withdrawal', 'withdrawal_cancellation', 'withdrawal_closure'):
                    header_intial -= rec.amount
            
            #=========== Get Previous Data ================#
            pre_line_datas = opt_lines.filtered(lambda x:x.investment_id.journal_id.id == bank.id)
#             if not pre_line_datas:
#                 columns = [{'name': ''}, 
#                                 {'name': ''},
#                                 {'name': ''},
#                                 {'name': ''},
#                                 self._format({'name': header_intial},figure_type='float',digit=2,is_currency=True),
#                                 {'name': ''},
#                             ]
#                 columns += [{'name':''}]*origin_ids_len                    
#                 columns +=  [
#                                 {'name': ''},
#                                 self._format({'name': header_intial},figure_type='float',digit=2,is_currency=True),
#                                 {'name': ''},
#                                 ]
#                 lines.append({
#                     'id': 'hierarchy',
#                     'name': '',
#                     'columns': columns,
#                     'level': 3,
#                     'unfoldable': False,
#                     'unfolded': True,
#                 })
#                 total_capital += header_intial
#                 final_amount += header_intial
#                 continue
            #========================#        
            day_diff = end - start
            day_diff = day_diff.days+1
            new_date = start
            count = 0
            total_rec_inc = 0
            for month_date in range(day_diff):
                count += 1
                total_rec_inc += 1
                month_name = self.get_month_name(new_date.month)
                p_rate = 0

                final_amount += header_intial
                total_capital += header_intial
                
                if new_date:
                    record_date_day = new_date.day
                    period_rate_id = self.env['investment.period.rate'].search([('rate_date','=',new_date),('product_type','=','TIIE')],limit=1)
                    if period_rate_id:
                        p_rate = period_rate_id.rate_days_28
                    else:
                        period_rate_id = self.env['investment.period.rate'].search([('rate_date','<',new_date),('product_type','=','TIIE')],limit=1,order='rate_date desc')
                        p_rate = period_rate_id.rate_days_28
                
                current_date_line = opt_lines.filtered(lambda x:x.investment_id.journal_id.id == bank.id and x.date_required and x.date_required==new_date).sorted('date_required')
                if not current_date_line:
                    
                    total_avg_final += final_amount
                    columns = [{'name': month_name}, 
                                    {'name': new_date.day},
                                    {'name': ''},
                                    self._format({'name': p_rate},figure_type='float',digit=4,is_currency=False),
                                    self._format({'name': final_amount},figure_type='float',digit=2,is_currency=True),
                                    self._format({'name': 0.0},figure_type='float',digit=2,is_currency=True),
                                ]
                    for r in origin_ids_data:
                        fund_amount = 0.0
#                         if r.id==rec.investment_fund_id.fund_id.id:
#                             fund_amount = self.get_fund_amount(r,domain,start,end)
                        columns += [self._format({'name': fund_amount},figure_type='float',digit=2,is_currency=True)]
                        
                    columns +=  [
                                    self._format({'name': 0.0},figure_type='float',digit=2,is_currency=True),
                                    self._format({'name': final_amount},figure_type='float',digit=2,is_currency=True),
                                    self._format({'name': total_avg_final/total_rec_inc},figure_type='float',digit=2,is_currency=True),
                                    ]
                    lines.append({
                        'id': 'hierarchy' + str(new_date),
                        'name': new_date.day,
                        'columns': columns,
                        'level': 3,
                        'unfoldable': False,
                        'unfolded': True,
                    })
                total_current_date_operation = len(current_date_line)
                total_current_date_operation_inc = 0
                    
                for rec in current_date_line:
                    total_current_date_operation_inc += 1
                    
                    capital = final_amount
                    entradas = 0
                    salidas  = 0
                    record_date_day = rec.date_required.day
                    show_amount = 0
                    show_avg = 0
                    if rec.type_of_operation == 'open_bal':
                        capital = rec.amount
                        final_amount += rec.amount
                        total_capital += rec.amount
                    if rec.type_of_operation in ('increase','increase_by_closing'):
                        entradas = rec.amount
                        total_entradas += rec.amount
                        final_amount += rec.amount
                        total_capital += rec.amount
                    if rec.type_of_operation in ('retirement','withdrawal_cancellation','withdrawal','withdrawal_closure'):
                        salidas = rec.amount
                        total_salidas += rec.amount
                        final_amount -= rec.amount
                        total_capital -= rec.amount
                    # precision = self.env['decimal.precision'].precision_get('Productive Accounts')

                    if total_current_date_operation_inc != total_current_date_operation:
                        show_avg = 0.0
                        show_amount = 0
                    else:
                        total_avg_final += final_amount
                        show_avg = total_avg_final/total_rec_inc
                        show_amount = final_amount
                    
                    columns = [{'name': month_name}, 
                                    {'name': rec.date_required.day},
                                    {'name': rec.investment_id.journal_id and rec.investment_id.journal_id.name or ''},
                                    self._format({'name': p_rate},figure_type='float',digit=4,is_currency=False),
                                    self._format({'name': capital},figure_type='float',digit=2,is_currency=True),
                                    self._format({'name': entradas},figure_type='float',digit=2,is_currency=True),
                                ]
                    for r in origin_ids_data:
                        fund_amount = 0.0
                        if r.id==rec.investment_fund_id.fund_id.id:
                            fund_amount = self.get_fund_amount(r,bank,domain,start,end)
                        columns += [self._format({'name': fund_amount},figure_type='float',digit=2,is_currency=True)]
                        
                    columns +=  [
                                    self._format({'name': salidas},figure_type='float',digit=2,is_currency=True),
                                    self._format({'name': show_amount},figure_type='float',digit=2,is_currency=True),
                                    self._format({'name': show_avg},figure_type='float',digit=2,is_currency=True),
                                    ]
                    lines.append({
                        'id': 'hierarchy' + str(rec.id),
                        'name': rec.date_required.day,
                        'columns': columns,
                        'level': 3,
                        'unfoldable': False,
                        'unfolded': True,
                    })
                new_date =  start + timedelta(days=count)
                header_intial = 0
                
            columns =[{'name': ''}, 
                            {'name': ''},
                            {'name': ''},
                            {'name': ''},
                            self._format({'name': total_capital},figure_type='float',digit=2,is_currency=True),
                            self._format({'name': total_entradas},figure_type='float',digit=2,is_currency=True),
                    ]
            columns += [{'name':''}]*origin_ids_len
            columns += [                            self._format({'name': total_salidas},figure_type='float',digit=2,is_currency=True),
                            self._format({'name': final_amount},figure_type='float',digit=2,is_currency=True),
                            {'name': ''},
                        ]
            
            lines.append({
                'id': 'hierarchy_total',
                'name': 'Total',
                'columns': columns,
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
            })
        
        #===================== Bank Data ==========#
        period_name = [{'name': ''}]
        for per in periods:
            period_name.append({'name': per.get('string'),'class':'number'})
        r_column =  7 + origin_ids_len - len(periods)
        if r_column > 0:
            for col in range(r_column):
                period_name.append({'name': ''})
                
        lines.append({
                'id': 'hierarchy_inst',
                'name': 'Institución',
                'columns': period_name,
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
                'colspan':2,
            })
        journal_ids = self.env['res.bank']
        journal_ids += records.mapped('investment_id.journal_id.bank_id')
        journal_ids += previous_records.mapped('investment_id.journal_id.bank_id')
        if journal_ids:
            journals = list(set(journal_ids.ids))
            journal_ids = self.env['res.bank'].browse(journals)
            
        
        amount_total = [{'name': 'Total'}]
        total_dict = {}
        for journal in journal_ids:
            total_ins = 0
            columns = [{'name': ''}]
            
            for period in periods:
                date_start = datetime.strptime(str(period.get('date_from')),
                                           DEFAULT_SERVER_DATE_FORMAT).date()
                date_end = datetime.strptime(str(period.get('date_to')),
                                         DEFAULT_SERVER_DATE_FORMAT).date()

                
                domain_bank_period = domain + [('investment_id.journal_id','in',bank_account_ids.ids),('date_required','>=',date_start),('date_required','<=',date_end),('investment_id.journal_id.bank_id','=',journal.id)]
                records_bank_periods = self.env['investment.operation'].search(domain_bank_period)

                inc_domain_bank_period = domain + [('investment_id.journal_id','in',bank_account_ids.ids),('date_required','<',date_start),('investment_id.journal_id.bank_id','=',journal.id)]
                inc_records_bank_periods = self.env['investment.operation'].search(inc_domain_bank_period)

                amount = 0
                amount += sum(x.amount for x in inc_records_bank_periods.filtered(lambda x:x.type_of_operation in ('increase','increase_by_closing','open_bal')))
                amount -= sum(x.amount for x in inc_records_bank_periods.filtered(lambda x:x.type_of_operation in ('retirement','withdrawal_cancellation','withdrawal','withdrawal_closure')))
                
                amount += sum(x.amount for x in records_bank_periods.filtered(lambda x:x.type_of_operation in ('increase','increase_by_closing','open_bal')))
                amount -= sum(x.amount for x in records_bank_periods.filtered(lambda x:x.type_of_operation in ('retirement','withdrawal_cancellation','withdrawal','withdrawal_closure')))
                columns.append(self._format({'name': amount},figure_type='float',digit=2,is_currency=True))
                
                if total_dict.get(period.get('string')):
                    old_amount = total_dict.get(period.get('string',0)) + amount
                    total_dict.update({period.get('string'):old_amount})
                else:
                    total_dict.update({period.get('string'):amount})
                total_ins += amount
            amount_total.append(self._format({'name': total_ins},figure_type='float',digit=2,is_currency=True))
            
            lines.append({
                'id': 'hierarchy_jr' + str(journal.id),
                'name': journal.name,
                'columns': columns,
                'level': 3,
                'unfoldable': False,
                'unfolded': True,
                'colspan':2,
            })

        total_name = [{'name': ''}]
        for per in total_dict:
            total_name.append(self._format({'name': total_dict.get(per)},figure_type='float',digit=2,is_currency=True))
            
        r_column = 8 + origin_ids_len - len(total_name)
        if r_column > 0:
            for col in range(r_column):
                total_name.append({'name': ''})
                
        lines.append({
                'id': 'total_name_bank',
                'name': 'Total',
                'columns': total_name,
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
                'colspan':2,
            })

        #================ Origin Data ====================#
        period_name = [{'name': ''}]
        for per in periods:
            period_name.append({'name': per.get('string'),'class':'number'})
        r_column = 7 + origin_ids_len - len(periods)
        if r_column > 0:
            for col in range(r_column):
                period_name.append({'name': ''})
        lines.append({
                'id': 'hierarchy_or_inst',
                'name': 'Tipo de recurso',
                'columns': period_name,
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
                'colspan':2,
            })

        # ==========================================================================
#         lines.append({
#                 'id': 'hierarchy_or_inst',
#                 'name': '',
#                 'columns': [
#                          {'name':'Fondos Ligados a Convenios'},
#                          {'name':''},
#                         ],
#                 'level': 2,
#                 'unfoldable': False,
#                 'unfolded': True,
#             })

        # ==========================================================================
#         lines.append({
#                 'id': 'hierarchy_fondos_patri',
#                 'name': '',
#                 'columns': [
#                          {'name':'Fondos de Recursos Patrimoniales'},
#                          {'name':''},
#                         ],
#                 'level': 2,
#                 'unfoldable': False,
#                 'unfolded': True,
#             })

        # # ==========================================================================
      
#         lines.append({
#                 'id': 'hierarchy_fondos_inst',
#                 'name': '',
#                 'columns': [
#                          {'name':'Fondo Institucional de Fortalecimiento'},
#                          {'name':''},
#                         ],
#                 'level': 2,
#                 'unfoldable': False,
#                 'unfolded': True,
#             })


                # ==========================================================================
#         lines.append({
#                 'id': 'hierarchy_fondos_man',
#                 'name': '',
#                 'columns': [
#                          {'name':'Fondo de Mantenimiento Mayor'},
#                          {'name':''},
#                         ],
#                 'level': 2,
#                 'unfoldable': False,
#                 'unfolded': True,
#             })

        origin_ids = self.env['agreement.fund']
        origin_ids += records.mapped('investment_fund_id.fund_id')        
        origin_ids += previous_records.mapped('investment_fund_id.fund_id')
        
        if origin_ids:
            origins = list(set(origin_ids.ids))
            origin_ids = self.env['agreement.fund'].browse(origins)

        amount_total = [{'name': 'Total'}]
        total_dict = {}
        for origin in origin_ids:
            total_ins = 0
            columns = [{'name': ''}]
            amount_total = [{'name': 'Total'}]
            for period in periods:
                date_start = datetime.strptime(str(period.get('date_from')),
                                           DEFAULT_SERVER_DATE_FORMAT).date()
                date_end = datetime.strptime(str(period.get('date_to')),
                                         DEFAULT_SERVER_DATE_FORMAT).date()


                domain_fund = domain + [('investment_id.journal_id','in',bank_account_ids.ids),('date_required','>=',date_start),('date_required','<=',date_end)]
                records_fund = self.env['investment.operation'].search(domain_fund)

                inc_domain_fund = domain + [('investment_id.journal_id','in',bank_account_ids.ids),('date_required','<',date_start)]
                inc_records_fund = self.env['investment.operation'].search(inc_domain_fund)

                amount = 0
                amount += sum(x.amount for x in inc_records_fund.filtered(lambda x:x.type_of_operation in ('increase','increase_by_closing','open_bal') and x.investment_fund_id.fund_id.id==origin.id))
                amount -= sum(x.amount for x in inc_records_fund.filtered(lambda x:x.type_of_operation in ('retirement','withdrawal_cancellation','withdrawal','withdrawal_closure') and x.investment_fund_id.fund_id.id==origin.id))
                
                amount += sum(x.amount for x in records_fund.filtered(lambda x:x.type_of_operation in ('increase','increase_by_closing','open_bal') and x.investment_fund_id.fund_id.id==origin.id))
                amount -= sum(x.amount for x in records_fund.filtered(lambda x:x.type_of_operation in ('retirement','withdrawal_cancellation','withdrawal','withdrawal_closure') and x.investment_fund_id.fund_id.id==origin.id))
                columns.append(self._format({'name': amount},figure_type='float',digit=2,is_currency=True))

                if total_dict.get(period.get('string')):
                    old_amount = total_dict.get(period.get('string',0)) + amount
                    total_dict.update({period.get('string'):old_amount})
                else:
                    total_dict.update({period.get('string'):amount})
                total_ins += amount
            amount_total.append(self._format({'name': total_ins},figure_type='float',digit=2,is_currency=True))

            #columns += [{'name':''}]*(origin_ids_len+7)
            lines.append({
                'id': 'hierarchy_or' + str(origin.id),
                'name': origin.name,
                'columns': columns,
                'level': 3,
                'unfoldable': False,
                'unfolded': True,
                'colspan':2,
            })

        total_name = [{'name': ''}]
        for per in total_dict:
            total_name.append(self._format({'name': total_dict.get(per)},figure_type='float',digit=2,is_currency=True))
            
        r_column = 8 + origin_ids_len - len(total_name)
        if r_column > 0:
            for col in range(r_column):
                total_name.append({'name': ''})
                
        lines.append({
                'id': 'total_name_bank',
                'name': 'Total',
                'columns': total_name,
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
                'colspan':2,
            })

        #===================== Currency Data ==========#
        period_name = [{'name': ''}]
        for per in periods:
            period_name.append({'name': per.get('string'),'class':'number'})
        r_column = 7 + origin_ids_len - len(periods)
        if r_column > 0:
            for col in range(r_column):
                period_name.append({'name': ''})
                
        lines.append({
                'id': 'hierarchy_inst',
                'name': 'Moneda' if self.env.user.lang == 'es_MX' else 'Currency',
                'columns': period_name,
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
                'colspan':2,
            })
        currency_ids = self.env['res.currency']
        currency_ids += records.mapped('investment_id.currency_id')
        currency_ids += previous_records.mapped('investment_id.currency_id')
                    
        if currency_ids:
            currencys = list(set(currency_ids.ids))
            currency_ids = self.env['res.currency'].browse(currencys)
            
        
        amount_total = [{'name': 'Total'}]
        total_dict = {}
        for currency in currency_ids:
            total_ins = 0
            columns = [{'name': ''}]
            
            for period in periods:
                date_start = datetime.strptime(str(period.get('date_from')),
                                           DEFAULT_SERVER_DATE_FORMAT).date()
                date_end = datetime.strptime(str(period.get('date_to')),
                                         DEFAULT_SERVER_DATE_FORMAT).date()

                domain_currency_period = domain + [('investment_id.journal_id','in',bank_account_ids.ids),('date_required','>=',date_start),('date_required','<=',date_end),('investment_id.currency_id','=',currency.id)]
                records_periods = self.env['investment.operation'].search(domain_currency_period)

                inc_domain_currency_period = domain + [('investment_id.journal_id','in',bank_account_ids.ids),('date_required','<',date_start),('investment_id.currency_id','=',currency.id)]
                inc_records_periods = self.env['investment.operation'].search(inc_domain_currency_period)

                amount = 0

                amount += sum(x.amount for x in inc_records_periods.filtered(lambda x:x.type_of_operation in ('increase','increase_by_closing','open_bal')))
                amount -= sum(x.amount for x in inc_records_periods.filtered(lambda x:x.type_of_operation in ('retirement','withdrawal_cancellation','withdrawal','withdrawal_closure')))
                
                amount += sum(x.amount for x in records_periods.filtered(lambda x:x.type_of_operation in ('increase','increase_by_closing','open_bal')))
                amount -= sum(x.amount for x in records_periods.filtered(lambda x:x.type_of_operation in ('retirement','withdrawal_cancellation','withdrawal','withdrawal_closure')))
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
                'name': currency.name,
                'columns': columns,
                'level': 3,
                'unfoldable': False,
                'unfolded': True,
                'colspan':2,
            })

        total_name = [{'name': ''}]
        for per in total_dict:
            total_name.append(self._format({'name': total_dict.get(per)},figure_type='float',digit=2,is_currency=True))
            
        r_column = 8 + origin_ids_len - len(total_name)
        if r_column > 0:
            for col in range(r_column):
                total_name.append({'name': ''})
                
        lines.append({
                'id': 'total_name_currency',
                'name': 'Total',
                'columns': total_name,
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
                'colspan':2,
            })
            
                    
        return lines

    def _get_report_name(self):
        return _("Report of Investment Funds in Productive Accounts")
    
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
        header_title = '''UNIVERSIDAD NACIONAL AUTÓNOMA DE MÉXICO\nPATRONATO UNIVERSITARIO\nDIRECCIÓN GENERAL DE FINANZAS\nSUBDIRECCION DE FINANZAS\nReporte de Fondos Institucionales en Cuentas Productivas'''
        sheet.merge_range(y_offset, col, 5, col+14, header_title,super_col_style)
        y_offset += 6
        col=1
        currect_time_msg = "Fecha y hora de impresión: "
        currect_time_msg += datetime.today().strftime('%d/%m/%Y %H:%M')
        sheet.merge_range(y_offset, col, y_offset, col+14, currect_time_msg,currect_date_style)
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
            header = self.env['ir.actions.report'].render_template("jt_investment.external_layout_investment_funds_productive_accounts", values=rcontext)
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
