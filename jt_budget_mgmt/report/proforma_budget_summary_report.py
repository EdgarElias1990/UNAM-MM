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

class ProformaBudgetSummaryReport(models.AbstractModel):
    _name = "proforma.budget.summary.report"
    _inherit = "account.report"
    _description = "Proforma Budget Summary"

    filter_journals = None
    filter_multi_company = True
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
    filter_budget_control = None
    filter_program_code_section = None

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
    
    def _get_columns_name(self, options):
        column_list = []
        column_list.append({'name': _("Program Code")})

        # Add program code structure fields
        for column in options['selected_program_fields']:
            column_list.append({'name': _(column)})

        for column in options['selected_budget_control']:
            column_list.append({'name': _(column)})
        return column_list

    @api.model
    def _init_filter_line_pages(self, options, previous_options=None):
        options['line_pages'] = []
        start = datetime.strptime(
            str(options['date'].get('date_from')), '%Y-%m-%d').date()
        end = datetime.strptime(
            options['date'].get('date_to'), '%Y-%m-%d').date()
                    
        budget_lines = self.env['expenditure.budget.line'].search(
            [('expenditure_budget_id.state', '=', 'validate'),('start_date', '>=', start), ('end_date', '<=', end)])
        program_codes = budget_lines.mapped('program_code_id')
        line_list = []
        for page in range(len(program_codes)):
            line_list.append(page)

        options['selected_line_pages'] = []

    @api.model
    def _init_filter_budget_control(self, options, previous_options=None):
        options['budget_control'] = []
        if self.env.user.lang == 'es_MX':
            list_labels = ['Partida de Gasto (PAR)', 'Autorizado', 'Total Asignado Anual', 'Asignado 1er Trimestre',
                           'Asignado 2do Trimestre', 'Asignado 3er Trimestre',
                           'Asignado 4to Trimestre', 'Modificado Anual',
                           'Por Ejercer', 'Comprometido', 'Devengado', 'Ejercido', 'Pagado', 'Disponible']
        else:
            list_labels = ['Expense Item', 'Authorized', 'Assigned Total Annual', 'Assigned 1st Trimester',
                           'Assigned 2nd Trimester', 'Assigned 3rd Trimester',
                           'Assigned 4th Trimester', 'Annual Modified',
                           'Per Exercise', 'Committed', 'Accrued', 'Exercised', 'Paid', 'Available']
        counter = 1

        if previous_options and previous_options.get('budget_control'):
            budget_control_map = dict((opt['id'], opt['selected'])
                                      for opt in previous_options['budget_control'] if
                                      opt['id'] != 'divider' and 'selected' in opt)
        else:
            budget_control_map = {}

        options['selected_budget_control'] = []
        for label in list_labels:
            options['budget_control'].append({
                'id': str(counter),
                'name': str(label),
                'code': str(label),
                'selected': budget_control_map.get(str(counter)),
            })
            if budget_control_map.get(str(counter)):
                options['selected_budget_control'].append(str(label))
            counter += 1

    @api.model
    def _init_filter_program_code_section(self, options, previous_options=None):
        options['code_sections'] = previous_options and previous_options.get(
            'code_sections') or []
        program_fields_ids = [int(acc) for acc in options['code_sections']]
        selected_program_fields = program_fields_ids \
                                  and self.env['report.program.fields'].browse(program_fields_ids) \
                                  or self.env['report.program.fields']
        options['selected_program_fields'] = selected_program_fields.mapped(
            'name')

        # Program Section filter
        options['section_program'] = previous_options and previous_options.get(
            'section_program') or []
        program_ids = [int(acc) for acc in options['section_program']]
        selected_programs = program_ids \
                            and self.env['program'].browse(program_ids) \
                            or self.env['program']
        options['selected_programs'] = selected_programs.mapped('key_unam')

        # Sub Program Section filter
        options['section_sub_program'] = previous_options and previous_options.get(
            'section_sub_program') or []
        sub_program_ids = [int(acc) for acc in options['section_sub_program']]
        selected_sub_programs = sub_program_ids \
                                and self.env['sub.program'].browse(sub_program_ids) \
                                or self.env['sub.program']
        options['selected_sub_programs'] = selected_sub_programs.mapped(
            'sub_program')

        # Dependency Section filter
        options['section_dependency'] = previous_options and previous_options.get(
            'section_dependency') or []
        dependency_ids = [int(acc) for acc in options['section_dependency']]
        selected_dependency = dependency_ids \
                              and self.env['dependency'].browse(dependency_ids) \
                              or self.env['dependency']
        options['selected_dependency'] = selected_dependency.mapped(
            'dependency')

        # Sub Dependency Section filter
        options['section_sub_dependency'] = previous_options and previous_options.get(
            'section_sub_dependency') or []
        sub_dependency_ids = [int(acc)
                              for acc in options['section_sub_dependency']]
        selected_sub_dependency = sub_dependency_ids \
                                  and self.env['sub.dependency'].browse(sub_dependency_ids) \
                                  or self.env['sub.dependency']
        options['selected_sub_dependency'] = selected_sub_dependency.mapped(
            'sub_dependency')

        # Expense Item filter
        options['section_expense_item'] = previous_options and previous_options.get(
            'section_expense_item') or []
        item_ids = [int(acc) for acc in options['section_expense_item']]
        selected_items = item_ids \
                         and self.env['expenditure.item'].browse(item_ids) \
                         or self.env['expenditure.item']
        options['selected_items'] = selected_items.mapped('item')

        # Origin Resource filter
        options['section_or'] = previous_options and previous_options.get(
            'section_or') or []
        or_ids = [int(acc) for acc in options['section_or']]
        selected_origins = or_ids \
                           and self.env['resource.origin'].browse(or_ids) \
                           or self.env['resource.origin']
        options['selected_or'] = selected_origins.mapped('key_origin')

        # Institutional Activity filter
        options['section_ai'] = previous_options and previous_options.get(
            'section_ai') or []
        ai_ids = [int(acc) for acc in options['section_ai']]
        selected_acitvities = ai_ids \
                              and self.env['institutional.activity'].browse(ai_ids) \
                              or self.env['institutional.activity']
        options['selected_ai'] = selected_acitvities.mapped('number')

        # Budget Program Conversion (CONPP) filter
        options['section_conpp'] = previous_options and previous_options.get(
            'section_conpp') or []
        conpp_ids = [int(acc) for acc in options['section_conpp']]
        selected_conpp = conpp_ids \
                         and self.env['budget.program.conversion'].browse(conpp_ids) \
                         or self.env['budget.program.conversion']
        options['selected_conpp'] = selected_conpp.mapped(
            'shcp').mapped('name')

        # SHCP Games (CONPA) filter
        options['section_conpa'] = previous_options and previous_options.get(
            'section_conpa') or []
        conpa_ids = [int(acc) for acc in options['section_conpa']]
        selected_conpa = conpa_ids \
                         and self.env['departure.conversion'].browse(conpa_ids) \
                         or self.env['departure.conversion']
        options['selected_conpa'] = selected_conpa.mapped('federal_part')

        # Type of Expense (TG) filter
        options['section_expense'] = previous_options and previous_options.get(
            'section_expense') or []
        expense_ids = [int(acc) for acc in options['section_expense']]
        selected_expenses = expense_ids \
                            and self.env['expense.type'].browse(expense_ids) \
                            or self.env['expense.type']
        options['selected_expenses'] = selected_expenses.mapped(
            'key_expenditure_type')

        # Geographic Location (UG) filter
        options['section_ug'] = previous_options and previous_options.get(
            'section_ug') or []
        ug_ids = [int(acc) for acc in options['section_ug']]
        selected_ug = ug_ids \
                      and self.env['geographic.location'].browse(ug_ids) \
                      or self.env['geographic.location']
        options['selected_ug'] = selected_ug.mapped('state_key')

        # Wallet Key (CC) filter
        options['section_wallet'] = previous_options and previous_options.get(
            'section_wallet') or []
        wallet_ids = [int(acc) for acc in options['section_wallet']]
        selected_wallets = wallet_ids \
                           and self.env['key.wallet'].browse(wallet_ids) \
                           or self.env['key.wallet']
        options['selected_wallets'] = selected_wallets.mapped(
            'wallet_password')

        # Project Type (TP) filter
        options['section_tp'] = previous_options and previous_options.get(
            'section_tp') or []
        tp_ids = [int(acc) for acc in options['section_tp']]
        selected_tp = tp_ids \
                      and self.env['project.type'].browse(tp_ids) \
                      or self.env['project.type']
        options['selected_tp'] = selected_tp.mapped('project_type_identifier')

        # Project Number filter
        options['section_pn'] = previous_options and previous_options.get(
            'section_pn') or []
        pn_ids = [int(acc) for acc in options['section_pn']]
        selected_pn = pn_ids \
                      and self.env['project.type'].browse(pn_ids) \
                      or self.env['project.type']
        options['selected_pn'] = selected_pn.mapped('number')

        # Stage filter
        options['section_stage'] = previous_options and previous_options.get(
            'section_stage') or []
        stage_ids = [int(acc) for acc in options['section_stage']]
        selected_stage = stage_ids \
                         and self.env['stage'].browse(stage_ids) \
                         or self.env['stage']
        options['selected_stage'] = selected_stage.mapped('stage_identifier')

        # Agreement Type filter
        options['section_agreement_type'] = previous_options and previous_options.get(
            'section_agreement_type') or []
        type_ids = [int(acc) for acc in options['section_agreement_type']]
        selected_type = type_ids \
                        and self.env['agreement.type'].browse(type_ids) \
                        or self.env['agreement.type']
        options['selected_type'] = selected_type.mapped('agreement_type')

        # Agreement Number filter
        options['section_agreement_number'] = previous_options and previous_options.get(
            'section_agreement_number') or []
        agreement_number_ids = [int(acc)
                                for acc in options['section_agreement_number']]
        selected_agreement_number = agreement_number_ids \
                                    and self.env['agreement.type'].browse(agreement_number_ids) \
                                    or self.env['agreement.type']
        options['selected_agreement_number'] = selected_agreement_number.mapped(
            'number_agreement')


    def check_item_range(self,item_range):
        key_i = int(item_range)
        if key_i >= 100 and key_i <= 199:
            return 1
        elif key_i >= 200 and key_i <= 299:
            return 2
        elif key_i >= 300 and key_i <= 399:
            return 3
        elif key_i >= 400 and key_i <= 499:
            return 4
        elif key_i >= 500 and key_i <= 599:
            return 5
        elif key_i >= 600 and key_i <= 699:
            return 6
        elif key_i >= 700 and key_i <= 799:
            return 7
        elif key_i >= 800 and key_i <= 899:
            return 8
        elif key_i >= 900 and key_i <= 999:
            return 9
 
        
    def all_lines_data(self,budget_line,options,lines,start,end):
        #print ("Start Time====",datetime.today())
        need_columns = []
        need_columns_with_format = []
        program_codes = budget_line.mapped('program_code_id')
        need_col_data_list = [] # Used to add total
        col_query = 'select pc.id,pc.program_code' 
        from_query = ' from program_code pc,expenditure_item exioder'
        where_query = ' where pc.id in %s and exioder.id=pc.item_id and exioder.item >= %s and exioder.item <= %s'
        order_by = ' order by exioder.item_group'
        #===== Grand Total Query=====#
        self.env.cr.execute('select pc.id from program_code pc,expenditure_item exioder where pc.id in %s and exioder.id=pc.item_id and exioder.item >= %s and exioder.item <= %s',(tuple(program_codes.ids),'100','999') )
        my_datas_total = self.env.cr.fetchall()
        program_code_list = []
        if my_datas_total:
            program_code_list = list(my_datas_total)                                                

        grand_total_dict = {}
        tuple_where_data = []
        need_total = False
        order_dep = False
        order_sub_dep = False
        order_program = False
        order_sub_program = False
        # Program code struture view fields
        need_to_skip = 0
        for column in options['selected_program_fields']:
            if column in ('Year', 'Año'):
                need_columns.append('year')
                col_query+=',yc.name as year'
                from_query += ',year_configuration yc'
                where_query += ' and pc.year=yc.id'

                need_to_skip += 1
            if column in ('Program', 'Programa'):
                #program = prog_code.program_id and prog_code.program_id.key_unam or ''
                need_columns.append('program')
                col_query+=',pp.key_unam as program'
                from_query += ',program pp'
                where_query += ' and pc.program_id=pp.id'
                order_program = ',pp.key_unam'
                order_by+=order_program
                need_to_skip += 1
            if column in ('Sub Program', 'Subprograma'):
                # subprogram = prog_code.sub_program_id and prog_code.sub_program_id.sub_program or ''
                need_columns.append('sub_program')
                col_query+=',sp.sub_program as sub_program'
                from_query += ',sub_program sp'
                where_query += ' and pc.sub_program_id=sp.id'
                order_sub_program = ',sp.sub_program'
                order_by+=order_sub_program
                
                need_to_skip += 1
            if column in ('Dependency', 'Dependencia'):
                #dependency = prog_code.dependency_id and prog_code.dependency_id.dependency or ''
                need_columns.append('dependency')
                col_query+=',dp.dependency as dependency'
                from_query += ',dependency dp'
                where_query += ' and pc.dependency_id=dp.id'
                order_dep = ',dp.dependency'
                order_by+=order_dep
                need_to_skip += 1
            if column in ('Sub Dependency', 'Subdependencia'):
                #subdependency = prog_code.sub_dependency_id and prog_code.sub_dependency_id.sub_dependency or ''
                need_columns.append('sub_dependency')
                col_query+=',sdp.sub_dependency as sub_dependency'
                from_query += ',sub_dependency sdp'
                where_query += ' and pc.sub_dependency_id=sdp.id'
                order_sub_dep = ',sdp.sub_dependency'
                order_by+=order_sub_dep
                need_to_skip += 1
            if column in ('Expenditure Item', 'Partida de Gasto (PAR)'):
                #item = prog_code.item_id and prog_code.item_id.item or ''
                need_columns.append('exp_name')
                col_query+=',expi.item as exp_name'
                from_query += ',expenditure_item expi'
                where_query += ' and pc.item_id=expi.id'
                order_expen_item = ',expi.item'
                order_by+=order_expen_item
                
                need_to_skip += 1
            if column in ('Check Digit', 'Dígito Verificador'):
                #check_digit = prog_code.check_digit or ''
                need_columns.append('check_digit')
                col_query+=',pc.check_digit as check_digit'
                order_check_digit = ',pc.check_digit'
                order_by+=order_check_digit
                
                #from_query += ',expenditure_item expi'
                #where_query += ' and pc.item_id=expi.id'
                need_to_skip += 1
            if column in ('Source of Resource', 'Origen del Recurso'):
                #sor = prog_code.resource_origin_id and prog_code.resource_origin_id.key_origin or ''
                need_columns.append('resource_origin_id')
                col_query+=',ro.key_origin as resource_origin_id'
                from_query += ',resource_origin ro'
                where_query += ' and pc.resource_origin_id=ro.id'
                order_resource_origin = ',ro.key_origin'
                order_by+=order_resource_origin
                
                need_to_skip += 1
            if column in ('Institutional Activity', 'Actividad Institucional'):
                #ai = prog_code.institutional_activity_id and prog_code.institutional_activity_id.number or ''
                need_columns.append('institutional_activity_id')
                col_query+=',inac.number as institutional_activity_id'
                from_query += ',institutional_activity inac'
                where_query += ' and pc.institutional_activity_id=inac.id'
                order_activity_number = ',inac.number'
                order_by+=order_activity_number
                
                need_to_skip += 1
            if column in ('Conversion of Budgetary Program', 'Conversión de Programa Presupuestario'):
                #conversion = prog_code.budget_program_conversion_id and \
                #             prog_code.budget_program_conversion_id.shcp and \
                #             prog_code.budget_program_conversion_id.shcp.name or ''
                need_columns.append('conversion_program')
                col_query+=',shcp.name as conversion_program'
                from_query += ',shcp_code shcp,budget_program_conversion bpc'
                where_query += ' and pc.budget_program_conversion_id=bpc.id and shcp.id=bpc.shcp'
                order_conversion_program = ',shcp.name'
                order_by+=order_conversion_program
                
                need_to_skip += 1
            if column in ('SHCP items', 'Conversión Con Partida (CONPA)'):
                #shcp = prog_code.conversion_item_id and prog_code.conversion_item_id.federal_part or ''
                need_columns.append('shcp_item')
                col_query+=',dc.federal_part as shcp_item'
                from_query += ',departure_conversion as dc'
                where_query += ' and pc.conversion_item_id=dc.id'
                order_federal_part = ',dc.federal_part'
                order_by+=order_federal_part
                
                need_to_skip += 1
            if column in ('Type of Expenditure', 'Tipo de Gasto'):
                #expense_type = prog_code.expense_type_id and prog_code.expense_type_id.key_expenditure_type or ''
                need_columns.append('type_of_expenditure')
                col_query+=',et.key_expenditure_type as type_of_expenditure'
                from_query += ',expense_type as et'
                where_query += ' and pc.expense_type_id=et.id'
                order_key_expenditure_type = ',et.key_expenditure_type'
                order_by+=order_key_expenditure_type
                
                need_to_skip += 1
            if column in ('Geographic Location', 'Ubicación Geográfica'):
                #location = prog_code.location_id and prog_code.location_id.state_key or ''
                need_columns.append('geographic_location')
                col_query+=',gl.state_key as geographic_location'
                from_query += ',geographic_location as gl'
                where_query += ' and pc.location_id=gl.id'
                order_state_key = ',gl.state_key'
                order_by+=order_state_key
                
                need_to_skip += 1
            if column in ('Wallet Key', 'Clave Cartera'):
                #wallet_key = prog_code.portfolio_id and prog_code.portfolio_id.wallet_password or ''
                need_columns.append('wallet_key')
                col_query+=',kw.wallet_password as wallet_key'
                from_query += ',key_wallet as kw'
                where_query += ' and pc.portfolio_id=kw.id'
                order_wallet_password = ',kw.wallet_password'
                order_by+=order_wallet_password
                
                need_to_skip += 1
            if column in ('Type of Project', 'Tipo de Proyecto'):
                #project_type = prog_code.project_type_id and prog_code.project_type_id.project_type_identifier or ''
                need_columns.append('type_of_project')
                col_query+=',ptype.project_type_identifier as type_of_project'
                from_query += ',project_type as ptype'
                where_query += ' and pc.project_type_id=ptype.id'
                order_project_type = ',ptype.project_type_identifier'
                order_by+=order_project_type
                
                need_to_skip += 1
            if column in ('Project Number', 'Número de Proyecto'):
                #project_number = prog_code.project_number or ''
                need_columns.append('project_number')
                col_query+=',projectp.number as project_number'
                from_query += ',project_type as ptypen,project_project projectp'
                where_query += ' and pc.project_type_id=ptypen.id and projectp.id=ptypen.project_id'
                order_project_number = ',projectp.number'
                order_by+=order_project_number
                
                need_to_skip += 1
            if column in ('Stage', 'Etapa'):
                #stage = prog_code.stage_id and prog_code.stage_id.stage_identifier or ''
                need_columns.append('stage_identofier')
                col_query+=',si.stage_identifier as stage_identofier'
                from_query += ',stage as si'
                where_query += ' and pc.stage_id=si.id'
                order_stage_identifier = ',si.stage_identifier'
                order_by+=order_stage_identifier
                
                need_to_skip += 1
            if column in ('Type of Agreement', 'Tipo de Convenio'):
                #agreement_type = prog_code.agreement_type_id and prog_code.agreement_type_id.agreement_type or ''
                need_columns.append('type_of_agreement')
                col_query+=',atype.agreement_type as type_of_agreement'
                from_query += ',agreement_type as atype'
                where_query += ' and pc.agreement_type_id=atype.id'
                order_agreement_type = ',atype.agreement_type'
                order_by+=order_agreement_type
                
                need_to_skip += 1
            if column in ('Agreement Number', 'Número de Convenio'):
                #agreement_number = prog_code.number_agreement or ''
                need_columns.append('number_of_agreement')
                col_query+=',atypen.number_agreement as number_of_agreement'
                from_query += ',agreement_type as atypen'
                where_query += ' and pc.agreement_type_id=atypen.id'
                order_agreement_number = ',atypen.number_agreement'
                order_by+=order_agreement_number
                
                need_to_skip += 1


        for column in options['selected_budget_control']:
#             amt = 0
            if column in ('Partida de Gasto (PAR)', 'Expense Item'):
                #amt = b_line.item_id and b_line.item_id.item or ''
                need_columns.append('exp_item')
                col_query+=',expic.item as exp_item,expic.item_group as item_group'
                from_query += ',expenditure_item expic'
                where_query += ' and pc.item_id=expic.id'
                need_total = True
            elif column in ('Authorized', 'Autorizado'):
                start_date = start.replace(month=1, day=1)
                end_date = end.replace(month=12, day=31)
                
                need_columns_with_format.append('authorized')
                col_query += ',(select coalesce(sum(ebl.authorized), 0) from expenditure_budget_line ebl where pc.id=ebl.program_code_id and COALESCE(ebl.imported_sessional, FALSE) = FALSE and start_date >= %s and end_date <= %s) as authorized'
                #tuple_where_data.append(False)
                tuple_where_data.append(start_date)
                tuple_where_data.append(end_date)
                #=== Grand Total ======#
                
                self.env.cr.execute("select coalesce(sum(ebl.authorized),0) from expenditure_budget_line ebl where ebl.program_code_id in %s and COALESCE(ebl.imported_sessional, FALSE) = FALSE and start_date >= %s and end_date <= %s", (tuple(program_code_list),start_date,end_date))
                my_datas = self.env.cr.fetchone()
                
                if my_datas:
                    grand_total_dict.update({'authorized':my_datas[0]})
                
            elif column in ('Assigned Total Annual', 'Total Asignado Anual'):
                need_columns_with_format.append('assigned')
                col_query += ',(select coalesce(sum(ebl.assigned),0) from expenditure_budget_line ebl where pc.id=ebl.program_code_id and start_date >= %s and end_date <= %s) as assigned'
                tuple_where_data.append(start)
                tuple_where_data.append(end)
                #=== Grand Total ======#
                self.env.cr.execute("select coalesce(sum(ebl.assigned),0) from expenditure_budget_line ebl where ebl.program_code_id in %s and start_date >= %s and end_date <= %s", (tuple(program_code_list),start,end))
                my_datas = self.env.cr.fetchone()
                if my_datas:
                    grand_total_dict.update({'assigned':my_datas[0]})
                
            elif column in ('Annual Modified', 'Modificado Anual'):
                need_columns_with_format.append('annual_modified')
                start_date = start.replace(month=1, day=1)
                end_date = end.replace(month=12, day=31)
                
                col_query += ',(select (select coalesce(SUM(CASE WHEN al.line_type = %s THEN al.amount ELSE -al.amount END),0) from adequacies_lines al,adequacies a where a.state=%s and al.program = pc.id and a.id=al.adequacies_id))+(select coalesce(sum(ebl.authorized), 0) from expenditure_budget_line ebl where pc.id=ebl.program_code_id and ebl.imported_sessional IS NULL and start_date >= %s and end_date <= %s) as annual_modified'
                tuple_where_data.append('increase')
                tuple_where_data.append('accepted')
                tuple_where_data.append(start_date)
                tuple_where_data.append(end_date)
                #=== Grand Total ======#
                self.env.cr.execute("select coalesce(SUM(CASE WHEN al.line_type = %s THEN al.amount ELSE -al.amount END),0) from adequacies_lines al,adequacies a where a.state=%s and al.program in %s and a.id=al.adequacies_id", ('increase','accepted',tuple(program_code_list)))
                my_datas = self.env.cr.fetchone()
                total_annual_modified = 0
                if my_datas:
                    total_annual_modified = my_datas[0]
                self.env.cr.execute("select coalesce(sum(ebl.authorized), 0) from expenditure_budget_line ebl where ebl.program_code_id in %s and ebl.imported_sessional IS NULL and start_date >= %s and end_date <= %s", (tuple(program_code_list),start_date,end_date))
                my_datas = self.env.cr.fetchone()
                if my_datas:
                    total_annual_modified += my_datas[0]
                grand_total_dict.update({'annual_modified':total_annual_modified})
                
            elif column in ('Assigned 1st Trimester', 'Asignado 1er Trimestre'):
                start_date = start.replace(month=1, day=1)
                end_date = end.replace(month=3, day=31)
                need_columns_with_format.append('assigned_1st')
                col_query += ',(select coalesce(sum(ebl.assigned),0) from expenditure_budget_line ebl where pc.id=ebl.program_code_id and start_date >= %s and end_date <= %s) as assigned_1st'
                tuple_where_data.append(start_date)
                tuple_where_data.append(end_date)
                #=== Grand Total ======#
                self.env.cr.execute("select coalesce(sum(ebl.assigned),0) from expenditure_budget_line ebl where ebl.program_code_id in %s and start_date >= %s and end_date <= %s", (tuple(program_code_list),start_date,end_date))
                my_datas = self.env.cr.fetchone()
                if my_datas:
                    grand_total_dict.update({'assigned_1st':my_datas[0]})
                
            elif column in ('Assigned 2nd Trimester', 'Asignado 2do Trimestre'):
                start_date = start.replace(month=4, day=1)
                end_date = end.replace(month=6, day=30)
                need_columns_with_format.append('assigned_2nd')
                col_query += ',(select coalesce(sum(ebl.assigned),0) from expenditure_budget_line ebl where pc.id=ebl.program_code_id and start_date >= %s and end_date <= %s) as assigned_2nd'
                tuple_where_data.append(start_date)
                tuple_where_data.append(end_date)
                #=== Grand Total ======#
                self.env.cr.execute("select coalesce(sum(ebl.assigned),0) from expenditure_budget_line ebl where ebl.program_code_id in %s and start_date >= %s and end_date <= %s", (tuple(program_code_list),start_date,end_date))
                my_datas = self.env.cr.fetchone()
                if my_datas:
                    grand_total_dict.update({'assigned_2nd':my_datas[0]})
                
            elif column in ('Assigned 3rd Trimester', 'Asignado 3er Trimestre'):
                start_date = start.replace(month=7, day=1)
                end_date = end.replace(month=9, day=30)
                need_columns_with_format.append('assigned_3rd')
                col_query += ',(select coalesce(sum(ebl.assigned),0) from expenditure_budget_line ebl where pc.id=ebl.program_code_id and start_date >= %s and end_date <= %s) as assigned_3rd'
                tuple_where_data.append(start_date)
                tuple_where_data.append(end_date)
                #=== Grand Total ======#
                self.env.cr.execute("select coalesce(sum(ebl.assigned),0) from expenditure_budget_line ebl where ebl.program_code_id in %s and start_date >= %s and end_date <= %s", (tuple(program_code_list),start_date,end_date))
                my_datas = self.env.cr.fetchone()
                if my_datas:
                    grand_total_dict.update({'assigned_3rd':my_datas[0]})

                
            elif column in ('Assigned 4th Trimester', 'Asignado 4to Trimestre'):
                start_date = start.replace(month=10, day=1)
                end_date = end.replace(month=12, day=31)
                need_columns_with_format.append('assigned_4th')
                col_query += ',(select coalesce(sum(ebl.assigned),0) from expenditure_budget_line ebl where pc.id=ebl.program_code_id and start_date >= %s and end_date <= %s) as assigned_4th'
                tuple_where_data.append(start_date)
                tuple_where_data.append(end_date)
                #=== Grand Total ======#
                self.env.cr.execute("select coalesce(sum(ebl.assigned),0) from expenditure_budget_line ebl where ebl.program_code_id in %s and start_date >= %s and end_date <= %s", (tuple(program_code_list),start_date,end_date))
                my_datas = self.env.cr.fetchone()
                if my_datas:
                    grand_total_dict.update({'assigned_4th':my_datas[0]})
                
            elif column in ('Per Exercise', 'Por Ejercer'):
                need_columns_with_format.append('per_exercise')
                col_query += ',(select coalesce(sum(ebl.available),0) from expenditure_budget_line ebl where pc.id=ebl.program_code_id and start_date >= %s and end_date <= %s) as per_exercise'
                tuple_where_data.append(start)
                tuple_where_data.append(end)
                #=== Grand Total ======#
                self.env.cr.execute("select coalesce(sum(ebl.available),0) from expenditure_budget_line ebl where ebl.program_code_id in %s and start_date >= %s and end_date <= %s", (tuple(program_code_list),start,end))
                my_datas = self.env.cr.fetchone()
                if my_datas:
                    grand_total_dict.update({'per_exercise':my_datas[0]})
                
            elif column in ('Committed', 'Comprometido'):
                need_columns_with_format.append('committed')
                col_query += ',(select coalesce(sum(abs(line.balance)+abs(line.tax_price_cr)),0) from account_move_line line,account_move amove where pc.id=line.program_code_id and amove.id=line.move_id and amove.payment_state=%s and amove.invoice_date >= %s and amove.invoice_date <= %s) as Committed'
                tuple_where_data.append('approved_payment')
                tuple_where_data.append(start)
                tuple_where_data.append(end)
                #=== Grand Total ======#
                self.env.cr.execute("select coalesce(sum(abs(line.balance)+abs(line.tax_price_cr)),0) from account_move_line line,account_move amove where line.program_code_id in %s and amove.id=line.move_id and amove.payment_state=%s and amove.invoice_date >= %s and amove.invoice_date <= %s", (tuple(program_code_list),'approved_payment',start,end))
                my_datas = self.env.cr.fetchone()
                if my_datas:
                    grand_total_dict.update({'committed':my_datas[0]})

            elif column in ('Accrued', 'Devengado'):
                need_columns_with_format.append('accrued')
                col_query += ',0.00 as accrued'
            elif column in ('Exercised', 'Ejercido'):
                need_columns_with_format.append('exercised')
                col_query += ',(select coalesce(sum(abs(line.balance)+abs(line.tax_price_cr)),0) from account_move_line line,account_move amove where pc.id=line.program_code_id and amove.id=line.move_id and amove.payment_state in %s and amove.invoice_date >= %s and amove.invoice_date <= %s) as exercised'
                tuple_where_data.append(('for_payment_procedure','payment_not_applied','assigned_payment_method'))
                tuple_where_data.append(start)
                tuple_where_data.append(end)

                #=== Grand Total ======#
                self.env.cr.execute("select coalesce(sum(abs(line.balance)+abs(line.tax_price_cr)),0) from account_move_line line,account_move amove where line.program_code_id in %s and amove.id=line.move_id and amove.payment_state in %s and amove.invoice_date >= %s and amove.invoice_date <= %s", (tuple(program_code_list),('for_payment_procedure','payment_not_applied'),start,end))
                my_datas = self.env.cr.fetchone()
                if my_datas:
                    grand_total_dict.update({'exercised':my_datas[0]})
                
            elif column in ('Paid', 'Pagado'):
                need_columns_with_format.append('paid')
#                 col_query += """, (select coalesce(sum(abs(amount_total_signed)),0) from account_move where id in 
#                                     (select DISTINCT amlp.move_id from account_move_line amlp where amlp.payment_id in  
#                                     (select DISTINCT apay.id from account_move_line line,account_move amove,account_payment apay 
#                                     where  pc.id=line.program_code_id and amove.id=line.move_id and amove.payment_state=%s and apay.payment_date >= %s and apay.payment_date <= %s and apay.payment_request_id = amove.id))) as paid """

                col_query += """,(select coalesce(sum(abs(line.balance)+abs(line.tax_price_cr)),0) from account_move_line line,account_move amove,account_payment apay 
                                    where  pc.id=line.program_code_id and amove.id=line.move_id and amove.payment_state=%s and apay.payment_date >= %s and apay.payment_date <= %s and apay.payment_request_id = amove.id) as paid """
                                    
                #col_query += ',(select coalesce(sum(line.price_total),0) from account_move_line line,account_move amove where pc.id=line.program_code_id and amove.id=line.move_id and amove.payment_state=%s and amove.invoice_date >= %s and amove.invoice_date <= %s) as paid'
                tuple_where_data.append('paid')
                tuple_where_data.append(start)
                tuple_where_data.append(end)
                #=== Grand Total ======#
                self.env.cr.execute("""(select coalesce(sum(abs(line.balance)+abs(line.tax_price_cr)),0) from account_move_line line,account_move amove,account_payment apay 
                                    where  line.program_code_id in %s and amove.id=line.move_id and amove.payment_state=%s and apay.payment_date >= %s and apay.payment_date <= %s and apay.payment_request_id = amove.id)""", (tuple(program_code_list),'paid',start,end))
                
                #self.env.cr.execute("select coalesce(sum(line.price_total),0) from account_move_line line,account_move amove where line.program_code_id in %s and amove.id=line.move_id and amove.payment_state=%s and amove.invoice_date >= %s and amove.invoice_date <= %s", (tuple(program_code_list),'paid',start,end))
                my_datas = self.env.cr.fetchone()
                if my_datas:
                    grand_total_dict.update({'paid':my_datas[0]})

                                
            elif column in ('Available', 'Disponible'):
                need_columns_with_format.append('available')
                col_query += ',(select coalesce(sum(ebl.available),0) from expenditure_budget_line ebl where pc.id=ebl.program_code_id and start_date >= %s and end_date <= %s) as available'
                tuple_where_data.append(start)
                tuple_where_data.append(end)
#                #=== Grand Total ======#
                self.env.cr.execute("select coalesce(sum(ebl.available),0) from expenditure_budget_line ebl where ebl.program_code_id in %s and start_date >= %s and end_date <= %s", (tuple(program_code_list),start,end))
                my_datas = self.env.cr.fetchone()
                if my_datas:
                    grand_total_dict.update({'available':my_datas[0]})
                 
            
        tuple_where_data.append(tuple(program_codes.ids))
        tuple_where_data.append('100')
        tuple_where_data.append('999')
        
#         if order_dep:
#             order_by+= order_dep
#         if order_sub_dep:
#             order_by+= order_sub_dep
#         if order_program:
#             order_by+= order_program
#         if order_sub_program:
#             order_by+= order_sub_program
        order_by += ',exioder.item'
        sql_query =  col_query +  from_query + where_query + order_by
        self.env.cr.execute(sql_query,tuple(tuple_where_data))
        my_datas = self.env.cr.dictfetchall()
        subtotal_dict = {}
        total_dict = {}
        pre_exp_range = 0
        pre_dependency = 0
        pre_sub_dependency = 0
        pre_program = 0
        pre_subprogram = 0
        #======= get the data count =========#
        selected_line_pages = options['selected_line_pages']
        selected_my_data = []
        
        for s in selected_line_pages:
            s = int(s)
            start = (s - 1) * 2000
            end = s * 2000
            
            selected_my_data = selected_my_data + my_datas[start:end]
        
        if not selected_line_pages:
            selected_my_data = my_datas[:2000]
        for data in selected_my_data:
            columns_in = []
            is_add_subtotal = False
            if need_total:
                exp_range = self.check_item_range(data.get('exp_item'))
                if pre_exp_range!=0 and pre_exp_range!=exp_range:
                    is_add_subtotal = True 
                if pre_dependency!=0 and data.get('dependency',0) and data.get('dependency',0) != pre_dependency:
                    is_add_subtotal = True
                if pre_sub_dependency!=0 and data.get('sub_dependency',0) and data.get('sub_dependency',0) != pre_sub_dependency:
                    is_add_subtotal = True
                if pre_subprogram!=0 and data.get('sub_program',0) and data.get('sub_program',0) != pre_subprogram:
                    is_add_subtotal = True
                if pre_program!=0 and data.get('program',0) and data.get('program',0) != pre_program:
                    is_add_subtotal = True
                
                if is_add_subtotal:
                    if subtotal_dict:
                        main_cols = []
                        for c in need_columns:
                            main_cols.append({'name': '','float_name': ''})
                        for c in need_columns_with_format:
                            amt=formatLang(self.env, subtotal_dict.get(c,0.0), currency_obj=False)
                            main_cols.append({'name':amt,'class':'number','float_name': subtotal_dict.get(c,0.0),})
            
                        lines.append({
                                'id': 0,
                                'name': _('Subtotal'),
                                'class': 'total',
                                'level': 2,
                                'columns': main_cols,
                            })
                
                    subtotal_dict = {}
                pre_exp_range=exp_range
                pre_dependency = data.get('dependency',0)
                pre_sub_dependency = data.get('sub_dependency',0)
                pre_subprogram = data.get('sub_program',0)
                pre_program = data.get('program',0)
                
            for c in need_columns:
                columns_in.append({'name':data.get(c)})
            for c in need_columns_with_format:
                amt=formatLang(self.env, data.get(c,0.0), currency_obj=False)
                columns_in.append({'name':amt,'class':'number','float_name': data.get(c,0.0),})
                if need_total:
                    if subtotal_dict.get(c,0.0):
                        subtotal_dict.update({c:subtotal_dict.get(c,0.0)+data.get(c,0.0)})
                    else:
                        subtotal_dict.update({c:data.get(c,0.0)})
                    if total_dict.get(c,0.0):
                        total_dict.update({c:total_dict.get(c,0.0)+data.get(c,0.0)})
                    else:
                        total_dict.update({c:data.get(c,0.0)})

            lines.append({
                           'id': data.get('id'),
                           'name':data.get('program_code'),
                           'columns': columns_in,
                           'level': 0,
                           'unfoldable': False,
                           'unfolded': True,
                       })
        if subtotal_dict and need_total:
            main_cols = []
            for c in need_columns:
                main_cols.append({'name': '','float_name': ''})
            for c in need_columns_with_format:
                amt=formatLang(self.env, subtotal_dict.get(c,0.0), currency_obj=False)
                main_cols.append({'name':amt,'class':'number','float_name': subtotal_dict.get(c,0.0),})

            lines.append({
                    'id': 0,
                    'name': _('Subtotal'),
                    'class': 'total',
                    'level': 2,
                    'columns': main_cols,
                })
            
        if total_dict and need_total:
            main_cols = []
            for c in need_columns:
                main_cols.append({'name': '','float_name': ''})
            for c in need_columns_with_format:
                amt=formatLang(self.env, total_dict.get(c,0.0), currency_obj=False)
                main_cols.append({'name':amt,'class':'number','float_name': total_dict.get(c,0.0),})

            lines.append({
                    'id': 0,
                    'name': _('Total'),
                    'class': 'total',
                    'level': 2,
                    'columns': main_cols,
                })
        if grand_total_dict and need_total:
            main_cols = []
            for c in need_columns:
                main_cols.append({'name': '','float_name': ''})
            for c in need_columns_with_format:
                amt=formatLang(self.env, grand_total_dict.get(c,0.0), currency_obj=False)
                main_cols.append({'name':amt,'class':'number','float_name': grand_total_dict.get(c,0.0),})

            lines.append({
                    'id': 0,
                    'name': _('Grand Total'),
                    'class': 'total',
                    'level': 2,
                    'columns': main_cols,
                })
            
        return lines,need_total,need_to_skip

    def _get_sum_trimster(self, all_b_lines, s_month, s_day, e_month, e_day):
        return sum(x.assigned if x.start_date.month == s_month and \
                                x.start_date.day == s_day and x.end_date.month == e_month and x.end_date.day == e_day \
                      else 0 for x in all_b_lines)

    @api.model
    def _get_lines(self, options, line_id=None):
        start = datetime.strptime(
            str(options['date'].get('date_from')), '%Y-%m-%d').date()
        end = datetime.strptime(
            options['date'].get('date_to'), '%Y-%m-%d').date()

        domain = [('expenditure_budget_id.state', '=', 'validate'),
             ('start_date', '>=', start), ('end_date', '<=', end)]

        if len(options['selected_programs']) > 0:
            domain.append(('program_code_id.program_id.key_unam', 'in', options['selected_programs']))
        if len(options['selected_sub_programs']) > 0:
            domain.append(('program_code_id.sub_program_id.sub_program', 'in', options['selected_sub_programs']))
        if len(options['selected_dependency']) > 0:
            domain.append(('program_code_id.dependency_id.dependency', 'in', options['selected_dependency']))
        if len(options['selected_sub_dependency']) > 0:
            domain.append(('program_code_id.sub_dependency_id.sub_dependency', 'in', options['selected_sub_dependency']))
        if len(options['selected_items']) > 0:
            domain.append(('program_code_id.item_id.item', 'in', options['selected_items']))
        if len(options['selected_or']) > 0:
            domain.append(('program_code_id.resource_origin_id.key_origin', 'in', options['selected_or']))
        if len(options['selected_ai']):
            domain.append(('program_code_id.institutional_activity_id.number', 'in', options['selected_ai']))
        if len(options['selected_conpp']) > 0:
            domain.append(('program_code_id.budget_program_conversion_id.shcp.name', 'in', options['selected_conpp']))
        if len(options['selected_conpa']) > 0:
            domain.append(('program_code_id.conversion_item_id.federal_part', 'in', options['selected_conpa']))
        if len(options['selected_expenses']) > 0:
            domain.append(('program_code_id.expense_type_id.key_expenditure_type', 'in', options['selected_expenses']))
        if len(options['selected_ug']) > 0:
            domain.append(('program_code_id.location_id.state_key', 'in', options['selected_ug']))
        if len(options['selected_wallets']) > 0:
            domain.append(('program_code_id.portfolio_id.wallet_password', 'in', options['selected_wallets']))
        if len(options['selected_tp']) > 0:
            domain.append(('program_code_id.project_type_id.project_type_identifier', 'in', options['selected_tp']))
        if len(options['selected_pn']) > 0:
            domain.append(('program_code_id.project_number', 'in', options['selected_pn']))
        if len(options['selected_stage']) > 0:
            domain.append(('program_code_id.stage_id.stage_identifier', 'in', options['selected_stage']))
        if len(options['selected_type']) > 0:
            domain.append(('program_code_id.agreement_type_id.agreement_type', 'in', options['selected_type']))
        if len(options['selected_agreement_number']) > 0:
            domain.append(('program_code_id.number_agreement', 'in', options['selected_agreement_number']))

        lines = []
        b_line_obj = self.env['expenditure.budget.line']
        adequacies_line_obj = self.env['adequacies.lines']
        item_list = {'1': [], '2': [], '3': [], '4': [], '5': [], '6': [], '7': [], '8': [], '9': []}
        budget_lines = b_line_obj.search(domain)

        #=================================== Start Haresh Test Code==============
        need_total = False
        need_to_skip = 0
        lines = []
        if budget_lines:
            
            lines,need_total,need_to_skip = self.all_lines_data(budget_lines,options,lines,start,end)
        return lines
        #================================= End Haresh Test Code ==========================

        
        for li in budget_lines:
            if li.program_code_id and li.program_code_id.item_id:
                key_i = int(li.program_code_id.item_id.item)
                if key_i >= 100 and key_i <= 199:
                    item_list.update({'1': item_list.get('1') + [li]})
                elif key_i >= 200 and key_i <= 299:
                    item_list.update({'2': item_list.get('2') + [li]})
                elif key_i >= 300 and key_i <= 399:
                    item_list.update({'3': item_list.get('3') + [li]})
                elif key_i >= 400 and key_i <= 499:
                    item_list.update({'4': item_list.get('4') + [li]})
                elif key_i >= 500 and key_i <= 599:
                    item_list.update({'5': item_list.get('5') + [li]})
                elif key_i >= 600 and key_i <= 699:
                    item_list.update({'6': item_list.get('6') + [li]})
                elif key_i >= 700 and key_i <= 799:
                    item_list.update({'7': item_list.get('7') + [li]})
                elif key_i >= 800 and key_i <= 899:
                    item_list.update({'8': item_list.get('8') + [li]})
                elif key_i >= 900 and key_i <= 999:
                    item_list.update({'9': item_list.get('9') + [li]})
        program_code_list = [] # To prevent duplication of program code
        need_total = False # If user select Expenditure Item then true this flag to display total
        for fc, budget_lines in item_list.items():
            if budget_lines:
 
                main_id = False # id for line
 
                # To append list with all columns
                main_list = []
 
                for b_line in budget_lines:
                    prog_code = b_line.program_code_id
                    if not main_id:
                        main_id = b_line
                    if prog_code in program_code_list:
                        continue
 
                    columns = []
                    col_data_list = [] # Used to add total
 
                    # Program code struture view fields
                    need_to_skip = 0
                    for column in options['selected_program_fields']:
                        if column in ('Year', 'Año'):
                            year = prog_code.year and prog_code.year.name or ''
                            columns.append({'name': str(year)})
                            col_data_list.append(str(year))
                            need_to_skip += 1
                        if column in ('Program', 'Programa'):
                            program = prog_code.program_id and prog_code.program_id.key_unam or ''
                            columns.append({'name': str(program)})
                            col_data_list.append(str(program))
                            need_to_skip += 1
                        if column in ('Sub Program', 'Subprograma'):
                            subprogram = prog_code.sub_program_id and prog_code.sub_program_id.sub_program or ''
                            columns.append({'name': str(subprogram)})
                            col_data_list.append(str(subprogram))
                            need_to_skip += 1
                        if column in ('Dependency', 'Dependencia'):
                            dependency = prog_code.dependency_id and prog_code.dependency_id.dependency or ''
                            columns.append({'name': str(dependency)})
                            col_data_list.append(str(dependency))
                            need_to_skip += 1
                        if column in ('Sub Dependency', 'Subdependencia'):
                            subdependency = prog_code.sub_dependency_id and prog_code.sub_dependency_id.sub_dependency or ''
                            columns.append({'name': str(subdependency)})
                            col_data_list.append(str(subdependency))
                            need_to_skip += 1
                        if column in ('Expenditure Item', 'Partida de Gasto (PAR)'):
                            item = prog_code.item_id and prog_code.item_id.item or ''
                            columns.append({'name': str(item)})
                            col_data_list.append(str(item))
                            need_to_skip += 1
                        if column in ('Check Digit', 'Dígito Verificador'):
                            check_digit = prog_code.check_digit or ''
                            columns.append({'name': str(check_digit)})
                            col_data_list.append(str(check_digit))
                            need_to_skip += 1
                        if column in ('Source of Resource', 'Origen del Recurso'):
                            sor = prog_code.resource_origin_id and prog_code.resource_origin_id.key_origin or ''
                            columns.append({'name': str(sor)})
                            col_data_list.append(str(sor))
                            need_to_skip += 1
                        if column in ('Institutional Activity', 'Actividad Institucional'):
                            ai = prog_code.institutional_activity_id and prog_code.institutional_activity_id.number or ''
                            columns.append({'name': str(ai)})
                            col_data_list.append(str(ai))
                            need_to_skip += 1
                        if column in ('Conversion of Budgetary Program', 'Conversión de Programa Presupuestario'):
                            conversion = prog_code.budget_program_conversion_id and \
                                         prog_code.budget_program_conversion_id.shcp and \
                                         prog_code.budget_program_conversion_id.shcp.name or ''
                            columns.append({'name': str(conversion)})
                            col_data_list.append(str(conversion))
                            need_to_skip += 1
                        if column in ('SHCP items', 'Conversión Con Partida (CONPA)'):
                            shcp = prog_code.conversion_item_id and prog_code.conversion_item_id.federal_part or ''
                            columns.append({'name': str(shcp)})
                            col_data_list.append(str(shcp))
                            need_to_skip += 1
                        if column in ('Type of Expenditure', 'Tipo de Gasto'):
                            expense_type = prog_code.expense_type_id and prog_code.expense_type_id.key_expenditure_type or ''
                            columns.append({'name': str(expense_type)})
                            col_data_list.append(str(expense_type))
                            need_to_skip += 1
                        if column in ('Geographic Location', 'Ubicación Geográfica'):
                            location = prog_code.location_id and prog_code.location_id.state_key or ''
                            columns.append({'name': str(location)})
                            col_data_list.append(str(location))
                            need_to_skip += 1
                        if column in ('Wallet Key', 'Clave Cartera'):
                            wallet_key = prog_code.portfolio_id and prog_code.portfolio_id.wallet_password or ''
                            columns.append({'name': str(wallet_key)})
                            col_data_list.append(str(wallet_key))
                            need_to_skip += 1
                        if column in ('Type of Project', 'Tipo de Proyecto'):
                            project_type = prog_code.project_type_id and prog_code.project_type_id.project_type_identifier or ''
                            columns.append({'name': str(project_type)})
                            col_data_list.append(str(project_type))
                            need_to_skip += 1
                        if column in ('Project Number', 'Número de Proyecto'):
                            project_number = prog_code.project_number or ''
                            columns.append({'name': str(project_number)})
                            col_data_list.append(str(project_number))
                            need_to_skip += 1
                        if column in ('Stage', 'Etapa'):
                            stage = prog_code.stage_id and prog_code.stage_id.stage_identifier or ''
                            columns.append({'name': str(stage)})
                            col_data_list.append(str(stage))
                            need_to_skip += 1
                        if column in ('Type of Agreement', 'Tipo de Convenio'):
                            agreement_type = prog_code.agreement_type_id and prog_code.agreement_type_id.agreement_type or ''
                            columns.append({'name': str(agreement_type)})
                            col_data_list.append(str(agreement_type))
                            need_to_skip += 1
                        if column in ('Agreement Number', 'Número de Convenio'):
                            agreement_number = prog_code.number_agreement or ''
                            columns.append({'name': str(agreement_number)})
                            col_data_list.append(str(agreement_number))
                            need_to_skip += 1
 
                    all_b_lines = b_line_obj.search([('program_code_id', '=', prog_code.id),
                                                     ('start_date', '>=', start), ('end_date', '<=', end)])
                    annual_modified = 0
                    adequacies_lines = adequacies_line_obj.search([('program', '=', prog_code.id),
                                                                   ('adequacies_id.state', '=', 'accepted')])
                    for ad_line in adequacies_lines:
                        if ad_line.line_type == 'increase':
                            annual_modified += ad_line.amount
                        elif ad_line.line_type == 'decrease':
                            annual_modified -= ad_line.amount
                    #authorized = sum(x.authorized for x in all_b_lines)
                    authorized = sum(x.authorized)
                    annual_modified = annual_modified
                    for column in options['selected_budget_control']:
                        amt = 0
                        if column in ('Partida de Gasto (PAR)', 'Expense Item'):
                            amt = b_line.item_id and b_line.item_id.item or ''
                            need_total = True
                        elif column in ('Authorized', 'Autorizado'):
                            amt = authorized
                        elif column in ('Assigned Total Annual', 'Total Asignado Anual'):
                            assigned = sum(x.assigned for x in all_b_lines)
                            amt = assigned
                        elif column in ('Annual Modified', 'Modificado Anual'):
                            amt = annual_modified
                        elif column in ('Assigned 1st Trimester', 'Asignado 1er Trimestre'):
                            amt = self._get_sum_trimster(all_b_lines, 1, 1, 3, 31)
                        elif column in ('Assigned 2nd Trimester', 'Asignado 2do Trimestre'):
                            amt = self._get_sum_trimster(all_b_lines, 4, 1, 6, 30)
                        elif column in ('Assigned 3rd Trimester', 'Asignado 3er Trimestre'):
                            amt = self._get_sum_trimster(all_b_lines, 7, 1, 9, 30)
                        elif column in ('Assigned 4th Trimester', 'Asignado 4to Trimestre'):
                            amt = self._get_sum_trimster(all_b_lines, 10, 1, 12, 31)
                        elif column in ('Per Exercise', 'Por Ejercer'):
                            amt = sum(x.available for x in all_b_lines)
                        elif column in ('Available', 'Disponible'):
                            amt = sum(x.available for x in all_b_lines)
                            
                        if isinstance(amt, float) or isinstance(amt, int):
                            columns.append({'class':'number','float_name': amt,'name': formatLang(self.env, amt, currency_obj=False)})
                        else:
                            columns.append({'float_name': amt,'name': amt})
                    if need_total:
                        main_list.append(col_data_list)
 
                    lines.append({
                        'id': b_line.id,
                        'name': prog_code.program_code,
                        'columns': columns,
                        'level': 0,
                        'unfoldable': False,
                        'unfolded': True,
                    })
                    program_code_list.append(prog_code)
                if need_total:
                    list_with_data = main_list
                    list_tot_data = list(map(sum, map(lambda l: map(float, l), zip(*list_with_data))))
                    main_cols = []
                    counter = 0
                    for l in list_tot_data:
                        if counter != 0:
                            main_cols.append({'class':'number','name': formatLang(self.env, l, currency_obj=False),'float_name': l})
                             
                        else:
                            main_cols.append({'name': '','float_name': ''})
                        counter += 1
                    if main_cols:
                        lines.append({
                            'id': main_id,
                            'name': _('Total'),
                            'class': 'total',
                            'level': 2,
                            'columns': main_cols,
                        })
                        
        selected_line_pages = options['selected_line_pages']
        all_list = []
        for s in selected_line_pages:
            s = int(s)
            start = (s - 1) * 500 + 1
            end = s * 500
            for i in range(start - 1, end):
                try:
                    all_list.append(lines[i])
                except:
                    pass
        if need_total:
            new_total_list = []
            new_total_list_all = []
            for al in all_list:
                if al.get('name') == 'Total':
                    if new_total_list:
                        list_with_data = []
                        for l in new_total_list:
                            new_list = []
                            for d in l:
                                new_list.append(d.get('float_name',0.0))
                            list_with_data.append(new_list)
                        list_tot_data = list(map(sum, map(lambda l: map(float, l), zip(*list_with_data))))
                        main_cols = []
                        counter = 0
                        for l in list_tot_data:
                            if counter > need_to_skip:
                                main_cols.append({'class':'number','name': formatLang(self.env, l, currency_obj=False),'float_name': l})
                            else:
                                main_cols.append({'name': '','float_name': ''})
                            counter += 1
                        al.update({
                            'id': 0,
                            'name': _('Subtotal'),
                            'class': 'total',
                            'level': 2,
                            'columns': main_cols,
                        })
                    new_total_list = []
                    new_total_list_all.append(al.get('columns'))
                else:
                    new_total_list.append(al.get('columns'))

            if new_total_list:
                list_with_data = []
                for l in new_total_list:
                    new_list = []
                    for d in l:
                        new_list.append(d.get('float_name',0.0))
                    list_with_data.append(new_list)

                list_tot_data = list(map(sum, map(lambda l: map(float, l), zip(*list_with_data))))
                main_cols = []
                counter = 0

                for l in list_tot_data:
                    if counter > need_to_skip:
                        main_cols.append({'class':'number','name': formatLang(self.env, l, currency_obj=False),'float_name': l})
                    else:
                        main_cols.append({'name': '','float_name': ''})
                    counter += 1
                all_list.append({
                    'id': 0,
                    'name': _('Subtotal'),
                    'class': 'total',
                    'level': 2,
                    'columns': main_cols,
                })
                new_total_list_all.append(main_cols)
            if len(all_list) > 0:

            #====== New Total Page =======#
                if new_total_list_all:
                    # need_to_add += 1
                    list_with_data = []
                    for l in new_total_list_all:
                        new_list = []
                        for d in l:
                            if d.get('name') == '':
                                new_list.append(0.0)
                            else:
                                new_list.append(d.get('float_name',0.0))
                             
                        list_with_data.append(new_list)
                    list_tot_data = list(map(sum, map(lambda l: map(float, l), zip(*list_with_data))))
                    main_cols = []
                    counter = 0
                    for l in list_tot_data:
                        if counter > need_to_skip:
                            main_cols.append({'class':'number','name': formatLang(self.env, l, currency_obj=False),'float_name': l})
                        else:
                            main_cols.append({'name': '','float_name': ''})
                        counter += 1
                    all_list.append({
                        'id': 0,
                        'name': _('Total'),
                        'class': 'total',
                        'level': 2,
                        'columns': main_cols,
                    })
                return all_list
            
            new_lines = []
            need_to_add = 0
            new_total_list = []
            new_total_list_all = []
            for al in lines[:500]:
                if al.get('name') == 'Total':
                    if new_total_list:
                        list_with_data = []
                        for l in new_total_list:
                            new_list = []
                            for d in l:
                                new_list.append(d.get('float_name',0.0))
                            list_with_data.append(new_list)
                        list_tot_data = list(map(sum, map(lambda l: map(float, l), zip(*list_with_data))))
                        main_cols = []
                        counter = 0
                        for l in list_tot_data:
                            if counter > need_to_skip:
                                main_cols.append({'class':'number','name': formatLang(self.env, l, currency_obj=False),'float_name': l})
                            else:
                                main_cols.append({'name': '','float_name': ''})
                            counter += 1
                        al.update({
                            'id': 0,
                            'name': _('SubTotal'),
                            'class': 'total',
                            'level': 2,
                            'columns': main_cols,
                        })
                             
                    new_total_list = []
                    new_lines.append(al)
                    new_total_list_all.append(al.get('columns'))
                else:
                    new_total_list.append(al.get('columns'))
                    new_lines.append(al)
            if new_total_list:
                need_to_add += 1
                list_with_data = []
                for l in new_total_list:
                    new_list = []
                    for d in l:
                        new_list.append(d.get('float_name',0.0))
                    list_with_data.append(new_list)
                list_tot_data = list(map(sum, map(lambda l: map(float, l), zip(*list_with_data))))
                main_cols = []
                counter = 0
                for l in list_tot_data:
                    if counter > need_to_skip:
                        main_cols.append({'class':'number','name': formatLang(self.env, l, currency_obj=False),'float_name': l})
                    else:
                        main_cols.append({'name': '','float_name': ''})
                    counter += 1
                new_lines.append({
                    'id': 0,
                    'name': _('Subtotal'),
                    'class': 'total',
                    'level': 2,
                    'columns': main_cols,
                })
                new_total_list_all.append(main_cols)
        #====== New Total Page =======#
            if new_total_list_all:
                need_to_add += 1
                list_with_data = []
                for l in new_total_list_all:
                    new_list = []
                    for d in l:
                        if d.get('name') == '':
                            new_list.append(0.0)
                        else:
                            new_list.append(d.get('float_name',0.0))
                         
                    list_with_data.append(new_list)
                list_tot_data = list(map(sum, map(lambda l: map(float, l), zip(*list_with_data))))
                main_cols = []
                counter = 0
                for l in list_tot_data:
                    if counter > need_to_skip:
                        main_cols.append({'class':'number','name': formatLang(self.env, l, currency_obj=False),'float_name': l})
                    else:
                        main_cols.append({'name': '','float_name': ''})
                    counter += 1
                new_lines.append({
                    'id': 0,
                    'name': _('Total'),
                    'class': 'total',
                    'level': 2,
                    'columns': main_cols,
                })

            return new_lines[:502]
        else:
            if len(all_list) > 0:
                return all_list
            return lines[:500]

    def _get_report_name(self):
        context = self.env.context
        date_report = fields.Date.from_string(context['date_from']) if context.get(
            'date_from') else fields.date.today()
        return '%s_%s_Summary_Report' % (
            date_report.year,
            str(date_report.month).zfill(2))
