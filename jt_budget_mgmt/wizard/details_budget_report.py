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
from odoo import models, fields, api, _
from datetime import datetime, timedelta
import calendar
from xlrd import *
import xlwt
import base64
from io import BytesIO
import math
from odoo.exceptions import UserError


class DetailsBudgetSummaryReport(models.TransientModel):

    _name = 'details.budget.summary.report'
    _description = 'Details Budget Summary Report'

    state = fields.Selection([('draft', 'Draft'), ('request', 'Request'),
                              ('download', 'Download')], default='draft')

    # Date period related fields
    filter_date = fields.Selection([
        ('this_month', 'This Month'),
        ('this_quarter', 'This Quarter'),
        ('this_year', 'This Financial Year'),
        ('last_month', 'Last Month'),
        ('last_quarter', 'Last Quarter'),
        ('last_year', 'Last Financial Year'),
        ('custom', 'Custom'),
    ])

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    name = fields.Char("Name")
    report_file = fields.Binary("Download Report", filters='.xls')

               
    @api.onchange('filter_date')
    def onchange_filter(self):
        if self.filter_date:
            date = datetime.now()
            filter_date = self.filter_date
            if filter_date == 'this_month':
                self.start_date = date.replace(day=1)
                self.end_date = date.replace(
                    day=calendar.monthrange(date.year, date.month)[1])
            elif filter_date == 'this_quarter':
                month = date.month
                if month >= 1 and month <= 3:
                    self.start_date = date.replace(month=1, day=1)
                    self.end_date = date.replace(month=3, day=31)
                elif month >= 4 and month <= 6:
                    self.start_date = date.replace(month=4, day=1)
                    self.end_date = date.replace(month=6, day=30)
                elif month >= 7 and month <= 9:
                    self.start_date = date.replace(month=7, day=1)
                    self.end_date = date.replace(month=9, day=30)
                else:
                    self.start_date = date.replace(month=10, day=1)
                    self.end_date = date.replace(month=12, day=31)
            elif filter_date == 'this_year':
                self.start_date = date.replace(month=1, day=1)
                self.end_date = date.replace(month=12, day=31)
            elif filter_date == 'last_month':
                today = datetime.today()
                first = today.replace(day=1)
                last_month_date = first - timedelta(days=1)
                last_month = last_month_date.month
                if last_month == 12:
                    year = date.year - 1
                    self.start_date = date.replace(
                        day=1, month=last_month, year=year)
                    self.end_date = date.replace(day=calendar.monthrange(date.year, last_month)[1], month=last_month,
                                                 year=year)
                else:
                    self.start_date = date.replace(day=1, month=last_month)
                    self.end_date = date.replace(day=calendar.monthrange(
                        date.year, last_month)[1], month=last_month)
            elif filter_date == 'last_quarter':
                month = date.month
                year = date.year
                if month >= 1 and month <= 3:
                    self.start_date = date.replace(month=1, day=1, year=year)
                    self.end_date = date.replace(month=12, day=31, year=year)
                elif month >= 4 and month <= 6:
                    self.start_date = date.replace(month=1, day=1)
                    self.end_date = date.replace(month=3, day=31)
                elif month >= 7 and month <= 9:
                    self.start_date = date.replace(month=4, day=1)
                    self.end_date = date.replace(month=6, day=30)
                else:
                    self.start_date = date.replace(month=7, day=1)
                    self.end_date = date.replace(month=9, day=30)
            elif filter_date == 'last_year':
                year = date.year - 1
                self.start_date = date.replace(month=1, day=1, year=year)
                self.end_date = date.replace(month=12, day=31, year=year)

    def add_report_header(self,row,col,header_style,ws1):
        if self.env.user.lang == 'es_MX':
            ws1.write(row, col, 'AÑO', header_style)
            col+=1
            ws1.write(row, col, 'Programa', header_style)
            col+=1
            ws1.write(row, col, 'Subprograma', header_style)
            col+=1
            ws1.write(row, col, 'Dependencia', header_style)
            col+=1
            ws1.write(row, col, 'Subdependencia', header_style)
            col+=1
            ws1.write(row, col, 'Partida de Gasto', header_style)
            col+=1
            ws1.write(row, col, 'Dígito Verificador', header_style)
            col+=1
            ws1.write(row, col, 'Origen del Recurso', header_style)
            col+=1
            ws1.write(row, col, 'Actividad Institucional', header_style)
            col+=1
            ws1.write(row, col, 'Conversion de Programa Presupuestario', header_style)
            col+=1
            ws1.write(row, col, 'Conversión Con Partida (CONPA)', header_style)
            col+=1
            ws1.write(row, col, 'Tipo de Gasto', header_style)
            col+=1
            ws1.write(row, col, 'Ubicación Geográfica', header_style)
            col+=1
            ws1.write(row, col, 'Clave Cartera', header_style)
            col+=1
            ws1.write(row, col, 'Tipo de Proyecto', header_style)
            col+=1
            ws1.write(row, col, 'Número de Proyecto', header_style)
            col+=1
            ws1.write(row, col, 'Etapa', header_style)
            col+=1
            ws1.write(row, col, 'Tipo de Convenio', header_style)
            col+=1
            ws1.write(row, col, 'Número de Convenio', header_style)
            col+=1
            #==== 2nd section ===#
            ws1.write(row, col, 'Autorizado Anual', header_style)
            col+=1
            ws1.write(row, col, 'Aut_1_Trim', header_style)
            col+=1
            ws1.write(row, col, 'Aut_2_Trim', header_style)
            col+=1
            ws1.write(row, col, 'Aut_3_Trim', header_style)
            col+=1
            ws1.write(row, col, 'Aut_4_Trim', header_style)
            col+=1
            #=====3rd section====#
            ws1.write(row, col, 'Ampliación Anual', header_style)
            col+=1
            ws1.write(row, col, 'Amp_1_Trim', header_style)
            col+=1
            ws1.write(row, col, 'Amp_2_Trim', header_style)
            col+=1
            ws1.write(row, col, 'Amp_3_Trim', header_style)
            col+=1
            ws1.write(row, col, 'Amp_4_Trim', header_style)
            col+=1                
            #=======4th section======#
            ws1.write(row, col, 'Reducción Anual', header_style)
            col+=1
            ws1.write(row, col, 'Red_1_Trim', header_style)
            col+=1
            ws1.write(row, col, 'Red_2_Trim', header_style)
            col+=1
            ws1.write(row, col, 'Red_3_Trim', header_style)
            col+=1
            ws1.write(row, col, 'Red_4_Trim', header_style)
            col+=1                  
            #=== 5th Section ====#
            ws1.write(row, col, 'Modificado Anual', header_style)
            col+=1
            ws1.write(row, col, 'Mod_1_Trim', header_style)
            col+=1
            ws1.write(row, col, 'Mod_2_Trim', header_style)
            col+=1
            ws1.write(row, col, 'Mod_3_Trim', header_style)
            col+=1
            ws1.write(row, col, 'Mod_4_Trim', header_style)
            col+=1                  
            
            #=== 6th section ====#
            ws1.write(row, col, 'Ejercido Anual', header_style)
            col+=1
            ws1.write(row, col, 'Ejer_ene', header_style)
            col+=1
            ws1.write(row, col, 'Ejer_feb', header_style)
            col+=1
            ws1.write(row, col, 'Ejer_mar', header_style)
            col+=1
            ws1.write(row, col, 'Ejer_abr', header_style)
            col+=1
            ws1.write(row, col, 'Ejer_may', header_style)
            col+=1
            ws1.write(row, col, 'Ejer_jun', header_style)
            col+=1
            ws1.write(row, col, 'Ejer_jul', header_style)
            col+=1
            ws1.write(row, col, 'Ejer_ago', header_style)
            col+=1
            ws1.write(row, col, 'Ejer_sep', header_style)
            col+=1
            ws1.write(row, col, 'Ejer_oct', header_style)
            col+=1
            ws1.write(row, col, 'Ejer_nov', header_style)
            col+=1
            ws1.write(row, col, 'Ejer_dic', header_style)
            col+=1
            ws1.write(row, col, 'Disponible_Anual', header_style)
            col += 1
            row+=1
        else:
            #=== 1st section ====#
            ws1.write(row, col, 'Year', header_style)
            col+=1
            ws1.write(row, col, 'Program', header_style)
            col+=1
            ws1.write(row, col, 'Sub Program', header_style)
            col+=1
            ws1.write(row, col, 'Dependency', header_style)
            col+=1
            ws1.write(row, col, 'Sub Dependency', header_style)
            col+=1
            ws1.write(row, col, 'Expenditure Item', header_style)
            col+=1
            ws1.write(row, col, 'Check Digit', header_style)
            col+=1
            ws1.write(row, col, 'Source of Resource', header_style)
            col+=1
            ws1.write(row, col, 'Institutional Activity', header_style)
            col+=1
            ws1.write(row, col, 'Conversion of Budgetary Program', header_style)
            col+=1
            ws1.write(row, col, 'SHCP items', header_style)
            col+=1
            ws1.write(row, col, 'Type of Expenditure', header_style)
            col+=1
            ws1.write(row, col, 'Geographic Location', header_style)
            col+=1
            ws1.write(row, col, 'Wallet Key', header_style)
            col+=1
            ws1.write(row, col, 'Type of Project', header_style)
            col+=1
            ws1.write(row, col, 'Project Number', header_style)
            col+=1
            ws1.write(row, col, 'Stage', header_style)
            col+=1
            ws1.write(row, col, 'Type of Agreement', header_style)
            col+=1
            ws1.write(row, col, 'Agreement Number', header_style)
            col+=1
            #==== 2nd section ===#
            ws1.write(row, col, 'Annual authorized', header_style)
            col+=1
            ws1.write(row, col, 'Authorized 1st quarter', header_style)
            col+=1
            ws1.write(row, col, 'Authorized 2nd quarter', header_style)
            col+=1
            ws1.write(row, col, 'Authorized 3rd quarter', header_style)
            col+=1
            ws1.write(row, col, 'Authorized 4th quarter', header_style)
            col+=1
            #=====3rd section====#
            ws1.write(row, col, 'Annual expansion', header_style)
            col+=1
            ws1.write(row, col, '1st quarter expansion', header_style)
            col+=1
            ws1.write(row, col, '2nd quarter expansion', header_style)
            col+=1
            ws1.write(row, col, '3rd quarter expansion', header_style)
            col+=1
            ws1.write(row, col, '4th quarter expansion', header_style)
            col+=1                
            #=======4th section======#
            ws1.write(row, col, 'Annual reduction', header_style)
            col+=1
            ws1.write(row, col, 'Reduction 1st quarter', header_style)
            col+=1
            ws1.write(row, col, 'Reduction 2nd quarter', header_style)
            col+=1
            ws1.write(row, col, 'Reduction 3rd quarter', header_style)
            col+=1
            ws1.write(row, col, 'Reduction 4th quarter', header_style)
            col+=1                  
            #=== 5th Section ====#
            ws1.write(row, col, 'Annual modified', header_style)
            col+=1
            ws1.write(row, col, 'Modified 1st quarter', header_style)
            col+=1
            ws1.write(row, col, 'Modified 2nd quarter', header_style)
            col+=1
            ws1.write(row, col, 'Modified 3rd quarter', header_style)
            col+=1
            ws1.write(row, col, 'Modified 4th quarter', header_style)
            col+=1                  
            
            #=== 6th section ====#
            ws1.write(row, col, 'Exercised annually', header_style)
            col+=1
            ws1.write(row, col, 'Exercised January', header_style)
            col+=1
            ws1.write(row, col, 'Exercised February', header_style)
            col+=1
            ws1.write(row, col, 'Exercised March', header_style)
            col+=1
            ws1.write(row, col, 'Exercised April', header_style)
            col+=1
            ws1.write(row, col, 'Exercised May', header_style)
            col+=1
            ws1.write(row, col, 'Exercised June', header_style)
            col+=1
            ws1.write(row, col, 'Exercised July', header_style)
            col+=1
            ws1.write(row, col, 'Exercised August', header_style)
            col+=1
            ws1.write(row, col, 'Exercised September', header_style)
            col+=1
            ws1.write(row, col, 'Exercised October', header_style)
            col+=1
            ws1.write(row, col, 'Exercised November', header_style)
            col+=1
            ws1.write(row, col, 'Exercised December', header_style)
            col+=1

            row+=1
        return row,col
        
    def request_data(self):
        # Search Programs
        start = self.start_date
        end = self.end_date
        q1_start_date = start.replace(month=1, day=1)
        q1_end_date = end.replace(month=3, day=31)
        q2_start_date = start.replace(month=4, day=1)
        q2_end_date = end.replace(month=6, day=30)
        q3_start_date = start.replace(month=7, day=1)
        q3_end_date = end.replace(month=9, day=30)
        q4_start_date = start.replace(month=10, day=1)
        q4_end_date = end.replace(month=12, day=31)
        
        b_line_obj = self.env['expenditure.budget.line']
                
        domain = [('expenditure_budget_id.state', '=', 'validate'),
             ('start_date', '>=', start), ('end_date', '<=', end),('program_code_id','!=',False)]

        budget_lines = b_line_obj.search(domain)
        program_codes = budget_lines.mapped('program_code_id')
        program_codes_list = [0]
        if program_codes:
            program_codes_list = program_codes.ids
            
        col_query = '''select yc.name as year,pp.key_unam as program,sp.sub_program as sub_program,
                        dp.dependency as dependency,sdp.sub_dependency as sub_dependency,expi.item as exp_name,
                        pc.check_digit as check_digit,ro.key_origin as resource_origin_id,
                        inac.number as institutional_activity_id,shcp.name as conversion_program,dc.federal_part as shcp_item,
                        et.key_expenditure_type as type_of_expenditure,gl.state_key as geographic_location,
                        kw.wallet_password as wallet_key,ptype.project_type_identifier as type_of_project,
                        projectp.number as project_number,si.stage_identifier as stage_identofier,
                        atype.agreement_type as type_of_agreement,atypen.number_agreement as number_of_agreement,
                        
                        (select coalesce(sum(ebl.authorized),0) from expenditure_budget_line ebl where pc.id=ebl.program_code_id and start_date >= %s and end_date <= %s and EXTRACT(MONTH FROM start_date) = 1 and EXTRACT(MONTH FROM end_date) = 12) as assigned,
                        (select coalesce(sum(ebl.assigned),0) from control_assigned_amounts_lines ebl where pc.id=ebl.program_code_id and start_date >= %s and end_date <= %s) as assigned_1st,
                        (select coalesce(sum(ebl.assigned),0) from control_assigned_amounts_lines ebl where pc.id=ebl.program_code_id and start_date >= %s and end_date <= %s) as assigned_2nd,
                        (select coalesce(sum(ebl.assigned),0) from control_assigned_amounts_lines ebl where pc.id=ebl.program_code_id and start_date >= %s and end_date <= %s) as assigned_3rd,
                        (select coalesce(sum(ebl.assigned),0) from control_assigned_amounts_lines ebl where pc.id=ebl.program_code_id and start_date >= %s and end_date <= %s) as assigned_4th,
                        
                        (select (select coalesce(SUM(CASE WHEN al.line_type = %s THEN al.amount ELSE 0 END),0) from adequacies_lines al,adequacies a where a.state=%s and a.adaptation_type = %s and a.date_of_budget_affected >= %s and a.date_of_budget_affected <= %s and al.program = pc.id and a.id=al.adequacies_id)
                        + (select coalesce(SUM(CASE WHEN al.line_type = %s THEN al.amount ELSE 0 END),0) from adequacies_lines al,adequacies a where a.state=%s and a.adaptation_type = %s and a.date_of_liquid_adu >= %s and a.date_of_liquid_adu <= %s and al.program = pc.id and a.id=al.adequacies_id)) as annual_expansion,
                        (select (select coalesce(SUM(CASE WHEN al.line_type = %s THEN al.amount ELSE 0 END),0) from adequacies_lines al,adequacies a where a.state=%s and a.adaptation_type = %s and a.date_of_budget_affected >= %s and a.date_of_budget_affected <= %s and al.program = pc.id and a.id=al.adequacies_id)
                        + (select coalesce(SUM(CASE WHEN al.line_type = %s THEN al.amount ELSE 0 END),0) from adequacies_lines al,adequacies a where a.state=%s and a.adaptation_type = %s and a.date_of_liquid_adu >= %s and a.date_of_liquid_adu <= %s and al.program = pc.id and a.id=al.adequacies_id)) as annual_expansion_q1,  
                        (select (select coalesce(SUM(CASE WHEN al.line_type = %s THEN al.amount ELSE 0 END),0) from adequacies_lines al,adequacies a where a.state=%s and a.adaptation_type = %s and a.date_of_budget_affected >= %s and a.date_of_budget_affected <= %s and al.program = pc.id and a.id=al.adequacies_id)
                        + (select coalesce(SUM(CASE WHEN al.line_type = %s THEN al.amount ELSE 0 END),0) from adequacies_lines al,adequacies a where a.state=%s and a.adaptation_type = %s and a.date_of_liquid_adu >= %s and a.date_of_liquid_adu <= %s and al.program = pc.id and a.id=al.adequacies_id)) as annual_expansion_q2,  
                        (select (select coalesce(SUM(CASE WHEN al.line_type = %s THEN al.amount ELSE 0 END),0) from adequacies_lines al,adequacies a where a.state=%s and a.adaptation_type = %s and a.date_of_budget_affected >= %s and a.date_of_budget_affected <= %s and al.program = pc.id and a.id=al.adequacies_id)
                        + (select coalesce(SUM(CASE WHEN al.line_type = %s THEN al.amount ELSE 0 END),0) from adequacies_lines al,adequacies a where a.state=%s and a.adaptation_type = %s and a.date_of_liquid_adu >= %s and a.date_of_liquid_adu <= %s and al.program = pc.id and a.id=al.adequacies_id)) as annual_expansion_q3,  
                        (select (select coalesce(SUM(CASE WHEN al.line_type = %s THEN al.amount ELSE 0 END),0) from adequacies_lines al,adequacies a where a.state=%s and a.adaptation_type = %s and a.date_of_budget_affected >= %s and a.date_of_budget_affected <= %s and al.program = pc.id and a.id=al.adequacies_id)
                        + (select coalesce(SUM(CASE WHEN al.line_type = %s THEN al.amount ELSE 0 END),0) from adequacies_lines al,adequacies a where a.state=%s and a.adaptation_type = %s and a.date_of_liquid_adu >= %s and a.date_of_liquid_adu <= %s and al.program = pc.id and a.id=al.adequacies_id)) as annual_expansion_q4,  

                        (select coalesce(sum(res.amount), 0) from standardization_line res,standardization ste where ste.id=res.standardization_id and ste.state=%s and res.state=%s and pc.id=res.code_id and res.quarter_start_day = 1 and res.quarter_start_month=1 and res.quarter_end_month=3 and res.quarter_end_day=31) as standardization_expansion_q1,
                        (select coalesce(sum(res.amount), 0) from standardization_line res,standardization ste where ste.id=res.standardization_id and ste.state=%s and res.state=%s and pc.id=res.code_id and res.quarter_start_day = 1 and res.quarter_start_month=4 and res.quarter_end_month=6 and res.quarter_end_day=30) as standardization_expansion_q2,
                        (select coalesce(sum(res.amount), 0) from standardization_line res,standardization ste where ste.id=res.standardization_id and ste.state=%s and res.state=%s and pc.id=res.code_id and res.quarter_start_day = 1 and res.quarter_start_month=7 and res.quarter_end_month=9 and res.quarter_end_day=30) as standardization_expansion_q3,
                        (select coalesce(sum(res.amount), 0) from standardization_line res,standardization ste where ste.id=res.standardization_id and ste.state=%s and res.state=%s and pc.id=res.code_id and res.quarter_start_day = 1 and res.quarter_start_month=10 and res.quarter_end_month=12 and res.quarter_end_day=31) as standardization_expansion_q4,
                        
                        (select (select coalesce(SUM(CASE WHEN al.line_type = %s THEN al.amount ELSE 0 END),0) from adequacies_lines al,adequacies a where a.state=%s and a.adaptation_type = %s and a.date_of_budget_affected >= %s and a.date_of_budget_affected <= %s and al.program = pc.id and a.id=al.adequacies_id)
                        + (select coalesce(SUM(CASE WHEN al.line_type = %s THEN al.amount ELSE 0 END),0) from adequacies_lines al,adequacies a where a.state=%s and a.adaptation_type = %s and a.date_of_liquid_adu >= %s and a.date_of_liquid_adu <= %s and al.program = pc.id and a.id=al.adequacies_id)) as annual_reduction,    
                        (select (select coalesce(SUM(CASE WHEN al.line_type = %s THEN al.amount ELSE 0 END),0) from adequacies_lines al,adequacies a where a.state=%s and a.adaptation_type = %s and a.date_of_budget_affected >= %s and a.date_of_budget_affected <= %s and al.program = pc.id and a.id=al.adequacies_id)
                        + (select coalesce(SUM(CASE WHEN al.line_type = %s THEN al.amount ELSE 0 END),0) from adequacies_lines al,adequacies a where a.state=%s and a.adaptation_type = %s and a.date_of_liquid_adu >= %s and a.date_of_liquid_adu <= %s and al.program = pc.id and a.id=al.adequacies_id)) as annual_reduction_q1,  
                        (select (select coalesce(SUM(CASE WHEN al.line_type = %s THEN al.amount ELSE 0 END),0) from adequacies_lines al,adequacies a where a.state=%s and a.adaptation_type = %s and a.date_of_budget_affected >= %s and a.date_of_budget_affected <= %s and al.program = pc.id and a.id=al.adequacies_id)
                        + (select coalesce(SUM(CASE WHEN al.line_type = %s THEN al.amount ELSE 0 END),0) from adequacies_lines al,adequacies a where a.state=%s and a.adaptation_type = %s and a.date_of_liquid_adu >= %s and a.date_of_liquid_adu <= %s and al.program = pc.id and a.id=al.adequacies_id)) as annual_reduction_q2,  
                        (select (select coalesce(SUM(CASE WHEN al.line_type = %s THEN al.amount ELSE 0 END),0) from adequacies_lines al,adequacies a where a.state=%s and a.adaptation_type = %s and a.date_of_budget_affected >= %s and a.date_of_budget_affected <= %s and al.program = pc.id and a.id=al.adequacies_id)
                        + (select coalesce(SUM(CASE WHEN al.line_type = %s THEN al.amount ELSE 0 END),0) from adequacies_lines al,adequacies a where a.state=%s and a.adaptation_type = %s and a.date_of_liquid_adu >= %s and a.date_of_liquid_adu <= %s and al.program = pc.id and a.id=al.adequacies_id)) as annual_reduction_q3,  
                        (select (select coalesce(SUM(CASE WHEN al.line_type = %s THEN al.amount ELSE 0 END),0) from adequacies_lines al,adequacies a where a.state=%s and a.adaptation_type = %s and a.date_of_budget_affected >= %s and a.date_of_budget_affected <= %s and al.program = pc.id and a.id=al.adequacies_id)
                        + (select coalesce(SUM(CASE WHEN al.line_type = %s THEN al.amount ELSE 0 END),0) from adequacies_lines al,adequacies a where a.state=%s and a.adaptation_type = %s and a.date_of_liquid_adu >= %s and a.date_of_liquid_adu <= %s and al.program = pc.id and a.id=al.adequacies_id)) as annual_reduction_q4,

                        (select coalesce(sum(res.amount), 0) from standardization_line res,standardization ste where ste.id=res.standardization_id and ste.state=%s and res.state=%s and pc.id=res.code_id and res.origin_id_start_day = 1 and res.origin_id_start_month=1 and res.origin_id_end_month=3 and res.origin_id_end_day=31) as standardization_reduction_q1,
                        (select coalesce(sum(res.amount), 0) from standardization_line res,standardization ste where ste.id=res.standardization_id and ste.state=%s and res.state=%s and pc.id=res.code_id and res.origin_id_start_day = 1 and res.origin_id_start_month=4 and res.origin_id_end_month=6 and res.origin_id_end_day=30) as standardization_reduction_q2,
                        (select coalesce(sum(res.amount), 0) from standardization_line res,standardization ste where ste.id=res.standardization_id and ste.state=%s and res.state=%s and pc.id=res.code_id and res.origin_id_start_day = 1 and res.origin_id_start_month=7 and res.origin_id_end_month=9 and res.origin_id_end_day=30) as standardization_reduction_q3,
                        (select coalesce(sum(res.amount), 0) from standardization_line res,standardization ste where ste.id=res.standardization_id and ste.state=%s and res.state=%s and pc.id=res.code_id and res.origin_id_start_day = 1 and res.origin_id_start_month=10 and res.origin_id_end_month=12 and res.origin_id_end_day=31) as standardization_reduction_q4,
                        
                        (select coalesce(sum(ebl.authorized), 0) from expenditure_budget_line ebl where pc.id=ebl.program_code_id and start_date >= %s and end_date <= %s and EXTRACT(MONTH FROM start_date) = 1 and EXTRACT(MONTH FROM end_date) = 12) as authorized,
                        (select coalesce(sum(ebl.authorized), 0) from expenditure_budget_line ebl where pc.id=ebl.program_code_id and start_date >= %s and end_date <= %s) as authorized_q1,
                        (select coalesce(sum(ebl.authorized), 0) from expenditure_budget_line ebl where pc.id=ebl.program_code_id and start_date >= %s and end_date <= %s) as authorized_q2,
                        (select coalesce(sum(ebl.authorized), 0) from expenditure_budget_line ebl where pc.id=ebl.program_code_id and start_date >= %s and end_date <= %s) as authorized_q3,
                        (select coalesce(sum(ebl.authorized), 0) from expenditure_budget_line ebl where pc.id=ebl.program_code_id and start_date >= %s and end_date <= %s) as authorized_q4  
                    '''
        from_query = ''' from program_code pc,expenditure_item exioder,year_configuration yc,program pp,
                         sub_program sp,dependency dp,sub_dependency sdp,expenditure_item expi,
                         resource_origin ro,institutional_activity inac,shcp_code shcp,budget_program_conversion bpc,
                         departure_conversion as dc,expense_type as et,geographic_location as gl,key_wallet as kw,project_type as ptype,
                         project_type as ptypen,project_project projectp,stage as si,agreement_type as atype,
                         agreement_type as atypen
                        '''
        
        where_query = ''' where pc.id in %s and exioder.id=pc.item_id 
                        and exioder.item >= %s and exioder.item <= %s and pc.year=yc.id 
                        and pc.program_id=pp.id and pc.sub_program_id=sp.id and pc.dependency_id=dp.id 
                        and pc.sub_dependency_id=sdp.id and pc.item_id=expi.id  and pc.resource_origin_id=ro.id 
                        and pc.institutional_activity_id=inac.id and pc.budget_program_conversion_id=bpc.id and shcp.id=bpc.shcp 
                        and pc.conversion_item_id=dc.id and pc.expense_type_id=et.id and pc.location_id=gl.id and pc.portfolio_id=kw.id 
                        and pc.project_type_id=ptype.id and pc.project_type_id=ptypen.id and projectp.id=ptypen.project_id 
                        and pc.stage_id=si.id and pc.agreement_type_id=atype.id and pc.agreement_type_id=atypen.id
                        '''
        
        order_by = ''' order by exioder.item_group,pp.key_unam,sp.sub_program,dp.dependency,sdp.sub_dependency,
                        expi.item,pc.check_digit,ro.key_origin,inac.number,shcp.name,dc.federal_part
                        ,et.key_expenditure_type,gl.state_key,kw.wallet_password,ptype.project_type_identifier
                        ,projectp.number,si.stage_identifier,atype.agreement_type,atypen.number_agreement
                    '''
        
        tuple_where_data = [q1_start_date,q4_end_date,q1_start_date,q1_end_date,q2_start_date,q2_end_date,q3_start_date,q3_end_date,q4_start_date,q4_end_date,
                            
                            'increase','accepted','compensated',start,end,'increase','accepted','liquid',start,end,
                            'increase','accepted','compensated',q1_start_date,q1_end_date,'increase','accepted','liquid',q1_start_date,q1_end_date,
                            'increase','accepted','compensated',q2_start_date,q2_end_date,'increase','accepted','liquid',q2_start_date,q2_end_date,
                            'increase','accepted','compensated',q3_start_date,q3_end_date,'increase','accepted','liquid',q3_start_date,q3_end_date,
                            'increase','accepted','compensated',q4_start_date,q4_end_date,'increase','accepted','liquid',q4_start_date,q4_end_date,
                            
                            'confirmed','authorized','confirmed','authorized','confirmed','authorized','confirmed','authorized',
                            
                            'decrease','accepted','compensated',start,end,'decrease','accepted','liquid',start,end,
                            'decrease','accepted','compensated',q1_start_date,q1_end_date,'decrease','accepted','liquid',q1_start_date,q1_end_date,
                            'decrease','accepted','compensated',q2_start_date,q2_end_date,'decrease','accepted','liquid',q2_start_date,q2_end_date,
                            'decrease','accepted','compensated',q3_start_date,q3_end_date,'decrease','accepted','liquid',q3_start_date,q3_end_date,
                            'decrease','accepted','compensated',q4_start_date,q4_end_date,'decrease','accepted','liquid',q4_start_date,q4_end_date,
                            
                            'confirmed','authorized','confirmed','authorized','confirmed','authorized','confirmed','authorized',
                            
                            start,end,q1_start_date,q1_end_date,q2_start_date,q2_end_date,q3_start_date,q3_end_date,q4_start_date,q4_end_date,
                            
                            tuple(program_codes_list),'100','999']
        
#         tuple_where_data.append()
#         tuple_where_data.append('100')
#         tuple_where_data.append('999')

        order_by += ',exioder.item'
        sql_query =  col_query +  from_query + where_query + order_by
        self.env.cr.execute(sql_query,tuple(tuple_where_data))
        my_datas = self.env.cr.dictfetchall()

        wb1 = xlwt.Workbook(encoding='utf-8')
        if self.env.user.lang == 'es_MX':
            ws1 = wb1.add_sheet('Reporte Detallado de Presupuesto')
        else:         
            ws1 = wb1.add_sheet('Details Budget Report')
        fp = BytesIO()
        
        #if my_datas:
        header_style = xlwt.easyxf('font: bold 1')
        float_sytle = xlwt.easyxf(num_format_str = '$#,##0.00')
        #total_style = xlwt.easyxf('num_format_str :0.00;' 'font: bold 1;' )

        ezxf = xlwt.easyxf
        total_style = ezxf(
            'font: italic true; pattern: pattern solid, fore_colour grey25',num_format_str='$#,##0.00')
#             ws1.set_panes_frozen(True)
#             ws1.set_horz_split_pos(1) 
#             ws1.set_vert_split_pos(18) 
        row = 0
        col = 0
        if self.env.user.lang == 'es_MX':
            ws1.write_merge(row, row,col,col+19, 'Reporte Detallado de Presupuesto',header_style)
        else:
            ws1.write_merge(row, row,col,col+19, 'Details Budget Report',header_style)
        
        row+=1
        col = 0
        row,col = self.add_report_header(row,col,header_style,ws1)
        total_assigned = 0
        total_assigned_1st = 0
        total_assigned_2nd = 0
        total_assigned_3rd = 0
        total_assigned_4th = 0
        
        total_annual_expansion = 0
        total_annual_expansion_q1 = 0
        total_annual_expansion_q2 = 0
        total_annual_expansion_q3 = 0
        total_annual_expansion_q4 = 0
        
        total_annual_reduction = 0
        total_annual_reduction_q1 = 0
        total_annual_reduction_q2 = 0
        total_annual_reduction_q3 = 0
        total_annual_reduction_q4 = 0
        
        total_authorized = 0
        total_authorized_q1 = 0
        total_authorized_q2 = 0
        total_authorized_q3 = 0
        total_authorized_q4 = 0
        proramti = ''
        buspago = self.env['account.move'].search([('payment_state', '=', 'for_payment_procedure'), ('date_approval_request', '>=', start), ('date_approval_request', '<=', end)])
        
        sumatotal = 0
        sumen = 0
        sumfe = 0
        summa = 0
        sumab = 0
        summay = 0
        sumjun = 0
        sumjul = 0
        sumag = 0
        sumse = 0
        sumoc = 0
        sumno = 0
        sumdi = 0

        sumatotalt = 0
        sument = 0
        sumfet = 0
        summat = 0
        sumabt = 0
        summayt = 0
        sumjunt = 0
        sumjult = 0
        sumagt = 0
        sumset = 0
        sumoct = 0
        sumnot = 0
        sumdit = 0
        verli=0
        for data in my_datas:
            
            #=== 1st section ====#
            col = 0
            ws1.write(row, col, data.get('year'))
            col+=1
            ws1.write(row, col, data.get('program'))
            col+=1
            ws1.write(row, col, data.get('sub_program'))
            col+=1
            ws1.write(row, col, data.get('dependency'))
            col+=1
            ws1.write(row, col, data.get('sub_dependency'))
            col+=1
            ws1.write(row, col, data.get('exp_name'))
            col+=1
            ws1.write(row, col, data.get('check_digit'))
            col+=1
            ws1.write(row, col, data.get('resource_origin_id'))
            col+=1
            ws1.write(row, col, data.get('institutional_activity_id'))
            col+=1
            ws1.write(row, col, data.get('conversion_program'))
            col+=1
            ws1.write(row, col, data.get('shcp_item'))
            col+=1
            ws1.write(row, col, data.get('type_of_expenditure'))
            col+=1
            ws1.write(row, col, data.get('geographic_location'))
            col+=1
            ws1.write(row, col, data.get('wallet_key'))
            col+=1
            ws1.write(row, col, data.get('type_of_project'))
            col+=1
            ws1.write(row, col, data.get('project_number'))
            col+=1
            ws1.write(row, col, data.get('stage_identofier'))
            col+=1
            ws1.write(row, col, data.get('type_of_agreement'))
            col+=1
            ws1.write(row, col, data.get('number_of_agreement'))
            col+=1
            proramti = str(data.get('year')) + str(data.get('program')) + str(data.get('sub_program')) + str(data.get('dependency')) + str(data.get('sub_dependency')) + str(data.get('exp_name')) + str(data.get('check_digit')) + str(data.get('resource_origin_id')) + str(data.get('institutional_activity_id')) + str(data.get('conversion_program')) + str(data.get('shcp_item')) + str(data.get('type_of_expenditure')) + str(data.get('geographic_location')) + str(data.get('wallet_key')) + str(data.get('type_of_project')) +  str(data.get('project_number')) + str(data.get('stage_identofier')) + str(data.get('type_of_agreement')) + str(data.get('number_of_agreement'))
            #==== 2nd section ====#
            total_assigned += data.get('assigned')
            ws1.write(row, col, data.get('assigned'),float_sytle)
            col+=1
            total_assigned_1st += data.get('assigned_1st')
            ws1.write(row, col, data.get('assigned_1st'),float_sytle)
            col+=1
            total_assigned_2nd += data.get('assigned_2nd')
            ws1.write(row, col, data.get('assigned_2nd'),float_sytle)
            col+=1
            total_assigned_3rd += data.get('assigned_3rd')
            ws1.write(row, col, data.get('assigned_3rd'),float_sytle)
            col+=1
            total_assigned_4th += data.get('assigned_4th')
            ws1.write(row, col, data.get('assigned_4th'),float_sytle)
            col+=1
            #==== 3rd section ====#
            total_standardization_expansion = data.get('standardization_expansion_q1') + data.get('standardization_expansion_q2')+data.get('standardization_expansion_q3')+data.get('standardization_expansion_q4') 
            total_annual_expansion += data.get('annual_expansion') + total_standardization_expansion
            ws1.write(row, col, data.get('annual_expansion')+total_standardization_expansion,float_sytle)
            col+=1
            total_annual_expansion_q1 += data.get('annual_expansion_q1') + data.get('standardization_expansion_q1')
            ws1.write(row, col, data.get('annual_expansion_q1')+data.get('standardization_expansion_q1') ,float_sytle)
            col+=1
            total_annual_expansion_q2 += data.get('annual_expansion_q2')+data.get('standardization_expansion_q2')
            ws1.write(row, col, data.get('annual_expansion_q2')+data.get('standardization_expansion_q2'),float_sytle)
            col+=1
            total_annual_expansion_q3 += data.get('annual_expansion_q3')+data.get('standardization_expansion_q3')
            ws1.write(row, col, data.get('annual_expansion_q3')+data.get('standardization_expansion_q3'),float_sytle)
            col+=1
            total_annual_expansion_q4 += data.get('annual_expansion_q4')+data.get('standardization_expansion_q4')
            ws1.write(row, col, data.get('annual_expansion_q4')+data.get('standardization_expansion_q4'),float_sytle)
            col+=1

            #==== 4th section ====#
            total_standardization_reduction = data.get('standardization_reduction_q1') + data.get('standardization_reduction_q2') + data.get('standardization_reduction_q3') + data.get('standardization_reduction_q4')
            total_annual_reduction += data.get('annual_reduction') + total_standardization_reduction
            ws1.write(row, col, data.get('annual_reduction')+total_standardization_reduction,float_sytle)
            col+=1
            total_annual_reduction_q1 += data.get('annual_reduction_q1') + data.get('standardization_reduction_q1')
            ws1.write(row, col, data.get('annual_reduction_q1')+data.get('standardization_reduction_q1'),float_sytle)
            col+=1
            total_annual_reduction_q2 += data.get('annual_reduction_q2') + data.get('standardization_reduction_q2')
            ws1.write(row, col, data.get('annual_reduction_q2')+data.get('standardization_reduction_q2'),float_sytle)
            col+=1
            total_annual_reduction_q3 += data.get('annual_reduction_q3') + data.get('standardization_reduction_q3')
            ws1.write(row, col, data.get('annual_reduction_q3') + data.get('standardization_reduction_q3'),float_sytle)
            col+=1
            total_annual_reduction_q4 += data.get('annual_reduction_q4') + data.get('standardization_reduction_q4')
            ws1.write(row, col, data.get('annual_reduction_q4')+data.get('standardization_reduction_q4'),float_sytle)
            col+=1
            
            #==== 5th section ====#
            authorized_q1 = data.get('assigned_1st') + data.get('annual_expansion_q1',0) + data.get('standardization_expansion_q1') - data.get('annual_reduction_q1',0) - data.get('standardization_reduction_q1',0)
            authorized_q2 = data.get('assigned_2nd') + data.get('annual_expansion_q2',0) + data.get('standardization_expansion_q2') - data.get('annual_reduction_q2',0) - data.get('standardization_reduction_q2',0)
            authorized_q3 = data.get('assigned_3rd') + data.get('annual_expansion_q3',0) + data.get('standardization_expansion_q3') - data.get('annual_reduction_q3',0) - data.get('standardization_reduction_q3',0)
            authorized_q4 = data.get('assigned_4th') + data.get('annual_expansion_q4',0) + data.get('standardization_expansion_q4') - data.get('annual_reduction_q4',0) - data.get('standardization_reduction_q4',0)
            authorized = authorized_q1 + authorized_q2 + authorized_q3 + authorized_q4
            total_authorized += authorized
            ws1.write(row, col, authorized,float_sytle)
            col+=1
            total_authorized_q1 += authorized_q1   
            ws1.write(row, col, authorized_q1,float_sytle)
            col+=1
            total_authorized_q2 += authorized_q2   
            ws1.write(row, col, authorized_q2,float_sytle)
            col+=1
            total_authorized_q3 += authorized_q3   
            ws1.write(row, col, authorized_q3,float_sytle)
            col+=1
            total_authorized_q4 += authorized_q4   
            ws1.write(row, col, authorized_q4,float_sytle)
            col+=1
            sumatotal = 0
            sumen = 0
            sumfe = 0
            summa = 0
            sumab = 0
            summay = 0
            sumjun = 0
            sumjul = 0
            sumag = 0
            sumse = 0
            sumoc = 0
            sumno = 0
            sumdi = 0
            for pagosapp in buspago:
                for llpago in pagosapp.invoice_line_ids:
                    if llpago.program_code_id.program_code == proramti:
                        if pagosapp.invoice_date.month == 1:
                            sumatotalt += pagosapp.amount_total
                            sumen = sumen + pagosapp.amount_total
                            sument += pagosapp.amount_total
                            sumatotal = sumatotal + pagosapp.amount_total
                        elif pagosapp.invoice_date.month == 2:
                            sumatotalt += pagosapp.amount_total
                            sumfe = sumfe + pagosapp.amount_total
                            sumfet += pagosapp.amount_total
                            sumatotal = sumatotal + pagosapp.amount_total
                        elif pagosapp.invoice_date.month == 3:
                            sumatotalt += pagosapp.amount_total
                            summa = summa + pagosapp.amount_total
                            summat += pagosapp.amount_total
                            sumatotal = sumatotal + pagosapp.amount_total
                        elif pagosapp.invoice_date.month == 4:
                            sumatotalt += pagosapp.amount_total
                            sumab = sumab + pagosapp.amount_total
                            sumabt += pagosapp.amount_total
                            sumatotal = sumatotal + pagosapp.amount_total
                        elif pagosapp.invoice_date.month == 5:
                            sumatotalt += pagosapp.amount_total
                            summay = summay + pagosapp.amount_total
                            summayt += pagosapp.amount_total
                            sumatotal = sumatotal + pagosapp.amount_total
                        elif pagosapp.invoice_date.month == 6:
                            sumatotalt += pagosapp.amount_total
                            sumjun = sumjun + pagosapp.amount_total
                            sumjunt += pagosapp.amount_total
                            sumatotal = sumatotal + pagosapp.amount_total
                        elif pagosapp.invoice_date.month == 7:
                            sumatotalt += pagosapp.amount_total
                            sumjul = sumjul + pagosapp.amount_total
                            sumjult += pagosapp.amount_total
                            sumatotal = sumatotal + pagosapp.amount_total
                        elif pagosapp.invoice_date.month == 8:
                            sumatotalt += pagosapp.amount_total
                            sumag = sumag + pagosapp.amount_total
                            sumagt += pagosapp.amount_total
                            sumatotal = sumatotal + pagosapp.amount_total
                        elif pagosapp.invoice_date.month == 9:
                            sumatotalt += pagosapp.amount_total
                            sumse = sumse + pagosapp.amount_total
                            sumset += pagosapp.amount_total
                            sumatotal = sumatotal + pagosapp.amount_total
                        elif pagosapp.invoice_date.month == 10:
                            sumatotalt += pagosapp.amount_total
                            sumoc = sumoc + pagosapp.amount_total
                            sumoct += pagosapp.amount_total
                            sumatotal = sumatotal + pagosapp.amount_total
                        elif pagosapp.invoice_date.month == 11:
                            sumatotalt += pagosapp.amount_total
                            sumno = sumno + pagosapp.amount_total
                            sumnot += pagosapp.amount_total
                            sumatotal = sumatotal + pagosapp.amount_total
                        elif pagosapp.invoice_date.month == 12:
                            sumatotalt += pagosapp.amount_total
                            sumatotal = sumatotal + pagosapp.amount_total
                            sumdi = sumdi + pagosapp.amount_total
                            sumdit += pagosapp.amount_total



            #=== 6th section ====#
            ws1.write(row, col, sumatotal,float_sytle)
            col+=1
            ws1.write(row, col, sumen,float_sytle)
            col+=1
            ws1.write(row, col, sumfe,float_sytle)
            col+=1
            ws1.write(row, col, summa,float_sytle)
            col+=1
            ws1.write(row, col, sumab,float_sytle)
            col+=1
            ws1.write(row, col, summay,float_sytle)
            col+=1
            ws1.write(row, col, sumjun,float_sytle)
            col+=1
            ws1.write(row, col, sumjul,float_sytle)
            col+=1
            ws1.write(row, col, sumag,float_sytle)
            col+=1
            ws1.write(row, col, sumse,float_sytle)
            col+=1
            ws1.write(row, col, sumoc,float_sytle)
            col+=1
            ws1.write(row, col, sumno,float_sytle)
            col+=1
            ws1.write(row, col, sumdi,float_sytle)
            col+=1
            ws1.write(row, col,  authorized - sumatotal, float_sytle)
            col += 1

            row+=1
        
        #===== Total=======#
        row+=1
        col=19
        #==== 2nd section ====#
        ws1.write(row, col, total_assigned,total_style)
        col+=1
        ws1.write(row, col, total_assigned_1st,total_style)
        col+=1
        ws1.write(row, col, total_assigned_2nd,total_style)
        col+=1
        ws1.write(row, col, total_assigned_3rd,total_style)
        col+=1
        ws1.write(row, col, total_assigned_4th,total_style)
        col+=1
        #==== 3rd section ====#
        ws1.write(row, col, total_annual_expansion,total_style)
        col+=1
        ws1.write(row, col, total_annual_expansion_q1,total_style)
        col+=1
        ws1.write(row, col, total_annual_expansion_q2,total_style)
        col+=1
        ws1.write(row, col, total_annual_expansion_q3,total_style)
        col+=1
        ws1.write(row, col, total_annual_expansion_q4,total_style)
        col+=1
        #==== 4th section ====#
        ws1.write(row, col, total_annual_reduction,total_style)
        col+=1
        ws1.write(row, col, total_annual_reduction_q1,total_style)
        col+=1
        ws1.write(row, col, total_annual_reduction_q2,total_style)
        col+=1
        ws1.write(row, col, total_annual_reduction_q3,total_style)
        col+=1
        ws1.write(row, col, total_annual_reduction_q4,total_style)
        col+=1
        #==== 5th section ====#
        ws1.write(row, col, total_authorized,total_style)
        col+=1
        ws1.write(row, col, total_authorized_q1,total_style)
        col+=1
        ws1.write(row, col, total_authorized_q2,total_style)
        col+=1
        ws1.write(row, col, total_authorized_q3,total_style)
        col+=1
        ws1.write(row, col, total_authorized_q4,total_style)
        col+=1
        #==== 6th Section =====#
        ws1.write(row, col, sumatotalt, total_style)
        col += 1
        ws1.write(row, col, sument,total_style)
        col+=1
        ws1.write(row, col, sumfet,total_style)
        col+=1
        ws1.write(row, col, summat,total_style)
        col+=1
        ws1.write(row, col, sumabt,total_style)
        col+=1
        ws1.write(row, col, summayt,total_style)
        col+=1
        ws1.write(row, col, sumjunt,total_style)
        col+=1
        ws1.write(row, col, sumjult,total_style)
        col+=1
        ws1.write(row, col, sumagt,total_style)
        col+=1
        ws1.write(row, col, sumset,total_style)
        col+=1
        ws1.write(row, col, sumoct,total_style)
        col+=1
        ws1.write(row, col, sumnot,total_style)
        col+=1
        ws1.write(row, col, sumdit,total_style)
        col+=1

            
        wb1.save(fp)
        out = base64.encodestring(fp.getvalue())
        self.report_file = out
        if self.env.user.lang == 'es_MX':
            self.name = 'reporte_detallado_de_presupuesto.xls'
        else:
            self.name = 'details_budget_report.xls'
        #self.state = 'download'
            
        #=======================#
        attch_obj = self.env['ir.attachment']
        vals = {'name': self.name,
                'datas': out,
                'res_model': 'jt_budget_mgmt.details.budget.summary.report',
                }
        attach_ids = attch_obj.search([
            ('res_model', '=', 'jt_budget_mgmt.details.budget.summary.report')])
        if attach_ids:
            try:
                attach_ids.sudo().unlink()
            except:
                pass
        doc_id = attch_obj.sudo().create(vals)
        
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/%s?download=true' % (doc_id.id),
            'target': 'current',
            'tag': 'close',
        }
        #========================================#
        return {
            'name': _('Report'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'details.budget.summary.report',
            'domain': [],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
        }
