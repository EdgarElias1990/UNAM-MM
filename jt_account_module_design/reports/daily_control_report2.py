# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import copy
import ast
from lxml import etree
from lxml.objectify import fromstring
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.tools.misc import formatLang, format_date
from odoo.tools import float_is_zero, ustr
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools.misc import xlsxwriter
from odoo.tools import config, date_utils, get_lang
import io
import base64
from datetime import datetime
from datetime import timedelta
import lxml.html


class DailyControlReport(models.Model):
    _name = "jt_account_module_design.daily.control.report.two"
    _description = "Daily Control Report"
    _inherit = "account.coa.report"

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
            DailyControlReport, self)._get_templates()
        templates[
            'main_table_header_template'] = 'account_reports.main_table_header'
        templates['main_template'] = 'account_reports.main_template'
        return templates

    def _get_columns_name(self, options):
        return [
            {'name': _('NO DE OF: ENVIADO A')},
            {'name': _('Fecha')},
            {'name': _('Folio')},
            {'name': _('Concepto')},
            {'name': _('Cuenta Bancaria')},
            {'name': _('Cargo')},
            {'name': _('Abono')},
            {'name': _('Cuenta Bancaria')},
            {'name': _('Cargo')},
            {'name': _('Abono')},
            {'name': _('Cuenta Bancaria')},
            {'name': _('Cargo')},
            {'name': _('Abono')},
            {'name': _('Cuenta Bancaria')},
            {'name': _('Cargo')},
            {'name': _('Abono')},
            {'name': _('Cuenta Bancaria')},
            {'name': _('Cargo')},
            {'name': _('Abono')},
            {'name': _('Cuenta Bancaria')},
            {'name': _('Cargo')},
            {'name': _('Abono')},
            {'name': _('Cuenta Bancaria')},
            {'name': _('Cargo')},
            {'name': _('Abono')},
#24 filas
        ]

    def _format(self, value, figure_type):
        if self.env.context.get('no_format'):
            return value
        value['no_format_name'] = value['name']

        if figure_type == 'float':
            currency_id = self.env.company.currency_id
            if currency_id.is_zero(value['name']):
                # don't print -0.0 in reports
                value['name'] = abs(value['name'])
                value['class'] = 'number text-muted'
            value['name'] = formatLang(
                self.env, value['name'], currency_obj=currency_id)
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
        records = self.env['request.open.balance.finance'].search(
            [('date_required', '>=', start), ('date_required', '<=', end), ('state', '=', 'confirmed')],order="operation_number")
        indi = 0
        totalcargobb = 0
        totalcargoba = 0
        totalcargose = 0
        totalcargohs = 0
        totalcargoci = 0
        totalcargoch = 0
        totalcargojp = 0
        totalabonobb = 0
        totalabonoba = 0
        totalabonose = 0
        totalabonohs = 0
        totalabonoci = 0
        totalabonoch = 0
        totalabonojp = 0
        totalmxn = 0.0
        totalusd = 0.0
        vvv = 0.0
        ssss = self._format({'name': vvv}, figure_type='float')
        for regis in records:
            addline = False
            #-------------Cargo------------
            if regis.bank_account_id.name[:13].upper() == 'BBVA BANCOMER':
                totalcargobb += float(regis.amount)
                if regis.currency_id.name == 'MXN':
                    totalmxn = totalmxn + float(regis.amount)
                elif regis.currency_id.name == 'USD':
                    totalusd = totalusd + float(regis.amount)
                addline = True
                lines.append({
                    'id': "currency_",
                    'name': '',
                    'columns': [
                        {'name': str(regis.date_required)},
                        {'name': str(regis.operation_number)},
                        {'name': str(regis.concept)},
                        {'name': str(regis.origin_account.acc_number)},
                        self._format({'name': regis.amount},figure_type='float'),
                        self._format({'name': vvv}, figure_type='float'),
                        {'name': '0'},
                        self._format({'name': vvv}, figure_type='float'),
                        self._format({'name': vvv}, figure_type='float'),
                        {'name': '0'},
                        self._format({'name': vvv}, figure_type='float'),
                        self._format({'name': vvv}, figure_type='float'),
                        {'name': '0'},
                        self._format({'name': vvv}, figure_type='float'),
                        self._format({'name': vvv}, figure_type='float'),
                        {'name': '0'},
                        self._format({'name': vvv}, figure_type='float'),
                        self._format({'name': vvv}, figure_type='float'),
                        {'name': '0'},
                        self._format({'name': vvv}, figure_type='float'),
                        self._format({'name': vvv}, figure_type='float'),
                        {'name': '0'},
                        self._format({'name': vvv}, figure_type='float'),
                        self._format({'name': vvv}, figure_type='float'),
                    ],

                    'level': 3,
                    'unfoldable': False,
                    'unfolded': True,
                })

            elif regis.bank_account_id.name[:7].upper() == 'BANAMEX':
                if regis.currency_id.name == 'MXN':
                    totalmxn = totalmxn + float(regis.amount)
                elif regis.currency_id.name == 'USD':
                    totalusd = totalusd + float(regis.amount)
                totalcargoba += float(regis.amount)
                addline = True
                lines.append({
                    'id': "currency_",
                    'name': '',
                    'columns': [
                        {'name': str(regis.date_required)},
                        {'name': str(regis.operation_number)},
                        {'name': str(regis.concept)},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': str(regis.origin_account.acc_number)},
                        self._format({'name': regis.amount},figure_type='float'),
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},

                    ],

                    'level': 3,
                    'unfoldable': False,
                    'unfolded': True,
                })

            elif regis.bank_account_id.name[:6].upper() == 'SERFIN':
                if regis.currency_id.name == 'MXN':
                    totalmxn = totalmxn + float(regis.amount)
                elif regis.currency_id.name == 'USD':
                    totalusd = totalusd + float(regis.amount)
                totalcargose += float(regis.amount)
                addline = True
                lines.append({
                    'id': "currency_",
                    'name': '',
                    'columns': [
                        {'name': str(regis.date_required)},
                        {'name': str(regis.operation_number)},
                        {'name': str(regis.concept)},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': str(regis.origin_account.acc_number)},
                        self._format({'name': regis.amount},figure_type='float'),
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},

                    ],

                    'level': 3,
                    'unfoldable': False,
                    'unfolded': True,
                })

            elif regis.bank_account_id.name[:4].upper() == 'HSBC':
                if regis.currency_id.name == 'MXN':
                    totalmxn = totalmxn + float(regis.amount)
                elif regis.currency_id.name == 'USD':
                    totalusd = totalusd + float(regis.amount)
                totalcargohs += float(regis.amount)
                addline = True
                lines.append({
                    'id': "currency_",
                    'name': '',
                    'columns': [
                        {'name': str(regis.date_required)},
                        {'name': str(regis.operation_number)},
                        {'name': str(regis.concept)},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': str(regis.origin_account.acc_number)},
                        self._format({'name': regis.amount},figure_type='float'),
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                    ],

                    'level': 3,
                    'unfoldable': False,
                    'unfolded': True,
                })

            elif regis.bank_account_id.name[:11].upper() == 'CITIBANAMEX':
                if regis.currency_id.name == 'MXN':
                    totalmxn = totalmxn + float(regis.amount)
                elif regis.currency_id.name == 'USD':
                    totalusd = totalusd + float(regis.amount)
                totalcargoci += float(regis.amount)
                addline = True
                lines.append({
                    'id': "currency_",
                    'name': '',
                    'columns': [
                        {'name': str(regis.date_required)},
                        {'name': str(regis.operation_number)},
                        {'name': str(regis.concept)},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': str(regis.origin_account.acc_number)},
                        self._format({'name': regis.amount},figure_type='float'),
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},

                    ],

                    'level': 3,
                    'unfoldable': False,
                    'unfolded': True,
                })

            elif regis.bank_account_id.name[:11].upper() == 'CHASE BANK':
                if regis.currency_id.name == 'MXN':
                    totalmxn = totalmxn + float(regis.amount)
                elif regis.currency_id.name == 'USD':
                    totalusd = totalusd + float(regis.amount)
                totalcargoch += float(regis.amount)
                addline = True
                lines.append({
                    'id': "currency_",
                    'name': '',
                    'columns': [
                        {'name': str(regis.date_required)},
                        {'name': str(regis.operation_number)},
                        {'name': str(regis.concept)},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': str(regis.origin_account.acc_number)},
                        self._format({'name': regis.amount},figure_type='float'),
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},

                    ],

                    'level': 3,
                    'unfoldable': False,
                    'unfolded': True,
                })

            elif regis.bank_account_id.name[:11].upper() == 'JP MORGAN':
                if regis.currency_id.name == 'MXN':
                    totalmxn = totalmxn + float(regis.amount)
                elif regis.currency_id.name == 'USD':
                    totalusd = totalusd + float(regis.amount)
                totalcargojp += float(regis.amount)
                addline = True
                lines.append({
                    'id': "currency_",
                    'name': '',
                    'columns': [
                        {'name': str(regis.date_required)},
                        {'name': str(regis.operation_number)},
                        {'name': str(regis.concept)},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': '0'},
                        {'name': ssss.get('name')},
                        {'name': ssss.get('name')},
                        {'name': str(regis.origin_account.acc_number)},
                        self._format({'name': regis.amount},figure_type='float'),
                        {'name': ssss.get('name')},

                    ],

                    'level': 3,
                    'unfoldable': False,
                    'unfolded': True,
                })

            #----------------Abonos-----------------
            if addline:
                if regis.desti_bank_account_id.name[:13].upper() == 'BBVA BANCOMER':
                    if regis.currency_id.name == 'MXN':
                        totalmxn = totalmxn + float(regis.amount)
                    elif regis.currency_id.name == 'USD':
                        totalusd = totalusd + float(regis.amount)
                    totalabonobb += float(regis.amount)
                    formateo = self._format({'name': regis.amount},figure_type='float')
                    lines[indi].get('columns')[3]['name'] = str(regis.desti_account.acc_number)
                    lines[indi].get('columns')[5]['name'] = formateo.get('name')

                elif regis.desti_bank_account_id.name[:7].upper() == 'BANAMEX':
                    if regis.currency_id.name == 'MXN':
                        totalmxn = totalmxn + float(regis.amount)
                    elif regis.currency_id.name == 'USD':
                        totalusd = totalusd + float(regis.amount)
                    totalabonoba += float(regis.amount)
                    formateo = self._format({'name': regis.amount}, figure_type='float')
                    lines[indi].get('columns')[6]['name'] = str(regis.desti_account.acc_number)
                    lines[indi].get('columns')[8]['name'] = formateo.get('name')

                elif regis.desti_bank_account_id.name[:6].upper() == 'SERFIN':
                    if regis.currency_id.name == 'MXN':
                        totalmxn = totalmxn + float(regis.amount)
                    elif regis.currency_id.name == 'USD':
                        totalusd = totalusd + float(regis.amount)
                    totalabonose += float(regis.amount)
                    formateo = self._format({'name': regis.amount}, figure_type='float')
                    lines[indi].get('columns')[9]['name'] = str(regis.desti_account.acc_number)
                    lines[indi].get('columns')[11]['name'] = formateo.get('name')

                elif regis.desti_bank_account_id.name[:4].upper() == 'HSBC':
                    if regis.currency_id.name == 'MXN':
                        totalmxn = totalmxn + float(regis.amount)
                    elif regis.currency_id.name == 'USD':
                        totalusd = totalusd + float(regis.amount)
                    totalabonohs += float(regis.amount)
                    formateo = self._format({'name': regis.amount}, figure_type='float')
                    lines[indi].get('columns')[12]['name'] = str(regis.desti_account.acc_number)
                    lines[indi].get('columns')[14]['name'] = formateo.get('name')

                elif regis.desti_bank_account_id.name[:11].upper() == 'CITIBANAMEX':
                    if regis.currency_id.name == 'MXN':
                        totalmxn = totalmxn + float(regis.amount)
                    elif regis.currency_id.name == 'USD':
                        totalusd = totalusd + float(regis.amount)
                    totalabonoci += float(regis.amount)
                    formateo = self._format({'name': regis.amount}, figure_type='float')
                    lines[indi].get('columns')[15]['name'] = str(regis.desti_account.acc_number)
                    lines[indi].get('columns')[17]['name'] = formateo.get('name')

                elif regis.desti_bank_account_id.name[:11].upper() == 'CHASE BANK':
                    if regis.currency_id.name == 'MXN':
                        totalmxn = totalmxn + float(regis.amount)
                    elif regis.currency_id.name == 'USD':
                        totalusd = totalusd + float(regis.amount)
                    totalabonoch += float(regis.amount)
                    formateo = self._format({'name': regis.amount}, figure_type='float')
                    lines[indi].get('columns')[18]['name'] = str(regis.desti_account.acc_number)
                    lines[indi].get('columns')[20]['name'] = formateo.get('name')

                elif regis.desti_bank_account_id.name[:11].upper() == 'JP MORGAN':
                    if regis.currency_id.name == 'MXN':
                        totalmxn = totalmxn + float(regis.amount)
                    elif regis.currency_id.name == 'USD':
                        totalusd = totalusd + float(regis.amount)
                    totalabonojp += float(regis.amount)
                    formateo = self._format({'name': regis.amount}, figure_type='float')
                    lines[indi].get('columns')[21]['name'] = str(regis.desti_account.acc_number)
                    lines[indi].get('columns')[23]['name'] = formateo.get('name')
                indi += 1

        lines.append({
            'id': "currency_",
            'name': 'TOTALES',
            'columns': [
                {'name': ''},
                {'name': ''},
                {'name': ''},
                {'name': ''},
                self._format({'name': float(totalcargobb)}, figure_type='float'),
                self._format({'name': float(totalabonobb)}, figure_type='float'),
                {'name': ''},
                self._format({'name': float(totalcargoba)}, figure_type='float'),
                self._format({'name': float(totalabonoba)}, figure_type='float'),
                {'name': ''},
                self._format({'name': float(totalcargose)}, figure_type='float'),
                self._format({'name': float(totalabonose)}, figure_type='float'),
                {'name': ''},
                self._format({'name': float(totalcargohs)}, figure_type='float'),
                self._format({'name': float(totalabonohs)}, figure_type='float'),
                {'name': ''},
                self._format({'name': float(totalcargoci)}, figure_type='float'),
                self._format({'name': float(totalabonoci)}, figure_type='float'),
                {'name': ''},
                self._format({'name': float(totalcargoch)}, figure_type='float'),
                self._format({'name': float(totalabonoch)}, figure_type='float'),
                {'name': ''},
                self._format({'name': float(totalcargojp)}, figure_type='float'),
                self._format({'name': float(totalabonojp)}, figure_type='float'),

            ],

            'level': 2,
            'unfoldable': False,
            'unfolded': True,
        })

        abonototal = totalcargobb + totalcargoba + totalcargose + totalcargohs + totalcargoci + totalcargoch + totalcargojp
        cargototal = totalabonobb + totalabonoba + totalabonose + totalabonohs + totalabonoci + totalabonoch + totalabonojp


        lines.append({
            'id': "currency_",
            'name': 'Total Abonos',
            'columns': [
                {'name': 'gg'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                self._format({'name': float(abonototal)}, figure_type='float'),

            ],

            'level': 2,
            'unfoldable': False,
            'unfolded': True,
        })

        lines.append({
            'id': "currency_",
            'name': 'Total Cargos',
            'columns': [
                {'name': 'gg'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                self._format({'name': float(cargototal)}, figure_type='float'),

            ],

            'level': 2,
            'unfoldable': False,
            'unfolded': True,
        })

        lines.append({
            'id': "currency_",
            'name': 'Total MXN',
            'columns': [
                {'name': 'gg'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                self._format({'name': float(totalmxn)}, figure_type='float'),

            ],

            'level': 2,
            'unfoldable': False,
            'unfolded': True,
        })

        lines.append({
            'id': "currency_",
            'name': 'Total USD',
            'columns': [
                {'name': 'gg'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                {'name': 'ff'},
                self._format({'name': float(totalusd)}, figure_type='float'),

            ],

            'level': 2,
            'unfoldable': False,
            'unfolded': True,
        })
        return lines

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

        base_url = self.env['ir.config_parameter'].sudo().get_param('report.url') or self.env[
            'ir.config_parameter'].sudo().get_param('web.base.url')
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
        body_html = body_html.replace(b'<div class="o_account_reports_header">', b'<div style="display:none;">')

        body = body.replace(b'<body class="o_account_reports_body_print">',
                            b'<body class="o_account_reports_body_print">' + body_html)
        if minimal_layout:
            header = ''
            footer = self.env['ir.actions.report'].render_template("web.internal_layout", values=rcontext)
            spec_paperformat_args = {'data-report-margin-top': 10, 'data-report-header-spacing': 10}
            footer = self.env['ir.actions.report'].render_template("web.minimal_layout",
                                                                   values=dict(rcontext, subst=True, body=footer))
        else:
            rcontext.update({
                'css': '',
                'o': self.env.user,
                'res_company': self.env.company,
            })
            header = self.env['ir.actions.report'].render_template(
                "jt_account_module_design.external_layout_daily_count_id", values=rcontext)
            header = header.decode('utf-8')  # Ensure that headers and footer are correctly encoded
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
                    headers = self.env['ir.actions.report'].render_template("web.minimal_layout",
                                                                            values=dict(rcontext, subst=True,
                                                                                        body=headers))

                for node in root.xpath(match_klass.format('footer')):
                    footer = lxml.html.tostring(node)
                    footer = self.env['ir.actions.report'].render_template("web.minimal_layout",
                                                                           values=dict(rcontext, subst=True,
                                                                                       body=footer))

            except lxml.etree.XMLSyntaxError:
                headers = header.encode()
                footer = b''
            header = headers

        landscape = False
        if len(self.with_context(print_mode=True).get_header(options)[-1]) > 5:
            landscape = True

        fec = datetime.now().strftime('%d/%m/%Y %H:%M')
        conc = '<div class="o_account_reports_summary"></div> <div class="float-right"> <span style="font-size:16px;">Fecha y hora de impresión &#160;' + fec + '</span></div>'
        body = body.replace(b'<div class="o_account_reports_summary"></div>', str.encode(conc))
        body = body.replace(b'<tr class="o_account_reports_level2  o_js_account_report_parent_row_unfolded" style="outline: thin solid; outline-width: 2px;">', b'<tr class="o_account_reports_level2  o_js_account_report_parent_row_unfolded" style="border-top:2px solid black">')

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
        default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})
        title_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2})
        super_col_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'align': 'center'})
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
        level_3_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})
        currect_date_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'align': 'right'})
        currect_date_style.set_border(0)
        super_col_style.set_border(0)
        # Set the first column width to 50
        sheet.set_column(0, 0, 20)
        sheet.set_column(0, 1, 15)
        sheet.set_column(0, 2, 15)
        sheet.set_column(0, 3, 15)
        sheet.set_column(0, 4, 20)
        super_columns = self._get_super_columns(options)
        y_offset = 0
        col = 0

        sheet.merge_range(y_offset, col, 6, col, '', super_col_style)
        if self.env.user and self.env.user.company_id and self.env.user.company_id.header_logo:
            filename = 'logo.png'
            image_data = io.BytesIO(base64.standard_b64decode(self.env.user.company_id.header_logo))
            sheet.insert_image(0, 0, filename,
                               {'image_data': image_data, 'x_offset': 8, 'y_offset': 3, 'x_scale': 0.6, 'y_scale': 0.6})

        col += 1
        header_title = '''UNIVERSIDAD NACIONAL AUTÓNOMA DE MÉXICO\nUniversity Board\nGeneral Directorate of Finance\n%s''' % self._get_report_name()
        sheet.merge_range(y_offset, col, 5, col + 3, header_title, super_col_style)
        y_offset += 6
        col = 1
        currect_time_msg = "Fecha y hora de impresión: "
        currect_time_msg += datetime.today().strftime('%d/%m/%Y %H:%M')
        sheet.merge_range(y_offset, col, y_offset, col + 3, currect_time_msg, currect_date_style)
        y_offset += 1
        sheet.merge_range(y_offset, 1, y_offset, 2, "PERIODO", super_col_style)
        y_offset += 1
        sheet.merge_range('E9:G9', "BBVA BANCOMER", super_col_style)
        sheet.merge_range('H9:J9', "BANAMEX", super_col_style)
        sheet.merge_range('K9:M9', "SERFIN", super_col_style)
        sheet.merge_range('N9:P9', "HSBC", super_col_style)
        sheet.merge_range('Q9:S9', "CITYBANAMEX", super_col_style)
        sheet.merge_range('T9:V9', "CHASE BANK", super_col_style)
        sheet.merge_range('W9:Y9', "JP MORGAN", super_col_style)
        y_offset += 1
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
        ctx.update({'no_format': True, 'print_mode': True, 'prefetch_fields': False})
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

            # write the first column, with a specific style to manage the indentation
            cell_type, cell_value = self._get_cell_type_value(lines[y])
            if cell_type == 'date':
                sheet.write_datetime(y + y_offset, 0, cell_value, date_default_col1_style)
            else:
                sheet.write(y + y_offset, 0, cell_value, col1_style)

            # write all the remaining cells
            for x in range(1, len(lines[y]['columns']) + 1):
                cell_type, cell_value = self._get_cell_type_value(lines[y]['columns'][x - 1])
                if cell_type == 'date':
                    sheet.write_datetime(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value,
                                         date_default_style)
                else:
                    sheet.write(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value, style)

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
                  'company_name': self.env.company.name, }
        report = {}
        # options.get('date',{}).update({'string':''})
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

        render_template = templates.get('main_template', 'jt_account_module_design.financial_statement_main_template')
        if line_id is not None:
            render_template = templates.get('line_template', 'account_reports.line_template')
        html = self.env['ir.ui.view'].render_template(
            render_template,
            values=dict(rcontext),
        )
        if self.env.context.get('print_mode', False):
            for k, v in self._replace_class().items():
                html = html.replace(k, v)
            # append footnote as well
            html = html.replace(b'<div class="js_account_report_footnotes"></div>',
                                self.get_html_footnotes(footnotes_to_render))

        html = html.replace(b'<th class="o_account_report_column_header " style="">',b'<th class="o_account_report_column_header " style="text-align:center !important">')
        html = html.replace(b'<thead>',b'<tr class="o_account_report_column_header"> <th colspan="4" class="o_account_report_column_header " style="text-align:center !important"></th><th colspan="3" class="o_account_report_column_header " style="text-align:center !important">BBVA BANCOMER</th><th colspan="3" class="o_account_report_column_header " style="text-align:center !important">BANAMEX</th><th colspan="3" class="o_account_report_column_header " style="text-align:center !important">SERFIN</th><th colspan="3" class="o_account_report_column_header " style="text-align:center !important">HSBC</th><th colspan="3" class="o_account_report_column_header " style="text-align:center !important">CITYBANAMEX</th><th colspan="3" class="o_account_report_column_header " style="text-align:center !important">CHASE BANK</th><th colspan="3" class="o_account_report_column_header " style="text-align:center !important">JP MORGAN</th></tr>')
        html = html.replace(b'</thead>',b' ')
        html = html.replace(b'<tbody>', b' ')
        html = html.replace(b'</tbody>', b' ')
        html = html.replace(b'<td class="o_account_report_line  o_account_report_line_indent" style="">', b'<td class="o_account_report_line  o_account_report_line_indent" style="text-align:center !important">')
        html = html.replace(b'<table class="o_account_reports_table table-hover">', b'<table class="o_account_reports_table table-hover" bordercolor="blue" border = "1"> ')
        html = html.replace(b'<td class="o_account_report_line number o_account_report_line_indent" style="">', b'<td class="o_account_report_line number o_account_report_line_indent" style="text-align:center !important">')
        html = html.replace(b'<tr class="o_account_reports_level2  o_js_account_report_parent_row_unfolded" style="">', b'<tr class="o_account_reports_level2  o_js_account_report_parent_row_unfolded" style="outline: thin solid; outline-width: 2px;">')
        html = html.replace(b'<td class="o_account_report_line  o_account_report_line_indent" style="text-align:center !important">\n                    <span class="o_account_report_column_value">\n                        ff\n                    </span>\n                </td>', b'')
        html = html.replace(b'<td class="o_account_report_line  o_account_report_line_indent" style="text-align:center !important">\n                    <span class="o_account_report_column_value">\n                        gg\n                    </span>\n                </td>',b'<td colspan="23"></td>')

        return html

    def _get_report_name(self):
        return _("Daily Control Report")
