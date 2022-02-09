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
from odoo import models, _
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.misc import formatLang
from odoo.tools.misc import xlsxwriter
import io
import base64
from odoo.tools import config, date_utils, get_lang
import lxml.html

class TaxReport(models.AbstractModel):

    _name = "jt_tax_transaction.taxpay.report"
    _inherit = "account.coa.report"
    _description = "​Tax Report to Enter/Pay"

    filter_date = {'mode': 'range', 'filter': 'this_month'}
    filter_comparison = None
    filter_all_entries = False
    filter_journals = True
    filter_analytic = None
    filter_unfold_all = None
    filter_cash_basis = None
    filter_hierarchy = None
    filter_unposted_in_period = None
    MAX_LINES = None

    def _get_reports_buttons(self):
        return [
            {'name': _('Export to PDF'), 'sequence': 1,
             'action': 'print_pdf', 'file_export_type': _('PDF')},
            {'name': _('Export (XLSX)'), 'sequence': 2,
             'action': 'print_xlsx', 'file_export_type': _('XLSX')},
        ]
    def _get_templates(self):
        templates = super(
            TaxReport, self)._get_templates()
        templates[
            'main_table_header_template'] = 'account_reports.main_table_header'
        templates['main_template'] = 'account_reports.main_template'
        return templates

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

    def _get_columns_name(self, options):
        return [

            {'name': ''},
            {'name': ''},
            {'name': ''},
        ]
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

    def _get_lines(self, options, line_id=None):
        lines = []

        if options.get('all_entries') is False:
            move_state_domain = ('move_id.state', '=', 'posted')
        else:
            move_state_domain = ('move_id.state', '!=', 'cancel')

        start = datetime.strptime(
            str(options['date'].get('date_from')), '%Y-%m-%d').date()
        end = datetime.strptime(
            options['date'].get('date_to'), '%Y-%m-%d').date()

        #domain = [('date', '>=', start),('date', '<=', end),move_state_domain]
        domain = [('date', '<=', end),move_state_domain]
        month_name = self.get_month_name(start.month)

        prev = start.replace(day=1) - timedelta(days=1)
        previous_month = self.get_month_name(prev.month)

        #===============220.001.001============#
        acc_amount_220_001_001_001 = 0
        account_id = self.env['account.account'].search([('code', '=', '220.001.001.001')], limit=1)
        if account_id:
            values= self.env['account.move.line'].search(domain + [('account_id', '=', account_id.id)])
            acc_amount_220_001_001_001 = sum(x.credit - x.debit for x in values)
            #acc_amount_220_001_001_001 = acc_amount_220_001_001_001/1000
    
        #===============115.001.001============#
        acc_amount_115_001_001 = 0
        account_id = self.env['account.account'].search([('code', '=', '115.001.001')], limit=1)
        if account_id:
            values= self.env['account.move.line'].search(domain + [('account_id', '=', account_id.id)])
            acc_amount_115_001_001 = sum(x.debit - x.credit for x in values)
            #acc_amount_115_001_001 = acc_amount_115_001_001/1000

        #===============220.001.001.003 ============#
        acc_amount_220_001_001_003 = 0
        account_id = self.env['account.account'].search([('code', '=', '220.001.001.003')], limit=1)
        if account_id:            
            values= self.env['account.move.line'].search(domain+[('account_id', '=', account_id.id)])
            acc_amount_220_001_001_003 = sum(x.credit - x.debit for x in values)
            #acc_amount_220_001_001_003 = acc_amount_220_001_001_003/1000

        total_isr = acc_amount_220_001_001_001 + acc_amount_220_001_001_003

        total_bal1 = total_isr - acc_amount_115_001_001
         
        lines.append({
            'id': 'hierarchy_account1',
            'name' : _('ISR withholding wages minus subsidy'), 
            'columns': [
                        {'name':''},
                         self._format({'name': total_bal1},figure_type='float'),
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-center',
        })

        lines.append({
            'id': 'hierarchy_account4',
            'name' : '220.001.001.001 ' +_('ISR SALARIES PAYROLL'), 
            'columns': [
                         self._format({'name': acc_amount_220_001_001_001},figure_type='float'),
                         {'name':''},
                        ],
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-left',
        })

        lines.append({
            'id': 'hierarchy_account6',
            'name' : '220.001.001.003 ' +_('ISR PAYMENT ADDITIONAL NOT TAXED'), 
            'columns': [
                         self._format({'name': acc_amount_220_001_001_003},figure_type='float'),
                         {'name':''},
                        ],
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-left',
        })

        lines.append({
            'id': 'hierarchy_account3',
            'name' : _('Total ISR. Withholding For Salaries'), 
            'columns': [
                        self._format({'name': total_isr},figure_type='float'),
                         {'name': ''},
                        ],
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-center',
        })

        lines.append({
            'id': 'hierarchy_account3',
            'name' : _('Employment Subsidy'), 
            'columns': [
                         {'name': _('Less:')},
                         {'name': ''},
                        ],
            'level': 4,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-left',
        })

        lines.append({
            'id': 'hierarchy_account3',
            'name' : '115.001.001 ' + _('employee subsidy'), 
            'columns': [
                        self._format({'name': acc_amount_115_001_001},figure_type='float'),
                         {'name': ''},
                         
                        ],
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-left',
        })

        #===============220.001.001.002 ============#
        acc_amount_220_001_001_002 = 0
        account_id = self.env['account.account'].search([('code', '=', '220.001.001.002')], limit=1)
        if account_id:            
            values= self.env['account.move.line'].search(domain+[('account_id', '=', account_id.id)])
            acc_amount_220_001_001_002 = sum(x.credit - x.debit for x in values)
            #acc_amount_220_001_001_002 = acc_amount_220_001_001_002/1000
        
        lines.append({
            'id': 'hierarchy_account1',
            'name' : _('ISR withholding For Assimilated wages'), 
            'columns': [
                        {'name':''},
                         self._format({'name': acc_amount_220_001_001_002},figure_type='float'),
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-center',
        })

        lines.append({
            'id': 'hierarchy_account5',
            'name' : '220.001.001.002 ' +_('ISR ASIMILATED FEES'), 
            'columns': [
                         self._format({'name': acc_amount_220_001_001_002},figure_type='float'),
                         {'name':''},
                        ],
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-left',
        })

         #===============220.001.002.001 ============#
        acc_amount_220_001_002_001 = 0
        account_id = self.env['account.account'].search([('code', '=', '220.001.002.001')], limit=1)
        if account_id:            
            values= self.env['account.move.line'].search(domain+[('account_id', '=', account_id.id)])
            acc_amount_220_001_002_001 = sum(x.credit - x.debit for x in values)
            #acc_amount_220_001_002_001 = acc_amount_220_001_002_001/1000

        #===============220.001.002.002 ============#
        acc_amount_220_001_002_002 = 0
        account_id = self.env['account.account'].search([('code', '=', '220.001.002.002')], limit=1)
        if account_id:            
            values= self.env['account.move.line'].search(domain+[('account_id', '=', account_id.id)])
            acc_amount_220_001_002_002 = sum(x.credit - x.debit for x in values)
            #acc_amount_220_001_002_002 = acc_amount_220_001_002_002/1000

        #===============220.001.002.003 ============#
        acc_amount_220_001_002_003 = 0
        account_id = self.env['account.account'].search([('code', '=', '220.001.002.003')], limit=1)
        if account_id:            
            values= self.env['account.move.line'].search(domain+[('account_id', '=', account_id.id)])
            acc_amount_220_001_002_003 = sum(x.credit - x.debit for x in values)
            #acc_amount_220_001_002_003 = acc_amount_220_001_002_003/1000

         #===============220.001.002.004 ============#
        acc_amount_220_001_002_004 = 0
        account_id = self.env['account.account'].search([('code', '=', '220.001.002.004')], limit=1)
        if account_id:            
            values= self.env['account.move.line'].search(domain+[('account_id', '=', account_id.id)])
            acc_amount_220_001_002_004 = sum(x.credit - x.debit for x in values)
            #acc_amount_220_001_002_004 = acc_amount_220_001_002_004/1000

        #===============220.001.002.005 ============#
        acc_amount_220_001_002_005 = 0
        account_id = self.env['account.account'].search([('code', '=', '220.001.002.005')], limit=1)
        if account_id:            
            values= self.env['account.move.line'].search(domain+[('account_id', '=', account_id.id)])
            acc_amount_220_001_002_005 = sum(x.credit - x.debit for x in values)
            #acc_amount_220_001_002_005 = acc_amount_220_001_002_005/1000

        ret_total = acc_amount_220_001_002_001 + acc_amount_220_001_002_002 + acc_amount_220_001_002_003 + acc_amount_220_001_002_004 + acc_amount_220_001_002_005

        lines.append({
            'id': 'hierarchy_account1',
            'name' : _('ISR Retained Professional Services'), 
            'columns': [
                        {'name':''},
                         self._format({'name': ret_total},figure_type='float'),
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-center',
        })

        #===============220.001.002.001 ============#
        
        lines.append({
            'id': 'hierarchy_account7',
            'name' : '220.001.002.001 ' +_('ISR-SP HONORISTS 10%'), 
            'columns': [
                         self._format({'name': acc_amount_220_001_002_001},figure_type='float'),
                         {'name':''},
                        ],
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-left',
        })

        #===============220.001.002.002 ============#
        
        lines.append({
            'id': 'hierarchy_account8',
            'name' : '220.001.002.002 ' +_('ISR-SP COPYRIGHT'), 
            'columns': [
                         self._format({'name': acc_amount_220_001_002_002},figure_type='float'),
                         {'name':''},
                        ],
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-left',
        })

        #===============220.001.002.003 ============#
        
        lines.append({
            'id': 'hierarchy_account9',
            'name' : '220.001.002.003 ' +_('ISR 25% RET. S / EXT FEES'), 
            'columns': [
                         self._format({'name': acc_amount_220_001_002_003},figure_type='float'),
                         {'name':''},
                        ],
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-left',
        })

        #===============220.001.002.004 ============#
        
        lines.append({
            'id': 'hierarchy_account10',
            'name' : '220.001.002.004 ' +_('ISR-SP HON. 10% cert. D.E.P. GAS'), 
            'columns': [
                         self._format({'name': acc_amount_220_001_002_004},figure_type='float'),
                         {'name':''},
                        ],
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-left',
        })

        #===============220.001.002.005 ============#
        
        lines.append({
            'id': 'hierarchy_account11',
            'name' : '220.001.002.005 ' +_('ISR-SP HON. Cert. D.E.P. CONACYT'), 
            'columns': [
                         self._format({'name': acc_amount_220_001_002_005},figure_type='float'),
                         {'name':''},
                        ],
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-left',
        })

        #===============220.001.003.001 ============#
        acc_amount_220_001_003_001 = 0
        account_id = self.env['account.account'].search([('code', '=', '220.001.003.001')], limit=1)
        if account_id:            
            values= self.env['account.move.line'].search(domain+[('account_id', '=', account_id.id)])
            acc_amount_220_001_003_001 = sum(x.credit - x.debit for x in values)
            #acc_amount_220_001_003_001 = acc_amount_220_001_003_001/1000
        
        lines.append({
            'id': 'hierarchy_account1',
            'name' : _('ISR Retained Lease'), 
            'columns': [
                        {'name':''},
                         self._format({'name': acc_amount_220_001_003_001},figure_type='float'),
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-center',
        })

        lines.append({
            'id': 'hierarchy_account12',
            'name' : '220.001.003.001 ' +_('ISR ON RENT PAID'), 
            'columns': [
                         self._format({'name': acc_amount_220_001_003_001},figure_type='float'),
                         {'name':''},
                        ],
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-left',
        })

        #===============220.001.004.001 ============#
        acc_amount_220_001_004_001 = 0
        account_id = self.env['account.account'].search([('code', '=', '220.001.004.001')], limit=1)
        if account_id:            
            values= self.env['account.move.line'].search(domain+[('account_id', '=', account_id.id)])
            acc_amount_220_001_004_001 = sum(x.credit - x.debit for x in values)
            #acc_amount_220_001_004_001 = acc_amount_220_001_004_001/1000

        #===============220.001.004.002 ============#
        acc_amount_220_001_004_002 = 0
        account_id = self.env['account.account'].search([('code', '=', '220.001.004.002')], limit=1)
        if account_id:            
            values= self.env['account.move.line'].search(domain+[('account_id', '=', account_id.id)])
            acc_amount_220_001_004_002 = sum(x.credit - x.debit for x in values)
            #acc_amount_220_001_004_002 = acc_amount_220_001_004_002/1000

        #===============220.001.004.003 ============#
        acc_amount_220_001_004_003 = 0
        account_id = self.env['account.account'].search([('code', '=', '220.001.004.003')], limit=1)
        if account_id:            
            values= self.env['account.move.line'].search(domain+[('account_id', '=', account_id.id)])
            acc_amount_220_001_004_003 = sum(x.credit - x.debit for x in values)
            #acc_amount_220_001_004_003 = acc_amount_220_001_004_003/1000

        #===============220.001.004.004 ============#
        acc_amount_220_001_004_004 = 0
        account_id = self.env['account.account'].search([('code', '=', '220.001.004.004')], limit=1)
        if account_id:            
            values= self.env['account.move.line'].search(domain+[('account_id', '=', account_id.id)])
            acc_amount_220_001_004_004 = sum(x.credit - x.debit for x in values)
            #acc_amount_220_001_004_004 = acc_amount_220_001_004_004/1000

        #===============220.001.004.005 ============#
        acc_amount_220_001_004_005 = 0
        account_id = self.env['account.account'].search([('code', '=', '220.001.004.005')], limit=1)
        if account_id:            
            values= self.env['account.move.line'].search(domain+[('account_id', '=', account_id.id)])
            acc_amount_220_001_004_005 = sum(x.credit - x.debit for x in values)
            #acc_amount_220_001_004_005 = acc_amount_220_001_004_005/1000

        #===============220.001.004.006 ============#
        acc_amount_220_001_004_006 = 0
        account_id = self.env['account.account'].search([('code', '=', '220.001.004.006')], limit=1)
        if account_id:            
            values= self.env['account.move.line'].search(domain+[('account_id', '=', account_id.id)])
            acc_amount_220_001_004_006 = sum(x.credit - x.debit for x in values)
            #acc_amount_220_001_004_006 = acc_amount_220_001_004_006/1000

        vat_total = acc_amount_220_001_004_001 + acc_amount_220_001_004_002 + acc_amount_220_001_004_003 + acc_amount_220_001_004_004 +  acc_amount_220_001_004_005 + acc_amount_220_001_004_006
        
        lines.append({
            'id': 'hierarchy_account1',
            'name' : _('VAT Withheld'), 
            'columns': [
                        {'name':''},
                         self._format({'name': vat_total},figure_type='float'),
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-center',
        })

        lines.append({
            'id': 'hierarchy_account13',
            'name' : '220.001.004.001 ' +_('VAT-SP HONORISTSRENTAL'), 
            'columns': [
                         self._format({'name': acc_amount_220_001_004_001},figure_type='float'),
                         {'name':''},
                        ],
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-left',
        })

        #===============220.001.004.002 ============#

        lines.append({
            'id': 'hierarchy_account14',
            'name' : '220.001.004.002 ' +_('VAT PAID'), 
            'columns': [
                         self._format({'name': acc_amount_220_001_004_002},figure_type='float'),
                         {'name':''},
                        ],
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-left',
        })

        #===============220.001.004.003 ============#
        
        lines.append({
            'id': 'hierarchy_account15',
            'name' : '220.001.004.003 ' +_('VAT TRANSPORTATION SERVICES'), 
            'columns': [
                         self._format({'name': acc_amount_220_001_004_003},figure_type='float'),
                         {'name':''},
                        ],
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-left',
        })

        #===============220.001.004.004 ============#
        
        lines.append({
            'id': 'hierarchy_account16',
            'name' : '220.001.004.004 ' +_('VAT-SP HON. Cert. D.E.P. GASOLIN'), 
            'columns': [
                         self._format({'name': acc_amount_220_001_004_004},figure_type='float'),
                         {'name':''},
                        ],
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-left',
        })

        #===============220.001.004.005 ============#
        
        lines.append({
            'id': 'hierarchy_account17',
            'name' : '220.001.004.005 ' +_('VAT-SERV.TRANSP.CERT. D.E.P. GAS'), 
            'columns': [
                         self._format({'name': acc_amount_220_001_004_005},figure_type='float'),
                         {'name':''},
                        ],
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-left',
        })

        #===============220.001.004.006 ============#
        
        lines.append({
            'id': 'hierarchy_account18',
            'name' : '220.001.004.006 ' +_('VAT-SP HON. Cert. D.E.P. CONACYT'), 
            'columns': [
                         self._format({'name': acc_amount_220_001_004_006},figure_type='float'),
                         {'name':''},
                        ],
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-left',
        })

        #===============220.001.005.001 ============#
        acc_amount_220_001_005_001 = 0
        account_id = self.env['account.account'].search([('code', '=', '220.001.005.001')], limit=1)
        if account_id:            
            values= self.env['account.move.line'].search(domain+[('account_id', '=', account_id.id)])
            acc_amount_220_001_005_001 = sum(x.credit - x.debit for x in values)
            #acc_amount_220_001_005_001 = acc_amount_220_001_005_001/1000

        #===============220.001.005.002 ============#
        acc_amount_220_001_005_002 = 0
        account_id = self.env['account.account'].search([('code', '=', '220.001.005.002')], limit=1)
        if account_id:            
            values= self.env['account.move.line'].search(domain+[('account_id', '=', account_id.id)])
            acc_amount_220_001_005_002 = sum(x.credit - x.debit for x in values)
            #acc_amount_220_001_005_002 = acc_amount_220_001_005_002/1000

        ieps_pay_total = acc_amount_220_001_005_001 + acc_amount_220_001_005_002

        lines.append({
            'id': 'hierarchy_account1',
            'name' : _('IEPS Payable'), 
            'columns': [
                        {'name':''},
                         self._format({'name': ieps_pay_total},figure_type='float'),
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-center',
        })
        
        lines.append({
            'id': 'hierarchy_account19',
            'name' : '220.001.005.001 ' +_('IEPS PLAG. Cert. D.E.P. T-UNAM'), 
            'columns': [
                         self._format({'name': acc_amount_220_001_005_001},figure_type='float'),
                         {'name':''},
                        ],
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-left',
        })

        #===============220.001.005.002 ============#
        
        lines.append({
            'id': 'hierarchy_account20',
            'name' : '220.001.005.002 ' +_('IEPS ALIM. NO BASIC CERT DEP'), 
            'columns': [
                         self._format({'name': acc_amount_220_001_005_002},figure_type='float'),
                         {'name':''},
                        ],
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-left',
        })
        
        #===============220.001.006.001 ============#
        acc_amount_220_001_006_001 = 0
        account_id = self.env['account.account'].search([('code', '=', '220.001.006.001')], limit=1)
        if account_id:            
            values= self.env['account.move.line'].search(domain+[('account_id', '=', account_id.id)])
            acc_amount_220_001_006_001 = sum(x.credit - x.debit for x in values)
            #acc_amount_220_001_006_001 = acc_amount_220_001_006_001/1000

        #===============220.001.006.002 ============#
        acc_amount_220_001_006_002 = 0
        account_id = self.env['account.account'].search([('code', '=', '220.001.006.002')], limit=1)
        if account_id:            
            values= self.env['account.move.line'].search(domain+[('account_id', '=', account_id.id)])
            acc_amount_220_001_006_002 = sum(x.credit - x.debit for x in values)
            #acc_amount_220_001_006_002 = acc_amount_220_001_006_002/1000

        #===============220.001.006.003 ============#
        acc_amount_220_001_006_003 = 0
        account_id = self.env['account.account'].search([('code', '=', '220.001.006.003')], limit=1)
        if account_id:            
            values= self.env['account.move.line'].search(domain+[('account_id', '=', account_id.id)])
            acc_amount_220_001_006_003 = sum(x.credit - x.debit for x in values)
            #acc_amount_220_001_006_003 = acc_amount_220_001_006_003/1000

        #===============220.001.006.004 ============#
        acc_amount_220_001_006_004 = 0
        account_id = self.env['account.account'].search([('code', '=', '220.001.006.004')], limit=1)
        if account_id:            
            values= self.env['account.move.line'].search(domain+[('account_id', '=', account_id.id)])
            acc_amount_220_001_006_004 = sum(x.credit - x.debit for x in values)
            #acc_amount_220_001_006_004 = acc_amount_220_001_006_004/1000

        vat_pay_total = acc_amount_220_001_006_001 + acc_amount_220_001_006_002 + acc_amount_220_001_006_003 + acc_amount_220_001_006_004

        lines.append({
            'id': 'hierarchy_account1',
            'name' : _('VAT Payable'), 
            'columns': [
                        {'name':''},
                         self._format({'name': vat_pay_total},figure_type='float'),
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-center',
        })
        
        lines.append({
            'id': 'hierarchy_account21',
            'name' : '220.001.006.001 ' +_('TRANSFERRED VAT CFDI¦S'), 
            'columns': [
                         self._format({'name': acc_amount_220_001_006_001},figure_type='float'),
                         {'name':''},
                        ],
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-left',
        })

        #===============220.001.006.002 ============#
        
        lines.append({
            'id': 'hierarchy_account22',
            'name' : '220.001.006.002 ' +_('VAT TO PAY YOUR'), 
            'columns': [
                         self._format({'name': acc_amount_220_001_006_002},figure_type='float'),
                         {'name':''},
                        ],
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-left',
        })

        #===============220.001.006.003 ============#
        
        lines.append({
            'id': 'hierarchy_account23',
            'name' : '220.001.006.003 ' +_('VAT TO PAY GAS STATION'), 
            'columns': [
                         self._format({'name': acc_amount_220_001_006_003},figure_type='float'),
                         {'name':''},
                        ],
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-left',
        })

        #===============220.001.006.004 ============#
        
        lines.append({
            'id': 'hierarchy_account23',
            'name' : '220.001.006.004 ' +_('VAT Balance In Favor You'), 
            'columns': [
                         self._format({'name': acc_amount_220_001_006_004},figure_type='float'),
                         {'name':''},
                        ],
            'level': 3,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-left',
        })

        total = total_bal1 + acc_amount_220_001_001_002 + ret_total + acc_amount_220_001_003_001 + vat_total + ieps_pay_total + vat_pay_total

        lines.append({
            'id': 'total',
            'name' : _('Total Taxes To Pay'), 
            'columns': [
                        {'name':''},
                         self._format({'name': total},figure_type='float'),
                        ],
            'level': 1,
            'unfoldable': False,
            'unfolded': True,
            'class':'text-left',
        })
        return lines

    def _get_report_name(self):
        return _("Tax Report to Enter/Pay")

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
        # commit the writes in the `ir.attachment` table. It is done thanks to
        # a key in the context.
        minimal_layout = False
        if not config['test_enable']:
            self = self.with_context(commit_assetsbundle=True)

        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'report.url') or self.env['ir.config_parameter'].sudo().get_param('web.base.url')
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

        body = body.replace(b'<body class="o_account_reports_body_print">',
                            b'<body class="o_account_reports_body_print">' + body_html)
        if minimal_layout:
            header = ''
            footer = self.env['ir.actions.report'].render_template(
                "web.internal_layout", values=rcontext)
            spec_paperformat_args = {
                'data-report-margin-top': 10, 'data-report-header-spacing': 10}
            footer = self.env['ir.actions.report'].render_template(
                "web.minimal_layout", values=dict(rcontext, subst=True, body=footer))
        else:
            rcontext.update({
                'css': '',
                'o': self.env.user,
                'res_company': self.env.company,
            })
            header = self.env['ir.actions.report'].render_template(
                "jt_check_controls.external_layout_check_amounts", values=rcontext)
            # Ensure that headers and footer are correctly encoded
            header = header.decode('utf-8')
            spec_paperformat_args = {}
            # Default header and footer in case the user customized
            # web.external_layout and removed the header/footer
            headers = header.encode()
            footer = b''
            # parse header as new header contains header, body and footer
            try:
                root = lxml.html.fromstring(header)
                match_klass = "//div[contains(concat(' ', normalize-space(@class), ' '), ' {} ')]"

                for node in root.xpath(match_klass.format('header')):
                    headers = lxml.html.tostring(node)
                    headers = self.env['ir.actions.report'].render_template(
                        "web.minimal_layout", values=dict(rcontext, subst=True, body=headers))

                for node in root.xpath(match_klass.format('footer')):
                    footer = lxml.html.tostring(node)
                    footer = self.env['ir.actions.report'].render_template(
                        "web.minimal_layout", values=dict(rcontext, subst=True, body=footer))

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
        header_title = '''UNIVERSIDAD NACIONAL AUTÓNOMA DE MÉXICO\nDIRECCION GENERAL DE CONTROL PRESUPUESTAL
CONTADURIA-ACCOUNTING\nINFORME DE IMPUESTOS A ENTERAR / PAGAR DEL %s DE %s Y %s DE %s'''
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

    def get_pdf(self, options, minimal_layout=True,line_id=None):
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
        body_html = body_html.replace(b'<div class="o_account_reports_header">',b'<div>')
        #<div class="o_account_reports_header">
        body = body.replace(b'<body class="o_account_reports_body_print">', b'<body class="o_account_reports_body_print">' + body_html)
        if minimal_layout:
            header = ''
            footer = self.env['ir.actions.report'].render_template("web.internal_layout", values=rcontext)
            spec_paperformat_args = {'data-report-margin-top': 10, 'data-report-header-spacing': 20}
            footer = self.env['ir.actions.report'].render_template("web.minimal_layout", values=dict(rcontext, subst=True, body=footer))
        else:
            lines = self._get_lines(options, line_id=line_id)
            start = datetime.strptime(
            str(options['date'].get('date_from')), '%Y-%m-%d').date()
            end = datetime.strptime(str(options['date'].get('date_to'))
            , '%Y-%m-%d').date()

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
                    'start':start,
                    'end':end,
                    'header_date' : header_date,
                })
            header = self.env['ir.actions.report'].render_template("jt_tax_transaction.external_layout_tax_pay", values=rcontext)
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
            start = datetime.strptime(str(options['date'].get('date_from')), '%Y-%m-%d').date()
            end = datetime.strptime(str(options['date'].get('date_to')), '%Y-%m-%d').date()
            start_date = start.strftime('%B %d')
            s_year = start.strftime('%Y')
            end_date = end.strftime('%B %d')
            e_year = end.strftime('%Y')
            start_month_name = start.strftime("%B")
            end_month_name = end.strftime("%B")
            
            if self.env.user.lang == 'es_MX':
                start_month_name = self.get_month_name(start.month)
                end_month_name = self.get_month_name(end.month)

            header_date = str(start.day).zfill(2) + " " + start_month_name+" DE "+str(start.year)
            header_date += " AL "+str(end.day).zfill(2) + " " + end_month_name +" DE "+str(end.year)


            sheet.merge_range(y_offset, col, 6, col, '', super_col_style)
            if self.env.user and self.env.user.company_id and self.env.user.company_id.header_logo:
                filename = 'logo.png'
                image_data = io.BytesIO(base64.standard_b64decode(
                    self.env.user.company_id.header_logo))
                sheet.insert_image(0, 0, filename, {
                                   'image_data': image_data, 'x_offset': 8, 'y_offset': 3, 'x_scale': 0.6, 'y_scale': 0.6})

            col += 1
            header_title = '''UNIVERSIDAD NACIONAL AUTÓNOMA DE MÉXICO\nDIRECCION GENERAL DE CONTROL PRESUPUESTAL
CONTADURÍA GENERAL\nREPORTE DE IMPUESTOS A ENTERAR/PAGAR DEL  %s
''' % (header_date)
            sheet.merge_range(y_offset, col, 5, col + 6,
                              header_title, super_col_style)
            y_offset += 6
            col = 1
            currect_time_msg = "Fecha de impresión: "
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
        # report = {'name': self._get_report_name(),
        #         'summary': report_manager.summary,
        #         'company_name': self.env.company.name,}
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

