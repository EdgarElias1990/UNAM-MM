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

from lxml import etree
from lxml.objectify import fromstring

from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval
from odoo.tools.xml_utils import _check_with_xsd


from odoo import models, api, _, fields, tools
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.misc import formatLang
from odoo.tools.misc import xlsxwriter
import io
import base64
from odoo.tools import config, date_utils, get_lang
import lxml.html

class AccountGeneralLedgerReport(models.AbstractModel):
    _inherit = "account.general.ledger"

    @api.model
    def _get_options_domain(self, options):
        # OVERRIDE
        domain = super(AccountGeneralLedgerReport, self)._get_options_domain(options)
#         if self.env.context and self.env.context.get('model','')=='jt_account_module_design.general.ledger.inherit':
#             #print ("===",options['date'])
#             new_domain = []
#             start = False
#             end = False
#             #if options.get('date',False) and options.get('date',{}).get('mode','')=='range':
#             if options.get('date',False) and options['date'].get('date_from',False):
#                     start = datetime.strptime(str(options['date'].get('date_from')), '%Y-%m-%d').date()
#             if options.get('date',False) and options['date'].get('date_to',False):
#                     end = datetime.strptime(options['date'].get('date_to'), '%Y-%m-%d').date()
#              
#             for d in domain:
#                 if d[0] == 'date':
#                     if start:
#                         new_domain.append(('date','>=',start))
#                         start = False
#                     elif end:
#                         new_domain.append(('date','<=',end))
#                     else:
#                           new_domain.append(d)
#                 else:
#                     new_domain.append(d)
            #domain = new_domain
        is_add_fiter = False
        is_add_dep_fiter = False
        dep_domain = []
        if options.get('selected_dependency',False) and len(options['selected_dependency']) > 0:
            dep_domain.append(('move_id.dependancy_id.dependency', 'in', options['selected_dependency']))
            is_add_dep_fiter = True
        if options.get('selected_sub_dependency',False) and len(options['selected_sub_dependency']) > 0:
            dep_domain.append(('move_id.sub_dependancy_id.sub_dependency', 'in', options['selected_sub_dependency']))
            is_add_dep_fiter = True

        move_line_ids = self.env['account.move.line']
        move_lines_dep_account_ids = self.env['account.account']
        if is_add_dep_fiter:
            move_lines_ids = self.env['account.move.line'].search(dep_domain)
            domain += [('move_id','in',move_lines_ids.mapped('move_id').ids)]
        return domain
    
class StatusProgramReport(models.AbstractModel):

    _name = "jt_account_module_design.general.ledger.inherit"
    _inherit = "account.report"
    _description = "Trial Balance"

    filter_program_code_section = True
    filter_date = {'mode': 'range', 'filter': 'this_month'}
    filter_comparison = {'date_from': '', 'date_to': '', 'filter': 'no_comparison', 'number_period': 1}
    filter_all_entries = False
    filter_journals = True
    #filter_analytic = True
    filter_unfold_all = False
    filter_cash_basis = None
    filter_hierarchy = False
    MAX_LINES = None
    
    
#     def _get_reports_buttons(self):
#         return [
#             {'name': _('Print Preview'), 'sequence': 1,
#              'action': 'print_pdf', 'file_export_type': _('PDF')},
#             {'name': _('Export (XLSX)'), 'sequence': 2,
#              'action': 'print_xlsx', 'file_export_type': _('XLSX')},
#         ]

#     @api.model
#     def _get_templates(self):
#         templates = super(StatusProgramReport, self)._get_templates()
#         templates['line_template'] = 'account_reports.line_template_general_ledger_report'
#         return templates
# 
# 
#     @api.model
#     def _get_columns_name(self, options):
#         return [
#             {'name': ''},
#             {'name': _('Date'), 'class': 'date'},
#             {'name': _('Communication')},
#             {'name': _('Partner')},
#             {'name': _('Currency'), 'class': 'number'},
#             {'name': _('Debit'), 'class': 'number'},
#             {'name': _('Credit'), 'class': 'number'},
#             {'name': _('Balance'), 'class': 'number'}
#         ]



    def open_general_ledger(self, options, params=None):
        if not params:
            params = {}
        ctx = self.env.context.copy()
        ctx.pop('id', '')
        action = self.env.ref('jt_account_module_design.action_general_accounting').read()[0]
        options['unfolded_lines'] = ['account_%s' % (params.get('id', ''),)]
        options['unfold_all'] = False
        ctx.update({'model': 'jt_account_module_design.account_coa.inherit'})
        action.update({'options': options, 'context': ctx, 'ignore_session': 'read'})
        return action
    
    @api.model
    def _init_filter_program_code_section(self, options, previous_options=None):
        options['is_code_sections'] = True
        options['code_sections'] = previous_options and previous_options.get(
            'code_sections') or []
        program_fields_ids = [int(acc) for acc in options['code_sections']]
        program_fields_ids = self.env['report.program.fields']
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


    def _get_templates(self):
        """Get this template for better fit of columns"""
        templates = super(StatusProgramReport, self)._get_templates()
        templates['main_table_header_template'] = 'l10n_mx_reports.template_coa_table_header'
        return templates


#     @api.model
#     def _get_templates(self):
#         templates = super(StatusProgramReport, self)._get_templates()
#         templates['main_table_header_template'] = 'account_reports.template_coa_table_header'
#         return templates

    def _get_columns_name(self, options):
        """Get more specific columns to use in SAT report"""
        columns = [{'name': ''}, {'name': _('Initial Balance'), 'class': 'number'}]
        if options.get('comparison') and options['comparison'].get('periods'):
            for period in options['comparison']['periods']:
                columns += [
                    {'name': _('Debit'), 'class': 'number'},
                    {'name': _('Credit'), 'class': 'number'},
                    ]
        return columns + [
            {'name': _('Debit'), 'class': 'number'},
            {'name': _('Credit'), 'class': 'number'},
            {'name': _('Total'), 'class': 'number'},
        ]

    def _post_process(self, grouped_accounts, initial_balances, options, comparison_table):
        afrl_obj = self.env['account.financial.html.report.line']
        lines = []
        n_cols = len(comparison_table) * 2 + 2
        total = [0.0] * n_cols
        afr_lines = afrl_obj.search([
            ('parent_id', '=', False),
            ('code', 'ilike', 'MX_COA_%')], order='code')
        for line in afr_lines:
            childs = self._get_lines_second_level(
                line.children_ids, grouped_accounts, initial_balances, options, comparison_table)
            if not childs:
                continue
            cols = ['']
            if not options.get('coa_only'):
                cols = cols * n_cols
                child_cols = [c['columns'] for c in childs if c.get('level') == 2]
                total_line = []
                for col in range(n_cols):
                    total_line += [sum(a[col] for a in child_cols)]
                    total[col] += total_line[col]
                for child in childs:
                    child['columns'] = [{'name': self.format_value(v)} for v in child['columns']]
            lines.append({
                'id': 'hierarchy_' + line.code,
                'name': line.name,
                'columns': [{'name': v} for v in cols],
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
            })
            lines.extend(childs)
            if not options.get('coa_only'):
                lines.append({
                    'id': 'total_%s' % line.code,
                    'name': _('Total %s') % line.name[2:],
                    'level': 0,
                    'class': 'hierarchy_total',
                    'columns': [{'name': self.format_value(v)} for v in total_line],
                })
        if not options.get('coa_only'):
            lines.append({
                'id': 'hierarchy_total',
                'name': _('Total'),
                'level': 0,
                'class': 'hierarchy_total',
                'columns': [{'name': self.format_value(v)} for v in total],
            })
        
        return lines

    @api.model
    def _get_lines_second_level(self, lines_child, grouped_accounts,
                                initial_balances, options, comparison_table):
        """Return list of tags found in the second level"""
        lines = []
        sorted_childs = sorted(lines_child, key=lambda a: a.name)
        for child in sorted_childs:
            account_lines = self._get_lines_third_level(
                child, grouped_accounts, initial_balances, options,
                comparison_table)
            if not account_lines:
                continue
            cols = [{'name': ''}]
            if not options.get('coa_only'):
                n_cols = len(comparison_table) * 2 + 2
                child_cols = [c['columns'] for c in account_lines if c.get('level') == 3]
                cols = []
                for col in range(n_cols):
                    cols += [sum(a[col] for a in child_cols)]
            lines.append({
                'id': 'level_one_%s' % child.id,
                'name': child.name,
                'columns': cols,
                'level': 2,
                'class': 'hierarchy_total' if not options.get('coa_only') else '',
                'unfoldable': True,
                'unfolded': True,
            })
            lines.extend(account_lines)
        return lines


    @api.model
    def _get_lines_third_level(self, line, grouped_accounts, initial_balances,
                               options, comparison_table):
        """Return list of accounts found in the third level"""
        lines = []
        company_id = self.env.context.get('company_id') or self.env.company
        domain = safe_eval(line.domain or '[]')
        domain += [
            ('deprecated', '=', False),
            ('company_id', '=',company_id.id),
        ]
        basis_account_ids = self.env['account.tax'].search_read(
            [('cash_basis_base_account_id', '!=', False)], ['cash_basis_base_account_id'])
        basis_account_ids = [account['cash_basis_base_account_id'][0] for account in basis_account_ids]
        domain.append((('id', 'not in', basis_account_ids)))
        account_ids = self.env['account.account'].search(domain, order='code')
        tags = account_ids.mapped('tag_ids').filtered(
            lambda r: r.color == 4).sorted(key=lambda a: a.name)
        for tag in tags:
            accounts = account_ids.search([
                ('tag_ids', 'in', [tag.id]),
                ('id', 'in', account_ids.ids),
            ])
            name = tag.name
            name = name[:63] + "..." if len(name) > 65 else name
            cols = [{'name': ''}]
            childs = self._get_lines_fourth_level(accounts, grouped_accounts, initial_balances, options, comparison_table)
            if not childs:
                continue
            if not options.get('coa_only'):
                n_cols = len(comparison_table) * 2 + 2
                child_cols = [c['columns'] for c in childs]
                cols = []
                for col in range(n_cols):
                    cols += [sum(a[col] for a in child_cols)]
            lines.append({
                'id': 'level_two_%s' % tag.id,
                'parent_id': 'level_one_%s' % line.id,
                'name': name,
                'columns': cols,
                'level': 3,
                'unfoldable': True,
                'unfolded': True,
                'tag_id': tag.id,
            })
            lines.extend(childs)
        return lines

    def _get_lines_fourth_level(self, accounts, grouped_accounts, initial_balances, options, comparison_table):
        lines = []
        company_id = self.env.context.get('company_id') or self.env.company
        is_zero = company_id.currency_id.is_zero
        for account in accounts:
            # skip accounts with all periods = 0 (debit and credit) and no initial balance
            if not options.get('coa_only'):
                non_zero = False
                for period in range(len(comparison_table)):
                    if account in grouped_accounts and (
                        not is_zero(initial_balances.get(account, 0)) or
                        not is_zero(grouped_accounts[account][period]['debit']) or
                        not is_zero(grouped_accounts[account][period]['credit'])
                    ):
                        non_zero = True
                        break
                if not non_zero:
                    continue
            name = account.code + " " + account.name
            name = name[:63] + "..." if len(name) > 65 else name
            tag = account.tag_ids.filtered(lambda r: r.color == 4)
            if len(tag) > 1:
                raise UserError(_(
                    'The account %s is incorrectly configured. Only one tag is allowed.'
                ) % account.name)
            nature = dict(tag.fields_get()['nature']['selection']).get(tag.nature, '')
            cols = [{'name': nature}]
            if not options.get('coa_only'):
                cols = self._get_cols(initial_balances, account, comparison_table, grouped_accounts)
            lines.append({
                'id': account.id,
                'parent_id': 'level_two_%s' % tag.id,
                'name': name,
                'level': 4,
                'columns': cols,
                'caret_options': 'account.account',
            })
        return lines

    def _get_cols(self, initial_balances, account, comparison_table, grouped_accounts):
        cols = [initial_balances.get(account, 0.0)]
        total_periods = 0
        for period in range(len(comparison_table)):
            amount = grouped_accounts[account][period]['balance']
            total_periods += amount
            cols += [grouped_accounts[account][period]['debit'],
                        grouped_accounts[account][period]['credit']]
        cols += [initial_balances.get(account, 0.0) + total_periods]
        return cols

    def _l10n_mx_edi_add_digital_stamp(self, path_xslt, cfdi):
        """Add digital stamp certificate attributes in XML report"""
        company_id = self.env.company
        certificate_ids = company_id.l10n_mx_edi_certificate_ids
        certificate_id = certificate_ids.sudo().get_valid_certificate()
        if not certificate_id:
            return cfdi
        tree = fromstring(cfdi)
        xslt_root = etree.parse(tools.file_open(path_xslt))
        cadena = str(etree.XSLT(xslt_root)(tree))
        sello = certificate_id.sudo().get_encrypted_cadena(cadena)
        tree.attrib['Sello'] = sello
        tree.attrib['noCertificado'] = certificate_id.serial_number
        tree.attrib['Certificado'] = certificate_id.sudo().get_data()[0]
        return etree.tostring(tree, pretty_print=True,
                              xml_declaration=True, encoding='UTF-8')

    def get_bce_dict(self, options):
        company = self.env.company
        xml_data = self._get_lines(options)
        accounts = []
        account_lines = [l for l in xml_data
                         if l.get('level') in [2, 3] and l.get('show', True)]
        for line in account_lines:
            cols = line.get('columns', [])
            initial, debit, credit, end = (
                cols[0].get('name', 0.0),
                cols[-3].get('name', 0.0),
                cols[-2].get('name', 0.0),
                cols[-1].get('name', 0.0))
            accounts.append({
                'number': line.get('name').split(' ', 1)[0],
                'initial': "%.2f" % (initial),
                'debit': "%.2f" % (debit),
                'credit': "%.2f" % (credit),
                'end': "%.2f" % (end),
            })
        date = fields.Date.from_string(self.env.context['date_from'])
        chart = {
            'vat': company.vat or '',
            'month': str(date.month).zfill(2),
            'year': date.year,
            'accounts': accounts,
            'type': 'N',
        }
        return chart

    @api.model
    def _get_lines(self, options, line_id=None):
        # Create new options with 'unfold_all' to compute the initial balances.
        # Then, the '_do_query' will compute all sums/unaffected earnings/initial balances for all comparisons.

        domain = []
        dep_domain = []
        is_add_fiter = False
        is_add_dep_fiter = False
        if len(options['selected_programs']) > 0:
            domain.append(('program_id.key_unam', 'in', options['selected_programs']))
            is_add_fiter = True
        if len(options['selected_sub_programs']) > 0:
            domain.append(('sub_program_id.sub_program', 'in', options['selected_sub_programs']))
            is_add_fiter = True
        if len(options['selected_dependency']) > 0:
            dep_domain.append(('move_id.dependancy_id.dependency', 'in', options['selected_dependency']))
            is_add_dep_fiter = True
        if len(options['selected_sub_dependency']) > 0:
            dep_domain.append(('move_id.sub_dependancy_id.sub_dependency', 'in', options['selected_sub_dependency']))
            is_add_dep_fiter = True
        if len(options['selected_items']) > 0:
            domain.append(('item_id.item', 'in', options['selected_items']))
            is_add_fiter = True
        if len(options['selected_or']) > 0:
            domain.append(('resource_origin_id.key_origin', 'in', options['selected_or']))
            is_add_fiter = True
            
        program_code_obj = self.env['program.code']
        program_codes = program_code_obj.search(domain)
        
        program_codes_account_ids = program_codes.mapped('item_id.unam_account_id')
        program_codes_account_ids = program_codes_account_ids.ids
        
        new_options = options.copy()
        new_options['unfold_all'] = True
        options_list = self._get_options_periods_list(new_options)
        accounts_results, taxes_results = self.env['account.general.ledger']._do_query(options_list, fetch_lines=False)

        move_lines_dep_account_ids = self.env['account.account']
        
        if is_add_dep_fiter:
            move_lines_ids = self.env['account.move.line'].search(dep_domain)
            move_lines_dep_account_ids = move_lines_ids.mapped('account_id')

        grouped_accounts = {}
        initial_balances = {}
        comparison_table = [options.get('date')]
        comparison_table += options.get('comparison') and options['comparison'].get('periods') or []
        for account, periods_results in accounts_results:
            if is_add_fiter and not account.id in program_codes_account_ids:
                continue

            if is_add_dep_fiter  and not account.id in move_lines_dep_account_ids.ids:
                continue
            
            grouped_accounts.setdefault(account, [])
            for i, res in enumerate(periods_results):
                
                if i == 0:
                    initial_balances[account] = res.get('initial_balance', {}).get('balance', 0.0)
#                 grouped_accounts[account].append({
#                     'balance': res.get('sum', {}).get('balance', 0.0),
#                     'debit': res.get('sum', {}).get('debit', 0.0),
#                     'credit': res.get('sum', {}).get('credit', 0.0),
#                 })

                grouped_accounts[account].append({
                    'balance': res.get('sum', {}).get('balance', 0.0) - res.get('initial_balance', {}).get('balance', 0.0),
                    'debit': res.get('sum', {}).get('debit', 0.0) - res.get('initial_balance', {}).get('debit', 0.0),
                    'credit': res.get('sum', {}).get('credit', 0.0) - res.get('initial_balance', {}).get('credit', 0.0),
                })
        
        return self._post_process(grouped_accounts, initial_balances, options, comparison_table)

    @api.model
    def get_xml(self, options):
        qweb = self.env['ir.qweb']
        version = '1.3'
        ctx = self._set_context(options)
        if not ctx.get('date_to'):
            return False
        ctx['no_format'] = True
        values = self.with_context(ctx).get_bce_dict(options)
        cfdicoa = qweb.render(CFDIBCE_TEMPLATE, values=values)
        for key, value in MX_NS_REFACTORING.items():
            cfdicoa = cfdicoa.replace(key.encode('UTF-8'),
                                      value.encode('UTF-8') + b':')
        cfdicoa = self._l10n_mx_edi_add_digital_stamp(
            CFDIBCE_XSLT_CADENA % version, cfdicoa)

        with tools.file_open(CFDIBCE_XSD % version, "rb") as xsd:
            _check_with_xsd(cfdicoa, xsd)
        return cfdicoa

    def _get_report_name(self):
        return ("Trial Balance")

#     def get_report_filename(self, options):
#         return super(StatusProgramReport, self.with_context(
#             self._set_context(options))).get_report_filename(options).upper()

#     def _get_report_name(self):
#         """The structure to name the Trial Balance reports is:
#         VAT + YEAR + MONTH + ReportCode
#         ReportCode:
#         BN - Trial balance with normal information
#         BC - Trial balance with with complementary information. (Now is
#         not suportes)"""
#         context = self.env.context
#         date_report = fields.Date.from_string(context['date_from']) if context.get(
#                 'date_from') else fields.Date.today()
#         # return ['%s%s%sBN' % (
#         #             self.env.company.vat or '',
#         #             date_report.year,
#         #             str(date_report.month).zfill(2))]
#         res = ''
#         return res

    def open_journal_items(self, options, params):
        new_params = params.copy()
        new_params.pop('financial_group_line_id', False)
        result= super(StatusProgramReport, self).open_journal_items(
            options, new_params)
        if result.get('domain'):
            domain = result.get('domain',[])
        else:
            domain = result.get('domain',[])

        if len(options['selected_dependency']) > 0:
            domain.append(('move_id.dependancy_id.dependency', 'in', options['selected_dependency']))
        if len(options['selected_sub_dependency']) > 0:
            domain.append(('move_id.sub_dependancy_id.sub_dependency', 'in', options['selected_sub_dependency']))
        result['domain'] = domain
        return result
        

    def view_all_journal_items(self, options, params):
        if not params.get('id') or 'hierarchy' in params.get('id'):
            return super(StatusProgramReport, self).view_all_journal_items(
                options, params)
        ctx = self._set_context(options)
        lines = self.with_context(**ctx)._get_lines(options)
        new_params = params.copy()
        new_params.pop('id', False)
        accounts = self._get_accounts_journal_items([params.get('id')], lines)
        ctx = {'search_default_account': 1}
        res = super(StatusProgramReport, self.with_context(
            **ctx)).view_all_journal_items(options, new_params)
        res.get('domain', []).append(('account_id', 'in', accounts))
        return res

    def _get_accounts_journal_items(self, params, lines):
        levels = [
            l.get('level') for l in lines if l.get('parent_id') in params]
        if levels and levels[0] == 4:
            return [
                l.get('id') for l in lines if l.get('parent_id') in params]
        params = [
            l.get('id') for l in lines if l.get('parent_id') in params]
        return self._get_accounts_journal_items(params, lines)

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
        

        rcontext_test = {
                'mode': 'print',
                'base_url': base_url,
                'company': self.env.company,
            } 
        rcontext_test.update({
                'css': '',
                'o': self.env.user,
                'res_company': self.env.company,
                'start' : start,
                'end' : end,
                'header_date' : header_date,
        })
        
        body_html = self.with_context(print_mode=True).get_html(options)

        body_header =  self.env['ir.actions.report'].render_template("jt_account_module_design.external_layout_trial_balance", values=rcontext_test)
        body_html = body_header+body_html
        
        body_html = body_html.replace(b'<div class="o_account_reports_header">',b'<div style="font-size:1px;text-align:center;">')
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
            end = datetime.strptime(
            options['date'].get('date_to'), '%Y-%m-%d').date()

            start_month_name = start.strftime("%B")
            end_month_name = end.strftime("%B")
            
            if self.env.user.lang == 'es_MX':
                start_month_name = self.get_month_name(start.month)
                end_month_name = self.get_month_name(end.month)

            header_date = str(start.day).zfill(2) + " " + start_month_name+" OF "+str(start.year)
            header_date += " AND "+str(end.day).zfill(2) + " " + end_month_name +" OF "+str(end.year)
            
            rcontext.update({
                    'css': '',
                    'o': self.env.user,
                    'res_company': self.env.company,
                    'start' : start,
                    'end' : end,
                    'header_date' : header_date,
            })
            header = b'<p></p>'
            # header = self.env['ir.actions.report'].render_template("jt_account_module_design.external_layout_trial_balance", values=rcontext)
            header = header.decode('utf-8') # Ensure that headers and footer are correctly encoded
            spec_paperformat_args = {'data-report-margin-top': 4, 'data-report-header-spacing': 4}
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
        

        sheet.merge_range(y_offset, col, 6, col, '', super_col_style)
        if self.env.user and self.env.user.company_id and self.env.user.company_id.header_logo:
            filename = 'logo.png'
            image_data = io.BytesIO(base64.standard_b64decode(
                self.env.user.company_id.header_logo))
            sheet.insert_image(0, 0, filename, {
                               'image_data': image_data, 'x_offset': 8, 'y_offset': 3, 'x_scale': 0.6, 'y_scale': 0.6})
        col += 1
        header_title = '''UNIVERSIDAD NACIONAL AUTÓNOMA DE MÉXICO\nDIRECCIÓN GENERAL DE CONTROL PRESUPUESTAL-CONTADURÍA GENERAL
        \nBALANZA DE COMPROBACIÓN DEL %s \nCifras en Pesos''' % (header_date)

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
        start = datetime.strptime(str(options['date'].get('date_from')), '%Y-%m-%d').date()
        end = datetime.strptime(str(options['date'].get('date_to')), '%Y-%m-%d').date()
        start_date = start.strftime('%B %d')
        s_year = start.strftime('%Y')
        end_date = end.strftime('%B %d')
        e_year = end.strftime('%Y')


        # Prevent inconsistency between options and context.
        self = self.with_context(self._set_context(options))

        templates = self._get_templates()
        report_manager = self._get_report_manager(options)
        # report = {'name': self._get_report_name(),
        #         'summary': report_manager.summary,
        #         'company_name': self.env.company.name,}
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
