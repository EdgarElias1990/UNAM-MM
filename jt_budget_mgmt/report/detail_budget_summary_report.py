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
from datetime import datetime
from odoo import models, fields, api, _
from odoo.tools.profiler import profile
from odoo.tools.misc import formatLang
import json

class DetailsBudgetSummaryReport(models.AbstractModel):
    _name = "details.budget.summary.report.onscreen"
    _inherit = "account.report"
    _description = "Details Budget Summary"

    filter_journals = None
    filter_multi_company = None
    filter_date = {'mode': 'range', 'filter': 'this_month'}
    filter_all_entries = None
    filter_comparison = None
    filter_journals = None
    filter_analytic = None
    filter_unfold_all = None
    filter_hierarchy = None
    filter_partner = None

    # Custom filters
    filter_line_pages = None
#     filter_budget_control = None
#     filter_program_code_section = None

    def _get_reports_buttons(self):
        return [
            #{'name': _(''), 'sequence': 2, 'action': 'print_pdf', 'file_export_type': _('PDF')},
            {'name': _('Export (XLSX)'), 'sequence': 2, 'action': 'print_xlsx', 'file_export_type': _('XLSX')},
        ]
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
    
#     def _get_templates(self):
#         templates = super(
#             DetailsBudgetSummaryReport, self)._get_templates()
#         templates[
#             'main_table_header_template'] = 'account_reports.main_table_header'
#         templates['main_template'] = 'account_reports.main_template'
#         return templates

    def _get_columns_name(self, options):
        column_list = [
                        {'name': _("Year")},
                        {'name': _("Program Code")},
                        {'name': _("Sub Program")},
                        {'name': _("Dependency")},
                        {'name': _("Sub Dependency")},
                        {'name': _("Expenditure Item")},
                        {'name': _("Check Digit")},
                        {'name': _("Source of Resource")},
                        {'name': _("Institutional Activity")},
                        {'name': _("Conversion of Budgetary Program")},
                        {'name': _("SHCP items")},
                        {'name': _("Type of Expenditure")},
                        {'name': _("Geographic Location")},
                        {'name': _("Wallet Key")},
                        {'name': _("Type of Project")},
                        {'name': _("Project Number")},
                        {'name': _("Stage")},
                        {'name': _("Type of Agreement")},
                        {'name': _("Agreement Number")},
                        
                        {'name': _("Annual authorized")},
                        {'name': _("Authorized 1st quarter")},
                        {'name': _("Authorized 2nd quarter")},
                        {'name': _("Authorized 3rd quarter")},
                        {'name': _("Authorized 4th quarter")},

                        {'name': _("Annual expansion")},
                        {'name': _("1st quarter expansion")},
                        {'name': _("2nd quarter expansion")},
                        {'name': _("3rd quarter expansion")},
                        {'name': _("4th quarter expansion")},
                        
                        {'name': _("Annual reduction")},
                        {'name': _("Reduction 1st quarter")},
                        {'name': _("Reduction 2nd quarter")},
                        {'name': _("Reduction 3rd quarter")},
                        {'name': _("Reduction 4th quarter")},
                        
                        {'name': _("Annual modified")},
                        {'name': _("Modified 1st quarter")},
                        {'name': _("Modified 2nd quarter")},
                        {'name': _("Modified 3rd quarter")},
                        {'name': _("Modified 4th quarter")},
                        
                        {'name': _("Exercised annually")},
                        {'name': _("Exercised January")},
                        {'name': _("Exercised February")},
                        {'name': _("Exercised March")},
                        {'name': _("Exercised April")},
                        {'name': _("Exercised May")},
                        {'name': _("Exercised June")},
                        {'name': _("Exercised July")},
                        {'name': _("Exercised August")},
                        {'name': _("Exercised September")},
                        {'name': _("Exercised October")},
                        {'name': _("Exercised November")},
                        {'name': _("Exercised December")},
                                                
                       ]
        return column_list
    
    @api.model
    def _init_filter_line_pages(self, options, previous_options=None):
        options['line_pages'] = []
        start = datetime.strptime(
            str(options['date'].get('date_from')), '%Y-%m-%d').date()
        end = datetime.strptime(
            options['date'].get('date_to'), '%Y-%m-%d').date()
                    
        budget_lines = self.env['expenditure.budget.line'].search(
            [('expenditure_budget_id.state', '=', 'validate'),('start_date', '>=', start), ('end_date', '<=', end),('program_code_id','!=',False)])
        program_codes = budget_lines.mapped('program_code_id')
        pages = round(len(program_codes) / 3000)
        line_list = []
        for page in range(1, pages + 1):
            line_list.append(page)

        list_labels = self._context.get('lines_data', line_list)
        counter = 1

        if previous_options and previous_options.get('line_pages'):
            line_pages_map = dict((opt['id'], opt['selected'])
                                  for opt in previous_options['line_pages'] if
                                  opt['id'] != 'divider' and 'selected' in opt)
        else:
            line_pages_map = {}

        options['selected_line_pages'] = []
        for label in list_labels:
            options['line_pages'].append({
                'id': str(counter),
                'name': str(label),
                'code': str(label),
                'selected': line_pages_map.get(str(counter)),
            })
            if line_pages_map.get(str(counter)):
                options['selected_line_pages'].append(str(label))
            counter += 1

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

    @api.model
    def _get_lines(self, options, line_id=None):
        lines = []
        start = datetime.strptime(
            str(options['date'].get('date_from')), '%Y-%m-%d').date()
        end = datetime.strptime(
            options['date'].get('date_to'), '%Y-%m-%d').date()

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
                        (select coalesce(sum(ebl.assigned),0) from expenditure_budget_line ebl where pc.id=ebl.program_code_id and start_date >= %s and end_date <= %s) as assigned_1st,
                        (select coalesce(sum(ebl.assigned),0) from expenditure_budget_line ebl where pc.id=ebl.program_code_id and start_date >= %s and end_date <= %s) as assigned_2nd,
                        (select coalesce(sum(ebl.assigned),0) from expenditure_budget_line ebl where pc.id=ebl.program_code_id and start_date >= %s and end_date <= %s) as assigned_3rd,
                        (select coalesce(sum(ebl.assigned),0) from expenditure_budget_line ebl where pc.id=ebl.program_code_id and start_date >= %s and end_date <= %s) as assigned_4th,
                        
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
        
        tuple_where_data = [start,end,q1_start_date,q1_end_date,q2_start_date,q2_end_date,q3_start_date,q3_end_date,q4_start_date,q4_end_date,
                            
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
#        return lines
    
        selected_line_pages = options['selected_line_pages']
        selected_my_data = []
        
        for s in selected_line_pages:
            s = int(s)
            start = (s - 1) * 3000
            end = s * 3000
            
            selected_my_data = selected_my_data + my_datas[start:end]
        #===== 2nd =======    
        total_assign = 0
        total_assigned_1st = 0
        total_assigned_2nd = 0 
        total_assigned_3rd = 0
        total_assigned_4th = 0
        #===== 3nd =======
        total_annual_expansion = 0
        total_annual_expansion_q1 = 0
        total_annual_expansion_q2 = 0
        total_annual_expansion_q3 = 0
        total_annual_expansion_q4 = 0
        #===== 4th =======
        total_annual_reduction = 0
        total_annual_reduction_q1 = 0
        total_annual_reduction_q2 = 0
        total_annual_reduction_q3 = 0
        total_annual_reduction_q4 = 0
        #===== 5th =======
        total_authorized = 0   
        total_authorized_q1 = 0   
        total_authorized_q2 = 0   
        total_authorized_q3 = 0   
        total_authorized_q4 = 0   
        
        if not selected_line_pages:
            selected_my_data = my_datas[:3000]
        for data in selected_my_data:
            #==== 2nd section ====#
            total_assign += data.get('assigned')
            total_assigned_1st += data.get('assigned_1st')
            total_assigned_2nd += data.get('assigned_2nd')
            total_assigned_3rd += data.get('assigned_3rd')
            total_assigned_4th += data.get('assigned_4th')
            
            total_standardization_expansion = data.get('standardization_expansion_q1') + data.get('standardization_expansion_q2')+data.get('standardization_expansion_q3')+data.get('standardization_expansion_q4')
            #==== 3nd section ====#
            total_annual_expansion += data.get('annual_expansion')+total_standardization_expansion
            total_annual_expansion_q1 += data.get('annual_expansion_q1')+data.get('standardization_expansion_q1')
            total_annual_expansion_q2 += data.get('annual_expansion_q2')+data.get('standardization_expansion_q2')
            total_annual_expansion_q3 += data.get('annual_expansion_q3')+data.get('standardization_expansion_q3')
            total_annual_expansion_q4 += data.get('annual_expansion_q4')+data.get('standardization_expansion_q4')
            #==== 4th section ====#
            total_standardization_reduction = data.get('standardization_reduction_q1') + data.get('standardization_reduction_q2') + data.get('standardization_reduction_q3') + data.get('standardization_reduction_q4')
            total_annual_reduction += data.get('annual_reduction') + total_standardization_reduction
            total_annual_reduction_q1 += data.get('annual_reduction_q1') + data.get('standardization_reduction_q1')
            total_annual_reduction_q2 += data.get('annual_reduction_q2') + data.get('standardization_reduction_q2')
            total_annual_reduction_q3 += data.get('annual_reduction_q3') + data.get('standardization_reduction_q3')
            total_annual_reduction_q4 += data.get('annual_reduction_q4') + data.get('standardization_reduction_q4')

            #==== 5th section ====#
            authorized_q1 = data.get('assigned_1st') + data.get('annual_expansion_q1',0) + data.get('standardization_expansion_q1') - data.get('annual_reduction_q1',0) - data.get('standardization_reduction_q1',0)
            authorized_q2 = data.get('assigned_2nd') + data.get('annual_expansion_q2',0) + data.get('standardization_expansion_q2') - data.get('annual_reduction_q2',0) - data.get('standardization_reduction_q2',0)
            authorized_q3 = data.get('assigned_3rd') + data.get('annual_expansion_q3',0) + data.get('standardization_expansion_q3') - data.get('annual_reduction_q3',0) - data.get('standardization_reduction_q3',0)
            authorized_q4 = data.get('assigned_4th') + data.get('annual_expansion_q4',0) + data.get('standardization_expansion_q4') - data.get('annual_reduction_q4',0) - data.get('standardization_reduction_q4',0)
            authorized = authorized_q1 + authorized_q2 + authorized_q3 + authorized_q4
            total_authorized += authorized   
            total_authorized_q1 += authorized_q1   
            total_authorized_q2 += authorized_q2   
            total_authorized_q3 += authorized_q3   
            total_authorized_q4 += authorized_q4   
            
            lines.append({
                'id': 'hierarchy1',
                'name': data.get('year'),
                'columns': [
                            {'name':data.get('program')},
                            {'name':data.get('sub_program')},
                            {'name':data.get('dependency')},
                            {'name':data.get('sub_dependency')},
                            {'name':data.get('exp_name')},
                            {'name':data.get('check_digit')},
                            {'name':data.get('resource_origin_id')},
                            {'name':data.get('institutional_activity_id')},
                            {'name':data.get('conversion_program')},
                            {'name':data.get('shcp_item')},
                            {'name':data.get('type_of_expenditure')},
                            {'name':data.get('geographic_location')},
                            {'name':data.get('wallet_key')},
                            {'name':data.get('type_of_project')},
                            {'name':data.get('project_number')},
                            {'name':data.get('stage_identofier')},
                            {'name':data.get('type_of_agreement')},
                            {'name':data.get('number_of_agreement')},
                            
                            self._format({'name': data.get('assigned')},figure_type='float'),
                            self._format({'name': data.get('assigned_1st')},figure_type='float'),
                            self._format({'name': data.get('assigned_2nd')},figure_type='float'),
                            self._format({'name': data.get('assigned_3rd')},figure_type='float'),
                            self._format({'name': data.get('assigned_4th')},figure_type='float'),
                            
                            self._format({'name': data.get('annual_expansion')+total_standardization_expansion},figure_type='float'),
                            self._format({'name': data.get('annual_expansion_q1')+data.get('standardization_expansion_q1')},figure_type='float'),
                            self._format({'name': data.get('annual_expansion_q2')+data.get('standardization_expansion_q2')},figure_type='float'),
                            self._format({'name': data.get('annual_expansion_q3')+data.get('standardization_expansion_q3')},figure_type='float'),
                            self._format({'name': data.get('annual_expansion_q4')+data.get('standardization_expansion_q4')},figure_type='float'),
                            
                            self._format({'name': data.get('annual_reduction')+total_standardization_reduction},figure_type='float'),
                            self._format({'name': data.get('annual_reduction_q1')+data.get('standardization_reduction_q1')},figure_type='float'),
                            self._format({'name': data.get('annual_reduction_q2')+data.get('standardization_reduction_q2')},figure_type='float'),
                            self._format({'name': data.get('annual_reduction_q3')+data.get('standardization_reduction_q3')},figure_type='float'),
                            self._format({'name': data.get('annual_reduction_q4')+data.get('standardization_reduction_q4')},figure_type='float'),

                            self._format({'name': authorized},figure_type='float'),
                            self._format({'name': authorized_q1},figure_type='float'),
                            self._format({'name': authorized_q2},figure_type='float'),
                            self._format({'name': authorized_q3},figure_type='float'),
                            self._format({'name': authorized_q4},figure_type='float'),
                            
                            self._format({'name': 0.0},figure_type='float'),
                            self._format({'name': 0.0},figure_type='float'),
                            self._format({'name': 0.0},figure_type='float'),
                            self._format({'name': 0.0},figure_type='float'),
                            self._format({'name': 0.0},figure_type='float'),
                            self._format({'name': 0.0},figure_type='float'),
                            self._format({'name': 0.0},figure_type='float'),
                            self._format({'name': 0.0},figure_type='float'),
                            self._format({'name': 0.0},figure_type='float'),
                            self._format({'name': 0.0},figure_type='float'),
                            self._format({'name': 0.0},figure_type='float'),
                            self._format({'name': 0.0},figure_type='float'),
                            self._format({'name': 0.0},figure_type='float'),

                            
                            ],
                'level': 3,
                'unfoldable': False,
                'unfolded': True,
            })
            
        lines.append({
            'id': 'hierarchy1',
            'name': '',
            'columns': [
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        {'name':''},
                        
                        self._format({'name': total_assign},figure_type='float'),
                        self._format({'name': total_assigned_1st},figure_type='float'),
                        self._format({'name': total_assigned_2nd},figure_type='float'),
                        self._format({'name': total_assigned_3rd},figure_type='float'),
                        self._format({'name': total_assigned_4th},figure_type='float'),
                        
                        self._format({'name': total_annual_expansion},figure_type='float'),
                        self._format({'name': total_annual_expansion_q1},figure_type='float'),
                        self._format({'name': total_annual_expansion_q2},figure_type='float'),
                        self._format({'name': total_annual_expansion_q3},figure_type='float'),
                        self._format({'name': total_annual_expansion_q4},figure_type='float'),

                        self._format({'name': total_annual_reduction},figure_type='float'),
                        self._format({'name': total_annual_reduction_q1},figure_type='float'),
                        self._format({'name': total_annual_reduction_q2},figure_type='float'),
                        self._format({'name': total_annual_reduction_q3},figure_type='float'),
                        self._format({'name': total_annual_reduction_q4},figure_type='float'),

                        self._format({'name': total_authorized},figure_type='float'),
                        self._format({'name': total_authorized_q1},figure_type='float'),
                        self._format({'name': total_authorized_q2},figure_type='float'),
                        self._format({'name': total_authorized_q3},figure_type='float'),
                        self._format({'name': total_authorized_q4},figure_type='float'),

                        self._format({'name': 0.0},figure_type='float'),
                        self._format({'name': 0.0},figure_type='float'),
                        self._format({'name': 0.0},figure_type='float'),
                        self._format({'name': 0.0},figure_type='float'),
                        self._format({'name': 0.0},figure_type='float'),
                        self._format({'name': 0.0},figure_type='float'),
                        self._format({'name': 0.0},figure_type='float'),
                        self._format({'name': 0.0},figure_type='float'),
                        self._format({'name': 0.0},figure_type='float'),
                        self._format({'name': 0.0},figure_type='float'),
                        self._format({'name': 0.0},figure_type='float'),
                        self._format({'name': 0.0},figure_type='float'),
                        self._format({'name': 0.0},figure_type='float'),
                        
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
        })
            
        return lines

    def _get_report_name(self):
        context = self.env.context
        date_report = fields.Date.from_string(context['date_from']) if context.get(
            'date_from') else fields.date.today()
        return '%s_%s_Summary_Report' % (
            date_report.year,
            str(date_report.month).zfill(2))

    
    
    
    
    
