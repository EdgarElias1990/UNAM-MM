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

class IncomeAnnualReport(models.AbstractModel):
    _name = "jt_income.income.annual.report"
    _inherit = "account.coa.report"
    _description = "Income Annual Report"

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

    def _get_reports_buttons(self):
        return [
            {'name': _('Export to PDF'), 'sequence': 1, 'action': 'print_pdf', 'file_export_type': _('PDF')},
            {'name': _('Export (XLSX)'), 'sequence': 2, 'action': 'print_xlsx', 'file_export_type': _('XLSX')},
        ]

    def _get_templates(self):
        templates = super(
            IncomeAnnualReport, self)._get_templates()
        templates[
            'main_table_header_template'] = 'account_reports.main_table_header'
        templates['main_template'] = 'account_reports.main_template'
        return templates

    def _get_columns_name(self, options):
        return [
            {'name': _('Nombre')},
            {'name': _('Cuenta Bancaria')},
            {'name': _('Cuenta')},
            {'name': _('Descripción cuenta contable')},
            {'name': _('Enero')},
            {'name': _('Febrero')},
            {'name': _('Marzo')},
            {'name': _('Abril')},
            {'name': _('Mayo')},
            {'name': _('Junio')},
            {'name': _('Julio')},
            {'name': _('Agosto')},
            {'name': _('Septiembre')},
            {'name': _('Octubre')},
            {'name': _('Noviembre')},
            {'name': _('Diciembre')},
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

    def _get_lines(self, options, line_id=None):
        lines = []
        start = datetime.strptime(
            str(options['date'].get('date_from')), '%Y-%m-%d').date()
        end = datetime.strptime(
            options['date'].get('date_to'), '%Y-%m-%d').date()
            
        self.env.cr.execute('''select max(ap.id) as id,ap.sub_origin_resource_id as sub_origin_resource_id,
                ap.journal_id as journal_id, 
                s0.report_name as sub_origin_name,s0.name as sub_origin_name_group_by,    
                
                COALESCE(sum(case when extract(month from payment_date) = 1 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) january,
                COALESCE(sum(case when extract(month from payment_date) = 2 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) february,
                COALESCE(sum(case when extract(month from payment_date) = 3 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) march,
                COALESCE(sum(case when extract(month from payment_date) = 4 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) april,
                COALESCE(sum(case when extract(month from payment_date) = 5 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) may,
                COALESCE(sum(case when extract(month from payment_date) = 6 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) june,
                COALESCE(sum(case when extract(month from payment_date) = 7 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) july,
                COALESCE(sum(case when extract(month from payment_date) = 8 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) august,
                COALESCE(sum(case when extract(month from payment_date) = 9 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) september,
                COALESCE(sum(case when extract(month from payment_date) = 10 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) october,
                COALESCE(sum(case when extract(month from payment_date) = 11 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) november,
                COALESCE(sum(case when extract(month from payment_date) = 12 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) december,
                COALESCE(sum((select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id))),0) as total
                from account_payment ap,sub_origin_resource s0
                where s0.id=ap.sub_origin_resource_id and ap.sub_origin_resource_id IS NOT NULL and ap.state in ('posted','reconciled') 
                and ap.partner_type='customer' and ap.payment_type = 'inbound' 
                and payment_date >= %s and payment_date <= %s
                and s0.name in ('Servicios de educación Bancos (INS-RINS)','Servicios de educación Caja Gral.','Aspirantes',
                                'D.B.I.N.','D.P.Y.D.','Venta almacén','Licenciatarios','DEP en garantia',
                                'DGIRE-bancos','DGIRE-caja')
                group by sub_origin_resource_id,sub_origin_name,sub_origin_name_group_by,journal_id
                order by sub_origin_name
                ''',(start,end))
        origin_datas = self.env.cr.fetchall()
        total_1 = 0
        total_2 = 0
        total_3 = 0
        total_4 = 0
        total_5 = 0
        total_6 = 0
        total_7 = 0
        total_8 = 0
        total_9 = 0
        total_10 = 0
        total_11 = 0
        total_12 = 0
        total_13 = 0
        
        for data in origin_datas:
            origin_id = self.env['sub.origin.resource'].browse(data[1])
            journal_id = self.env['account.journal'].browse(data[2])
            lines.append({
                'id': 'hierarchy1_' + str(data[1]),
                'name': data[3],
                'columns': [{'name': journal_id and journal_id.bank_account_id and journal_id.bank_account_id.acc_number or ''},
                            {'name': origin_id and origin_id.report_account_code or ''},
                            {'name': origin_id and origin_id.report_account_name or ''},
                            self._format({'name': data[5]},figure_type='float'),
                            self._format({'name': data[6]},figure_type='float'),
                            self._format({'name': data[7]},figure_type='float'),
                            self._format({'name': data[8]},figure_type='float'),
                            self._format({'name': data[9]},figure_type='float'),
                            self._format({'name': data[10]},figure_type='float'),
                            self._format({'name': data[11]},figure_type='float'),
                            self._format({'name': data[12]},figure_type='float'),
                            self._format({'name': data[13]},figure_type='float'),
                            self._format({'name': data[14]},figure_type='float'),
                            self._format({'name': data[15]},figure_type='float'),
                            self._format({'name': data[16]},figure_type='float'),
                            self._format({'name': data[17]},figure_type='float'),
                            ],
                'level': 3,
                'unfoldable': False,
                'unfolded': True,
            })
            total_1 += data[5]
            total_2 += data[6]
            total_3 += data[7]
            total_4 += data[8]
            total_5 += data[9]
            total_6 += data[10]
            total_7 += data[11]
            total_8 += data[12]
            total_9 += data[13]
            total_10 += data[14]
            total_11 += data[15]
            total_12 += data[16]
            total_13 += data[17]

        lines.append({
            'id': 'hierarchy1_total',
            'name': "SUMAS",
            'columns': [{'name': ''},
                        {'name': ''},
                        {'name': ''},
                        self._format({'name': total_1},figure_type='float'),
                        self._format({'name': total_2},figure_type='float'),
                        self._format({'name': total_3},figure_type='float'),
                        self._format({'name': total_4},figure_type='float'),
                        self._format({'name': total_5},figure_type='float'),
                        self._format({'name': total_6},figure_type='float'),
                        self._format({'name': total_7},figure_type='float'),
                        self._format({'name': total_8},figure_type='float'),
                        self._format({'name': total_9},figure_type='float'),
                        self._format({'name': total_10},figure_type='float'),
                        self._format({'name': total_11},figure_type='float'),
                        self._format({'name': total_12},figure_type='float'),
                        self._format({'name': total_13},figure_type='float'),
                        ],
            'level': 2,
            'unfoldable': False,
            'unfolded': True,
        })
        lines.append({
            'id': 'hierarchy2_resumen',
            'name': "",
            'columns': [{'name': ''},
                        {'name': ''},
                        {'name': 'RESUMEN'},
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
            'level': 2,
            'unfoldable': False,
            'unfolded': True,
        })
        #================= INGRESOS POR SERVICIOS DE EDUCACIÓN=========#
        total_1 = 0
        total_2 = 0
        total_3 = 0
        total_4 = 0
        total_5 = 0
        total_6 = 0
        total_7 = 0
        total_8 = 0
        total_9 = 0
        total_10 = 0
        total_11 = 0
        total_12 = 0
        total_13 = 0

        self.env.cr.execute('''select -1 as id,NULL as sub_origin_resource_id,NULL as journal_id,
                '1) INGRESOS POR SERVICIOS DE EDUCACIÓN' as sub_origin_name,
                'Resumen' as sub_origin_name_group_by,
                COALESCE(sum(case when extract(month from payment_date) = 1 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) january,
                COALESCE(sum(case when extract(month from payment_date) = 2 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) february,
                COALESCE(sum(case when extract(month from payment_date) = 3 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) march,
                COALESCE(sum(case when extract(month from payment_date) = 4 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) april,
                COALESCE(sum(case when extract(month from payment_date) = 5 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) may,
                COALESCE(sum(case when extract(month from payment_date) = 6 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) june,
                COALESCE(sum(case when extract(month from payment_date) = 7 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) july,
                COALESCE(sum(case when extract(month from payment_date) = 8 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) august,
                COALESCE(sum(case when extract(month from payment_date) = 9 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) september,
                COALESCE(sum(case when extract(month from payment_date) = 10 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) october,
                COALESCE(sum(case when extract(month from payment_date) = 11 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) november,
                COALESCE(sum(case when extract(month from payment_date) = 12 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) december,
                COALESCE(sum((select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id))),0) as total
                from sub_origin_resource s1,account_payment ap 
                where ap.sub_origin_resource_id = s1.id and ap.state in ('posted','reconciled')
                and payment_date >= %s and payment_date <= %s
                and s1.name in ('Servicios de educación Bancos (INS-RINS)','Servicios de educación Caja Gral.')
            ''',(start,end))
        origin_datas = self.env.cr.fetchall()
        
        for data in origin_datas: 
            lines.append({
                'id': 'hierarchy2_ing',
                'name': data[3],
                'columns': [{'name': ''},
                            {'name': ''},
                            {'name': ''},
                            self._format({'name': data[5]},figure_type='float'),
                            self._format({'name': data[6]},figure_type='float'),
                            self._format({'name': data[7]},figure_type='float'),
                            self._format({'name': data[8]},figure_type='float'),
                            self._format({'name': data[9]},figure_type='float'),
                            self._format({'name': data[10]},figure_type='float'),
                            self._format({'name': data[11]},figure_type='float'),
                            self._format({'name': data[12]},figure_type='float'),
                            self._format({'name': data[13]},figure_type='float'),
                            self._format({'name': data[14]},figure_type='float'),
                            self._format({'name': data[15]},figure_type='float'),
                            self._format({'name': data[16]},figure_type='float'),
                            self._format({'name': data[17]},figure_type='float'),
                            ],
                'level': 3,
                'unfoldable': False,
                'unfolded': True,
            })
            total_1 += data[5]
            total_2 += data[6]
            total_3 += data[7]
            total_4 += data[8]
            total_5 += data[9]
            total_6 += data[10]
            total_7 += data[11]
            total_8 += data[12]
            total_9 += data[13]
            total_10 += data[14]
            total_11 += data[15]
            total_12 += data[16]
            total_13 += data[17]

        #========== ASPIRANTES ============#
        self.env.cr.execute('''select -2 as id,NULL as sub_origin_resource_id,NULL as journal_id,
                '2) ASPIRANTES' as sub_origin_name,
                'Resumen' as sub_origin_name_group_by,
                COALESCE(sum(case when extract(month from payment_date) = 1 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) january,
                COALESCE(sum(case when extract(month from payment_date) = 2 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) february,
                COALESCE(sum(case when extract(month from payment_date) = 3 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) march,
                COALESCE(sum(case when extract(month from payment_date) = 4 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) april,
                COALESCE(sum(case when extract(month from payment_date) = 5 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) may,
                COALESCE(sum(case when extract(month from payment_date) = 6 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) june,
                COALESCE(sum(case when extract(month from payment_date) = 7 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) july,
                COALESCE(sum(case when extract(month from payment_date) = 8 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) august,
                COALESCE(sum(case when extract(month from payment_date) = 9 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) september,
                COALESCE(sum(case when extract(month from payment_date) = 10 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) october,
                COALESCE(sum(case when extract(month from payment_date) = 11 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) november,
                COALESCE(sum(case when extract(month from payment_date) = 12 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) december,
                COALESCE(sum((select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id))),0) as total
                from sub_origin_resource s1,account_payment ap 
                where ap.sub_origin_resource_id = s1.id and ap.state in ('posted','reconciled')
                and s1.name in ('Aspirantes')   
                and payment_date >= %s and payment_date <= %s
            ''',(start,end))
        origin_datas = self.env.cr.fetchall()
        
        for data in origin_datas: 
            lines.append({
                'id': 'hierarchy2_aspi',
                'name': data[3],
                'columns': [{'name': ''},
                            {'name': ''},
                            {'name': ''},
                            self._format({'name': data[5]},figure_type='float'),
                            self._format({'name': data[6]},figure_type='float'),
                            self._format({'name': data[7]},figure_type='float'),
                            self._format({'name': data[8]},figure_type='float'),
                            self._format({'name': data[9]},figure_type='float'),
                            self._format({'name': data[10]},figure_type='float'),
                            self._format({'name': data[11]},figure_type='float'),
                            self._format({'name': data[12]},figure_type='float'),
                            self._format({'name': data[13]},figure_type='float'),
                            self._format({'name': data[14]},figure_type='float'),
                            self._format({'name': data[15]},figure_type='float'),
                            self._format({'name': data[16]},figure_type='float'),
                            self._format({'name': data[17]},figure_type='float'),
                            ],
                'level': 3,
                'unfoldable': False,
                'unfolded': True,
            })
            total_1 += data[5]
            total_2 += data[6]
            total_3 += data[7]
            total_4 += data[8]
            total_5 += data[9]
            total_6 += data[10]
            total_7 += data[11]
            total_8 += data[12]
            total_9 += data[13]
            total_10 += data[14]
            total_11 += data[15]
            total_12 += data[16]
            total_13 += data[17]

        #========== SUBTOTAL 1) +2) ============#
        self.env.cr.execute('''select -3 as id,NULL as sub_origin_resource_id,NULL as journal_id,
                '   SUBTOTAL 1) +2)' as sub_origin_name,
                'Resumen' as sub_origin_name_group_by,
                COALESCE(sum(case when extract(month from payment_date) = 1 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) january,
                COALESCE(sum(case when extract(month from payment_date) = 2 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) february,
                COALESCE(sum(case when extract(month from payment_date) = 3 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) march,
                COALESCE(sum(case when extract(month from payment_date) = 4 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) april,
                COALESCE(sum(case when extract(month from payment_date) = 5 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) may,
                COALESCE(sum(case when extract(month from payment_date) = 6 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) june,
                COALESCE(sum(case when extract(month from payment_date) = 7 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) july,
                COALESCE(sum(case when extract(month from payment_date) = 8 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) august,
                COALESCE(sum(case when extract(month from payment_date) = 9 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) september,
                COALESCE(sum(case when extract(month from payment_date) = 10 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) october,
                COALESCE(sum(case when extract(month from payment_date) = 11 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) november,
                COALESCE(sum(case when extract(month from payment_date) = 12 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) december,
                COALESCE(sum((select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id))),0) as total
                from sub_origin_resource s1,account_payment ap 
                where ap.sub_origin_resource_id = s1.id and ap.state in ('posted','reconciled')
                and s1.name in ('Aspirantes','Servicios de educación Bancos (INS-RINS)','Servicios de educación Caja Gral.')
                and payment_date >= %s and payment_date <= %s      
            ''',(start,end))
        origin_datas = self.env.cr.fetchall()
        
        for data in origin_datas: 
            lines.append({
                'id': 'hierarchy2_sub_1_2',
                'name': data[3],
                'columns': [{'name': ''},
                            {'name': ''},
                            {'name': ''},
                            self._format({'name': data[5]},figure_type='float'),
                            self._format({'name': data[6]},figure_type='float'),
                            self._format({'name': data[7]},figure_type='float'),
                            self._format({'name': data[8]},figure_type='float'),
                            self._format({'name': data[9]},figure_type='float'),
                            self._format({'name': data[10]},figure_type='float'),
                            self._format({'name': data[11]},figure_type='float'),
                            self._format({'name': data[12]},figure_type='float'),
                            self._format({'name': data[13]},figure_type='float'),
                            self._format({'name': data[14]},figure_type='float'),
                            self._format({'name': data[15]},figure_type='float'),
                            self._format({'name': data[16]},figure_type='float'),
                            self._format({'name': data[17]},figure_type='float'),
                            ],
                'level': 3,
                'unfoldable': False,
                'unfolded': True,
            })

        #========== 3) DGIRE ============#
        self.env.cr.execute('''select -4 as id,NULL as sub_origin_resource_id,NULL as journal_id,
                '3) DGIRE' as sub_origin_name,
                'Resumen' as sub_origin_name_group_by,
                COALESCE(sum(case when extract(month from payment_date) = 1 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) january,
                COALESCE(sum(case when extract(month from payment_date) = 2 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) february,
                COALESCE(sum(case when extract(month from payment_date) = 3 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) march,
                COALESCE(sum(case when extract(month from payment_date) = 4 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) april,
                COALESCE(sum(case when extract(month from payment_date) = 5 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) may,
                COALESCE(sum(case when extract(month from payment_date) = 6 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) june,
                COALESCE(sum(case when extract(month from payment_date) = 7 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) july,
                COALESCE(sum(case when extract(month from payment_date) = 8 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) august,
                COALESCE(sum(case when extract(month from payment_date) = 9 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) september,
                COALESCE(sum(case when extract(month from payment_date) = 10 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) october,
                COALESCE(sum(case when extract(month from payment_date) = 11 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) november,
                COALESCE(sum(case when extract(month from payment_date) = 12 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) december,
                COALESCE(sum((select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id))),0) as total
                from sub_origin_resource s1,account_payment ap 
                where ap.sub_origin_resource_id = s1.id and ap.state in ('posted','reconciled')
                and s1.name in ('DGIRE-bancos','DGIRE-caja')   
                and payment_date >= %s and payment_date <= %s
            ''',(start,end))
        origin_datas = self.env.cr.fetchall()
        
        for data in origin_datas: 
            lines.append({
                'id': 'hierarchy2_dgi',
                'name': data[3],
                'columns': [{'name': ''},
                            {'name': ''},
                            {'name': ''},
                            self._format({'name': data[5]},figure_type='float'),
                            self._format({'name': data[6]},figure_type='float'),
                            self._format({'name': data[7]},figure_type='float'),
                            self._format({'name': data[8]},figure_type='float'),
                            self._format({'name': data[9]},figure_type='float'),
                            self._format({'name': data[10]},figure_type='float'),
                            self._format({'name': data[11]},figure_type='float'),
                            self._format({'name': data[12]},figure_type='float'),
                            self._format({'name': data[13]},figure_type='float'),
                            self._format({'name': data[14]},figure_type='float'),
                            self._format({'name': data[15]},figure_type='float'),
                            self._format({'name': data[16]},figure_type='float'),
                            self._format({'name': data[17]},figure_type='float'),
                            ],
                'level': 3,
                'unfoldable': False,
                'unfolded': True,
            })
            total_1 += data[5]
            total_2 += data[6]
            total_3 += data[7]
            total_4 += data[8]
            total_5 += data[9]
            total_6 += data[10]
            total_7 += data[11]
            total_8 += data[12]
            total_9 += data[13]
            total_10 += data[14]
            total_11 += data[15]
            total_12 += data[16]
            total_13 += data[17]

        #========== 4) PATRIMONIALES ============#
        self.env.cr.execute('''select -5 as id,NULL as sub_origin_resource_id,NULL as journal_id,
                '4) PATRIMONIALES' as sub_origin_name,
                'Resumen' as sub_origin_name_group_by,
                COALESCE(sum(case when extract(month from payment_date) = 1 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) january,
                COALESCE(sum(case when extract(month from payment_date) = 2 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) february,
                COALESCE(sum(case when extract(month from payment_date) = 3 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) march,
                COALESCE(sum(case when extract(month from payment_date) = 4 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) april,
                COALESCE(sum(case when extract(month from payment_date) = 5 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) may,
                COALESCE(sum(case when extract(month from payment_date) = 6 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) june,
                COALESCE(sum(case when extract(month from payment_date) = 7 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) july,
                COALESCE(sum(case when extract(month from payment_date) = 8 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) august,
                COALESCE(sum(case when extract(month from payment_date) = 9 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) september,
                COALESCE(sum(case when extract(month from payment_date) = 10 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) october,
                COALESCE(sum(case when extract(month from payment_date) = 11 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) november,
                COALESCE(sum(case when extract(month from payment_date) = 12 then (select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end),0) december,
                COALESCE(sum((select COALESCE(sum(amount_untaxed_signed),0) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id))),0) as total
                from sub_origin_resource s1,account_payment ap 
                where ap.sub_origin_resource_id = s1.id and ap.state in ('posted','reconciled')
                and s1.name in ('D.B.I.N.','D.P.Y.D.','Venta almacén','Licenciatarios','DEP en garantia')
                and payment_date >= %s and payment_date <= %s                      
            ''',(start,end))
        origin_datas = self.env.cr.fetchall()
        
        for data in origin_datas: 
            lines.append({
                'id': 'hierarchy2_pat',
                'name': data[3],
                'columns': [{'name': ''},
                            {'name': ''},
                            {'name': ''},
                            self._format({'name': data[5]},figure_type='float'),
                            self._format({'name': data[6]},figure_type='float'),
                            self._format({'name': data[7]},figure_type='float'),
                            self._format({'name': data[8]},figure_type='float'),
                            self._format({'name': data[9]},figure_type='float'),
                            self._format({'name': data[10]},figure_type='float'),
                            self._format({'name': data[11]},figure_type='float'),
                            self._format({'name': data[12]},figure_type='float'),
                            self._format({'name': data[13]},figure_type='float'),
                            self._format({'name': data[14]},figure_type='float'),
                            self._format({'name': data[15]},figure_type='float'),
                            self._format({'name': data[16]},figure_type='float'),
                            self._format({'name': data[17]},figure_type='float'),
                            ],
                'level': 3,
                'unfoldable': False,
                'unfolded': True,
            })
            total_1 += data[5]
            total_2 += data[6]
            total_3 += data[7]
            total_4 += data[8]
            total_5 += data[9]
            total_6 += data[10]
            total_7 += data[11]
            total_8 += data[12]
            total_9 += data[13]
            total_10 += data[14]
            total_11 += data[15]
            total_12 += data[16]
            total_13 += data[17]

    #====== Total Resumen ========#
        lines.append({
            'id': 'hierarchy2_total_resumen',
            'name': "SUMAS",
            'columns': [{'name': ''},
                        {'name': ''},
                        {'name': ''},
                        self._format({'name': total_1},figure_type='float'),
                        self._format({'name': total_2},figure_type='float'),
                        self._format({'name': total_3},figure_type='float'),
                        self._format({'name': total_4},figure_type='float'),
                        self._format({'name': total_5},figure_type='float'),
                        self._format({'name': total_6},figure_type='float'),
                        self._format({'name': total_7},figure_type='float'),
                        self._format({'name': total_8},figure_type='float'),
                        self._format({'name': total_9},figure_type='float'),
                        self._format({'name': total_10},figure_type='float'),
                        self._format({'name': total_11},figure_type='float'),
                        self._format({'name': total_12},figure_type='float'),
                        self._format({'name': total_13},figure_type='float'),
                        ],
            'level': 2,
            'unfoldable': False,
            'unfolded': True,
            })
            
        return lines

    def _get_report_name(self):
        return _("Income Annual Report")
    
    @api.model
    def _get_super_columns(self, options):
        date_cols = options.get('date') and [options['date']] or []
        date_cols += (options.get('comparison') or {}).get('periods', [])
        columns = reversed(date_cols)
        return {'columns': columns, 'x_offset': 1, 'merge': 5}
    
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
    
    def get_header_year_list(self,options):
        start = datetime.strptime(
            str(options['date'].get('date_from')), '%Y-%m-%d').date()
        end = datetime.strptime(
            options['date'].get('date_to'), '%Y-%m-%d').date()
        
        str1 = ''
        if start.year == end.year:
            if start.month != end.month:
                str1 = self.get_month_name(start.month) + "-" +self.get_month_name(end.month) + " " + str(start.year)
            else:   
                str1 = self.get_month_name(start.month) + " " + str(start.year)
        else:
            str1 = self.get_month_name(start.month)+" "+ str(start.year) + "-" +self.get_month_name(end.month) + " " + str(end.year)
        return str1


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
#         sheet.set_column(0, 0,15)
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
        
#         sheet.merge_range(y_offset, col, 6, col, '')
#         if self.env.user and self.env.user.company_id and self.env.user.company_id.header_logo:
#             filename = 'logo.png'
#             image_data = io.BytesIO(base64.standard_b64decode(self.env.user.company_id.header_logo))
#             sheet.insert_image(0,0, filename, {'image_data': image_data,'x_offset':8,'y_offset':3,'x_scale':0.6,'y_scale':0.6})
        
#         col += 1
        header_title = '''DIRECCIÓN GENERAL DE FINANZAS\nDIRECCIÓN DE INGRESOS Y OPERACIÓN FINANCIERA\nDEPARTAMENTO DE INGRESOS\nINFORME ANUAL INGRESOS\nINGRESOS POR SERVICIOS DE EDUCACIÓN Y PATRIMONIALES\n%s\nREAL'''%(self.get_header_year_list(options))
        sheet.merge_range(y_offset, col, 5, col+16, header_title,super_col_style)
        y_offset += 6
#         col=1
#         currect_time_msg = "Fecha y hora de impresión: "
#         currect_time_msg += datetime.today().strftime('%d/%m/%Y %H:%M')
#         sheet.merge_range(y_offset, col, y_offset, col+17, currect_time_msg,currect_date_style)
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
#             header = self.env['ir.actions.report'].render_template("jt_income.pdf_external_layout_income_annual_report_new", values=rcontext)
#             
#             header = header.decode('utf-8') # Ensure that headers and footer are correctly encoded
#             current_filtered = self.get_header_year_list(options)
#             header.replace("REAL", "Test")
            header='''<div class="header">
                        <div class="row">
                            <div class="col-12 text-center">
                                   <span style="font-size:16px;">DIRECCIÓN GENERAL DE FINANZAS</span><br/>
                                   <span style="font-size:14px;">DIRECCIÓN DE INGRESOS Y OPERACIÓN FINANCIERA</span><br/>
                                   <span style="font-size:12px;">DEPARTAMENTO DE INGRESOS</span><br/>
                                   <span style="font-size:12px;">INFORME ANUAL INGRESOS</span><br/>
                                   <span style="font-size:12px;">INGRESOS POR SERVICIOS DE EDUCACIÓN Y PATRIMONIALES</span><br/>
                                   <span style="font-size:12px;">%s</span><br/>
                                   <span style="font-size:12px;">REAL</span><br/>
                            </div>
                        </div>
                    </div>
                    <div class="article" data-oe-model="res.users" data-oe-id="2" data-oe-lang="en_US">
                      
                    </div>
                '''%(self.get_header_year_list(options))
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
