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


class BudgetSummaryReportDownload(models.TransientModel):

    _name = 'summary.report.download'
    _description = 'Budget Summary Report Download'

    state = fields.Selection([('draft', 'Draft'), ('request', 'Request'),
                              ('download', 'Download')], default='draft')
    name = fields.Char("Name")
    report_file = fields.Binary("Download Report", filters='.xls')

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

    # Budget Control Related fields
    budget_control_ids = fields.Many2many(
        'budget.control', string='Budget Control', translate=True)

    # Program Code Section Related fields
    code_section_ids = fields.Many2many(
        'code.structure', string='Programming Code Section', translate=True)
    program_ids = fields.Many2many('program', string='Program')
    sub_program_ids = fields.Many2many('sub.program', string='Sub-Program')
    dependency_ids = fields.Many2many('dependency', string='Dependency')
    sub_dependency_ids = fields.Many2many(
        'sub.dependency', string='Sub-Dependency')
    item_ids = fields.Many2many('expenditure.item', string='Expense Item')
    origin_ids = fields.Many2many('resource.origin', string='Origin Resource')
    activity_ids = fields.Many2many(
        'institutional.activity', string='Institutional Activity')
    conpp_ids = fields.Many2many(
        'budget.program.conversion', string='Budget Program Conversion (CONPP)')
    conpa_ids = fields.Many2many(
        'departure.conversion', string='SHCP Games (CONPA)')
    expense_type_ids = fields.Many2many(
        'expense.type', string='Type of Expense (TG)')
    location_ids = fields.Many2many(
        'geographic.location', string='Geographic Location (UG)')
    wallet_ids = fields.Many2many('key.wallet', string='Wallet Key (CC)')
    project_type_ids = fields.Many2many(
        'project.type', string='Project Type (TP)')
    stage_ids = fields.Many2many('stage', string='Stage (E)')
    agreement_type_ids = fields.Many2many(
        'agreement.type', string='Type of agreement (TC)')

    favourite_report_id = fields.Many2one(
        'favourite.summary.report', string='Favourite Report')
    favourite_name = fields.Char('Name')

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

    def request_data(self):
        print('aqui2')
        # Search Programs
        domain = [('state', '=', 'validated')]
        if self.program_ids:
            domain.append(('program_id', 'in', self.program_ids.ids))
        if self.sub_program_ids:
            domain.append(('sub_program_id', 'in', self.sub_program_ids.ids))
        if self.dependency_ids:
            domain.append(('dependency_id', 'in', self.dependency_ids.ids))
        if self.sub_dependency_ids:
            domain.append(('sub_dependency_id', 'in',
                           self.sub_dependency_ids.ids))
        if self.item_ids:
            domain.append(('item_id', 'in', self.item_ids.ids))
        if self.origin_ids:
            domain.append(('resource_origin_id', 'in', self.origin_ids.ids))
        if self.activity_ids:
            domain.append(('institutional_activity_id', 'in', self.activity_ids.ids))
        if self.conpp_ids:
            domain.append(('budget_program_conversion_id', 'in', self.conpp_ids.ids))
        if self.conpa_ids:
            domain.append(('conversion_item_id', 'in', self.conpa_ids.ids))
        if self.expense_type_ids:
            domain.append(('expense_type_id', 'in', self.expense_type_ids.ids))
        if self.location_ids:
            domain.append(('location_id', 'in', self.location_ids.ids))
        if self.wallet_ids:
            domain.append(('portfolio_id', 'in', self.wallet_ids.ids))
        if self.project_type_ids:
            domain.append(('project_type_id', 'in', self.project_type_ids.ids))
        if self.stage_ids:
            domain.append(('stage_id', 'in', self.stage_ids.ids))
        if self.agreement_type_ids:
            domain.append(('agreement_type_id', 'in', self.wallet_ids.ids))

        programs = self.env['program.code'].search(domain, order='item_id')
        code_lines = []
        code_lines_new = []
        bud_line_obj = self.env['expenditure.budget.line']
        start = self.start_date
        end = self.end_date
#         data_with_item = [{1: []}, {2: []}, {3: []}, {4: []}, {5: []}, {6: []}, {7: []}, {8: []}, {9: []}]
#         data_with_item_cron = [{1: []}, {2: []}, {3: []}, {4: []}, {5: []}, {6: []}, {7: []}, {8: []}, {9: []}]
        
        for code in programs:
            #key_i = int(code.item_id.item)
            all_b_lines = bud_line_obj.search([('program_code_id', '=', code.id),
                                               ('expenditure_budget_id.state', '=', 'validate'), ('start_date', '>=', start), ('end_date', '<=', end)])
            if all_b_lines:
                
                code_lines.append({code: all_b_lines})                
                #code_lines_new.append({code.id: all_b_lines.ids})
                              
        data_with_item = [{1: []}, {2: []}, {3: []}, {4: []}, {5: []}, {6: []}, {7: []}, {8: []}, {9: []}]
        data_with_item_cron = [{1: []}, {2: []}, {3: []}, {4: []}, {5: []}, {6: []}, {7: []}, {8: []}, {9: []}]
        for cl in code_lines:
            for code, lines in cl.items():
                key_i = int(code.item_id.item)
                if key_i >= 100 and key_i <= 199:
                    data_with_item[0] = {1: data_with_item[0].get(1) + [{code: lines}]}
                    data_with_item_cron[0] = {1: data_with_item_cron[0].get(1) + [{code.id: lines.ids}]}
                elif key_i >= 200 and key_i <= 299:
                    data_with_item[1] = {2: data_with_item[1].get(2) + [{code: lines}]}
                    data_with_item_cron[1] = {2: data_with_item_cron[1].get(2) + [{code.id: lines.ids}]}
                elif key_i >= 300 and key_i <= 399:
                    data_with_item[2] = {3: data_with_item[2].get(3) + [{code: lines}]}
                    data_with_item_cron[2] = {3: data_with_item_cron[2].get(3) + [{code.id: lines.ids}]}
                elif key_i >= 400 and key_i <= 499:
                    data_with_item[3] = {4: data_with_item[3].get(4) + [{code: lines}]}
                    data_with_item_cron[3] = {4: data_with_item_cron[3].get(4) + [{code.id: lines.ids}]}
                elif key_i >= 500 and key_i <= 599:
                    data_with_item[4] = {5: data_with_item[4].get(5) + [{code: lines}]}
                    data_with_item_cron[4] = {5: data_with_item_cron[4].get(5) + [{code.id: lines.ids}]}
                elif key_i >= 600 and key_i <= 699:
                    data_with_item[5] = {6: data_with_item[5].get(6) + [{code: lines}]}
                    data_with_item_cron[5] = {6: data_with_item_cron[5].get(6) + [{code.id: lines.ids}]}
                elif key_i >= 700 and key_i <= 799:
                    data_with_item[6] = {7: data_with_item[6].get(7) + [{code: lines}]}
                    data_with_item_cron[6] = {7: data_with_item_cron[6].get(7) + [{code.id: lines.ids}]}
                elif key_i >= 800 and key_i <= 899:
                    data_with_item[7] = {8: data_with_item[7].get(8) + [{code: lines}]}
                    data_with_item_cron[7] = {8: data_with_item_cron[7].get(8) + [{code.id: lines.ids}]}
                elif key_i >= 900 and key_i <= 999:
                    data_with_item[8] = {9: data_with_item[8].get(9) + [{code: lines}]}
                    data_with_item_cron[8] = {9: data_with_item_cron[8].get(9) + [{code.id: lines.ids}]}
                                        
#        code_obj = self.env['program.code']
#         data_with_item_cron = [{1: []}, {2: []}, {3: []}, {4: []}, {5: []}, {6: []}, {7: []}, {8: []}, {9: []}]
#         for cl in code_lines_new:
#             for code, lines in cl.items():
#                 code_b = code_obj.browse(code)
#                 key_i = int(code_b.item_id.item)
#                 if key_i >= 100 and key_i <= 199:
#                     data_with_item_cron[0] = {1: data_with_item_cron[0].get(1) + [{code: lines}]}
#                 elif key_i >= 200 and key_i <= 299:
#                     data_with_item_cron[1] = {2: data_with_item_cron[1].get(2) + [{code: lines}]}
#                 elif key_i >= 300 and key_i <= 399:
#                     data_with_item_cron[2] = {3: data_with_item_cron[2].get(3) + [{code: lines}]}
#                 elif key_i >= 400 and key_i <= 499:
#                     data_with_item_cron[3] = {4: data_with_item_cron[3].get(4) + [{code: lines}]}
#                 elif key_i >= 500 and key_i <= 599:
#                     data_with_item_cron[4] = {5: data_with_item_cron[4].get(5) + [{code: lines}]}
#                 elif key_i >= 600 and key_i <= 699:
#                     data_with_item_cron[5] = {6: data_with_item_cron[5].get(6) + [{code: lines}]}
#                 elif key_i >= 700 and key_i <= 799:
#                     data_with_item_cron[6] = {7: data_with_item_cron[6].get(7) + [{code: lines}]}
#                 elif key_i >= 800 and key_i <= 899:
#                     data_with_item_cron[7] = {8: data_with_item_cron[7].get(8) + [{code: lines}]}
#                 elif key_i >= 900 and key_i <= 999:
#                     data_with_item_cron[8] = {9: data_with_item_cron[8].get(9) + [{code: lines}]}


        if code_lines:
            if len(code_lines) <= 5000:
                adequacies_line_obj = self.env['adequacies.lines']
                wb1 = xlwt.Workbook(encoding='utf-8')
                ws1 = wb1.add_sheet('Proforma Summary Report')
                fp = BytesIO()
                header_style = xlwt.easyxf('font: bold 1')
                total_style = xlwt.easyxf('font: bold 1;' 'borders: top thin, right thin, bottom thin, left thin;')

                row = 1
                col = 0
                if self.env.user.lang == 'es_MX':
                    ws1.write(row, col, "Código Programático", header_style)
                else:
                    ws1.write(row, col, "Program Code", header_style)
                for bug_con in self.budget_control_ids:
                    col += 1
                    ws1.write(row, col, bug_con.name, header_style)
                for code_sec in self.code_section_ids:
                    col += 1
                    value = ''
                    if self.env.user.lang == 'es_MX':
                        if code_sec.section == 'year':
                            value = 'AÑO'
                        elif code_sec.section == 'pr':
                            value = 'Programa'
                        elif code_sec.section == 'sp':
                            value = 'Subprograma'
                        elif code_sec.section == 'dep':
                            value = 'Dependencia'
                        elif code_sec.section == 'sd':
                            value = 'Subdependencia'
                        elif code_sec.section == 'par':
                            value = 'Partida de Gasto'
                        elif code_sec.section == 'dv':
                            value = 'Dígito Verificador'
                        elif code_sec.section == 'or':
                            value = 'Origen del Recurso'
                        elif code_sec.section == 'ai':
                            value = 'Actividad Institucional'
                        elif code_sec.section == 'conpp':
                            value = 'Conversion de Programa Presupuestario'
                        elif code_sec.section == 'conpa':
                            value = 'Conversión Con Partida (CONPA)'
                        elif code_sec.section == 'tg':
                            value = 'Tipo de Gasto'
                        elif code_sec.section == 'ug':
                            value = 'Ubicación Geográfica'
                        elif code_sec.section == 'cc':
                            value = 'Clave Cartera'
                        elif code_sec.section == 'tp':
                            value = 'Tipo de Proyecto'
                        elif code_sec.section == 'np':
                            value = 'Número de Proyecto'
                        elif code_sec.section == 'e':
                            value = 'Etapa'
                        elif code_sec.section == 'tc':
                            value = 'Tipo de Convenio'
                        elif code_sec.section == 'nc':
                            value = 'Número de Convenio'
                    else:
                        if code_sec.section == 'year':
                            value = 'Year'
                        elif code_sec.section == 'pr':
                            value = 'Program'
                        elif code_sec.section == 'sp':
                            value = 'Sub Program'
                        elif code_sec.section == 'dep':
                            value = 'Dependency'
                        elif code_sec.section == 'sd':
                            value = 'Sub Dependency'
                        elif code_sec.section == 'par':
                            value = 'Expenditure Item'
                        elif code_sec.section == 'dv':
                            value = 'Check Digit'
                        elif code_sec.section == 'or':
                            value = 'Source of Resource'
                        elif code_sec.section == 'ai':
                            value = 'Institutional Activity'
                        elif code_sec.section == 'conpp':
                            value = 'Conversion of Budgetary Program'
                        elif code_sec.section == 'conpa':
                            value = 'SHCP items'
                        elif code_sec.section == 'tg':
                            value = 'Type of Expenditure'
                        elif code_sec.section == 'ug':
                            value = 'Geographic Location'
                        elif code_sec.section == 'cc':
                            value = 'Wallet Key'
                        elif code_sec.section == 'tp':
                            value = 'Type of Project'
                        elif code_sec.section == 'np':
                            value = 'Project Number'
                        elif code_sec.section == 'e':
                            value = 'Stage'
                        elif code_sec.section == 'tc':
                            value = 'Type of Agreement'
                        elif code_sec.section == 'nc':
                            value = 'Agreement Number'
                    ws1.write(row, col, value, header_style)

                row += 1

                for data in data_with_item:
                    for ik, ld in data.items():
                        need_total = False
                        tot_authrized = 0
                        tot_assign_manu = 0
                        tot_assign_fir = 0
                        tot_assign_sec = 0
                        tot_assign_third = 0
                        tot_assign_for = 0
                        tot_annual_modi = 0
                        tot_per_ex = 0
                        tot_commited = 0
                        tot_accured = 0
                        tot_excercised = 0
                        tot_paid = 0
                        tot_available = 0
                        if data.get(ik):
                            for cd in ld:
                                for code, lines in cd.items():
                                    col = 0
                                    all_b_lines = lines
                                    if all_b_lines:
                                        annual_modified = 0
                                        adequacies_lines = adequacies_line_obj.search([('program', '=', code.id),
                                                                                       ('adequacies_id.state', '=', 'accepted')])
                                        for ad_line in adequacies_lines:
                                            if ad_line.line_type == 'increase':
                                                annual_modified += ad_line.amount
                                            elif ad_line.line_type == 'decrease':
                                                annual_modified -= ad_line.amount
                                        ws1.write(row, col, code.program_code)
                                        for bug_con in self.budget_control_ids:
                                            col += 1
                                            value = 0
                                            authorized = sum(x.authorized for x in all_b_lines)
                                            annual_modified = annual_modified + authorized
                                            if bug_con.name in ('Expenditure Item', 'Partida'):
                                                need_total = True
                                                value = code.item_id.item
                                            elif bug_con.name in ('Authorized', 'Autorizada'):
                                                value = authorized
                                                tot_authrized += authorized
                                            elif bug_con.name in ('Assigned Total Annual','Total Anual Asignado'):
                                                value = sum(x.assigned for x in all_b_lines)
                                                tot_assign_manu += value
                                            elif bug_con.name in ('Annual Modified', 'Modificado Anual'):
                                                value = annual_modified
                                                tot_annual_modi += value
                                            elif bug_con.name in ('Assigned 1st Trimester', 'Asignado 1er Trimestre'):
                                                value = sum(x.assigned if x.start_date.month == 1 and
                                                            x.start_date.day == 1 and x.end_date.month == 3 and x.end_date.day == 31
                                                            else 0 for x in all_b_lines)
                                                tot_assign_fir += value
                                            elif bug_con.name in ('Assigned 2nd Trimester', 'Asignado 2do Trimestre'):
                                                value = sum(x.assigned if x.start_date.month == 4 and
                                                            x.start_date.day == 1 and x.end_date.month == 6 and x.end_date.day == 30
                                                            else 0 for x in all_b_lines)
                                                tot_assign_sec += value
                                            elif bug_con.name in ('Assigned 3rd Trimester', 'Asignado 3er Trimestre'):
                                                value = sum(x.assigned if x.start_date.month == 7 and
                                                            x.start_date.day == 1 and x.end_date.month == 9 and x.end_date.day == 30
                                                            else 0 for x in all_b_lines)
                                                tot_assign_third += value
                                            elif bug_con.name in ('Assigned 4th Trimester', 'Asignado 4to Trimestre'):
                                                value = sum(x.assigned if x.start_date.month == 10 and
                                                            x.start_date.day == 1 and x.end_date.month == 12 and x.end_date.day == 31
                                                            else 0 for x in all_b_lines)
                                                tot_assign_for += value
                                            elif bug_con.name in ('Per Exercise', 'Por Ejercer'):
                                                value = sum(x.available for x in all_b_lines)
                                                tot_per_ex += value
                                            elif bug_con.name in ('Committed', 'Comprometido'):
                                                value = 0
                                                self.env.cr.execute("select coalesce(sum(abs(line.balance)+abs(line.tax_price_cr)),0) as committed from account_move_line line,account_move amove where line.program_code_id=%s and amove.id=line.move_id and amove.payment_state=%s and amove.invoice_date >= %s and amove.invoice_date <= %s", (code.id,'approved_payment',self.start_date,self.end_date))
                                                my_datas = self.env.cr.fetchone()
                                                if my_datas:
                                                    value = my_datas[0]                                                
                                                tot_commited += value
                                            elif bug_con.name in ('Accrued', 'Devengado'):
                                                value = 0
                                                tot_accured += 0
                                            elif bug_con.name in ('Exercised', 'Ejercido'):
                                                value = 0
                                                self.env.cr.execute("select coalesce(sum(abs(line.balance)+abs(line.tax_price_cr)),0) as committed from account_move_line line,account_move amove where line.program_code_id=%s and amove.id=line.move_id and amove.payment_state in %s and amove.invoice_date >= %s and amove.invoice_date <= %s", (code.id,('for_payment_procedure','payment_not_applied'),self.start_date,self.end_date))
                                                my_datas = self.env.cr.fetchone()
                                                if my_datas:
                                                    value = my_datas[0]                                                
                                                tot_excercised += value
                                            elif bug_con.name in ('Paid', 'Pagado'):
                                                value = 0
                                                self.env.cr.execute("select coalesce(sum(abs(line.balance)+abs(line.tax_price_cr)),0) as committed from account_move_line line,account_move amove where line.program_code_id=%s and amove.id=line.move_id and amove.payment_state=%s and amove.invoice_date >= %s and amove.invoice_date <= %s", (code.id,'paid',self.start_date,self.end_date))
                                                my_datas = self.env.cr.fetchone()
                                                if my_datas:
                                                    value = my_datas[0]                                                
                                                
                                                tot_paid += value
                                            elif bug_con.name in ('Available', 'Disponible'):
                                                value = sum(x.available for x in all_b_lines)
                                                tot_available += value
                                            ws1.write(row, col, value)
                                        for code_sec in self.code_section_ids:
                                            col += 1
                                            value = ''
                                            if code_sec.section == 'year':
                                                value = code.year.name
                                            elif code_sec.section == 'pr':
                                                value = code.program_id.key_unam
                                            elif code_sec.section == 'sp':
                                                value = code.sub_program_id.sub_program
                                            elif code_sec.section == 'dep':
                                                value = code.dependency_id.dependency
                                            elif code_sec.section == 'sd':
                                                value = code.sub_dependency_id.sub_dependency
                                            elif code_sec.section == 'par':
                                                value = code.item_id.item
                                            elif code_sec.section == 'dv':
                                                value = code.check_digit
                                            elif code_sec.section == 'or':
                                                value = code.resource_origin_id.key_origin
                                            elif code_sec.section == 'ai':
                                                value = code.institutional_activity_id.number
                                            elif code_sec.section == 'conpp':
                                                value = code.budget_program_conversion_id.shcp.name
                                            elif code_sec.section == 'conpa':
                                                value = code.conversion_item_id.federal_part
                                            elif code_sec.section == 'tg':
                                                value = code.expense_type_id.key_expenditure_type
                                            elif code_sec.section == 'ug':
                                                value = code.location_id.state_key
                                            elif code_sec.section == 'cc':
                                                value = code.portfolio_id.wallet_password
                                            elif code_sec.section == 'tp':
                                                value = code.project_type_id.project_type_identifier
                                            elif code_sec.section == 'np':
                                                value = code.project_type_id.number
                                            elif code_sec.section == 'e':
                                                value = code.stage_id.stage_identifier
                                            elif code_sec.section == 'tc':
                                                value = code.agreement_type_id.agreement_type
                                            elif code_sec.section == 'nc':
                                                value = code.agreement_type_id.number_agreement
                                            ws1.write(row, col, value)
                                        row += 1
                            if need_total:
                                row += 1
                                total_col = 0
                                if self.env.user.lang == 'es_MX':
                                    if ik == 1:
                                        ws1.write(row, total_col, 'Total del grupo 100 - 199', total_style)
                                    elif ik == 2:
                                        ws1.write(row, total_col, 'Total del grupo 200 - 299', total_style)
                                    elif ik == 3:
                                        ws1.write(row, total_col, 'Total del grupo 300 - 399', total_style)
                                    elif ik == 4:
                                        ws1.write(row, total_col, 'Total del grupo 400 - 499', total_style)
                                    elif ik == 5:
                                        ws1.write(row, total_col, 'Total del grupo 500 - 599', total_style)
                                    elif ik == 6:
                                        ws1.write(row, total_col, 'Total del grupo 600 - 699', total_style)
                                    elif ik == 7:
                                        ws1.write(row, total_col, 'Total del grupo 700 - 799', total_style)
                                    elif ik == 8:
                                        ws1.write(row, total_col, 'Total del grupo 800 - 899', total_style)
                                    elif ik == 9:
                                        ws1.write(row, total_col, 'Total del grupo 900 - 999', total_style)
                                else:
                                    if ik == 1:
                                        ws1.write(row, total_col, 'Total of Group 100 - 199', total_style)
                                    elif ik == 2:
                                        ws1.write(row, total_col, 'Total of Group 200 - 299', total_style)
                                    elif ik == 3:
                                        ws1.write(row, total_col, 'Total of Group 300 - 399', total_style)
                                    elif ik == 4:
                                        ws1.write(row, total_col, 'Total of Group 400 - 499', total_style)
                                    elif ik == 5:
                                        ws1.write(row, total_col, 'Total of Group 500 - 599', total_style)
                                    elif ik == 6:
                                        ws1.write(row, total_col, 'Total of Group 600 - 699', total_style)
                                    elif ik == 7:
                                        ws1.write(row, total_col, 'Total of Group 700 - 799', total_style)
                                    elif ik == 8:
                                        ws1.write(row, total_col, 'Total of Group 800 - 899', total_style)
                                    elif ik == 9:
                                        ws1.write(row, total_col, 'Total of Group 900 - 999', total_style)
                                for bug_con in self.budget_control_ids:
                                    total_col += 1
                                    value = ''
                                    if bug_con.name in ('Expenditure Item', 'Partida'):
                                        value = ''
                                    elif bug_con.name in ('Authorized', 'Autorizada'):
                                        value = tot_authrized
                                    elif bug_con.name in ('Assigned Total Annual','Total Anual Asignado'):
                                        value = tot_assign_manu
                                    elif bug_con.name in ('Annual Modified', 'Modificado Anual'):
                                        value = tot_annual_modi
                                    elif bug_con.name in ('Assigned 1st Trimester', 'Asignado 1er Trimestre'):
                                        value = tot_assign_fir
                                    elif bug_con.name in ('Assigned 2nd Trimester', 'Asignado 2do Trimestre'):
                                        value = tot_assign_sec
                                    elif bug_con.name in ('Assigned 3rd Trimester', 'Asignado 3er Trimestre'):
                                        value = tot_assign_third
                                    elif bug_con.name in ('Assigned 4th Trimester', 'Asignado 4to Trimestre'):
                                        value = tot_assign_for
                                    elif bug_con.name in ('Per Exercise', 'Por Ejercer'):
                                        value = tot_per_ex
                                    elif bug_con.name in ('Committed', 'Comprometido'):
                                        value = tot_commited
                                    elif bug_con.name in ('Accrued', 'Devengado'):
                                        value = tot_accured
                                    elif bug_con.name in ('Exercised', 'Ejercido'):
                                        value = tot_excercised
                                    elif bug_con.name in ('Paid', 'Pagado'):
                                        value = tot_paid
                                    elif bug_con.name in ('Available', 'Disponible'):
                                        value = tot_available
                                    ws1.write(row, total_col, value, total_style)
                                row += 2

                wb1.save(fp)
                out = base64.encodestring(fp.getvalue())
                self.report_file = out
                self.name = 'proforma_summary_report.xls'
                self.state = 'download'
            else:
                req_report = self.env['requested.reports']
                current_time = datetime.now()
                req_rep_vals = {
                    'name': 'Report Request At ' + str(current_time),
                    'requested_by': self.env.user.id,
                    'requested_time': current_time,
                    'filter_date': self.filter_date,
                    'start_date': self.start_date,
                    'end_date': self.end_date,
                    'budget_control_ids': [(4, rec.id) for rec in self.budget_control_ids],
                    'code_section_ids': [(4, rec.id) for rec in self.code_section_ids],
                    'program_ids': [(4, rec.id) for rec in self.program_ids],
                    'sub_program_ids': [(4, rec.id) for rec in self.sub_program_ids],
                    'dependency_ids': [(4, rec.id) for rec in self.dependency_ids],
                    'sub_dependency_ids': [(4, rec.id) for rec in self.sub_dependency_ids],
                    'item_ids': [(4, rec.id) for rec in self.item_ids],
                    'origin_ids': [(4, rec.id) for rec in self.origin_ids],
                    'activity_ids': [(4, rec.id) for rec in self.activity_ids],
                    'conpp_ids': [(4, rec.id) for rec in self.conpp_ids],
                    'conpa_ids': [(4, rec.id) for rec in self.conpa_ids],
                    'expense_type_ids': [(4, rec.id) for rec in self.expense_type_ids],
                    'location_ids': [(4, rec.id) for rec in self.location_ids],
                    'wallet_ids': [(4, rec.id) for rec in self.wallet_ids],
                    'project_type_ids': [(4, rec.id) for rec in self.project_type_ids],
                    'stage_ids': [(4, rec.id) for rec in self.stage_ids],
                    'agreement_type_ids': [(4, rec.id) for rec in self.agreement_type_ids],
                }
                report = req_report.create(req_rep_vals)
                if report:
                    prev_cron_id = False
                    for data in data_with_item_cron:
                        for ik, ld in data.items():
                            if data.get(ik):
                                bud_lines = ld
                                total_cron = math.ceil(len(bud_lines) / 5000)
                                for seq in range(1, total_cron + 1):
                                    nextcall = datetime.now()
                                    nextcall = nextcall + timedelta(seconds=10)
                                    lines = bud_lines[:5000]
                                    cron_vals = {
                                        'name': 'Report Request' + str(current_time),
                                        'state': 'code',
                                        'nextcall': nextcall,
                                        'numbercall': -1,
                                        'code': "model.download_report()",
                                        'model_id': self.env.ref('jt_budget_mgmt.model_requested_reports').id,
                                        'user_id': self.env.user.id,
                                        'req_report_id': report.id
                                    }

                                    # Final process
                                    cron = self.env['ir.cron'].sudo().create(cron_vals)
                                    req_report_file_id = self.env['report.files'].create({
                                        'report_id': report.id,
                                        'cron_id': cron.id
                                    })
                                    cron.write({'code': "model.download_report(" +
                                                        str(req_report_file_id.id) +
                                                "," + str(lines) + ")",
                                                'req_report_file_id': req_report_file_id})
                                    if prev_cron_id:
                                        cron.write(
                                            {'prev_cron_id': prev_cron_id, 'active': False})
                                    del bud_lines[:5000]
                                    prev_cron_id = cron.id
                    self.write({'state': 'request'})
        print(self.state)
        if self.state != 'draft':
            return {
                'name': 'Report Download Progress',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': False,
                'res_model': 'summary.report.download',
                'domain': [],
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_id': self.id,
            }
        elif self.state == 'draft':
            raise UserError(_('No hay datos que mostrar para esta consulta'))

    def save_favourite(self):
        if not self.favourite_name:
            raise UserError(_('Please enter a name to save the filter.'))
        vals = {'state': self.state,
                'name': self.name,
                'report_file': self.report_file,
                'filter_date': self.filter_date,
                'start_date': self.start_date,
                'end_date': self.end_date,
                'budget_control_ids': self.budget_control_ids.ids,
                'code_section_ids': self.code_section_ids.ids,
                'program_ids': self.program_ids.ids,
                'sub_program_ids': self.sub_program_ids.ids,
                'dependency_ids': self.dependency_ids.ids,
                'sub_dependency_ids': self.sub_dependency_ids.ids,
                'item_ids': self.item_ids.ids,
                'origin_ids': self.origin_ids.ids,
                'activity_ids': self.activity_ids.ids,
                'conpp_ids': self.conpp_ids.ids,
                'conpa_ids': self.conpa_ids.ids,
                'expense_type_ids': self.expense_type_ids.ids,
                'location_ids': self.location_ids.ids,
                'wallet_ids': self.wallet_ids.ids,
                'project_type_ids': self.project_type_ids.ids,
                'stage_ids': self.stage_ids.ids,
                'agreement_type_ids': self.agreement_type_ids.ids,
                'favourite_user_id': self.env.user.id,
                'favourite_name': self.favourite_name
                }
        self.env['favourite.summary.report'].create(vals)
        return {
            "type": "ir.actions.do_nothing",
        }

    @api.onchange('favourite_report_id')
    def onchange_favourite_report_id(self):
        if self.favourite_report_id:
            self.state = self.favourite_report_id.state
            self.name = self.favourite_report_id.name
            self.report_file = self.favourite_report_id.report_file
            self.filter_date = self.favourite_report_id.filter_date
            self.start_date = self.favourite_report_id.start_date
            self.end_date = self.favourite_report_id.end_date
            self.budget_control_ids = self.favourite_report_id.budget_control_ids.ids
            self.code_section_ids = self.favourite_report_id.code_section_ids.ids
            self.program_ids = self.favourite_report_id.program_ids.ids
            self.sub_program_ids = self.favourite_report_id.sub_program_ids.ids
            self.dependency_ids = self.favourite_report_id.dependency_ids.ids
            self.sub_dependency_ids = self.favourite_report_id.sub_dependency_ids.ids
            self.item_ids = self.favourite_report_id.item_ids.ids
            self.origin_ids = self.favourite_report_id.origin_ids.ids
            self.activity_ids = self.favourite_report_id.activity_ids.ids
            self.conpp_ids = self.favourite_report_id.conpp_ids.ids
            self.conpa_ids = self.favourite_report_id.conpa_ids.ids
            self.expense_type_ids = self.favourite_report_id.expense_type_ids.ids
            self.location_ids = self.favourite_report_id.location_ids.ids
            self.wallet_ids = self.favourite_report_id.wallet_ids.ids
            self.project_type_ids = self.favourite_report_id.project_type_ids.ids
            self.stage_ids = self.favourite_report_id.stage_ids.ids
            self.agreement_type_ids = self.favourite_report_id.agreement_type_ids.ids
        else:
            self.unlink()
