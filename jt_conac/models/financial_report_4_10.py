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
from odoo import models, _,api
import unicodedata
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.misc import formatLang
from odoo.tools import config, date_utils, get_lang
from odoo.tools.misc import xlsxwriter
import base64
import lxml.html
import io

class StatesAndProgramReports(models.AbstractModel):
    _name = "jt_conac.states.and.program.report"
    _inherit = "account.coa.report"
    _description = "States and Program Reports"

    filter_date = {'mode': 'range', 'filter': 'this_month'}
    filter_comparison = {'date_from': '', 'date_to': '', 'filter': 'no_comparison', 'number_period': 1}
    filter_all_entries = False
    filter_journals = False
    filter_analytic = False
    filter_unfold_all = False
    filter_cash_basis = None
    filter_hierarchy = False
    filter_unposted_in_period = False
    MAX_LINES = None

    def _get_templates(self):
        templates = super(StatesAndProgramReports, self)._get_templates()
        templates['main_table_header_template'] = 'jt_budget_mgmt.template_analytic_status_header'
        templates['main_template'] = 'account_reports.main_template'
        return templates

    def _get_columns_name(self, options):
        columns = [{'name': _('Concepto')}]
        if options.get('comparison') and options['comparison'].get('periods'):
            comparison = options.get('comparison')
            period_list = comparison.get('periods')
            period_list.reverse()
            columns += [
                           {'name': _('Aprobado')},
                           {'name': _('Ampliaciones/ (Reducciones)')},
                           {'name': _('Modificado')},
                           {'name': _('Devengado')},
                           {'name': _('Pagado')},
                           {'name': _('Subejercicio')},
                       ] * (len(period_list) + 1)
        else:
            columns = [
                {'name': _('Concepto')}, {'name': _('Aprobado')},
                {'name': _('Ampliaciones/ (Reducciones)')},
                {'name': _('Modificado')},
                {'name': _('Devengado')},
                {'name': _('Pagado')},
                {'name': _('Subejercicio')},
            ]
        return columns

    def strip_accents(self, text):
        return ''.join(char for char in
                       unicodedata.normalize('NFKD', text)
                       if unicodedata.category(char) != 'Mn')

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

    def add_new_lines(self,lines,options,shcp,item_list,level_2_line,name,periods,period_total,main_period_total):

        states_obj = self.env['states.program']
        bud_line_obj = self.env['expenditure.budget.line']
        adeq_obj = self.env['adequacies']
        adequacies = adeq_obj.search([('state', '=', 'accepted')])

        line_cols = []
        
        for period in periods:
            period_name = period.get('string')
            paid_amt = 0
            amt = 0
            ade_amt = 0

            budget_lines = self.env['expenditure.budget.line']
            date_start = datetime.strptime(str(period.get('date_from')), DEFAULT_SERVER_DATE_FORMAT).date()
            date_end = datetime.strptime(str(period.get('date_to')), DEFAULT_SERVER_DATE_FORMAT).date()
            if period.get('period_type') == 'month':
                budget_lines = bud_line_obj.search([('program_code_id.item_id.item','in',item_list),('program_code_id.budget_program_conversion_id.shcp.name','=',shcp),('expenditure_budget_id.state', '=', 'validate'),
                                                    ('state', '=', 'success'),('imported_sessional','=',False)])
                
            elif period.get('period_type') == 'quarter':
                budget_lines = bud_line_obj.search([('program_code_id.item_id.item','in',item_list),('program_code_id.budget_program_conversion_id.shcp.name','=',shcp),('expenditure_budget_id.state', '=', 'validate'),
                                                    ('state', '=', 'success'),('start_date', '>=', date_start),
                                                    ('end_date', '<=', date_end),
                                                    ])
                
            else:
                budget_lines = bud_line_obj.search([('program_code_id.item_id.item','in',item_list),('program_code_id.budget_program_conversion_id.shcp.name','=',shcp),('expenditure_budget_id.state', '=', 'validate'),
                                                    ('start_date', '>=', date_start), ('state', '=', 'success'),
                                                    ('end_date', '<=', date_end),('imported_sessional','=',False)])
            for line in budget_lines:
                if period.get('period_type') == 'month':
                    if date_start >= line.start_date and date_end <= line.end_date:
                        pass
                    else:
                        continue
                
                amt += line.authorized
                

            for ade in adequacies:
                if ade.adaptation_type == 'liquid' and ade.date_of_liquid_adu >= date_start and \
                        ade.date_of_liquid_adu <= date_end:
                    for line in ade.adequacies_lines_ids.filtered(lambda x:x.program and x.program.item_id.item in item_list and x.program.budget_program_conversion_id.shcp.name == shcp):
                        if line.line_type == 'increase':
                            ade_amt += line.amount
                        else:
                            ade_amt -= line.amount

                elif ade.adaptation_type != 'liquid' and ade.date_of_budget_affected >= date_start \
                        and ade.date_of_budget_affected <= date_end:
                    for line in ade.adequacies_lines_ids.filtered(lambda x:x.program and x.program.item_id.item in item_list and x.program.budget_program_conversion_id.shcp.name == shcp):
                        if line.line_type == 'increase':
                            ade_amt += line.amount
                        else:
                            ade_amt -= line.amount

            paid_budget_lines = bud_line_obj.search([('program_code_id.item_id.item','in',item_list),('program_code_id.budget_program_conversion_id.shcp.name','=',shcp),('expenditure_budget_id.state', '=', 'validate'),
                            ('start_date', '>=', date_start), ('state', '=', 'success'),
                            ('end_date', '<=', date_end)])

            program_code_ids = paid_budget_lines.mapped('program_code_id')
            for program in program_code_ids: 
                self.env.cr.execute("select coalesce(sum(abs(line.balance)+abs(line.tax_price_cr)),0) as committed from account_move_line line,account_move amove where line.program_code_id in %s and amove.id=line.move_id and amove.payment_state=%s and amove.invoice_date >= %s and amove.invoice_date <= %s", (tuple(program.ids),'paid',date_start,date_end))
                my_datas = self.env.cr.fetchone()
                if my_datas:
                    paid_amt += my_datas[0]              
                

            line_cols += [self._format({'name': amt},figure_type='float'),
                      self._format({'name': ade_amt},figure_type='float'),
                      self._format({'name': amt + ade_amt},figure_type='float'),
                      {'name': ''}, 
                      self._format({'name': paid_amt},figure_type='float'),
                      self._format({'name': amt + ade_amt},figure_type='float')]                                              
                    
            if period_name in period_total:
                pe_dict = period_total.get(period_name)
                period_total.update({period_name: {'auth': pe_dict.get('auth') + amt,
                                               'ade': pe_dict.get('ade') + ade_amt,
                                               'modi': pe_dict.get('modi') + (amt + ade_amt),
                                               'paid_amt' : pe_dict.get('paid_amt') + paid_amt,
                                               'sub': pe_dict.get('sub') + (amt + ade_amt)}})
            else:
                period_total.update({period_name: {'auth': amt, 'ade': ade_amt,
                                               'modi': amt + ade_amt,
                                               'paid_amt' : paid_amt,
                                               'sub': amt + ade_amt}})
            if period_name in main_period_total:
                pe_dict = main_period_total.get(period_name)
                main_period_total.update(
                    {period_name: {'auth': pe_dict.get('auth') + amt,
                                   'ade': pe_dict.get('ade') + ade_amt,
                                   'modi': pe_dict.get('modi') + (amt + ade_amt),
                                   'paid_amt' : pe_dict.get('paid_amt') + paid_amt,
                                   'sub': pe_dict.get('sub') + (amt + ade_amt)}})
            else:
                main_period_total.update({period_name: {'auth': amt, 'ade': ade_amt,
                                               'modi': amt + ade_amt,
                                               'paid_amt' : paid_amt,
                                               'sub': amt + ade_amt}})

        lines.append({
            'id': 'level_two_1_%s' % level_2_line.id,
            'name': name,
            'columns': line_cols,
            'level': 3,
            'unfoldable': False,
            'unfolded': False,
            'parent_id': 'level_two_%s' % level_2_line.id,
        })
        
        return lines,period_total,main_period_total

    def check_extra_item(self,program_code_id):
        if program_code_id.budget_program_conversion_id and program_code_id.budget_program_conversion_id.shcp and program_code_id.budget_program_conversion_id.shcp.name:
            if 'S243' == program_code_id.budget_program_conversion_id.shcp.name:
                if program_code_id.item_id.item in ['731','732','733','734']:
                    return False
            if 'K027' == program_code_id.budget_program_conversion_id.shcp.name:
                if program_code_id.item_id.item in ['612','622','623','232']:
                    return False
            if 'K009' == program_code_id.budget_program_conversion_id.shcp.name:
                if program_code_id.item_id.item in ['621']:
                    return False
                
        return True
    def _get_lines(self, options, line_id=None):
        states_obj = self.env['states.program']
        bud_line_obj = self.env['expenditure.budget.line']
        adeq_obj = self.env['adequacies']
        adequacies = adeq_obj.search([('state', '=', 'accepted')])

        comparison = options.get('comparison')
        periods = []
        if comparison and comparison.get('filter') != 'no_comparison':
            period_list = comparison.get('periods')
            period_list.reverse()
            periods = [period for period in period_list]
        periods.append(options.get('date'))

        period_shcp_auth_dict = {}
        main_period_total = {}
        budget_lines = self.env['expenditure.budget.line']
        for period in periods:
            period_name = period.get('string')
            date_start = datetime.strptime(str(period.get('date_from')), DEFAULT_SERVER_DATE_FORMAT).date()
            date_end = datetime.strptime(str(period.get('date_to')), DEFAULT_SERVER_DATE_FORMAT).date()
            if period.get('period_type') == 'month':
                budget_lines = bud_line_obj.search([('expenditure_budget_id.state', '=', 'validate'),
                                                    ('state', '=', 'success'),('imported_sessional','=',False)])

#             if period.get('period_type') == 'month':
#                 budget_lines = bud_line_obj.search([('expenditure_budget_id.state', '=', 'validate'),
#                                                     ('state', '=', 'success'),('start_date', '>=', date_start),
#                                                     ('end_date', '<=', date_end),
#                                                     ])
                
            elif period.get('period_type') == 'quarter':
                budget_lines = bud_line_obj.search([('expenditure_budget_id.state', '=', 'validate'),
                                                    ('state', '=', 'success'),('start_date', '>=', date_start),
                                                    ('end_date', '<=', date_end),
                                                    ])
                
            else:
                budget_lines = bud_line_obj.search([('expenditure_budget_id.state', '=', 'validate'),
                                                    ('start_date', '>=', date_start), ('state', '=', 'success'),
                                                    ('end_date', '<=', date_end),('imported_sessional','=',False)])
            
            for line in budget_lines:
                if period.get('period_type') == 'month':
                    if date_start >= line.start_date and date_end <= line.end_date:
                        pass
                    else:
                        continue
#                 if line.program_code_id and line.program_code_id.budget_program_conversion_id and \
#                         line.program_code_id.budget_program_conversion_id.desc:
                if line.program_code_id and line.program_code_id.desc_program and self.check_extra_item(line.program_code_id):
                    heading_name = line.program_code_id.desc_program.upper()
                    heading_name = self.strip_accents(heading_name)
                    if period_name in period_shcp_auth_dict.keys():
                        pe_dict = period_shcp_auth_dict.get(period_name)
                        if heading_name in pe_dict.keys():
                            pe_dict.update({heading_name: pe_dict.get(heading_name) + [line]})
                        else:
                            pe_dict.update({heading_name: [line]})
                    else:
                        period_shcp_auth_dict.update({period_name: {heading_name: [line]}})
        for period, section_data in period_shcp_auth_dict.items():
            for section, line_list in section_data.items():
                shcp_dict = {}
                for line in line_list:
                    shcp = line.program_code_id.budget_program_conversion_id.shcp
                    if shcp not in shcp_dict:
                        shcp_dict.update({shcp: line.authorized})
                    else:
                        shcp_dict.update({shcp: shcp_dict.get(shcp) + line.authorized})
                sec_dict = period_shcp_auth_dict.get(period)
                sec_dict.update({section: shcp_dict})

        period_prog_dict_ade = {}
        for period in periods:
            period_name = period.get('string')
            prog_dict_ade = {}
            date_from = datetime.strptime(str(period.get('date_from')), DEFAULT_SERVER_DATE_FORMAT).date()
            date_to = datetime.strptime(str(period.get('date_to')), DEFAULT_SERVER_DATE_FORMAT).date()
            for ade in adequacies:
                if ade.adaptation_type == 'liquid' and ade.date_of_liquid_adu >= date_from and \
                        ade.date_of_liquid_adu <= date_to:
                    for line in ade.adequacies_lines_ids:
                        if line.program:
                            prog_name = line.program.desc_program and line.program.desc_program.upper() or ''
                            prog_name = self.strip_accents(prog_name)
                            shcp = line.program.budget_program_conversion_id.shcp.name
                            if prog_name in prog_dict_ade.keys():
                                shcp_dict = prog_dict_ade.get(prog_name)[0]
                                if shcp in shcp_dict.keys():
                                    if line.line_type == 'increase':
                                        shcp_dict.update({shcp: shcp_dict.get(shcp) + line.amount})
                                    else:
                                        shcp_dict.update({shcp: shcp_dict.get(shcp) - line.amount})
                                else:
                                    if line.line_type == 'increase':
                                        shcp_dict.update({shcp: line.amount})
                                    else:
                                        shcp_dict.update({shcp: -line.amount})
                            else:
                                if line.line_type == 'increase':
                                    prog_dict_ade.update({prog_name: [{shcp: line.amount}]})
                                else:
                                    prog_dict_ade.update({prog_name: [{shcp: -line.amount}]})

                elif ade.adaptation_type != 'liquid' and ade.date_of_budget_affected >= date_from \
                        and ade.date_of_budget_affected <= date_to:
                    for line in ade.adequacies_lines_ids:
                        if line.program:
                            prog_name = line.program.desc_program and line.program.desc_program.upper() or ''
                            prog_name = self.strip_accents(prog_name)
                            shcp = line.program.budget_program_conversion_id.shcp.name
                            if prog_name in prog_dict_ade.keys():
                                shcp_dict = prog_dict_ade.get(prog_name)[0]
                                if shcp in shcp_dict.keys():
                                    if line.line_type == 'increase':
                                        shcp_dict.update({shcp: shcp_dict.get(shcp) + line.amount})
                                    else:
                                        shcp_dict.update({shcp: shcp_dict.get(shcp) - line.amount})
                                else:
                                    if line.line_type == 'increase':
                                        shcp_dict.update({shcp: line.amount})
                                    else:
                                        shcp_dict.update({shcp: -line.amount})
                            else:
                                if line.line_type == 'increase':
                                    prog_dict_ade.update({prog_name: [{shcp: line.amount}]})
                                else:
                                    prog_dict_ade.update({prog_name: [{shcp: -line.amount}]})
            period_prog_dict_ade.update({period_name: prog_dict_ade})

        period_paid_amount_dict = {}
        for period in periods:
            period_name = period.get('string')
            prog_dict_paid = {}
             
            period_date_from = datetime.strptime(str(period.get('date_from')), DEFAULT_SERVER_DATE_FORMAT).date()
            period_date_to = datetime.strptime(str(period.get('date_to')), DEFAULT_SERVER_DATE_FORMAT).date()
            
            period_budget_lines = bud_line_obj.search([('expenditure_budget_id.state', '=', 'validate'),
                            ('start_date', '<=', period_date_from), ('state', '=', 'success'),
                            ('end_date', '>=', period_date_to)])
            #shcp_budget_line = period_budget_lines.filtered(lambda x:x.program_code_id.budget_program_conversion_id.shcp.id==shcp.id)
            program_code_ids = period_budget_lines.mapped('program_code_id')
            for program in program_code_ids: 
                prog_name = program.desc_program and program.desc_program.upper() or ''
                prog_name = self.strip_accents(prog_name)
                shcp = program.budget_program_conversion_id.shcp.name
                self.env.cr.execute("select coalesce(sum(abs(line.balance)+abs(line.tax_price_cr)),0) as committed from account_move_line line,account_move amove where line.program_code_id in %s and amove.id=line.move_id and amove.payment_state=%s and amove.invoice_date >= %s and amove.invoice_date <= %s", (tuple(program.ids),'paid',period_date_from,period_date_to))
                my_datas = self.env.cr.fetchone()
                paid_amt = 0
                if my_datas:
                    paid_amt = my_datas[0]              
                
                if prog_name in prog_dict_paid.keys():
                    shcp_dict = prog_dict_paid.get(prog_name)[0]
                    
                    if shcp in shcp_dict.keys():
                        shcp_dict.update({shcp: shcp_dict.get(shcp) + paid_amt})
                    else:
                        shcp_dict.update({shcp: paid_amt})
                else:
                    prog_dict_paid.update({prog_name: [{shcp: paid_amt}]})
                    
            period_paid_amount_dict.update({period_name: prog_dict_paid})
            
        lines = []
        
        hierarchy_lines = states_obj.sudo().search([('parent_id', '=', False)], order='code')
        for line in hierarchy_lines:
            lines.append({
                'id': 'hierarchy_' + line.code,
                'name': line.concept,
                'columns': [{'name': ''}, {'name': ''}, {'name': ''},
                            {'name': ''}, {'name': ''}, {'name': ''}] * len(periods),
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
            })
            level_1_lines = states_obj.search([('parent_id', '=', line.id)])
            for level_1_line in level_1_lines:
                lines.append({
                        'id': 'level_one_%s' % level_1_line.id,
                    'name': level_1_line.concept,
                    'columns': [{'name': ''}, {'name': ''}, {'name': ''},
                                {'name': ''}, {'name': ''}, {'name': ''}] * len(periods),
                    'level': 2,
                    'unfoldable': True,
                    'unfolded': True,
                    'parent_id': 'hierarchy_' + line.code,
                })
                level_2_lines = states_obj.search([('parent_id', '=', level_1_line.id)])
                for level_2_line in level_2_lines:
                    lines.append({
                        'id': 'level_two_%s' % level_2_line.id,
                        'name': level_2_line.concept,
                        'columns': [{'name': ''}, {'name': ''}, {'name': ''},
                                    {'name': ''}, {'name': ''}, {'name': ''}] * len(periods),
                        'level': 2,
                        'unfoldable': True,
                        'unfolded': True,
                        'parent_id': 'hierarchy_' + line.code,
                    })
                    line_concept = level_2_line.concept.upper()
                    line_concept = self.strip_accents(line_concept)

                    concept_dict = {}
                    shcp_list = []
                    period_total = {}
                    
                    becas = self.env.ref('jt_conac.27').id
                    mantenimiento = self.env.ref('jt_conac.28').id
                    obras = self.env.ref('jt_conac.29').id
                    
                    if becas and becas== level_2_line.id:
                        lines,period_total,main_period_total = self.add_new_lines(lines,options,'S243',['731','732','733','734'],level_2_line,'S243 Becas',periods,period_total,main_period_total)
                    elif mantenimiento and mantenimiento== level_2_line.id:
                        lines,period_total,main_period_total = self.add_new_lines(lines,options,'K027',['612','622','623','232'],level_2_line,'K027 Mantenimiento',periods,period_total,main_period_total)
                    elif obras and obras== level_2_line.id:
                        lines,period_total,main_period_total = self.add_new_lines(lines,options,'K009',['621'],level_2_line,'K009 Obras',periods,period_total,main_period_total)
                    
                    else:
                        for period in periods:
                            period_name = period.get('string')
                            if period_name in period_shcp_auth_dict.keys():
                                if line_concept in period_shcp_auth_dict.get(period_name):
                                    for shcp, amt in period_shcp_auth_dict.get(period_name).get(line_concept).items():
                                        if period_name in concept_dict:
                                            shcp_dict = concept_dict.get(period_name)
                                            if shcp in shcp_dict:
                                                shcp_dict.update({shcp: shcp_dict.get(shcp) + amt})
                                            else:
                                                shcp_dict.update({shcp: amt})
                                        else:
                                            concept_dict.update({period_name: {shcp: amt}})
                                        if shcp not in shcp_list:
                                            shcp_list.append(shcp)
                        for shcp in shcp_list:
                            line_cols = []
                            for period in periods:
                                period_name = period.get('string')
                                if period_name in concept_dict:
                                    if shcp in concept_dict.get(period_name).keys():
                                        paid_amt = 0
                                        amt = concept_dict.get(period_name).get(shcp)
                                        ade_amt = 0
                                        
                                        if period_name in period_prog_dict_ade.keys():
                                            per_dict = period_prog_dict_ade.get(period_name)
                                            if line_concept in per_dict.keys():
                                                shcp_dict = per_dict.get(line_concept)[0]
                                                if shcp.name in shcp_dict.keys():
                                                    ade_amt = shcp_dict.get(shcp.name)
                                        if period_name in period_paid_amount_dict.keys():
                                            per_dict = period_paid_amount_dict.get(period_name)
                                            if line_concept in per_dict.keys():
                                                shcp_dict = per_dict.get(line_concept)[0]
                                                if shcp.name in shcp_dict.keys():
                                                    paid_amt = shcp_dict.get(shcp.name)
                                        
                                        
                                        if period_name in period_total:
                                            pe_dict = period_total.get(period_name)
                                            period_total.update({period_name: {'auth': pe_dict.get('auth') + amt,
                                                                           'ade': pe_dict.get('ade') + ade_amt,
                                                                           'modi': pe_dict.get('modi') + (amt + ade_amt),
                                                                           'paid_amt' : pe_dict.get('paid_amt') + paid_amt,
                                                                           'sub': pe_dict.get('sub') + (amt + ade_amt)}})
                                        else:
                                            period_total.update({period_name: {'auth': amt, 'ade': ade_amt,
                                                                           'modi': amt + ade_amt,
                                                                           'paid_amt' : paid_amt,
                                                                           'sub': amt + ade_amt}})
                                        if period_name in main_period_total:
                                            pe_dict = main_period_total.get(period_name)
                                            main_period_total.update(
                                                {period_name: {'auth': pe_dict.get('auth') + amt,
                                                               'ade': pe_dict.get('ade') + ade_amt,
                                                               'modi': pe_dict.get('modi') + (amt + ade_amt),
                                                               'paid_amt' : pe_dict.get('paid_amt') + paid_amt,
                                                               'sub': pe_dict.get('sub') + (amt + ade_amt)}})
                                        else:
                                            main_period_total.update({period_name: {'auth': amt, 'ade': ade_amt,
                                                                           'modi': amt + ade_amt,
                                                                           'paid_amt' : paid_amt,
                                                                           'sub': amt + ade_amt}})
                                        line_cols += [self._format({'name': amt},figure_type='float'),
                                                  self._format({'name': ade_amt},figure_type='float'),
                                                  self._format({'name': amt + ade_amt},figure_type='float'),
                                                  {'name': ''}, 
                                                  self._format({'name': paid_amt},figure_type='float'),
                                                  self._format({'name': amt + ade_amt},figure_type='float')]                                              
                                    else:
                                        line_cols += [{'name': ''}] * 6
                                else:
                                    line_cols += [{'name': ''}] * 6
                            name = shcp.name
                            if shcp.desc:
                                name += ' '
                                name += shcp.desc
                            lines.append({
                                'id': 'level_two_%s' % shcp.id,
                                'name': name,
                                'columns': line_cols,
                                'level': 3,
                                'unfoldable': False,
                                'unfolded': False,
                                'parent_id': 'level_two_%s' % level_2_line.id,
                            })

                    total_cols = []
                    need_to_add = False
                    for period in periods:
                        period_name = period.get('string')
                        if period_name in period_total:
                            pe_dict = period_total.get(period_name)
                            total_cols += [self._format({'name': pe_dict.get('auth')},figure_type='float'),
                                    self._format({'name': pe_dict.get('ade')},figure_type='float'),
                                    self._format({'name': pe_dict.get('modi')},figure_type='float'),
                                    {'name': ''},
                                    self._format({'name': pe_dict.get('paid_amt')},figure_type='float'),
                                    self._format({'name': pe_dict.get('sub')},figure_type='float')]
                            if not need_to_add:
                                need_to_add = True
                        else:
                            total_cols += [{'name': ''}] * 6
                    if need_to_add:
                        lines.append({
                            'id': 'level_two',
                            'name': _('Total'),
                            'columns': total_cols,
                            'level': 4,
                            'class': 'total',
                            'unfoldable': False,
                            'unfolded': False,
                            'parent_id': 'level_two_%s' % level_2_line.id,
                        })
        main_total_cols = []
        need_to_add = False
        for period in periods:
            period_name = period.get('string')
            if period_name in main_period_total:
                pe_dict = main_period_total.get(period_name)
                main_total_cols += [self._format({'name': pe_dict.get('auth')},figure_type='float'),
                                    self._format({'name': pe_dict.get('ade')},figure_type='float'),
                                    self._format({'name': pe_dict.get('modi')},figure_type='float'),
                                    {'name': ''},
                                    self._format({'name': pe_dict.get('paid_amt')},figure_type='float'),
                                    self._format({'name': pe_dict.get('sub')},figure_type='float')]                                    
                if not need_to_add:
                    need_to_add = True
            else:
                main_total_cols += [{'name': ''}] * 6

        if self.env.user.lang == 'es_MX':                
            lines.append({
                'id': 'hierarchy_' + str(line.id),
                'name': 'Gran Total',
                'columns': main_total_cols,
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
            })
        else:
            lines.append({
                'id': 'hierarchy_' + str(line.id),
                'name': 'Main Total',
                'columns': main_total_cols,
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
            })
            
        return lines
    def _get_report_name(self):
        return _("States and Program Reports")

    @api.model
    def _get_super_columns(self, options):
        date_cols = options.get('date') and [options['date']] or []
        date_cols += (options.get('comparison') or {}).get('periods', [])
        columns = reversed(date_cols)
        return {'columns': columns, 'x_offset': 1, 'merge': 6}

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
        }

        body = self.env['ir.ui.view'].render_template(
            "account_reports.print_template",
            values=dict(rcontext),
        )
        body_html = self.with_context(print_mode=True,get_sign_col=True).get_html(options)
        body_html = body_html.replace(b'<div class="o_account_reports_header">',b'<div style="display:none;">')

        body = body.replace(b'<body class="o_account_reports_body_print">', b'<body class="o_account_reports_body_print">' + body_html)
        if minimal_layout:
            header = ''
            footer = self.env['ir.actions.report'].render_template("web.internal_layout", values=rcontext)
            spec_paperformat_args = {'data-report-margin-top': 10, 'data-report-header-spacing': 10}
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
            header = self.env['ir.actions.report'].render_template("jt_conac.external_layout_of_analytical_states_and_program_reports", values=rcontext)
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
    
        header_title = _('''NATIONAL AUTONOMOUS UNIVERSITY OF MEXICO\nSTATES AND PROGRAM REPORTS''')
        header_title += "\n"
        header_title += str(header_date)
        sheet.merge_range(y_offset, col, 5, col + 6,
                          header_title, super_col_style)
        y_offset += 6
        col = 1
        currect_time_msg = "Fecha y hora de impresión: "
        currect_time_msg += datetime.today().strftime('%d/%m/%Y %H:%M')
        sheet.merge_range(y_offset, col, y_offset, col + 6,
                          currect_time_msg, currect_date_style)
        y_offset += 1
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
                    'options': options,
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
    
     
    
