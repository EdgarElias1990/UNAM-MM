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
from odoo import models, fields
from io import BytesIO
import xlwt
import base64


class ProformaBudgetSummary(models.TransientModel):

    _name = 'proforma.budget.summary'
    _description = 'Proforma budget summary'

    report = fields.Binary('Prepared file', readonly=True)
    name = fields.Char('File Name', size=100)

    # def _get_templates(self):
    #     templates = super(ProformaBudgetSummary, self)._get_templates()
    #     templates[
    #         'main_table_header_template'] = 'account_reports.main_table_header'
    #     templates['main_template'] = 'account_reports.main_template'
    #     return templates

    def generate_report_xls(self):
        fp = BytesIO()

        wb1 = xlwt.Workbook(encoding='utf-8')
        ws1 = wb1.add_sheet('Proforma Budget Summary Report')

        first_header_content_style = xlwt.easyxf("font: name Helvetica size 100 px, bold 1, height 270; "
                                                 "align: horiz center")
        sub_header_style = xlwt.easyxf('pattern: pattern solid, fore_colour white;' 'font: name Helvetica size 12 px, '
                                       'bold 1, height 170;' 'borders: top thin, right thin, bottom thin, left thin;' "alignment: wrap 0;")
        sub_header_content_style = xlwt.easyxf(
            "font: name Helvetica size 10 px, height 170;" "alignment: wrap 0;")

        row = 1
        col = 0
        ws1.row(row).height = 500

        labels = ['Program code', 'Authorized', 'Assigned', 'Modified',
                  'For exercising', 'Committed', 'Accrued', 'Exercised', 'Paid out', 'Available']
        length = len(labels)

        ws1.write_merge(row, row, 0, length - 1,
                        "Proforma Budget Summary Report", first_header_content_style)
        row += 1
        ws1.row(row).height = 300

        for rec in range(0, length):
            ws1.write(row, col + rec, labels[rec], sub_header_style)
        row += 1
        col = 0

        program_code = self.env['program.code'].search([])
        for code in program_code:
            ws1.write(row, col, code.program_code, sub_header_content_style)
            row += 1
        wb1.save(fp)

        context = {}
        out = base64.encodestring(fp.getvalue())
        context['name'] = 'Summary_Report.xls'

        context['file'] = out
        record = self.create({})
        record.write({'report': out, 'name': context['name']})
        return record.id

    def load_report_js(self):
        ctx = {}
        return {
            'type': 'ir.actions.client',
            'tag': 'ProformaBudgetSummary',
            'context': ctx,
        }

    def generate_report(self):
        report = self.env.ref(
            'jt_budget_mgmt.summary_report')

        ctx = self.env.context.copy()
        program_code = self.env['program.code'].search([])
        ctx['program_code'] = program_code.ids

        file = None

        if ctx.get('type') == 'view':
            file = report.with_context(
                ctx).render_qweb_html([])
            return file
        elif ctx.get('type') == 'download_pdf':
            file = report.with_context(
                ctx).render_qweb_pdf()
        elif ctx.get('type') == 'download_xls':
            record = self.generate_report_xls()
            return record

        context = {}
        out = base64.b64encode(file[0])
        context['name'] = 'Summary_Report.pdf'

        context['file'] = out
        record = self.create({})
        record.write({'report': out, 'name': context['name']})

        return record.id
