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
from datetime import datetime ,timedelta,date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.misc import formatLang
from odoo.tools.misc import xlsxwriter
import io
import base64
from odoo.tools import config, date_utils, get_lang
import lxml.html
from dateutil.relativedelta import relativedelta


class IndicatorsReport(models.AbstractModel):
    _name = "jt_investment.indicators.report"
    _inherit = "account.coa.report"
    _description = "Indicators Report"

    filter_date = {'mode': 'range', 'filter': 'this_month'}
    filter_comparison = {'date_from': '', 'date_to': '', 'filter': 'no_comparison', 'number_period': 1}
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
            {'name': _('Export to PDF'), 'sequence': 1, 'action': 'print_pdf', 'file_export_type': _('PDF')},
            {'name': _('Export (XLSX)'), 'sequence': 2, 'action': 'print_xlsx', 'file_export_type': _('XLSX')},
        ]

    def _get_templates(self):
        templates = super(
            IndicatorsReport, self)._get_templates()
        templates[
            'main_table_header_template'] = 'account_reports.main_table_header'
        templates['main_template'] = 'account_reports.main_template'
        return templates

    def _get_columns_name(self, options):
        columns = [{'name': _('Indicadores')}]
        if options.get('comparison') and options['comparison'].get('periods'):
            comparison = options.get('comparison')
            period_list = comparison.get('periods')
            period_list.reverse()
            columns += [
                        {'name': _('Inicio Mes')},
                        {'name': _('Fin Mes')},
                        {'name': _('Dia')},
                        {'name': _('Alto Mes')},
                        {'name': _('Dia')},
                        {'name': _('Bajo Mes')},
                        {'name': _('Promedio')},
                       ] * (len(period_list) + 1)
        else:
        
            columns =  [
                {'name': _('Indicadores')},
                {'name': _('Inicio Mes')},
                {'name': _('Fin Mes')},
                {'name': _('Dia')},
                {'name': _('Alto Mes')},
                {'name': _('Dia')},
                {'name': _('Bajo Mes')},
                {'name': _('Promedio')},
            ]
        return columns
    
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
            value['name'] = formatLang(self.env, value['name'], currency_obj=currency_id,digits=4)
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

        comparison = options.get('comparison')
        periods = []
        if comparison and comparison.get('filter') != 'no_comparison':
            period_list = comparison.get('periods')
            period_list.reverse()
            periods = [period for period in period_list]
        periods.append(options.get('date'))
        
        start = datetime.strptime(
            str(options['date'].get('date_from')), '%Y-%m-%d').date()
        end = datetime.strptime(
            options['date'].get('date_to'), '%Y-%m-%d').date()


        
        #==================== CETES Rate ======================#
        CETES_columns_28 = []
        CETES_columns_91 = []
        CETES_columns_182 = []
        CETES_columns_364 = []
        for period in periods:
            date_start = datetime.strptime(str(period.get('date_from')),
                                           DEFAULT_SERVER_DATE_FORMAT).date()
            date_end = datetime.strptime(str(period.get('date_to')),
                                         DEFAULT_SERVER_DATE_FORMAT).date()
            
            cetes_rate = self.env['investment.period.rate'].search([('rate_date','>=',date_start),
                                                        ('rate_date','<=',date_end),('product_type','=','CETES')])
            if cetes_rate:
                start_month_date = min(x.rate_date for x in cetes_rate)
                end_month_date = max(x.rate_date for x in cetes_rate)
                start_month_rec = max(x for x in cetes_rate.filtered(lambda x:x.rate_date==start_month_date))
                end_month_rec = max(x for x in cetes_rate.filtered(lambda x:x.rate_date==end_month_date))
                
                max_high_rate_28 = max(x.rate_days_28 for x in cetes_rate)
                min_high_rate_28 = min(x.rate_days_28 for x in cetes_rate)
                max_rate_28_rec = max(x for x in cetes_rate.filtered(lambda x:x.rate_days_28==max_high_rate_28))
                min_rate_28_rec = max(x for x in cetes_rate.filtered(lambda x:x.rate_days_28==min_high_rate_28))
                total_rate = sum(x.rate_days_28 for x in cetes_rate)           
                total_rec = len(cetes_rate)
                avg = total_rate/total_rec
                 
                CETES_columns_28 += [self._format({'name': start_month_rec.rate_days_28},figure_type='float'),
                                self._format({'name': end_month_rec.rate_days_28},figure_type='float'),
                                {'name': max_rate_28_rec.rate_date},
                                self._format({'name': max_rate_28_rec.rate_days_28},figure_type='float'),
                                {'name': min_rate_28_rec.rate_date},
                                self._format({'name': min_rate_28_rec.rate_days_28},figure_type='float'),
                                self._format({'name': avg},figure_type='float'),
                                ]
                 
                max_high_rate_91 = max(x.rate_days_91 for x in cetes_rate)
                min_high_rate_91 = min(x.rate_days_91 for x in cetes_rate)
                max_rate_91_rec = max(x for x in cetes_rate.filtered(lambda x:x.rate_days_91==max_high_rate_91))
                min_rate_91_rec = max(x for x in cetes_rate.filtered(lambda x:x.rate_days_91==min_high_rate_91))
                total_rate = sum(x.rate_days_91 for x in cetes_rate)           
                total_rec = len(cetes_rate)
                avg = total_rate/total_rec
    
                CETES_columns_91 += [self._format({'name': start_month_rec.rate_days_91},figure_type='float'),
                                self._format({'name': end_month_rec.rate_days_91},figure_type='float'),
                                {'name': max_rate_91_rec.rate_date},
                                self._format({'name': max_rate_91_rec.rate_days_91},figure_type='float'),
                                {'name': min_rate_91_rec.rate_date},
                                self._format({'name': min_rate_91_rec.rate_days_91},figure_type='float'),
                                self._format({'name': avg},figure_type='float'),
                                ]
                
                max_high_rate_182 = max(x.rate_days_182 for x in cetes_rate)
                min_high_rate_182 = min(x.rate_days_182 for x in cetes_rate)
                max_rate_182_rec = max(x for x in cetes_rate.filtered(lambda x:x.rate_days_182==max_high_rate_182))
                min_rate_182_rec = max(x for x in cetes_rate.filtered(lambda x:x.rate_days_182==min_high_rate_182))
                total_rate = sum(x.rate_days_182 for x in cetes_rate)           
                total_rec = len(cetes_rate)
                avg = total_rate/total_rec
                
                CETES_columns_182 += [self._format({'name': start_month_rec.rate_days_182},figure_type='float'),
                                self._format({'name': end_month_rec.rate_days_182},figure_type='float'),
                                {'name': max_rate_182_rec.rate_date},
                                self._format({'name': max_rate_182_rec.rate_days_182},figure_type='float'),
                                {'name': min_rate_182_rec.rate_date},
                                self._format({'name': min_rate_182_rec.rate_days_182},figure_type='float'),
                                self._format({'name': avg},figure_type='float'),
                                ] 
                    
                max_high_rate_364 = max(x.rate_days_364 for x in cetes_rate)
                min_high_rate_364 = min(x.rate_days_364 for x in cetes_rate)
                max_rate_364_rec = max(x for x in cetes_rate.filtered(lambda x:x.rate_days_364==max_high_rate_364))
                min_rate_364_rec = max(x for x in cetes_rate.filtered(lambda x:x.rate_days_364==min_high_rate_364))
                total_rate = sum(x.rate_days_364 for x in cetes_rate)           
                total_rec = len(cetes_rate)
                avg = total_rate/total_rec
    
                CETES_columns_364 += [self._format({'name': start_month_rec.rate_days_364},figure_type='float'),
                                self._format({'name': end_month_rec.rate_days_364},figure_type='float'),
                                {'name': max_rate_364_rec.rate_date},
                                self._format({'name': max_rate_364_rec.rate_days_364},figure_type='float'),
                                {'name': min_rate_364_rec.rate_date},
                                self._format({'name': min_rate_364_rec.rate_days_364},figure_type='float'),
                                self._format({'name': avg},figure_type='float'),
                                ]
                                 
        lines.append({
            'id': 'hierarchy_cetes',
            'name': 'A) CETES',
            'columns': [{'name': ''}, 
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

        lang = self.env.user.lang
        lines.append({
            'id': 'hierarchy_cetes_28_days',
            'name': '28 Días' if lang == 'es_MX' else '28 DAYS',
            'columns': CETES_columns_28,
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
        })
        lines.append({
            'id': 'hierarchy_cetes_91_days',
            'name': '91 Días' if lang == 'es_MX' else '91 DAYS',
            'columns': CETES_columns_91,
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
        })
        lines.append({
            'id': 'hierarchy_cetes_182_days',
            'name': '182 Días' if lang == 'es_MX' else '182 DAYS',
            'columns': CETES_columns_182,
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
        })

        lines.append({
            'id': 'hierarchy_cetes_364_days',
            'name': '364 Días' if lang == 'es_MX' else '364 DAYS',
            'columns': CETES_columns_364,
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
        })

            
        #==================== Bonds Rate ======================#
        bonds_columns_3 = []
        bonds_columns_5 = []
        bonds_columns_7 = []
        bonds_columns_10 = []
        bonds_columns_20 = []
        bonds_columns_30 = []
        for period in periods:
            date_start = datetime.strptime(str(period.get('date_from')),
                                           DEFAULT_SERVER_DATE_FORMAT).date()
            date_end = datetime.strptime(str(period.get('date_to')),
                                         DEFAULT_SERVER_DATE_FORMAT).date()
        
            bonds_rate = self.env['investment.period.rate'].search([('rate_date','>=',date_start),('rate_date','<=',date_end),('product_type','=','BONUS')])        
            if bonds_rate:
                start_month_date = min(x.rate_date for x in bonds_rate)
                end_month_date = max(x.rate_date for x in bonds_rate)
                start_month_rec = max(x for x in bonds_rate.filtered(lambda x:x.rate_date==start_month_date))
                end_month_rec = max(x for x in bonds_rate.filtered(lambda x:x.rate_date==end_month_date))
    
                #====== bonds 3 Years ========
                max_high_rate_3 = max(x.rate_year_3 for x in bonds_rate)
                min_high_rate_3 = min(x.rate_year_3 for x in bonds_rate)
                max_rate_3_rec = max(x for x in bonds_rate.filtered(lambda x:x.rate_year_3==max_high_rate_3))
                min_rate_3_rec = max(x for x in bonds_rate.filtered(lambda x:x.rate_year_3==min_high_rate_3))
                total_rate = sum(x.rate_year_3 for x in bonds_rate)           
                total_rec = len(bonds_rate)
                avg = total_rate/total_rec
                
                bonds_columns_3 += [self._format({'name': start_month_rec.rate_year_3},figure_type='float'),
                                self._format({'name': end_month_rec.rate_year_3},figure_type='float'),
                                {'name': max_rate_3_rec.rate_date},
                                self._format({'name': max_rate_3_rec.rate_year_3},figure_type='float'),
                                {'name': min_rate_3_rec.rate_date},
                                self._format({'name': min_rate_3_rec.rate_year_3},figure_type='float'),
                                self._format({'name': avg},figure_type='float'),
                                ]             
    
                #====== bonds 5 Years ========
                max_high_rate_5 = max(x.rate_year_5 for x in bonds_rate)
                min_high_rate_5 = min(x.rate_year_5 for x in bonds_rate)
                max_rate_5_rec = max(x for x in bonds_rate.filtered(lambda x:x.rate_year_5==max_high_rate_5))
                min_rate_5_rec = max(x for x in bonds_rate.filtered(lambda x:x.rate_year_5==min_high_rate_5))
                total_rate = sum(x.rate_year_5 for x in bonds_rate)           
                total_rec = len(bonds_rate)
                avg = total_rate/total_rec
                             
                bonds_columns_5 += [self._format({'name': start_month_rec.rate_year_5},figure_type='float'),
                                self._format({'name': end_month_rec.rate_year_5},figure_type='float'),
                                {'name': max_rate_5_rec.rate_date},
                                self._format({'name': max_rate_5_rec.rate_year_5},figure_type='float'),
                                {'name': min_rate_5_rec.rate_date},
                                self._format({'name': min_rate_5_rec.rate_year_5},figure_type='float'),
                                self._format({'name': avg},figure_type='float'),
                                ]
                                
                #====== bonds 7 Years ========
                max_high_rate_7 = max(x.rate_year_7 for x in bonds_rate)
                min_high_rate_7 = min(x.rate_year_7 for x in bonds_rate)
                max_rate_7_rec = max(x for x in bonds_rate.filtered(lambda x:x.rate_year_7==max_high_rate_7))
                min_rate_7_rec = max(x for x in bonds_rate.filtered(lambda x:x.rate_year_7==min_high_rate_7))
                total_rate = sum(x.rate_year_7 for x in bonds_rate)           
                total_rec = len(bonds_rate)
                avg = total_rate/total_rec
                
                bonds_columns_7 += [self._format({'name': start_month_rec.rate_year_7},figure_type='float'),
                                self._format({'name': end_month_rec.rate_year_7},figure_type='float'),
                                {'name': max_rate_7_rec.rate_date},
                                self._format({'name': max_rate_7_rec.rate_year_7},figure_type='float'),
                                {'name': min_rate_7_rec.rate_date},
                                self._format({'name': min_rate_7_rec.rate_year_7},figure_type='float'),
                                self._format({'name': avg},figure_type='float'),
                                ]
                             
                #====== bonds 10 Years ========
                max_high_rate_10 = max(x.rate_year_10 for x in bonds_rate)
                min_high_rate_10 = min(x.rate_year_10 for x in bonds_rate)
                max_rate_10_rec = max(x for x in bonds_rate.filtered(lambda x:x.rate_year_10==max_high_rate_10))
                min_rate_10_rec = max(x for x in bonds_rate.filtered(lambda x:x.rate_year_10==min_high_rate_10))
                total_rate = sum(x.rate_year_10 for x in bonds_rate)           
                total_rec = len(bonds_rate)
                avg = total_rate/total_rec
                
                bonds_columns_10 += [self._format({'name': start_month_rec.rate_year_10},figure_type='float'),
                                self._format({'name': end_month_rec.rate_year_10},figure_type='float'),
                                {'name': max_rate_10_rec.rate_date},
                                self._format({'name': max_rate_10_rec.rate_year_10},figure_type='float'),
                                {'name': min_rate_10_rec.rate_date},
                                self._format({'name': min_rate_10_rec.rate_year_10},figure_type='float'),
                                self._format({'name': avg},figure_type='float'),
                                ]
                                 
                #====== bonds 20 Years ========
                max_high_rate_20 = max(x.rate_year_20 for x in bonds_rate)
                min_high_rate_20 = min(x.rate_year_20 for x in bonds_rate)
                max_rate_20_rec = max(x for x in bonds_rate.filtered(lambda x:x.rate_year_20==max_high_rate_20))
                min_rate_20_rec = max(x for x in bonds_rate.filtered(lambda x:x.rate_year_20==min_high_rate_20))
                total_rate = sum(x.rate_year_20 for x in bonds_rate)           
                total_rec = len(bonds_rate)
                avg = total_rate/total_rec
                
                bonds_columns_20 += [self._format({'name': start_month_rec.rate_year_20},figure_type='float'),
                                self._format({'name': end_month_rec.rate_year_20},figure_type='float'),
                                {'name': max_rate_20_rec.rate_date},
                                self._format({'name': max_rate_20_rec.rate_year_20},figure_type='float'),
                                {'name': min_rate_20_rec.rate_date},
                                self._format({'name': min_rate_20_rec.rate_year_20},figure_type='float'),
                                self._format({'name': avg},figure_type='float'),
                                ]
                             
    
                #====== bonds 30 Years ========
                max_high_rate_30 = max(x.rate_year_30 for x in bonds_rate)
                min_high_rate_30 = min(x.rate_year_30 for x in bonds_rate)
                max_rate_30_rec = max(x for x in bonds_rate.filtered(lambda x:x.rate_year_30==max_high_rate_30))
                min_rate_30_rec = max(x for x in bonds_rate.filtered(lambda x:x.rate_year_30==min_high_rate_30))
                total_rate = sum(x.rate_year_30 for x in bonds_rate)           
                total_rec = len(bonds_rate)
                avg = total_rate/total_rec
                
                bonds_columns_30 += [self._format({'name': start_month_rec.rate_year_30},figure_type='float'),
                                self._format({'name': end_month_rec.rate_year_30},figure_type='float'),
                                {'name': max_rate_20_rec.rate_date},
                                self._format({'name': max_rate_30_rec.rate_year_30},figure_type='float'),
                                {'name': min_rate_30_rec.rate_date},
                                self._format({'name': min_rate_30_rec.rate_year_30},figure_type='float'),
                                self._format({'name': avg},figure_type='float'),
                                ]
                            
        lines.append({
            'id': 'hierarchy_bonds',
            'name': 'B) BONOS',
            'columns': [{'name': ''}, 
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
            'id': 'hierarchy_bond_3_year',
            'name': '3 Años' if lang == 'es_MX' else '3 YEARS',
            'columns': bonds_columns_3,
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
        })

        lines.append({
            'id': 'hierarchy_bond_5_year',
            'name': '5 Años' if lang == 'es_MX' else '5 YEARS',
            'columns': bonds_columns_5,
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
        })

        lines.append({
            'id': 'hierarchy_bond_7_year',
            'name': '7 Años' if lang == 'es_MX' else '7 YEARS',
            'columns': bonds_columns_7,
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
        })

        lines.append({
            'id': 'hierarchy_bond_10_year',
            'name': '10 Años' if lang == 'es_MX' else '10 YEARS',
            'columns': bonds_columns_10,
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
        })

        lines.append({
            'id': 'hierarchy_bond_20_year',
            'name': '10 Años' if lang == 'es_MX' else '20 YEARS',
            'columns': bonds_columns_20,
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
        })
 
        lines.append({
           'id': 'hierarchy_bond_30_year',
           'name': '30 Años' if lang == 'es_MX' else '30 YEARS',
           'columns': bonds_columns_30,
           'level': 3,
           'unfoldable': False,
           'unfolded': True,
        })
   

        #==================== UdiBonds Rate ======================#
        UdiBonds_columns_3 = []
        UdiBonds_columns_5 = []
        UdiBonds_columns_10 = []
        UdiBonds_columns_20 = []
        UdiBonds_columns_30 = []
        
        for period in periods:
            date_start = datetime.strptime(str(period.get('date_from')),
                                           DEFAULT_SERVER_DATE_FORMAT).date()
            date_end = datetime.strptime(str(period.get('date_to')),
                                         DEFAULT_SERVER_DATE_FORMAT).date()
        
            udibonos_rate = self.env['investment.period.rate'].search([('rate_date','>=',date_start),('rate_date','<=',date_end),('product_type','=','UDIBONOS')])
                    
            if udibonos_rate:
                start_month_date = min(x.rate_date for x in udibonos_rate)
                end_month_date = max(x.rate_date for x in udibonos_rate)
                start_month_rec = max(x for x in udibonos_rate.filtered(lambda x:x.rate_date==start_month_date))
                end_month_rec = max(x for x in udibonos_rate.filtered(lambda x:x.rate_date==end_month_date))
    
                #====== bonds 3 Years ========
                max_high_rate_3 = max(x.rate_year_3 for x in udibonos_rate)
                min_high_rate_3 = min(x.rate_year_3 for x in udibonos_rate)
                max_rate_3_rec = max(x for x in udibonos_rate.filtered(lambda x:x.rate_year_3==max_high_rate_3))
                min_rate_3_rec = max(x for x in udibonos_rate.filtered(lambda x:x.rate_year_3==min_high_rate_3))
                total_rate = sum(x.rate_year_3 for x in udibonos_rate)           
                total_rec = len(udibonos_rate)
                avg = total_rate/total_rec
                
                UdiBonds_columns_3 += [self._format({'name': start_month_rec.rate_year_3},figure_type='float'),
                                self._format({'name': end_month_rec.rate_year_3},figure_type='float'),
                                {'name': max_rate_3_rec.rate_date},
                                self._format({'name': max_rate_3_rec.rate_year_3},figure_type='float'),
                                {'name': min_rate_3_rec.rate_date},
                                self._format({'name': min_rate_3_rec.rate_year_3},figure_type='float'),
                                self._format({'name': avg},figure_type='float'),
                                ]              
    
                #====== bonds 5 Years ========
                max_high_rate_5 = max(x.rate_year_5 for x in udibonos_rate)
                min_high_rate_5 = min(x.rate_year_5 for x in udibonos_rate)
                max_rate_5_rec = max(x for x in udibonos_rate.filtered(lambda x:x.rate_year_5==max_high_rate_5))
                min_rate_5_rec = max(x for x in udibonos_rate.filtered(lambda x:x.rate_year_5==min_high_rate_5))
                total_rate = sum(x.rate_year_5 for x in udibonos_rate)           
                total_rec = len(udibonos_rate)
                avg = total_rate/total_rec
                
                UdiBonds_columns_5 += [self._format({'name': start_month_rec.rate_year_5},figure_type='float'),
                                self._format({'name': end_month_rec.rate_year_5},figure_type='float'),
                                {'name': max_rate_5_rec.rate_date},
                                self._format({'name': max_rate_5_rec.rate_year_5},figure_type='float'),
                                {'name': min_rate_5_rec.rate_date},
                                self._format({'name': min_rate_5_rec.rate_year_5},figure_type='float'),
                                self._format({'name': avg},figure_type='float'),
                                ]
                                  
                #====== bonds 10 Years ========
                max_high_rate_10 = max(x.rate_year_10 for x in udibonos_rate)
                min_high_rate_10 = min(x.rate_year_10 for x in udibonos_rate)
                max_rate_10_rec = max(x for x in udibonos_rate.filtered(lambda x:x.rate_year_10==max_high_rate_10))
                min_rate_10_rec = max(x for x in udibonos_rate.filtered(lambda x:x.rate_year_10==min_high_rate_10))
                total_rate = sum(x.rate_year_10 for x in udibonos_rate)           
                total_rec = len(udibonos_rate)
                avg = total_rate/total_rec
                
                UdiBonds_columns_10 += [self._format({'name': start_month_rec.rate_year_10},figure_type='float'),
                                self._format({'name': end_month_rec.rate_year_10},figure_type='float'),
                                {'name': max_rate_10_rec.rate_date},
                                self._format({'name': max_rate_10_rec.rate_year_10},figure_type='float'),
                                {'name': min_rate_10_rec.rate_date},
                                self._format({'name': min_rate_10_rec.rate_year_10},figure_type='float'),
                                self._format({'name': avg},figure_type='float'),
                                ]
                                  
                #====== Udibonds 20 Years ========
                max_high_rate_20 = max(x.rate_year_20 for x in udibonos_rate)
                min_high_rate_20 = min(x.rate_year_20 for x in udibonos_rate)
                max_rate_20_rec = max(x for x in udibonos_rate.filtered(lambda x:x.rate_year_20==max_high_rate_20))
                min_rate_20_rec = max(x for x in udibonos_rate.filtered(lambda x:x.rate_year_20==min_high_rate_20))
                total_rate = sum(x.rate_year_20 for x in udibonos_rate)           
                total_rec = len(udibonos_rate)
                avg = total_rate/total_rec
                
                UdiBonds_columns_20 += [self._format({'name': start_month_rec.rate_year_20},figure_type='float'),
                                self._format({'name': end_month_rec.rate_year_20},figure_type='float'),
                                {'name': max_rate_20_rec.rate_date},
                                self._format({'name': max_rate_20_rec.rate_year_20},figure_type='float'),
                                {'name': min_rate_20_rec.rate_date},
                                self._format({'name': min_rate_20_rec.rate_year_20},figure_type='float'),
                                self._format({'name': avg},figure_type='float'),
                                ]
                                 
                #====== Udibonds 30 Years ========
                max_high_rate_30 = max(x.rate_year_30 for x in udibonos_rate)
                min_high_rate_30 = min(x.rate_year_30 for x in udibonos_rate)
                max_rate_30_rec = max(x for x in udibonos_rate.filtered(lambda x:x.rate_year_30==max_high_rate_30))
                min_rate_30_rec = max(x for x in udibonos_rate.filtered(lambda x:x.rate_year_30==min_high_rate_30))
                total_rate = sum(x.rate_year_30 for x in udibonos_rate)           
                total_rec = len(udibonos_rate)
                avg = total_rate/total_rec
                
                UdiBonds_columns_30 += [self._format({'name': start_month_rec.rate_year_30},figure_type='float'),
                                self._format({'name': end_month_rec.rate_year_30},figure_type='float'),
                                {'name': max_rate_20_rec.rate_date},
                                self._format({'name': max_rate_30_rec.rate_year_30},figure_type='float'),
                                {'name': min_rate_30_rec.rate_date},
                                self._format({'name': min_rate_30_rec.rate_year_30},figure_type='float'),
                                self._format({'name': avg},figure_type='float'),
                                ]
        lines.append({
            'id': 'hierarchy_bonds',
            'name': 'C) UDIBONOS',
            'columns': [{'name': ''}, 
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
            'id': 'hierarchy_udibond_3_year',
            'name': '3 Años' if lang == 'es_MX' else '3 YEARS',
            'columns': UdiBonds_columns_3,
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
        })

        lines.append({
            'id': 'hierarchy_udibond_5_year',
            'name': '5 Años' if lang == 'es_MX' else '5 YEARS',
            'columns': UdiBonds_columns_5,
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
        })

        lines.append({
            'id': 'hierarchy_udibond_10_year',
            'name': '10 Años' if lang == 'es_MX' else '10 YEARS',
            'columns': UdiBonds_columns_10,
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
        })
        lines.append({
            'id': 'hierarchy_udibond_20_year',
            'name': '20 Años' if lang == 'es_MX' else '20 YEARS',
            'columns': UdiBonds_columns_20,
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
        })
        lines.append({
            'id': 'hierarchy_udibond_30_year',
            'name': '30 Años' if lang == 'es_MX' else '30 YEARS',
            'columns': UdiBonds_columns_30,
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
        })

        #==================== TIIE Rate ======================#
        TIIE_columns_1 = []
        TIIE_columns_28 = []
        TIIE_columns_91 = []
        TIIE_columns_182 = []
        
        for period in periods:
            date_start = datetime.strptime(str(period.get('date_from')),
                                           DEFAULT_SERVER_DATE_FORMAT).date()
            date_end = datetime.strptime(str(period.get('date_to')),
                                         DEFAULT_SERVER_DATE_FORMAT).date()
        
            TIIE = self.env['investment.period.rate'].search([('rate_date','>=',date_start),('rate_date','<=',date_end),('product_type','=','PAGARE')])
            
            if TIIE:
                start_month_date = min(x.rate_date for x in TIIE)
                end_month_date = max(x.rate_date for x in TIIE)
                start_month_rec = max(x for x in TIIE.filtered(lambda x:x.rate_date==start_month_date))
                end_month_rec = max(x for x in TIIE.filtered(lambda x:x.rate_date==end_month_date))
                    
                max_high_rate_364 = max(x.rate_daily for x in TIIE)
                min_high_rate_364 = min(x.rate_daily for x in TIIE)
                max_rate_364_rec = max(x for x in TIIE.filtered(lambda x:x.rate_daily==max_high_rate_364))
                min_rate_364_rec = max(x for x in TIIE.filtered(lambda x:x.rate_daily==min_high_rate_364))
                total_rate = sum(x.rate_daily for x in TIIE)           
                total_rec = len(TIIE)
                avg = total_rate/total_rec
                
                TIIE_columns_1 += [self._format({'name': start_month_rec.rate_daily},figure_type='float'),
                                self._format({'name': end_month_rec.rate_daily},figure_type='float'),
                                {'name': max_rate_364_rec.rate_date},
                                self._format({'name': max_rate_364_rec.rate_daily},figure_type='float'),
                                {'name': min_rate_364_rec.rate_date},
                                self._format({'name': min_rate_364_rec.rate_daily},figure_type='float'),
                                self._format({'name': avg},figure_type='float'),
                                ]
                                 
                max_high_rate_28 = max(x.rate_days_28 for x in TIIE)
                min_high_rate_28 = min(x.rate_days_28 for x in TIIE)
                max_rate_28_rec = max(x for x in TIIE.filtered(lambda x:x.rate_days_28==max_high_rate_28))
                min_rate_28_rec = max(x for x in TIIE.filtered(lambda x:x.rate_days_28==min_high_rate_28))
                total_rate = sum(x.rate_days_28 for x in TIIE)           
                total_rec = len(TIIE)
                avg = total_rate/total_rec
                
                TIIE_columns_28 += [self._format({'name': start_month_rec.rate_days_28},figure_type='float'),
                                self._format({'name': end_month_rec.rate_days_28},figure_type='float'),
                                {'name': max_rate_28_rec.rate_date},
                                self._format({'name': max_rate_28_rec.rate_days_28},figure_type='float'),
                                {'name': min_rate_28_rec.rate_date},
                                self._format({'name': min_rate_28_rec.rate_days_28},figure_type='float'),
                                self._format({'name': avg},figure_type='float'),
                                ]
                
                max_high_rate_91 = max(x.rate_days_91 for x in TIIE)
                min_high_rate_91 = min(x.rate_days_91 for x in TIIE)
                max_rate_91_rec = max(x for x in TIIE.filtered(lambda x:x.rate_days_91==max_high_rate_91))
                min_rate_91_rec = max(x for x in TIIE.filtered(lambda x:x.rate_days_91==min_high_rate_91))
                total_rate = sum(x.rate_days_91 for x in TIIE)           
                total_rec = len(TIIE)
                avg = total_rate/total_rec
                
                TIIE_columns_91 += [self._format({'name': start_month_rec.rate_days_91},figure_type='float'),
                                self._format({'name': end_month_rec.rate_days_91},figure_type='float'),
                                {'name': max_rate_91_rec.rate_date},
                                self._format({'name': max_rate_91_rec.rate_days_91},figure_type='float'),
                                {'name': min_rate_91_rec.rate_date},
                                self._format({'name': min_rate_91_rec.rate_days_91},figure_type='float'),
                                self._format({'name': avg},figure_type='float'),
                                ]
                    
                max_high_rate_182 = max(x.rate_days_182 for x in TIIE)
                min_high_rate_182 = min(x.rate_days_182 for x in TIIE)
                max_rate_182_rec = max(x for x in TIIE.filtered(lambda x:x.rate_days_182==max_high_rate_182))
                min_rate_182_rec = max(x for x in TIIE.filtered(lambda x:x.rate_days_182==min_high_rate_182))
                total_rate = sum(x.rate_days_182 for x in TIIE)           
                total_rec = len(TIIE)
                avg = total_rate/total_rec
                
                TIIE_columns_182 += [self._format({'name': start_month_rec.rate_days_182},figure_type='float'),
                                self._format({'name': end_month_rec.rate_days_182},figure_type='float'),
                                {'name': max_rate_182_rec.rate_date},
                                self._format({'name': max_rate_182_rec.rate_days_182},figure_type='float'),
                                {'name': min_rate_182_rec.rate_date},
                                self._format({'name': min_rate_182_rec.rate_days_182},figure_type='float'),
                                self._format({'name': avg},figure_type='float'),
                                ]
                                
        lines.append({
            'id': 'hierarchy_cetes',
            'name': 'D) TIIE',
            'columns': [{'name': ''}, 
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
            'id': 'hierarchy_tiie_daily_days',
            'name': 'Diariamente' if lang == 'es_MX' else 'Daily',
            'columns': TIIE_columns_1,
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
        })

        lines.append({
            'id': 'hierarchy_TIIE_28_days',
            'name': '28 Días' if lang == 'es_MX' else '28 DAYS',
            'columns': TIIE_columns_28,
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
        })
        lines.append({
            'id': 'hierarchy_TIIE_91_days',
            'name': '91 Días' if lang == 'es_MX' else '91 DAYS',
            'columns': TIIE_columns_91,
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
        })
        lines.append({
            'id': 'hierarchy_TIIE_182_days',
            'name': '182 Días' if lang == 'es_MX' else '182 DAYS',
            'columns': TIIE_columns_182,
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
        })
                
                
        #===================== Currency Filter ============================#
        currency_ids = self.env['res.currency'].search([('id','!=',self.env.user.company_id.currency_id.id)])
        
        for currency in currency_ids:
            currency_col = []
            for period in periods:
                date_start = datetime.strptime(str(period.get('date_from')),
                                               DEFAULT_SERVER_DATE_FORMAT).date()
                date_end = datetime.strptime(str(period.get('date_to')),
                                             DEFAULT_SERVER_DATE_FORMAT).date()
                
                currency_rates = self.env['res.currency.rate'].search([('name','>=',date_start),('name','<=',date_end),('currency_id','=',currency.id)])
                
                if currency_rates:
                    start_month_date = min(x.name for x in currency_rates)
                    end_month_date = max(x.name for x in currency_rates)
                    start_month_rec = max(x for x in currency_rates.filtered(lambda x:x.name==start_month_date))
                    end_month_rec = max(x for x in currency_rates.filtered(lambda x:x.name==end_month_date))
        
                    
                    max_high_rate_364 = max(x.rate for x in currency_rates)
                    min_high_rate_364 = min(x.rate for x in currency_rates)
                    max_rate_364_rec = max(x for x in currency_rates.filtered(lambda x:x.rate==max_high_rate_364))
                    min_rate_364_rec = max(x for x in currency_rates.filtered(lambda x:x.rate==min_high_rate_364))
                    total_rate = sum(x.rate for x in currency_rates)           
                    total_rec = len(currency_rates)
                    avg = total_rate/total_rec
                    if avg != 0:
                        avg = 1/avg
                    im = start_month_rec.rate
                    if start_month_rec.rate != 0:
                        im = 1/im
                    em = end_month_rec.rate
                    if end_month_rec.rate != 0:
                        em = 1/em
                    maxr = max_rate_364_rec.rate
                    if max_rate_364_rec.rate != 0:
                        maxr = 1/maxr
                    minr = min_rate_364_rec.rate
                    if min_rate_364_rec.rate != 0:
                        minr = 1/minr
                        
                    currency_col += [self._format({'name': im},figure_type='float'),
                                    self._format({'name': em},figure_type='float'),
                                    {'name': max_rate_364_rec.name},
                                    self._format({'name': maxr},figure_type='float'),
                                    {'name': min_rate_364_rec.name},
                                    self._format({'name': minr},figure_type='float'),
                                    self._format({'name': avg},figure_type='float'),
                                    ]
                     
            
            lines.append({
                'id': 'hierarchy_cetes',
                'name': currency.name,
                'columns': [{'name': ''}, 
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
                'id': 'hierarchy_tiie_daily_days',
                'name': 'Diariamente' if lang == 'es_MX' else 'Daily',
                'columns': currency_col,
                'level': 3,
                'unfoldable': False,
                'unfolded': True,
            })
            
        return lines

    def _get_report_name(self):
        return _("Indicators Report")
    
    @api.model
    def _get_super_columns(self, options):
        date_cols = options.get('date') and [options['date']] or []
        date_cols += (options.get('comparison') or {}).get('periods', [])
        columns = reversed(date_cols)
        return {'columns': columns, 'x_offset': 1, 'merge': 7}


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
        header_title = '''UNIVERSIDAD NACIONAL AUTÓNOMA DE MÉXICO\nPATRONATO UNIVERSITARIO\nDIRECCIÓN GENERAL DE FINANZAS\nSUBDIRECCION DE FINANZAS\nREPORTE DE INDICADORES'''
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
            rcontext.update({
                    'css': '',
                    'o': self.env.user,
                    'res_company': self.env.company,
                })
            header = self.env['ir.actions.report'].render_template("jt_investment.external_layout_indicators_report", values=rcontext)
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
