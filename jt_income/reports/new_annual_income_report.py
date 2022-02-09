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

class AnnualIncomeReport(models.AbstractModel):
    _name = "jt_income.annual.income.report"
    _inherit = "account.coa.report"
    _description = "Annual Income Report"

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

    def _get_reports_buttons(self):
        return [
            {'name': _('Export to PDF'), 'sequence': 1, 'action': 'print_pdf', 'file_export_type': _('PDF')},
            {'name': _('Export (XLSX)'), 'sequence': 2, 'action': 'print_xlsx', 'file_export_type': _('XLSX')},
        ]

    def _get_templates(self):
        templates = super(
            AnnualIncomeReport, self)._get_templates()
        templates[
            'main_table_header_template'] = 'account_reports.main_table_header'
        templates['main_template'] = 'account_reports.main_template'
        return templates

    def get_header(self, options):
        columns = self._get_columns_name(options)
        return [[
                {'name':''},
                {'name': _('EXPRESADO EN MILES DE PESOS'),'class':'align-center','colspan': 16},
 
            ],
            columns]
        
#         return[
#  
#             [
#                 {'name':''},
#                 {'name':''},
#                 {'name':''},
#                 {'name':''},
#                 {'name':''},
#                 {'name':''},
#                 {'name': _('EXPRESADO EN MILES DE PESOS'),'class':'align-center'},
#                 {'name':''},
#                 {'name':''},
#                 {'name':''},
#                 {'name':''},
#                 {'name':''},
#                 {'name':''},
#                 {'name':''},
#                 {'name':''},
#                 {'name':''},
#  
#             ],
#  
#             [
#             {'name': _('Mes')},
#             {'name': _('Subsidio')},
#             {'name': _('Subsidio por cobrar')},
#             {'name': _('Inscripciones y Colegiaturas')},
#             {'name': _('Concurso de selección')},
#             {'name': _('Incorporación y Revalidación')},
#             {'name': _('Ingresos Extraordinarios')},
#             {'name': _('Patrimonial Income')},
#             {'name': _('Productos Financieros')},
#             {'name': _('Total')},
#             {'name': _('Nomina')},
#             {'name': _('Proveedores')},
#             {'name': _('Otras Prestaciones')},
#             {'name': _('Fondo Mantenimiento Mayor')},
#             {'name': _('Fondos FIF')},
#             {'name': _('Total')},
#             ]
#         ]

    def _get_columns_name(self, options):
        return [
            {'name': _('Mes')},
            {'name': _('Subsidio')},
            {'name': _('Subsidio por cobrar')},
            {'name': _('Inscripciones y Colegiaturas')},
            {'name': _('Concurso de selección')},
            {'name': _('Incorporación y Revalidación')},
            {'name': _('Ingresos Extraordinarios')},
            {'name': _('Patrimonial Income')},
            {'name': _('Productos Financieros')},
            {'name': _('Total')},
            {'name': _('Nomina')},
            {'name': _('Proveedores')},
            {'name': _('Otras Prestaciones')},
            {'name': _('Fondo Mantenimiento Mayor')},
            {'name': _('Fondos FIF')},
            {'name': _('Total')},
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

    def _get_lines(self, options, line_id=None):
        lines = []
        start = datetime.strptime(
            str(options['date'].get('date_from')), '%Y-%m-%d').date()
        end = datetime.strptime(
            options['date'].get('date_to'), '%Y-%m-%d').date()

        currency_list = [0]
        for select_curreny in options.get('currency'):
            if select_curreny.get('selected',False)==True:
                currency_list.append(select_curreny.get('id',0))

        is_company_currency = False
        if self.env.company.currency_id.id in currency_list:
            is_company_currency = True
        
        year_list_tuple = range(start.year, end.year+1)
        year_list = []
        
        start_year = str(start.year)
        end_year = str(end.year)

        start_year_month = start.month
        end_year_month = end.month
        
        for y in year_list_tuple:
            year_list.append(str(y))
        total_subsidy = 0
        total_subsidy_receivable = 0
        total_enrollment_and_tuition = 0
        total_selection_contest = 0
        total_incorporation_and_revalidation = 0
        total_extraordinary_income = 0
        total_patrimonial_income = 0
        total_financial_products = 0
        master_total_1 = 0
        total_nomina = 0
        total_suppliers = 0
        total_other_benefits = 0
        total_major_maintenance_fund = 0
        total_FIF_funds = 0
        master_total_2 = 0
        
        if is_company_currency:
            self.env.cr.execute('''
                    select max(am.id) as id,
                    Cast((extract(year from am.invoice_date)) as Text) as year,
                    Cast((extract(month from am.invoice_date)) as Integer) as month,
                    COALESCE(sum(case when am.type_of_revenue_collection = 'dgoae_trades' then abs(am.amount_untaxed_signed) else 0 end),0) enrollment_and_tuition,
                    COALESCE(sum(case when am.type_of_revenue_collection = 'dgae_ref' and am.sub_origin_resource_name in ('Applicants','Aspirantes') then abs(am.amount_untaxed_signed) else 0 end),0) selection_contest,
                    COALESCE(sum(case when am.income_type = 'own' and am.sub_origin_resource_name in ('Incorporation and revalidation of studies','Incorporación y revalidación de estudios') then abs(am.amount_untaxed_signed) else 0 end),0) incorporation_and_revalidation,
                    COALESCE(sum(case when am.type_of_revenue_collection = 'billing' and am.income_type = 'extra' and am.sub_origin_resource_name not in ('Financial Products','Productos financieros') then abs(am.amount_untaxed_signed) else 0 end),0) extraordinary_income,
                    COALESCE(sum(case when am.income_type = 'own' and am.sub_origin_resource_name in ('Patrimonial income','Ingresos patrimoniales') then abs(am.amount_untaxed_signed) else 0 end),0) patrimonial_income,
                    COALESCE(sum(case when am.income_type = 'extra' and am.sub_origin_resource_name  in ('Financial Products','Productos financieros') then abs(am.amount_untaxed_signed) else 0 end),0) financial_products,
                    COALESCE(sum(case when am.is_payroll_payment_request = True and am.payment_state='for_payment_procedure' then abs(am.amount_untaxed_signed) else 0 end),0) nomina,
                    COALESCE(sum(case when am.is_payment_request = True and am.payment_state='for_payment_procedure' then abs(am.amount_untaxed_signed) else 0 end),0) suppliers,
                    0 as major_maintenance_fund,
                    0 as fif_funds,
                    COALESCE(sum(case when am.is_different_payroll_request = True and am.payment_state='for_payment_procedure' then abs(am.amount_untaxed_signed) else 0 end),0) as other_benefits
                    from account_move am
                    where am.state='posted' and am.currency_id in %s 
                    and am.invoice_date >= %s and am.invoice_date <= %s and am.invoice_date IS NOT NULL
                    group by year,month
                    order by year,month
                    ''' ,(tuple(currency_list),start,end))
            
            data_dict = {}    
            invoice_datas = self.env.cr.fetchall()
            for data in invoice_datas:
                if data_dict.get(data[1]):
                    year_dict = data_dict.get(data[1])                
                    year_dict.update({data[2]:{
                        'year': data[1],
                        'month' : data[2],
                        'enrollment_and_tuition' : data[3],
                        'selection_contest' : data[4],
                        'incorporation_and_revalidation' : data[5],
                        'extraordinary_income' : data[6],
                        'patrimonial_income' : data[7],
                        'financial_products' : data[8],
                        'nomina' : data[9],
                        'suppliers' : data[10],
                        'major_maintenance_fund' : data[11],
                        'fif_funds' : data[12],
                        'other_benefits' : data[13],
                        }})
                    
                else:
                    data_dict.update({data[1]:{data[2]:{
                        'year': data[1],
                        'month' : data[2],
                        'enrollment_and_tuition' : data[3],
                        'selection_contest' : data[4],
                        'incorporation_and_revalidation' : data[5],
                        'extraordinary_income' : data[6],
                        'patrimonial_income' : data[7],
                        'financial_products' : data[8],
                        'nomina' : data[9],
                        'suppliers' : data[10],
                        'major_maintenance_fund' : data[11],
                        'fif_funds' : data[12],
                        'other_benefits' : data[13],
                        }}})
            
            self.env.cr.execute('''     
                select 
                    year as year,
                    COALESCE(sum(january),0) as january,COALESCE(sum(amount_deposite_january),0) as amount_deposite_january,
                    COALESCE(sum(february),0) as february,COALESCE(sum(amount_deposite_february),0) as amount_deposite_february,
                    COALESCE(sum(march),0) as march,COALESCE(sum(amount_deposite_march),0) as amount_deposite_march,
                    COALESCE(sum(april),0) as april,COALESCE(sum(amount_deposite_april),0) as amount_deposite_april,
                    COALESCE(sum(may),0) as may,COALESCE(sum(amount_deposite_may),0) as amount_deposite_may,
                    COALESCE(sum(june),0) as june,COALESCE(sum(amount_deposite_june),0) as amount_deposite_june,
                    COALESCE(sum(july),0) as july,COALESCE(sum(amount_deposite_july),0) as amount_deposite_july,
                    COALESCE(sum(august),0) as august,COALESCE(sum(amount_deposite_august),0) as amount_deposite_august,
                    COALESCE(sum(september),0) as september,COALESCE(sum(amount_deposite_september),0) as amount_deposite_september,
                    COALESCE(sum(october),0) as october,COALESCE(sum(amount_deposite_october),0) as amount_deposite_october,
                    COALESCE(sum(november),0) as november,COALESCE(sum(amount_deposite_november),0) as amount_deposite_november,
                    COALESCE(sum(december),0) as december,COALESCE(sum(amount_deposite_december),0) as amount_deposite_december 
                from calendar_assigned_amounts_lines cal,calendar_assigned_amounts ca
                where ca.state = 'validate' and ca.id=cal.calendar_assigned_amount_id
                and cal.currency_id in %s and year in %s
                group by year
                ''',(tuple(currency_list),tuple(year_list),))
             
            subsidy_data = self.env.cr.fetchall()
            
            for data in subsidy_data:
                if data_dict.get(data[0]):
                    year_dict = data_dict.get(data[0],{})
                    first = 1
                    sec = 2
                    for i in range(12):
                        j = i+1
                        if data[0] == start_year and j < start_year_month:
                            continue
                        if data[0] == end_year and j > end_year_month:
                            continue
                        
                        mont_dict = year_dict.get(j,{})
                        if mont_dict:
                            mont_dict.update({'year':data[0],'month':j,'subsidy_2020':data[first],'subsidy_receivable':data[sec]})
                        else:
                            year_dict.update({j:{'year':data[0],'month':j,'subsidy_2020':data[first],'subsidy_receivable':data[sec]}})
                        first +=2
                        sec += 2
                else:
                    first = 1
                    sec = 2
                    data_dict_subsydy = {}
                    for i in range(12):
                        j = i+1
                        if data[0] == start_year and j < start_year_month:
                            continue
                        if data[0] == end_year and j > end_year_month:
                            continue
                    
                        data_dict_subsydy.update({j:{'year':data[0],'month':j,'subsidy_2020':data[first],'subsidy_receivable':data[sec]}})
                        first +=2
                        sec += 2
                        
                    data_dict.update({data[0]:data_dict_subsydy})
                                                            
    
            previous_year = ''
            for year in data_dict:
                mont_dict = data_dict.get(year) 
                for month in mont_dict:
                    month_dict = mont_dict.get(month)
                    if previous_year!= month_dict.get('year',''):
                        previous_year = month_dict.get('year','')
                        lines.append({
                            'id': 'hierarchy1_' + month_dict.get('year',''),
                            'name': month_dict.get('year'),
                            'columns': [{'name': ''},
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
                                        {'name': ''},
                                        {'name': ''},
                                        {'name': ''},
                                        {'name': ''},
                                        ],
                            'level': 1,
                            'unfoldable': False,
                            'unfolded': True,
                        })


                    subsidy = month_dict.get('subsidy_2020',0.0)/1000
                    subsidy_receivable = month_dict.get('subsidy_receivable',0.0)/1000
                    enrollment_and_tuition  = month_dict.get('enrollment_and_tuition',0.0)/1000
                    selection_contest = month_dict.get('selection_contest',0.0)/1000
                    incorporation_and_revalidation = month_dict.get('incorporation_and_revalidation',0.0)/1000
                    extraordinary_income = month_dict.get('extraordinary_income',0.0)/1000
                    patrimonial_income = month_dict.get('patrimonial_income',0.0)/1000
                    financial_products = month_dict.get('financial_products',0.0)/1000
                    total_1 = enrollment_and_tuition + selection_contest + incorporation_and_revalidation + extraordinary_income + patrimonial_income + financial_products
                    nomina = month_dict.get('nomina',0.0)/1000
                    suppliers = month_dict.get('suppliers',0.0)/1000
                    other_benefits = month_dict.get('other_benefits',0.0)/1000
                    major_maintenance_fund = month_dict.get('major_maintenance_fund',0.0)/1000
                    FIF_funds = month_dict.get('fif_funds',0.0)/1000
                    total_2 = nomina + suppliers + other_benefits + major_maintenance_fund + FIF_funds

                    total_subsidy += subsidy
                    total_subsidy_receivable += subsidy_receivable
                    total_enrollment_and_tuition += enrollment_and_tuition
                    total_selection_contest += selection_contest
                    total_incorporation_and_revalidation += incorporation_and_revalidation
                    total_extraordinary_income += extraordinary_income
                    total_patrimonial_income += patrimonial_income
                    total_financial_products += financial_products
                    master_total_1 += total_1
                    total_nomina += nomina
                    total_suppliers += suppliers
                    total_other_benefits += other_benefits
                    total_major_maintenance_fund += major_maintenance_fund
                    total_FIF_funds += FIF_funds
                    master_total_2 += total_2
                         
                    lines.append({
                        'id': 'hierarchy1_' + month_dict.get('year','')+str(month_dict.get('month','')),
                        'name': self.get_month_name(month_dict.get('month',0)),
                        'columns': [
                                    self._format({'name': subsidy},figure_type='float'),
                                    self._format({'name': subsidy_receivable},figure_type='float'),
                                    self._format({'name': enrollment_and_tuition},figure_type='float'),
                                    self._format({'name': selection_contest},figure_type='float'),
                                    self._format({'name': incorporation_and_revalidation},figure_type='float'),
                                    self._format({'name': extraordinary_income},figure_type='float'),
                                    self._format({'name': patrimonial_income},figure_type='float'),
                                    self._format({'name': financial_products},figure_type='float'),
                                    self._format({'name': total_1},figure_type='float'),
                                    self._format({'name': nomina},figure_type='float'),
                                    self._format({'name': suppliers},figure_type='float'),
                                    self._format({'name': other_benefits},figure_type='float'),
                                    self._format({'name': major_maintenance_fund},figure_type='float'),
                                    self._format({'name': FIF_funds},figure_type='float'),
                                    self._format({'name': total_2},figure_type='float'),
                                    ],
                        'level': 3,
                        'unfoldable': False,
                        'unfolded': True,
                    })
        else:
            self.env.cr.execute('''
                    select max(am.id) as id,
                    Cast((extract(year from am.invoice_date)) as Text) as year,
                    Cast((extract(month from am.invoice_date)) as Integer) as month,
                    COALESCE(sum(case when am.type_of_revenue_collection = 'dgoae_trades' then abs(am.amount_untaxed) else 0 end),0) enrollment_and_tuition,
                    COALESCE(sum(case when am.type_of_revenue_collection = 'dgae_ref' and am.sub_origin_resource_name in ('Applicants','Aspirantes') then abs(am.amount_untaxed) else 0 end),0) selection_contest,
                    COALESCE(sum(case when am.income_type = 'own' and am.sub_origin_resource_name in ('Incorporation and revalidation of studies','Incorporación y revalidación de estudios') then abs(am.amount_untaxed) else 0 end),0) incorporation_and_revalidation,
                    COALESCE(sum(case when am.type_of_revenue_collection = 'billing' and am.income_type = 'extra' and am.sub_origin_resource_name not in ('Financial Products','Productos financieros') then abs(am.amount_untaxed) else 0 end),0) extraordinary_income,
                    COALESCE(sum(case when am.income_type = 'own' and am.sub_origin_resource_name in ('Patrimonial income','Ingresos patrimoniales') then abs(am.amount_untaxed) else 0 end),0) patrimonial_income,
                    COALESCE(sum(case when am.income_type = 'extra' and am.sub_origin_resource_name  in ('Financial Products','Productos financieros') then abs(am.amount_untaxed) else 0 end),0) financial_products,
                    COALESCE(sum(case when am.is_payroll_payment_request = True and am.payment_state='for_payment_procedure' then abs(am.amount_untaxed) else 0 end),0) nomina,
                    COALESCE(sum(case when am.is_payment_request = True and am.payment_state='for_payment_procedure' then abs(am.amount_untaxed) else 0 end),0) suppliers,
                    0 as major_maintenance_fund,
                    0 as fif_funds,
                    COALESCE(sum(case when am.is_different_payroll_request = True and am.payment_state='for_payment_procedure' then abs(am.amount_untaxed) else 0 end),0) as other_benefits
                    from account_move am
                    where am.state='posted' and am.currency_id in %s 
                    and am.invoice_date >= %s and am.invoice_date <= %s and am.invoice_date IS NOT NULL
                    group by year,month
                    order by year,month
                    ''' ,(tuple(currency_list),start,end))
            
            data_dict = {}    
            invoice_datas = self.env.cr.fetchall()
            for data in invoice_datas:
                if data_dict.get(data[1]):
                    year_dict = data_dict.get(data[1])                
                    year_dict.update({data[2]:{
                        'year': data[1],
                        'month' : data[2],
                        'enrollment_and_tuition' : data[3],
                        'selection_contest' : data[4],
                        'incorporation_and_revalidation' : data[5],
                        'extraordinary_income' : data[6],
                        'patrimonial_income' : data[7],
                        'financial_products' : data[8],
                        'nomina' : data[9],
                        'suppliers' : data[10],
                        'major_maintenance_fund' : data[11],
                        'fif_funds' : data[12],
                        'other_benefits' : data[13],
                        }})
                    
                else:
                    data_dict.update({data[1]:{data[2]:{
                        'year': data[1],
                        'month' : data[2],
                        'enrollment_and_tuition' : data[3],
                        'selection_contest' : data[4],
                        'incorporation_and_revalidation' : data[5],
                        'extraordinary_income' : data[6],
                        'patrimonial_income' : data[7],
                        'financial_products' : data[8],
                        'nomina' : data[9],
                        'suppliers' : data[10],
                        'major_maintenance_fund' : data[11],
                        'fif_funds' : data[12],
                        'other_benefits' : data[13],
                        }}})
            
            self.env.cr.execute('''     
                select 
                    year as year,
                    COALESCE(sum(january),0) as january,COALESCE(sum(amount_deposite_january),0) as amount_deposite_january,
                    COALESCE(sum(february),0) as february,COALESCE(sum(amount_deposite_february),0) as amount_deposite_february,
                    COALESCE(sum(march),0) as march,COALESCE(sum(amount_deposite_march),0) as amount_deposite_march,
                    COALESCE(sum(april),0) as april,COALESCE(sum(amount_deposite_april),0) as amount_deposite_april,
                    COALESCE(sum(may),0) as may,COALESCE(sum(amount_deposite_may),0) as amount_deposite_may,
                    COALESCE(sum(june),0) as june,COALESCE(sum(amount_deposite_june),0) as amount_deposite_june,
                    COALESCE(sum(july),0) as july,COALESCE(sum(amount_deposite_july),0) as amount_deposite_july,
                    COALESCE(sum(august),0) as august,COALESCE(sum(amount_deposite_august),0) as amount_deposite_august,
                    COALESCE(sum(september),0) as september,COALESCE(sum(amount_deposite_september),0) as amount_deposite_september,
                    COALESCE(sum(october),0) as october,COALESCE(sum(amount_deposite_october),0) as amount_deposite_october,
                    COALESCE(sum(november),0) as november,COALESCE(sum(amount_deposite_november),0) as amount_deposite_november,
                    COALESCE(sum(december),0) as december,COALESCE(sum(amount_deposite_december),0) as amount_deposite_december 
                from calendar_assigned_amounts_lines cal,calendar_assigned_amounts ca
                where ca.state = 'validate' and ca.id=cal.calendar_assigned_amount_id
                and cal.currency_id in %s and year in %s
                group by year
                ''',(tuple(currency_list),tuple(year_list),))
             
            subsidy_data = self.env.cr.fetchall()
            
            for data in subsidy_data:
                if data_dict.get(data[0]):
                    year_dict = data_dict.get(data[0],{})
                    first = 1
                    sec = 2
                    for i in range(12):
                        j = i+1
                        if data[0] == start_year and j < start_year_month:
                            continue
                        if data[0] == end_year and j > end_year_month:
                            continue
                        
                        mont_dict = year_dict.get(j,{})
                        if mont_dict:
                            mont_dict.update({'year':data[0],'month':j,'subsidy_2020':data[first],'subsidy_receivable':data[sec]})
                        else:
                            year_dict.update({j:{'year':data[0],'month':j,'subsidy_2020':data[first],'subsidy_receivable':data[sec]}})
                        first +=2
                        sec += 2
                else:
                    first = 1
                    sec = 2
                    data_dict_subsydy = {}
                    for i in range(12):
                        j = i+1
                        if data[0] == start_year and j < start_year_month:
                            continue
                        if data[0] == end_year and j > end_year_month:
                            continue
                    
                        data_dict_subsydy.update({j:{'year':data[0],'month':j,'subsidy_2020':data[first],'subsidy_receivable':data[sec]}})
                        first +=2
                        sec += 2
                        
                    data_dict.update({data[0]:data_dict_subsydy})
                                                            
    
            previous_year = ''
            for year in data_dict:
                mont_dict = data_dict.get(year) 
                for month in mont_dict:
                    month_dict = mont_dict.get(month)
                    if previous_year!= month_dict.get('year',''):
                        previous_year = month_dict.get('year','')
                        lines.append({
                            'id': 'hierarchy1_' + month_dict.get('year',''),
                            'name': month_dict.get('year'),
                            'columns': [{'name': ''},
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
                                        {'name': ''},
                                        {'name': ''},
                                        {'name': ''},
                                        {'name': ''},
                                        ],
                            'level': 1,
                            'unfoldable': False,
                            'unfolded': True,
                        })
                         
                    subsidy = month_dict.get('subsidy_2020',0.0)/1000
                    subsidy_receivable = month_dict.get('subsidy_receivable',0.0)/1000
                    enrollment_and_tuition  = month_dict.get('enrollment_and_tuition',0.0)/1000
                    selection_contest = month_dict.get('selection_contest',0.0)/1000
                    incorporation_and_revalidation = month_dict.get('incorporation_and_revalidation',0.0)/1000
                    extraordinary_income = month_dict.get('extraordinary_income',0.0)/1000
                    patrimonial_income = month_dict.get('patrimonial_income',0.0)/1000
                    financial_products = month_dict.get('financial_products',0.0)/1000
                    total_1 = enrollment_and_tuition + selection_contest + incorporation_and_revalidation + extraordinary_income + patrimonial_income + financial_products
                    nomina = month_dict.get('nomina',0.0)/1000
                    suppliers = month_dict.get('suppliers',0.0)/1000
                    other_benefits = month_dict.get('other_benefits',0.0)/1000
                    major_maintenance_fund = month_dict.get('major_maintenance_fund',0.0)/1000
                    FIF_funds = month_dict.get('fif_funds',0.0)/1000
                    total_2 = nomina + suppliers + other_benefits + major_maintenance_fund + FIF_funds

                    total_subsidy += subsidy
                    total_subsidy_receivable += subsidy_receivable
                    total_enrollment_and_tuition += enrollment_and_tuition
                    total_selection_contest += selection_contest
                    total_incorporation_and_revalidation += incorporation_and_revalidation
                    total_extraordinary_income += extraordinary_income
                    total_patrimonial_income += patrimonial_income
                    total_financial_products += financial_products
                    master_total_1 += total_1
                    total_nomina += nomina
                    total_suppliers += suppliers
                    total_other_benefits += other_benefits
                    total_major_maintenance_fund += major_maintenance_fund
                    total_FIF_funds += FIF_funds
                    master_total_2 += total_2
                         
                    lines.append({
                        'id': 'hierarchy1_' + month_dict.get('year','')+str(month_dict.get('month','')),
                        'name': self.get_month_name(month_dict.get('month',0)),
                        'columns': [
                                    self._format({'name': subsidy},figure_type='float'),
                                    self._format({'name': subsidy_receivable},figure_type='float'),
                                    self._format({'name': enrollment_and_tuition},figure_type='float'),
                                    self._format({'name': selection_contest},figure_type='float'),
                                    self._format({'name': incorporation_and_revalidation},figure_type='float'),
                                    self._format({'name': extraordinary_income},figure_type='float'),
                                    self._format({'name': patrimonial_income},figure_type='float'),
                                    self._format({'name': financial_products},figure_type='float'),
                                    self._format({'name': total_1},figure_type='float'),
                                    self._format({'name': nomina},figure_type='float'),
                                    self._format({'name': suppliers},figure_type='float'),
                                    self._format({'name': other_benefits},figure_type='float'),
                                    self._format({'name': major_maintenance_fund},figure_type='float'),
                                    self._format({'name': FIF_funds},figure_type='float'),
                                    self._format({'name': total_2},figure_type='float'),
                                    ],
                        'level': 3,
                        'unfoldable': False,
                        'unfolded': True,
                    })
        

        if lines:
            lines.append({
                'id': 'hierarchy1_' + month_dict.get('year','')+str(month_dict.get('month','')),
                'name': 'SUMAS',
                'columns': [
                            self._format({'name': total_subsidy},figure_type='float'),
                            self._format({'name': total_subsidy_receivable},figure_type='float'),
                            self._format({'name': total_enrollment_and_tuition},figure_type='float'),
                            self._format({'name': total_selection_contest},figure_type='float'),
                            self._format({'name': total_incorporation_and_revalidation},figure_type='float'),
                            self._format({'name': total_extraordinary_income},figure_type='float'),
                            self._format({'name': total_patrimonial_income},figure_type='float'),
                            self._format({'name': total_financial_products},figure_type='float'),
                            self._format({'name': master_total_1},figure_type='float'),
                            self._format({'name': total_nomina},figure_type='float'),
                            self._format({'name': total_suppliers},figure_type='float'),
                            self._format({'name': total_other_benefits},figure_type='float'),
                            self._format({'name': total_major_maintenance_fund},figure_type='float'),
                            self._format({'name': total_FIF_funds},figure_type='float'),
                            self._format({'name': master_total_2},figure_type='float'),
                            ],
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
            })
            
        return lines

    def _get_report_name(self):
        return _("Annual Income Report")
    
    @api.model
    def _get_super_columns(self, options):
        date_cols = options.get('date') and [options['date']] or []
        date_cols += (options.get('comparison') or {}).get('periods', [])
        columns = reversed(date_cols)
        return {'columns': columns, 'x_offset': 1, 'merge': 5}


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
        
        #Set the first column width to 50
        sheet.set_column(0, 0,15)
#         sheet.set_column(0, 1,20)
#         sheet.set_column(0, 2,20)
#         sheet.set_column(0, 3,12)
#         sheet.set_column(0, 4,20)
        #sheet.set_row(0, 0,50)
        #sheet.col(0).width = 90 * 20
        super_columns = self._get_super_columns(options)
        #y_offset = bool(super_columns.get('columns')) and 1 or 0
        #sheet.write(y_offset, 0,'', title_style)
        y_offset = 0
        col = 0
        
        sheet.merge_range(y_offset, col, 6, col, '')
        if self.env.user and self.env.user.company_id and self.env.user.company_id.header_logo:
            filename = 'logo.png'
            image_data = io.BytesIO(base64.standard_b64decode(self.env.user.company_id.header_logo))
            sheet.insert_image(0,0, filename, {'image_data': image_data,'x_offset':8,'y_offset':3,'x_scale':0.47,'y_scale':0.6})
        
        col += 1
        header_title = '''PATRONATO UNIVERSITARIO\nTESORERÍA\nDIRECCIÓN GENERAL DE FINANZAS\nPRONÓSTICO DE INGRESOS/EGRESOS 2020\n(Miles de pesos)'''
        sheet.merge_range(y_offset, col, 6, col+14, header_title,super_col_style)
        y_offset += 7
#         col=1
#         currect_time_msg = "Fecha y hora de impresión: "
#         currect_time_msg += datetime.today().strftime('%d/%m/%Y %H:%M')
#         sheet.merge_range(y_offset, col, y_offset, col+3, currect_time_msg,currect_date_style)
#         y_offset += 1
        
        # Todo in master: Try to put this logic elsewhere
#         x = super_columns.get('x_offset', 0)
#         for super_col in super_columns.get('columns', []):
#             cell_content = super_col.get('string', '').replace('<br/>', ' ').replace('&nbsp;', ' ')
#             x_merge = super_columns.get('merge')
#             if x_merge and x_merge > 1:
#                 sheet.merge_range(0, x, 0, x + (x_merge - 1), cell_content, super_col_style)
#                 x += x_merge
#             else:
#                 sheet.write(0, x, cell_content, super_col_style)
#                 x += 1
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
            header = self.env['ir.actions.report'].render_template("jt_income.external_layout_income_annual_report", values=rcontext)
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
        currency_list = 'Moneda : '
        currency_name = False
        for select_curreny in options.get('currency'):
            if select_curreny.get('selected',False)==True:
                if currency_name:
                    currency_name += ',' 
                    currency_name+=select_curreny.get('name','')
                else:
                    currency_name=select_curreny.get('name','')
        if currency_name:
            currency_list += currency_name
            
        report = {'name':currency_list}
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
