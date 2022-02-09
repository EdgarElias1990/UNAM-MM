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
from odoo import models, fields, api
import xlrd
import xlwt
import base64
from io import BytesIO
from datetime import datetime
import yaml

class RequestedReports(models.Model):

    _name = 'requested.reports'
    _description = 'Requested Reports'
    _rec_name = 'name'

    name = fields.Char(string='Name')
    report_file = fields.Binary(string='Download Report', filters='.xls')
    report_file_name = fields.Char(string='Download Report Name')
    requested_by = fields.Many2one("res.users",string='Requested By')
    requested_time = fields.Datetime("Requested Time")
    execution_time = fields.Datetime("Execution Time")
    prepared_time = fields.Datetime("Prepared Time")
    state = fields.Selection([('in_progress',"In Process"),('failed','Failed'),('complete',"Ready To Download")],
                             default="in_progress",string="Status")
    cron_id = fields.Many2one("ir.cron", "Scheduled Cron")

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
    budget_control_ids = fields.Many2many('budget.control', string='Budget Control')

    # Program Code Section Related fields
    code_section_ids = fields.Many2many('code.structure', string='Programming Code Section', translate=True)
    program_ids = fields.Many2many('program', string='Program')
    sub_program_ids = fields.Many2many('sub.program', string='Sub-Program')
    dependency_ids = fields.Many2many('dependency', string='Dependency')
    sub_dependency_ids = fields.Many2many('sub.dependency', string='Sub-Dependency')
    item_ids = fields.Many2many('expenditure.item', string='Expense Item')
    origin_ids = fields.Many2many('resource.origin', string='Origin Resource')
    activity_ids = fields.Many2many('institutional.activity', string='Institutional Activity')
    conpp_ids = fields.Many2many('budget.program.conversion', string='Budget Program Conversion (CONPP)')
    conpa_ids = fields.Many2many('departure.conversion', string='SHCP Games (CONPA)')
    expense_type_ids = fields.Many2many('expense.type', string='Type of Expense (TG)')
    location_ids = fields.Many2many('geographic.location', string='Geographic Location (UG)')
    wallet_ids = fields.Many2many('key.wallet', string='Wallet Key (CC)')
    project_type_ids = fields.Many2many('project.type', string='Project Type (TP)')
    stage_ids = fields.Many2many('stage', string='Stage (E)')
    agreement_type_ids = fields.Many2many('agreement.type', string='Type of agreement (TC)')

    # Program code ids
    # program_code_ids = fields.Many2many('program.code', string="Program Codes")
    # code_lines = fields.Text()
    removed_cron = fields.Boolean()
    file_ids = fields.One2many('report.files', 'report_id')

    def merge_files(self, report):
        wb1 = xlwt.Workbook()
        ws1 = wb1.add_sheet('Proforma Summary Report')
        fp = BytesIO()
        xlsfiles = []
        for file in report.file_ids:
            xlsfiles.append(file.file)
        outrow_idx = 0
        for f in xlsfiles:
            # This is all untested; essentially just pseudocode for concept!
            insheet = xlrd.open_workbook(file_contents=base64.decodestring(f)).sheets()[0]
            if outrow_idx == 0:
                for row_idx in range(insheet.nrows):
                    for col_idx in range(insheet.ncols):
                        ws1.write(outrow_idx, col_idx,
                                  insheet.cell_value(row_idx, col_idx))
                    outrow_idx += 1
            else:
                for row_idx in range(2, insheet.nrows):
                    for col_idx in range(insheet.ncols):
                        ws1.write(outrow_idx, col_idx,
                                  insheet.cell_value(row_idx, col_idx))
                    outrow_idx += 1
        wb1.save(fp)
        out = base64.encodestring(fp.getvalue())
        report.report_file = out
        report.report_file_name = 'proforma_summary_report.xls'

    def remove_cron_records(self):
        for report in self.search([]):
            if report.state == 'complete' and not report.removed_cron:
                for file in report.file_ids:
                    if file.cron_id:
                        file.cron_id.unlink()

    def download_report(self, report_file_id, code_lines):
        report_file = self.env['report.files'].browse(int(report_file_id))
        report = report_file.report_id
        adequacies_line_obj = self.env['adequacies.lines']
        bud_line_obj = self.env['expenditure.budget.line']
        code_obj = self.env['program.code']
        if not report.execution_time:
            report_file.report_id.execution_time = datetime.now()
        if not report.state == 'in_progress':
            report_file.report_id.state = 'in_progress'
        code_lines = yaml.load(str(code_lines))
        wb1 = xlwt.Workbook(encoding='utf-8')
        ws1 = wb1.add_sheet('Proforma Summary Report')
        fp = BytesIO()
        header_style = xlwt.easyxf('font: bold 1')
        total_style = xlwt.easyxf('font: bold 1;' 'borders: top thin, right thin, bottom thin, left thin;')

        row = 1
        col = 0
        if report.requested_by.lang == 'es_MX':
            ws1.write(row, col, "Código Programático", header_style)
        else:
            ws1.write(row, col, "Program Code", header_style)
        for bug_con in report.budget_control_ids:
            col += 1
            value = ''
            if report.requested_by.lang == 'es_MX':
                if bug_con.name in ('Expenditure Item', 'Partida'):
                    value = 'Partida'
                elif bug_con.name in ('Authorized', 'Autorizada'):
                    value = 'Autorizada'
                elif bug_con.name in ('Assigned Total Annual', 'Total Anual Asignado'):
                    value = 'Total Anual Asignado'
                elif bug_con.name in ('Annual Modified', 'Modificado Anual'):
                    value = 'Modificado Anual'
                elif bug_con.name in ('Assigned 1st Trimester', 'Asignado 1er Trimestre'):
                    value = 'Asignado 1er Trimestre'
                elif bug_con.name in ('Assigned 2nd Trimester', 'Asignado 2do Trimestre'):
                    value = 'Asignado 2do Trimestre'
                elif bug_con.name in ('Assigned 3rd Trimester', 'Asignado 3er Trimestre'):
                    value = 'Asignado 3er Trimestre'
                elif bug_con.name in ('Assigned 4th Trimester', 'Asignado 4to Trimestre'):
                    value = 'Asignado 4to Trimestre'
                elif bug_con.name in ('Per Exercise', 'Por Ejercer'):
                    value = 'Por Ejercer'
                elif bug_con.name in ('Committed', 'Comprometido'):
                    value = 'Comprometido'
                elif bug_con.name in ('Accrued', 'Devengado'):
                    value = 'Devengado'
                elif bug_con.name in ('Exercised', 'Ejercido'):
                    value = 'Ejercido'
                elif bug_con.name in ('Paid', 'Pagado'):
                    value = 'Pagado'
                elif bug_con.name in ('Available', 'Disponible'):
                    value = 'Disponible'
            else:
                if bug_con.name in ('Expenditure Item', 'Partida'):
                    value = 'Expenditure Item'
                elif bug_con.name in ('Authorized', 'Autorizada'):
                    value = 'Authorized'
                elif bug_con.name in ('Assigned Total Annual', 'Total Anual Asignado'):
                    value = 'Assigned Total Annual'
                elif bug_con.name in ('Annual Modified', 'Modificado Anual'):
                    value = 'Annual Modified'
                elif bug_con.name in ('Assigned 1st Trimester', 'Asignado 1er Trimestre'):
                    value = 'Assigned 1st Trimester'
                elif bug_con.name in ('Assigned 2nd Trimester', 'Asignado 2do Trimestre'):
                    value = 'Assigned 2nd Trimester'
                elif bug_con.name in ('Assigned 3rd Trimester', 'Asignado 3er Trimestre'):
                    value = 'Assigned 3rd Trimester'
                elif bug_con.name in ('Assigned 4th Trimester', 'Asignado 4to Trimestre'):
                    value = 'Assigned 4th Trimester'
                elif bug_con.name in ('Per Exercise', 'Por Ejercer'):
                    value = 'Per Exercise'
                elif bug_con.name in ('Committed', 'Comprometido'):
                    value = 'Committed'
                elif bug_con.name in ('Accrued', 'Devengado'):
                    value = 'Accrued'
                elif bug_con.name in ('Exercised', 'Ejercido'):
                    value = 'Exercised'
                elif bug_con.name in ('Paid', 'Pagado'):
                    value = 'Paid'
                elif bug_con.name in ('Available', 'Disponible'):
                    value = 'Available'
            ws1.write(row, col, value, header_style)
        for code_sec in report.code_section_ids:
            col += 1
            value = ''
            if report.requested_by.lang == 'es_MX':
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
                    value = 'Partida SHCP'
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

        row +=1
        # start = report.start_date
        # end = report.end_date
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
        item_for_total = ''
        for cd in code_lines:
            for code, bud_lines in cd.items():
                col = 0
                code = code_obj.browse(code)
                item_for_total = code.item_id.item
                all_b_lines = bud_line_obj.browse(bud_lines)
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
                    for bug_con in report.budget_control_ids:
                        col += 1
                        value = 0
                        authorized = sum(x.authorized for x in all_b_lines)
                        annual_modified = authorized + annual_modified
                        if bug_con.name in ('Expenditure Item', 'Partida'):
                            need_total = True
                            value = code.item_id.item
                        elif bug_con.name in ('Authorized', 'Autorizada'):
                            value =  authorized
                            tot_authrized += authorized
                        elif bug_con.name in ('Assigned Total Annual','Total Anual Asignado'):
                            value = sum(x.assigned for x in all_b_lines)
                            tot_assign_manu += value
                        elif bug_con.name in ('Annual Modified', 'Modificado Anual'):
                            value = annual_modified
                            tot_annual_modi += value
                        elif bug_con.name in ('Assigned 1st Trimester', 'Asignado 1er Trimestre'):
                            value = sum(x.assigned if x.start_date.month == 1 and \
                                        x.start_date.day == 1 and x.end_date.month == 3 and x.end_date.day == 31 \
                                                        else 0 for x in all_b_lines)
                            tot_assign_fir += value
                        elif bug_con.name in ('Assigned 2nd Trimester', 'Asignado 2do Trimestre'):
                            value = sum(x.assigned if x.start_date.month == 4 and \
                                        x.start_date.day == 1 and x.end_date.month == 6 and x.end_date.day == 30 \
                                                        else 0 for x in all_b_lines)
                            tot_assign_sec += value
                        elif bug_con.name in ('Assigned 3rd Trimester', 'Asignado 3er Trimestre'):
                            value = sum(x.assigned if x.start_date.month == 7 and \
                                        x.start_date.day == 1 and x.end_date.month == 9 and x.end_date.day == 30 \
                                                        else 0 for x in all_b_lines)
                            tot_assign_third += value
                        elif bug_con.name in ('Assigned 4th Trimester', 'Asignado 4to Trimestre'):
                            value = sum(x.assigned if x.start_date.month == 10 and \
                                        x.start_date.day == 1 and x.end_date.month == 12 and x.end_date.day == 31 \
                                                        else 0 for x in all_b_lines)
                            tot_assign_for += value
                        elif bug_con.name in ('Per Exercise', 'Por Ejercer'):
                            value = sum(x.available for x in all_b_lines)
                            tot_per_ex += value
                        elif bug_con.name in ('Committed', 'Comprometido'):
                            value = 0
                            tot_commited += value
                        elif bug_con.name in ('Accrued', 'Devengado'):
                            value = 0
                            tot_accured += value
                        elif bug_con.name in ('Exercised', 'Ejercido'):
                            value = 0
                            tot_excercised += value
                        elif bug_con.name in ('Paid', 'Pagado'):
                            value = 0
                            tot_paid += value
                        elif bug_con.name in ('Available', 'Disponible'):
                            value = sum(x.available for x in all_b_lines)
                            tot_available += value
                        ws1.write(row, col, value)
                    for code_sec in report.code_section_ids:
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
                    row +=1
        if need_total:
            row += 1
            total_col = 0
            f_item = item_for_total[0] if item_for_total else ''
            if f_item:
                if report.requested_by.lang == 'es_MX':
                    if f_item == '1':
                        ws1.write(row, total_col, 'Total del grupo 100 - 199', total_style)
                    elif f_item == '2':
                        ws1.write(row, total_col, 'Total del grupo 200 - 299', total_style)
                    elif f_item == '3':
                        ws1.write(row, total_col, 'Total del grupo 300 - 399', total_style)
                    elif f_item == '4':
                        ws1.write(row, total_col, 'Total del grupo 400 - 499', total_style)
                    elif f_item == '5':
                        ws1.write(row, total_col, 'Total del grupo 500 - 599', total_style)
                    elif f_item == '6':
                        ws1.write(row, total_col, 'Total del grupo 600 - 699', total_style)
                    elif f_item == '7':
                        ws1.write(row, total_col, 'Total del grupo 700 - 799', total_style)
                    elif f_item == '8':
                        ws1.write(row, total_col, 'Total del grupo 800 - 899', total_style)
                    elif f_item == '9':
                        ws1.write(row, total_col, 'Total del grupo 900 - 999', total_style)
                else:
                    if f_item == '1':
                        ws1.write(row, total_col, 'Total of Group 100 - 199', total_style)
                    elif f_item == '2':
                        ws1.write(row, total_col, 'Total of Group 200 - 299', total_style)
                    elif f_item == '3':
                        ws1.write(row, total_col, 'Total of Group 300 - 399', total_style)
                    elif f_item == '4':
                        ws1.write(row, total_col, 'Total of Group 400 - 499', total_style)
                    elif f_item == '5':
                        ws1.write(row, total_col, 'Total of Group 500 - 599', total_style)
                    elif f_item == '6':
                        ws1.write(row, total_col, 'Total of Group 600 - 699', total_style)
                    elif f_item == '7':
                        ws1.write(row, total_col, 'Total of Group 700 - 799', total_style)
                    elif f_item == '8':
                        ws1.write(row, total_col, 'Total of Group 800 - 899', total_style)
                    elif f_item == '9':
                        ws1.write(row, total_col, 'Total of Group 900 - 999', total_style)
            for bug_con in report.budget_control_ids:
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
        report_file.file = out
        report_file.name = 'proforma_summary_report.xls'
        another_cron = self.env['ir.cron'].search([('prev_cron_id', '=', report_file.cron_id.id),
                                                   ('active', '=', False)])
        if another_cron:
            another_cron.active = True
        else:
            report.state = 'complete'
            report.prepared_time = datetime.now()
            report.merge_files(report)


class ReportFiles(models.Model):

    _name = 'report.files'
    _description = "Report Files"

    report_id = fields.Many2one('requested.reports')
    cron_id = fields.Many2one('ir.cron')
    file = fields.Binary("File")
    name = fields.Char("File name")

class Cron(models.Model):

    _inherit = 'ir.cron'

    req_report_id = fields.Many2one('requested.reports')
    req_report_file_id = fields.Many2one('report.files')
