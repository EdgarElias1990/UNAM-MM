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
from odoo import models, fields, api, _,tools
from datetime import datetime, timedelta

class IncomeBYItemReportWizard(models.TransientModel):
    _name = 'income.by.item.report.wizard'
    _description = 'IncomeBYItemReportWizard'

    currency_id = fields.Many2one(
        'res.currency', "Currency")

    filter_date = fields.Selection([
        ('this_year', 'This Financial Year'),
        ('custom', 'Custom'),
    ],default="this_year")
    
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    @api.onchange('filter_date')
    def onchange_filter(self):
        if self.filter_date:
            date = datetime.now()
            filter_date = self.filter_date
            if filter_date == 'this_year':
                self.start_date = date.replace(month=1, day=1)
                self.end_date = date.replace(month=12, day=31)

    def generate_reports(self):

        list_ids = []
        currency_list = []
        year_list_tuple = range(self.start_date.year, self.end_date.year+1)
        year_list = []
        
        start_year = str(self.start_date.year)
        end_year = str(self.end_date.year)

        start_year_month = self.start_date.month
        end_year_month = self.end_date.month
        
        for y in year_list_tuple:
            year_list.append(str(y))
        currency_name = ''    
        if self.currency_id:
            currency_list.append(self.currency_id.id)
            currency_name = self.currency_id.name
        else:
            currency_ids = self.env['res.currency'].search([])
            currency_list = currency_ids.ids
        
        self.env.cr.execute('''
                select max(am.id) as id,
                Cast((extract(year from am.invoice_date)) as Text) as year,
                Cast((extract(month from am.invoice_date)) as Integer) as month,
                sum(case when am.type_of_revenue_collection = 'dgoae_trades' then abs(am.amount_untaxed_signed) else 0 end) enrollment_and_tuition,
                sum(case when am.type_of_revenue_collection = 'dgae_ref' and am.sub_origin_resource_name in ('Applicants','Aspirantes') then abs(am.amount_untaxed_signed) else 0 end) selection_contest,
                sum(case when am.income_type = 'own' and am.sub_origin_resource_name in ('Incorporation and revalidation of studies','Incorporación y revalidación de estudios') then abs(am.amount_untaxed_signed) else 0 end) incorporation_and_revalidation,
                sum(case when am.type_of_revenue_collection = 'billing' and am.income_type = 'extra' and am.sub_origin_resource_name not in ('Financial Products','Productos financieros') then abs(am.amount_untaxed_signed) else 0 end) extraordinary_income,
                sum(case when am.income_type = 'own' and am.sub_origin_resource_name in ('Patrimonial income','Ingresos patrimoniales') then abs(am.amount_untaxed_signed) else 0 end) patrimonial_income,
                sum(case when am.income_type = 'extra' and am.sub_origin_resource_name  in ('Financial Products','Productos financieros') then abs(am.amount_untaxed_signed) else 0 end) financial_products,
                sum(case when am.is_payroll_payment_request = True and am.payment_state='for_payment_procedure' then abs(am.amount_untaxed_signed) else 0 end) nomina,
                sum(case when am.is_payment_request = True and am.payment_state='for_payment_procedure' then abs(am.amount_untaxed_signed) else 0 end) suppliers,
                0 as major_maintenance_fund,
                0 as fif_funds,
                sum(case when am.is_different_payroll_request = True and am.payment_state='for_payment_procedure' then abs(am.amount_untaxed_signed) else 0 end) as other_benefits
                from account_move am
                where am.state='posted' and am.currency_id in %s 
                and am.invoice_date >= %s and am.invoice_date <= %s and am.invoice_date IS NOT NULL
                group by year,month
                ''' ,(tuple(currency_list),self.start_date,self.end_date))
        
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
                                                        

                    
        for year in data_dict:
            mont_dict = data_dict.get(year) 
            for month in mont_dict:
                month_dict = mont_dict.get(month)
                vals = {
                    'year': month_dict.get('year'),
                    'month' : month_dict.get('month'),
                    'enrollment_and_tuition' : month_dict.get('enrollment_and_tuition',0.0)/1000,
                    'selection_contest' : month_dict.get('selection_contest',0.0)/1000,
                    'incorporation_and_revalidation' : month_dict.get('incorporation_and_revalidation',0.0)/1000,
                    'extraordinary_income' : month_dict.get('extraordinary_income',0.0)/1000,
                    'patrimonial_income' : month_dict.get('patrimonial_income',0.0)/1000,
                    'financial_products' : month_dict.get('financial_products',0.0)/1000,
                    'nomina' : month_dict.get('nomina',0.0)/1000,
                    'suppliers' : month_dict.get('suppliers',0.0)/1000,
                    'major_maintenance_fund' : month_dict.get('major_maintenance_fund',0.0)/1000,
                    'fif_funds' : month_dict.get('fif_funds',0.0)/1000,
                    'other_benefits' : month_dict.get('other_benefits',0.0)/1000,
                    'subsidy_2020' : month_dict.get('subsidy_2020',0.0)/1000,
                    'subsidy_receivable' : month_dict.get('subsidy_receivable',0.0)/1000,
                    'currency_name':currency_name,
                    }             
                rec = self.env['income.by.item.report.data'].create(vals)
                list_ids.append(rec.id)
                
        return {
            'name': 'Annual Income Report',
            'view_type': 'form',
            'view_mode': 'list',
            'view_id': False,
            'res_model': 'income.by.item.report.data',
            'domain': [('id','in',list_ids)],
            'type': 'ir.actions.act_window',
            'context' : {'search_default_year':1}
        }
        
class IncomeBYItemReportData(models.TransientModel):
    _name = 'income.by.item.report.data'
    _description = 'IncomeBYItemReportData'
    _order = 'year,month'
    
    def get_month_name(self):
        for rec in self:
            month_name = ''
            if rec.month:
                if self.env.user.lang == 'es_MX':
                    if rec.month==1:
                        month_name = 'Enero'
                    elif rec.month==2:
                        month_name = 'Febrero'
                    elif rec.month==3:
                        month_name = 'Marzo'
                    elif rec.month==4:
                        month_name = 'Abril'
                    elif rec.month==5:
                        month_name = 'Mayo'
                    elif rec.month==6:
                        month_name = 'Junio'
                    elif rec.month==7:
                        month_name = 'Julio'
                    elif rec.month==8:
                        month_name = 'Agosto'
                    elif rec.month==9:
                        month_name = 'Septiembre'
                    elif rec.month==10:
                        month_name = 'Octubre'
                    elif rec.month==11:
                        month_name = 'Noviembre'
                    elif rec.month==12:
                        month_name = 'Diciembre'
                else:
                    if rec.month==1:
                        month_name = 'January'
                    elif rec.month==2:
                        month_name = 'February'
                    elif rec.month==3:
                        month_name = 'March'
                    elif rec.month==4:
                        month_name = 'April'
                    elif rec.month==5:
                        month_name = 'May'
                    elif rec.month==6:
                        month_name = 'June'
                    elif rec.month==7:
                        month_name = 'July'
                    elif rec.month==8:
                        month_name = 'August'
                    elif rec.month==9:
                        month_name = 'September'
                    elif rec.month==10:
                        month_name = 'October'
                    elif rec.month==11:
                        month_name = 'November'
                    elif rec.month==12:
                        month_name = 'December'
                        
            rec.month_name = month_name
                    
    year = fields.Char('Year')
    month = fields.Integer('Month No')
    month_name = fields.Char(compute="get_month_name",string='Month')
    currency_name = fields.Char("Currency")
    subsidy_2020 = fields.Float('Subsidy 2020')
    subsidy_receivable = fields.Float('Subsidy Receivable')
    enrollment_and_tuition = fields.Float('Enrollment And Tuition')
    selection_contest = fields.Float("Selection Contest")
    incorporation_and_revalidation = fields.Float("Incorporation And Revalidation")
    extraordinary_income = fields.Float("Extraordinary Income")
    patrimonial_income = fields.Float("Patrimonial Income")
    financial_products = fields.Float("Financial Products")
    total_other_income = fields.Float(string="Total",compute="get_total_other_income")
    nomina = fields.Float("Nomina")
    suppliers = fields.Float("Suppliers")
    other_benefits = fields.Float("Other Benefits")
    major_maintenance_fund = fields.Float("Major Maintenance Fund")
    fif_funds = fields.Float("FIF Funds")
    total_other_expense = fields.Float(string="Total",compute="get_total_other_expense")
       
    def get_total_other_income(self):
        for rec in self:
            rec.total_other_income = rec.enrollment_and_tuition + rec.selection_contest+rec.incorporation_and_revalidation+rec.extraordinary_income+rec.patrimonial_income+rec.financial_products

    def get_total_other_expense(self):
        for rec in self:
            rec.total_other_expense = rec.major_maintenance_fund + rec.fif_funds+rec.nomina+rec.suppliers+rec.other_benefits


class IncomeByItemMonthReport(models.Model):
    
    _name = 'income.by.item.month.report'
    _description = 'Income By Item Month Report'
    _order = 'year,month'
    _auto = False

    
    year = fields.Char('Year')
    month = fields.Integer('Month No')
#    month_name = fields.Char('Month')
    enrollment_and_tuition = fields.Float('Enrollment And Tuition')
    selection_contest = fields.Float("Selection Contest")
    incorporation_and_revalidation = fields.Float("Incorporation And Revalidation")
    extraordinary_income = fields.Float("Extraordinary Income")
    patrimonial_income = fields.Float("Patrimonial Income")
    financial_products = fields.Float("Financial Products")
    total_other_income = fields.Float(string="Total",compute="get_total_other_income")
    nomina = fields.Float("Nomina")
    suppliers = fields.Float("Suppliers")
    other_benefits = fields.Float("Other Benefits")
    major_maintenance_fund = fields.Float("Major Maintenance Fund")
    fif_funds = fields.Float("FIF Funds")
    total_other_expense = fields.Float(string="Total",compute="get_total_other_expense")
       
    def get_total_other_income(self):
        for rec in self:
            rec.total_other_income = rec.enrollment_and_tuition + rec.selection_contest+rec.incorporation_and_revalidation+rec.extraordinary_income+rec.patrimonial_income+rec.financial_products

    def get_total_other_expense(self):
        for rec in self:
            rec.total_other_expense = rec.major_maintenance_fund + rec.fif_funds+rec.nomina+rec.suppliers+rec.other_benefits

#TO_CHAR(TO_DATE((extract(month from am.date))::text,'MM'),'Month') as month_name,
            
    def init(self):
        tools.drop_view_if_exists(self.env.cr,self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
                select max(am.id) as id,
                Cast((extract(year from am.invoice_date)) as Text) as year,
                (extract(month from am.invoice_date)) as month,
                sum(case when am.type_of_revenue_collection = 'dgoae_trades' then abs(am.amount_untaxed_signed) else 0 end) enrollment_and_tuition,
                sum(case when am.type_of_revenue_collection = 'dgae_ref' and am.sub_origin_resource_name in ('Applicants','Aspirantes') then abs(am.amount_untaxed_signed) else 0 end) selection_contest,
                sum(case when am.income_type = 'own' and am.sub_origin_resource_name in ('Incorporation and revalidation of studies','Incorporación y revalidación de estudios') then abs(am.amount_untaxed_signed) else 0 end) incorporation_and_revalidation,
                sum(case when am.type_of_revenue_collection = 'deposit_cer' and am.income_type = 'extra' and am.sub_origin_resource_name not in ('Financial Products','Productos financieros') then abs(am.amount_untaxed_signed) else 0 end) extraordinary_income,
                sum(case when am.income_type = 'own' and am.sub_origin_resource_name in ('Patrimonial income','Ingresos patrimoniales') then abs(am.amount_untaxed_signed) else 0 end) patrimonial_income,
                sum(case when am.income_type = 'extra' and am.sub_origin_resource_name  in ('Financial Products','Productos financieros') then abs(am.amount_untaxed_signed) else 0 end) financial_products,
                sum(case when am.is_payroll_payment_request = True and am.payment_state='for_payment_procedure' then abs(am.amount_untaxed_signed) else 0 end) nomina,
                sum(case when am.is_payment_request = True and am.payment_state='for_payment_procedure' then abs(am.amount_untaxed_signed) else 0 end) suppliers,
                0 as major_maintenance_fund,
                0 as fif_funds,
                0 as other_benefits
                from account_move am
                where am.state='posted' 
                group by year,month
                            )'''% (self._table,) 
        )    

