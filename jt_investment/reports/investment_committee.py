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


class InvestmentCommittee(models.AbstractModel):
    _name = "jt_investment.investment.committee"
    _inherit = "account.coa.report"
    _description = "Report to the Investment Committee"

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

    filter_bank = True
    filter_currency = True

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
    def _get_filter_journals(self):
        return self.env['account.journal'].search([('company_id', 'in', self.env.user.company_ids.ids or [self.env.company.id])
        ], order="company_id, name")
        
#         return self.env['account.journal'].search([
#             ('bank_account_id.for_investments','=',True),('company_id', 'in', self.env.user.company_ids.ids or [self.env.company.id])
#         ], order="company_id, name")
        
    @api.model
    def _get_filter_bank(self):
        #bank_acc_ids = self.env['res.partner.bank'].search([('for_investments','=',True)])
        bank_acc_ids = self.env['res.partner.bank'].search([])
        return bank_acc_ids.mapped('bank_id')
        

    @api.model
    def _init_filter_bank(self, options, previous_options=None):
        if self.filter_bank is None:
            return
        if previous_options and previous_options.get('bank'):
            journal_map = dict((opt['id'], opt['selected']) for opt in previous_options['bank'] if opt['id'] != 'divider' and 'selected' in opt)
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

    

    def _get_reports_buttons(self):
        return [
            {'name': _('Export to PDF'), 'sequence': 1, 'action': 'print_pdf', 'file_export_type': _('PDF')},
            {'name': _('Export (XLSX)'), 'sequence': 2, 'action': 'print_xlsx', 'file_export_type': _('XLSX')},
        ]

    def _get_templates(self):
        templates = super(
            InvestmentCommittee, self)._get_templates()
        templates[
            'main_table_header_template'] = 'account_reports.main_table_header'
        templates['main_template'] = 'account_reports.main_template'
        return templates

    def _get_columns_name(self, options):
        return [
            {'name': _('Concepto')},
            {'name': _('Banco')},
            {'name':_('moneda')},
            {'name': _('Importe')},
            {'name': _('Tipo')},
            {'name': _('Fondo')},
            {'name': _('Tasa de rendimiento')},
            {'name': _('Tasa Rendimiento')},
            {'name': _('Procentual extra')},
            {'name': _('Destino Rendimiento')},
        ]

    def _format(self, value,figure_type,digit,is_currency):
        if self.env.context.get('no_format'):
            return value
        value['no_format_name'] = value['name']
        if is_currency:
            currency_id = self.env.company.currency_id
        else:
            currency_id = False
        if figure_type == 'float':
            
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
        currency_list = []
        contract_list = []
        bank_list = []
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
            cetes_domain=[('state','=','confirmed')]
            udibonos_domain = [('state','=','confirmed')]
            bonds_domain = [('state','=','confirmed')]
            will_pay_domain = [('state','=','confirmed')]
            sale_domain = [('state','=','confirmed')]
            productive_domain = [('state','=','confirmed')]
            line_productive_domain = [('investment_id.state','=','confirmed')]
        else:
            cetes_domain=[('state','not in',('rejected','canceled'))]
            udibonos_domain = [('state','not in',('rejected','canceled'))]
            bonds_domain = [('state','not in',('rejected','canceled'))]
            will_pay_domain = [('state','not in',('rejected','canceled'))]
            sale_domain = [('state','not in',('rejected','canceled'))]
            productive_domain = [('state','not in',('rejected','canceled'))]
            line_productive_domain = [('investment_id.state','not in',('rejected','canceled'))]

        for bank in options.get('bank'):
            if bank.get('selected',False)==True:
                bank_list.append(bank.get('id',0))

        if bank_list:
            cetes_domain += [('bank_id','in',bank_list)]
            udibonos_domain += [('bank_id','in',bank_list)]
            bonds_domain += [('bank_id','in',bank_list)]
            will_pay_domain += [('bank_id','in',bank_list)]
            sale_domain += [('journal_id.bank_id','in',bank_list)]
            productive_domain += [('journal_id.bank_id','in',bank_list)]
            line_productive_domain += [('investment_id.journal_id.bank_id','in',bank_list)]
        

        for select_curreny in options.get('currency'):
            if select_curreny.get('selected',False)==True:
                currency_list.append(select_curreny.get('id',0))

        if currency_list:
            cetes_domain += [('currency_id','in',currency_list)]
            udibonos_domain += [('currency_id','in',currency_list)]
            bonds_domain += [('currency_id','in',currency_list)]
            will_pay_domain += [('currency_id','in',currency_list)]
            sale_domain += [('currency_id','in',currency_list)]
            productive_domain += [('currency_id','in',currency_list)]
            line_productive_domain += [('investment_id.currency_id','in',currency_list)]

        for journal in options.get('journals'):
            if journal.get('selected',False)==True:
                journal_list.append(journal.get('id',0))

        if journal_list:
            cetes_domain += [('new_journal_id','in',journal_list)]
            udibonos_domain += [('new_journal_id','in',journal_list)]
            bonds_domain += [('new_journal_id','in',journal_list)]
            will_pay_domain += [('new_journal_id','in',journal_list)]
            sale_domain += [('new_journal_id','in',journal_list)]
            productive_domain += [('new_journal_id','in',journal_list)]
            line_productive_domain += [('investment_id.new_journal_id','in',journal_list)]
        

        start = datetime.strptime(
            str(options['date'].get('date_from')), '%Y-%m-%d').date()
        end = datetime.strptime(
            options['date'].get('date_to'), '%Y-%m-%d').date()

        cetes_domain_1 =cetes_domain + [('date_time','>=',start),('date_time','<=',end)]
        udibonos_domain_1 = udibonos_domain + [('date_time','>=',start),('date_time','<=',end)]
        bonds_domain_1 =bonds_domain + [('date_time','>=',start),('date_time','<=',end)]
        will_pay_domain_1 =will_pay_domain + [('date_time','>=',start),('date_time','<=',end)]
        sale_domain_1 =sale_domain + [('invesment_date','>=',start),('invesment_date','<=',end)]
        productive_domain_1 =productive_domain + [('invesment_date','>=',start),('invesment_date','<=',end)]
        line_productive_domain_1 =line_productive_domain + [('date_required','>=',start),('date_required','<=',end)]
        
        cetes_records = self.env['investment.cetes'].search(cetes_domain_1,order='currency_id')
        udibonos_records = self.env['investment.udibonos'].search(udibonos_domain_1,order='currency_id')
        bonds_records = self.env['investment.bonds'].search(bonds_domain_1,order='currency_id')
        will_pay_records = self.env['investment.will.pay'].search(will_pay_domain_1,order='currency_id')
        sale_security_ids = self.env['purchase.sale.security'].search(sale_domain_1,order='currency_id')
        productive_ids = self.env['investment.investment'].search(productive_domain_1,order='currency_id')
        line_productive_ids = self.env['investment.operation'].search(line_productive_domain_1)

        line_productive_ids = line_productive_ids.mapped('investment_id')
        productive_ids += line_productive_ids
        if productive_ids:
            productive_ids = list(set(productive_ids.ids))
            productive_ids = self.env['investment.investment'].browse(productive_ids)
  
        #line_productive_ids = line_productive_ids - productive_ids
        line_productive_ids = []        
        lines.append({
            'id': 'hierarchy_account_main',
            'name': 'Cuentas productivas',
            'columns': [{'name': ''}, 
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
        })

        total_amount = 0

        #===== Investment =======#        
        for account in productive_ids:

            inv_amt = 0
            pro_lines = account.line_ids.filtered(lambda x: x.line_state == 'done' and x.date_required and x.date_required <= end)
            inv_amt += sum(a.amount for a in pro_lines.filtered(lambda x: x.line_state ==
                                                                  'done' and x.type_of_operation in ('open_bal', 'increase', 'increase_by_closing')))
            inv_amt -= sum(a.amount for a in pro_lines.filtered(lambda x: x.line_state == 'done' and x.type_of_operation in (
                'retirement', 'withdrawal', 'withdrawal_cancellation', 'withdrawal_closure')))
            
            total_amount += inv_amt
            precision = self.env['decimal.precision'].precision_get('Productive Accounts')
            fund_id = False
            if account.line_ids:
                fund_id = account.line_ids.mapped('investment_fund_id')
            lines.append({
                'id': 'hierarchy_account' + str(account.id),
                'name' : '', 
                'columns': [
                            {'name':  account.journal_id and account.journal_id.bank_id and account.journal_id.bank_id.name or ''},
                            {'name':account.currency_id.name},
                            self._format({'name': inv_amt},figure_type='float',digit=2,is_currency=True),
                            {'name': 'Cuentas productivas'},
                            {'name': fund_id and fund_id[0].fund_id and fund_id[0].fund_id.name or ''},
                            {'name': account.rate_of_returns and account.rate_of_returns.name or ''},
                            self._format({'name': account.interest_rate},figure_type='float',digit=precision,is_currency=False),
                            self._format({'name': account.extra_percentage},figure_type='float',digit=precision,is_currency=False),
                            {'name': account.yield_id and account.yield_id.name or ''},
                            ],
                'level': 3,
                'unfoldable': False,
                'unfolded': True,
            })
        #==========line data==========#
        for account in line_productive_ids:

            inv_amt = 0
            pro_lines = account.line_ids.filtered(lambda x: x.line_state == 'done' and x.date_required and x.date_required <= end)
            inv_amt += sum(a.amount for a in pro_lines.filtered(lambda x: x.line_state ==
                                                                  'done' and x.type_of_operation in ('open_bal', 'increase', 'increase_by_closing')))
            inv_amt -= sum(a.amount for a in pro_lines.filtered(lambda x: x.line_state == 'done' and x.type_of_operation in (
                'retirement', 'withdrawal', 'withdrawal_cancellation', 'withdrawal_closure')))
            fund_id = False
            if account.line_ids:
                fund_id = account.line_ids.mapped('investment_fund_id')
            
            total_amount += inv_amt
            lines.append({
                'id': 'hierarchy_account' + str(account.id),
                'name' : '', 
                'columns': [
                            {'name':  account.journal_id and account.journal_id.bank_id and account.journal_id.bank_id.name or ''},
                            {'name':account.currency_id.name},
                            self._format({'name': inv_amt},figure_type='float',digit=2,is_currency=True),
                            {'name': 'Cuentas productivas'},
                            {'name': fund_id and fund_id[0].fund_id and fund_id[0].fund_id.name or ''},
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
            'id': 'hierarchy_account_productivas_total',
            'name': 'Total',
            'columns': [
                        {'name':''}, 
                        {'name': ''},
                        self._format({'name': total_amount},figure_type='float',digit=2,is_currency=True),
                        {'name': ''},
                        {'name': ''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
        })

        #=====================Investment Currency Data ==========#
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
        currency_ids += productive_ids.mapped('currency_id')

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

                productive_records_domain = productive_domain + [('currency_id','=',currency.id),('invesment_date','>=',date_start),('invesment_date','<=',date_end)]
                productive_currency = self.env['investment.investment'].search(productive_records_domain,order='currency_id')
            
                amount = 0
                for p_acc in productive_currency:
                    pro_lines = p_acc.line_ids.filtered(lambda x: x.line_state == 'done' and x.date_required and x.date_required <= date_end)
                    amount += sum(a.amount for a in pro_lines.filtered(lambda x: x.line_state ==
                                                                          'done' and x.type_of_operation in ('open_bal', 'increase', 'increase_by_closing')))
                    amount -= sum(a.amount for a in pro_lines.filtered(lambda x: x.line_state == 'done' and x.type_of_operation in (
                        'retirement', 'withdrawal', 'withdrawal_cancellation', 'withdrawal_closure')))
                    
                #amount += sum(x.actual_amount for x in productive_currency)
        
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

        lines.append({
            'id': 'hierarchy_cetes_main',
            'name': 'CETES',
            'columns': [{'name': ''}, 
                        {'name': ''}, 
                        {'name': ''},
                        {'name': ''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
        })

        cetes_total_amount = 0
        #==== CETES========#        
        for cetes in cetes_records:
            cetes_total_amount += cetes.nominal_value
            precision = self.env['decimal.precision'].precision_get('CETES')
            lines.append({
                'id': 'hierarchy_cetes' + str(cetes.id),
                'name' : '', 
                'columns': [ 
                             
                            {'name':  cetes.bank_id and cetes.bank_id.name or ''},
                            {'name':cetes.currency_id.name},
                            self._format({'name': cetes.nominal_value},figure_type='float',digit=2,is_currency=True),
                            {'name': 'CETES'},
                            {'name': cetes.fund_id and cetes.fund_id.name or ''},
                            {'name': cetes.rate_of_returns and cetes.rate_of_returns.name or ''},
                            self._format({'name': cetes.yield_rate},figure_type='float',digit=precision,is_currency=False),
                            {'name':''},
                            {'name': cetes.yield_id and cetes.yield_id.name or ''},
                            ],
                'level': 3,
                'unfoldable': False,
                'unfolded': True,
            })

        lines.append({
            'id': 'hierarchy_cetes_total',
            'name': 'Total',
            'columns': [
                        {'name':''}, 
                        {'name': ''},
                        self._format({'name': cetes_total_amount},figure_type='float',digit=2,is_currency=True),
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name':''},
                        {'name':''},
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
        })


        #=====================CETES Currency Data ==========#
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
        currency_ids += cetes_records.mapped('currency_id')

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

                cetes_records_domain =cetes_domain + [('currency_id','=',currency.id),('date_time','>=',date_start),('date_time','<=',date_end)]
                cetes_currency = self.env['investment.cetes'].search(cetes_records_domain,order='currency_id')
            
                amount = 0
                amount += sum(x.nominal_value for x in cetes_currency)
        
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

        lines.append({
            'id': 'hierarchy_udibonos_main',
            'name': 'UDIBONOS',
            'columns': [{'name': ''}, 
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
        })

        udibonos_total_amount = 0
        #==== udibonos========#
        for udibonos in udibonos_records:
            udibonos_total_amount += udibonos.nominal_value
            precision = self.env['decimal.precision'].precision_get('UDIBONOS')
            
            lines.append({
                'id': 'hierarchy_udibonos' + str(udibonos.id),
                'name': '',
                'columns': [ 
                             
                            {'name':udibonos.bank_id and udibonos.bank_id.name or ''},
                            {'name':udibonos.currency_id.name},
                            self._format({'name': udibonos.nominal_value},figure_type='float',digit=2,is_currency=True),
                            {'name': 'UDIBONOS'},
                            {'name': udibonos.fund_id and udibonos.fund_id.name or ''},
                            {'name': udibonos.rate_of_returns and udibonos.rate_of_returns.name or ''},
                            self._format({'name': udibonos.interest_rate},figure_type='float',digit=precision,is_currency=False),
                            {'name':''},
                            {'name': udibonos.yield_id and udibonos.yield_id.name or ''},
                            ],
                'level': 3,
                'unfoldable': False,
                'unfolded': True,
            })


        lines.append({
            'id': 'hierarchy_udibonos_total',
            'name': 'Total',
            'columns': [
                         
                        {'name': ''},
                        {'name':''},
                        self._format({'name': udibonos_total_amount},figure_type='float',digit=2,is_currency=True),
                        {'name': ''},
                        {'name': ''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
        })


        #=====================Udibonos Currency Data ==========#
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
        currency_ids += udibonos_records.mapped('currency_id')

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

                udibonos_records_domain = udibonos_domain + [('currency_id','=',currency.id),('date_time','>=',date_start),('date_time','<=',date_end)]
                udibonos_currency = self.env['investment.udibonos'].search(udibonos_records_domain,order='currency_id')
            
                amount = 0
                amount += sum(x.nominal_value for x in udibonos_currency)
        
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

        lines.append({
            'id': 'hierarchy_bonds_main',
            'name': 'BONOS',
            'columns': [{'name': ''}, 
                        {'name': ''}, 
                        {'name': ''},
                        {'name': ''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
        })

        bonds_total_amount = 0
        #==== bonds========#
        for bonds in bonds_records:
            bonds_total_amount += bonds.nominal_value
            precision = self.env['decimal.precision'].precision_get('BONDS')
            lines.append({
                'id': 'hierarchy_bonds' + str(bonds.id),
                'name': '',
                'columns': [ 
                             
                            {'name': bonds.bank_id and bonds.bank_id.name or ''},
                            {'name':bonds.currency_id.name},
                            self._format({'name': bonds.nominal_value},figure_type='float',digit=2,is_currency=True),
                            {'name': 'BONOS'},
                            {'name': bonds.fund_id and bonds.fund_id.name or ''},
                            {'name': bonds.rate_of_returns and bonds.rate_of_returns.name or ''},
                            self._format({'name': bonds.interest_rate},figure_type='float',digit=precision,is_currency=False),
                            {'name':''},
                           {'name': bonds.yield_id and bonds.yield_id.name or ''},
                            ],
                'level': 3,
                'unfoldable': False,
                'unfolded': True,
            })

        lines.append({
            'id': 'hierarchy_bonds_total',
            'name': 'Total',
            'columns': [
                        {'name': ''},
                        {'name':''},
                        self._format({'name': bonds_total_amount},figure_type='float',digit=2,is_currency=True),
                        {'name': ''},
                        {'name': ''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
        })

        #=====================bonds Currency Data ==========#
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
        currency_ids += bonds_records.mapped('currency_id')

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

                bonds_records_domain =bonds_domain + [('currency_id','=',currency.id),('date_time','>=',date_start),('date_time','<=',date_end)]
                bonds_currency = self.env['investment.bonds'].search(bonds_records_domain,order='currency_id')
            
                amount = 0
                amount += sum(x.nominal_value for x in bonds_currency)
        
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


        lines.append({
            'id': 'hierarchy_pay_main',
            'name': 'Pagaré',
            'columns': [{'name': ''}, 
                        {'name': ''}, 
                        {'name': ''},
                        {'name': ''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
        })

        pay_total_amount = 0
        #==== I will pay========#
        for pay in will_pay_records:
            pay_total_amount += pay.amount
            precision = self.env['decimal.precision'].precision_get('REPAY')
            lines.append({
                'id': 'hierarchy_pay' + str(pay.id),
                'name': '',
                'columns': [
                             
                            {'name': pay.bank_id and pay.bank_id.name or ''},
                            {'name':pay.currency_id.name},
                            self._format({'name': pay.amount},figure_type='float',digit=2,is_currency=True),
                            {'name': 'Pagaré'},
                            {'name': pay.fund_id and pay.fund_id.name or ''},
                            {'name': pay.rate_of_returns and pay.rate_of_returns.name or ''},
                            self._format({'name': pay.interest_rate},figure_type='float',digit=precision,is_currency=False),
                            {'name':''},
                            {'name': pay.yield_id and pay.yield_id.name or ''},
                            ],
                'level': 3,
                'unfoldable': False,
                'unfolded': True,
            })

        lines.append({
            'id': 'hierarchy_pay_total',
            'name': 'Total',
            'columns': [
                        {'name': ''},
                        {'name':''},
                        self._format({'name': pay_total_amount},figure_type='float',digit=2,is_currency=True),
                        {'name': ''},
                        {'name': ''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
        })

        #=====================pay Currency Data ==========#
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
        currency_ids += will_pay_records.mapped('currency_id')

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

                pay_records_domain =will_pay_domain + [('currency_id','=',currency.id),('date_time','>=',date_start),('date_time','<=',date_end)]
                pay_currency = self.env['investment.will.pay'].search(pay_records_domain,order='currency_id')
    
                amount = 0
                amount += sum(x.amount for x in pay_currency)
        
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

#         lines.append({
#             'id': 'hierarchy_funds',
#             'name': 'Funds',
#             'columns': [{'name': ''}, 
#                         {'name': ''}, 
#                         {'name': ''},
#                         {'name': ''},
#                         {'name': ''},
#                         {'name': ''},
#                         ],
#             'level': 1,
#             'unfoldable': False,
#             'unfolded': True,
#         })

        lines.append({
            'id': 'hierarchy_sale_main',
            'name': 'Títulos',
            'columns': [{'name': ''}, 
                        {'name': ''}, 
                        {'name': ''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
        })
        
        sale_total_amount = 0
        #==== Sale Security========#
        for sale in sale_security_ids:
            if sale.movement and sale.movement=='buy':
                sale_total_amount += sale.amount
            if sale.movement and sale.movement=='sell':
                sale_total_amount -= sale.amount

            lines.append({
                'id': 'hierarchy_sale' + str(sale.id),
                'name': '',
                'columns': [  
                             
                            {'name': sale.journal_id and sale.journal_id.bank_id and sale.journal_id.bank_id.name or ''},
                            {'name':sale.currency_id.name},
                            self._format({'name': sale.amount},figure_type='float',digit=2,is_currency=True),
                            {'name': 'Títulos'},
                            {'name': sale.fund_id and sale.fund_id.name or ''},
                            {'name': sale.rate_of_returns and sale.rate_of_returns.name or ''},
                            self._format({'name': sale.price},figure_type='float',digit=4,is_currency=False),
                            {'name':''},
                            {'name': sale.yield_id and sale.yield_id.name or ''},
                            ],
                'level': 3,
                'unfoldable': False,
                'unfolded': True,
            })

        lines.append({
            'id': 'hierarchy_sale_total',
            'name': 'Total',
            'columns': [
                        {'name':''}, 
                        {'name': ''},
                        self._format({'name': sale_total_amount},figure_type='float',digit=2,is_currency=True),
                        {'name': ''},
                        {'name': ''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
        })

        #=====================Security Currency Data ==========#
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
        currency_ids += sale_security_ids.mapped('currency_id')

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

                sale_records_domain = sale_domain + [('currency_id','=',currency.id),('invesment_date','>=',date_start),('invesment_date','<=',date_end)]
                sale_currency = self.env['purchase.sale.security'].search(sale_records_domain,order='currency_id')
                
                amount = 0
                for x in sale_currency:
                    if x.movement and x.movement=='buy':
                        amount += x.amount
                    if x.movement and x.movement=='sell':
                        amount -= x.amount
                #amount += sum(x.amount for x in sale_currency)
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
                    
        return lines

    def _get_report_name(self):
        return _("Report to the Investment Committee")
    
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
        header_title = '''UNIVERSIDAD NACIONAL AUTÓNOMA DE MÉXICO\nPATRONATO UNIVERSITARIO\nDIRECCIÓN GENERAL DE FINANZAS\nSUBDIRECCION DE FINANZAS\nREPORTE PARA EL COMITÉ DE INVERSIONES'''
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
            'extra_data': False
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
                'period_name': period_name
            })
            header = self.env['ir.actions.report'].with_context(period_name=period_name).render_template(
                "jt_investment.external_layout_investment_committee",
                values=rcontext)
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
