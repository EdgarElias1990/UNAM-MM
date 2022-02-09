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
from odoo import models, fields,api,_
from odoo.exceptions import ValidationError
from datetime import datetime
import base64
import io
import pytz

class ControlAmountsReceived(models.Model):

    _name = 'control.amounts.received'
    _description = 'Control of amounts received'
    _rec_name = 'folio'

    def _get_amount(self):
        for record in self:
            record.amount_to_receive = sum(
                record.line_ids.mapped('amount_assigned'))
            record.amount_received = sum(
                record.line_ids.mapped('amount_deposited'))
            record.amount_pending = record.amount_to_receive - record.amount_received

    date = fields.Date(string='Deposit date')
    folio = fields.Integer(string='Folio')
    budget_id = fields.Many2one('expenditure.budget', string='Budget')
    journal_id = fields.Many2one("account.journal", string="Journal")
    file = fields.Binary(string='Seasonal file')
    made_by_id = fields.Many2one('res.users', string='Made by')
    observations = fields.Text(string='Observations')
    line_ids = fields.One2many('control.amounts.received.line',
                               'control_id', string='Control of amounts received lines',domain=[('state', 'in', ('success','manual'))])

    import_line_ids = fields.One2many('control.amounts.received.line',
                               'control_id', string='Imported Lines',domain=[('state', 'in', ('draft','fail'))])
    
    calendar_assigned_amount_id = fields.Many2one(
        'calendar.assigned.amounts', string='Calendar of assigned amount')
    state = fields.Selection([('draft', 'Draft'), ('validate', 'Validated')], default='draft',string='Status')

    file = fields.Binary(string='Seasonal File', copy=False)
    filename = fields.Char(string="File Name", copy=False)
    import_date = fields.Date(string='Import Date', copy=False,default=fields.Date.context_today)
    user_id = fields.Many2one('res.users', string='Responsible',
                              default=lambda self: self.env.user, tracking=True, copy=False)
    obs_calender_amount = fields.Text(string='Observations')
    obs_cont_amount = fields.Text(string='Observations')
    amount_to_receive = fields.Float(
        string='Amount to receive', compute='_get_amount')
    amount_received = fields.Float(
        string='Amount received', compute='_get_amount')
    amount_pending = fields.Float(
        string='Amount pending', compute='_get_amount')

    move_line_ids = fields.One2many('account.move.line', 'control_id', string="Journal Items")
    import_status = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Completed')], default='draft', copy=False)

    def _compute_total_rows(self):
        for budget in self:
            budget.failed_rows = self.env['control.amounts.received.line'].search_count(
                [('control_id', '=', budget.id), ('state', '=', 'fail')])
            budget.success_rows = self.env['control.amounts.received.line'].search_count(
                [('control_id', '=', budget.id), ('state', '=', 'success')])
            budget.total_rows = self.env['control.amounts.received.line'].search_count(
                [('control_id', '=', budget.id),('state', '!=', 'manual')])

    failed_rows = fields.Integer(
        string='Failed Rows', compute="_compute_total_rows")
    success_rows = fields.Integer(
        string='Success Rows', compute="_compute_total_rows")
    total_rows = fields.Integer(
        string="Total Rows", compute="_compute_total_rows")

    failed_row_file = fields.Binary(string='Failed Rows File')
    fialed_row_filename = fields.Char(
        string='File name', default=lambda self: _("Failed_Rows.txt"))
        
    @api.depends('date')
    def _compute_month_int(self):
        for record in self:
            record.month_int = 0
            if record.date:
                record.month_int = record.date.month

    month_int = fields.Integer(string='Month Integer', store=True, compute='_compute_month_int')

    def unlink(self):
        for control in self:
            if control.state in ('validate'):
                if self.env.user.lang == 'es_MX':
                    raise ValidationError(_("No puedes eliminar un Registro del Subsidio Federal en estatus Validado."))
                else:
                    raise ValidationError('You cannot delete a Registration of Federal Subsidy in Validated status!')
            
        return super(ControlAmountsReceived, self).unlink()

    @api.model
    def default_get(self, fields):
        res = super(ControlAmountsReceived, self).default_get(fields)
        daily_income_jour = self.env.ref('jt_conac.daily_income_jour')
        if daily_income_jour:
            res.update({'journal_id': daily_income_jour.id})
        return res

    @api.model
    def create(self, vals):
        vals['folio'] = self.env['ir.sequence'].next_by_code(
            'control.amount.received') or _('New')
        res = super(ControlAmountsReceived, self).create(vals)
        return res

    def validate_import_line(self):
        if len(self.import_line_ids.ids) > 0:

            counter = 0
            failed_row = ""
            failed_line_ids = []
            success_line_ids = []
            # object
            bank_account_obj = self.env['res.partner.bank'].search_read([], fields=['id', 'acc_number'])
            shcp_code_obj = self.env['shcp.code'].search_read([], fields=['id', 'name'])
            departure_conversion_obj = self.env['departure.conversion'].search_read([], fields=['id', 'federal_part'])
            
            
            for line in self.import_line_ids:
                counter += 1
                line_vals = [line.branch_cr, line.unit_cr, line.folio_clc, line.clc_status, line.deposit_date, line.application_date,
                             line.currency_name, line.bank_account, line.year, line.branch,
                             line.unit, line.month_no, line.line_f, line.sfa,
                             line.sfe , line.prg, line.ai, line.ip,line.line_p, line.tg,line.ff,line.ef,line.amount_deposited,line.proposed_date]

                # Validation Authorized Amount
                amount_deposited = 0
                try:
                    amount_deposited = float(line.amount_deposited)
                    if amount_deposited <= 0:
                        failed_row += str(line_vals) + \
                                      "------>> Deposited Amount should be greater than 0!"
                        failed_line_ids.append(line.id)
                        continue
                except:
                    failed_row += str(line_vals) + \
                                  "------>> Invalid Deposited Amount Format"
                    failed_line_ids.append(line.id)
                    continue
                
                # Validate Bank Account
                bank_account_no = False
                if line.bank_account:
                    bank_account_no = list(filter(lambda prog: prog['acc_number'] == line.bank_account, bank_account_obj))
                    bank_account_no = bank_account_no[0]['id'] if bank_account_no else False
                if not bank_account_no:
                    failed_row += str(line_vals) + \
                                  "------>> Bank Account not exist\n"
                    failed_line_ids.append(line.id)
                    continue

                # Validate SHCP Code
                shcp_id = False
                if line.ip and line.line_p:
                    shcp_code = line.ip + line.line_p
                    shcp_id = list(filter(lambda prog: prog['name'] == shcp_code, shcp_code_obj))
                    shcp_id = shcp_id[0]['id'] if shcp_id else False
                if not shcp_id:
                    failed_row += str(line_vals) + \
                                  "------>> Invalid SHCP Program Code Format\n"
                    failed_line_ids.append(line.id)
                    continue

                # Validate Federal Item
#                 federal_item = False
#                 if line.ogto:
#                     federal_item = list(filter(lambda prog: prog['federal_part'] == line.ogto, departure_conversion_obj))
#                     federal_item = federal_item[0]['id'] if federal_item else False
#                 if not federal_item:
#                     failed_row += str(line_vals) + \
#                                   "------>> Invalid SHCP Games(CONPA) Format\n"
#                     failed_line_ids.append(line.id)
#                     continue

                # Validate Month
                if line.month_no and line.month_no < 1 and line.month_no > 12:
                    failed_row += str(line_vals) + \
                                  "------>> Invalid Month No. Format \n"
                    failed_line_ids.append(line.id)
                    continue
                
                if bank_account_no:
                    line.bank_account_id = bank_account_no
                    bank_account_rec = self.env['res.partner.bank'].browse(bank_account_no)
                    line.bank_id = bank_account_rec and bank_account_rec.bank_id and bank_account_rec.bank_id.id or False
                line.shcp_id = shcp_id
                #line.conpa_id = federal_item
                success_line_ids.append(line.id)
                
            failed_lines = self.env['control.amounts.received.line'].search(
                [('control_id', '=', self.id), ('id', 'in', failed_line_ids)])
            success_lines = self.env['control.amounts.received.line'].search(
                [('control_id', '=', self.id), ('id', 'in', success_line_ids)])
            success_lines.write({'state': 'success'})
            for l in failed_lines:
                if l.state == 'draft':
                    l.state = 'fail'

            failed_data = False
            vals = {}
            if failed_row != "":
                content = ""
                if self.failed_row_file:
                    file_data = base64.b64decode(self.failed_row_file)
                    content += io.StringIO(file_data.decode("utf-8")).read()
                content += "\n"
                content += "...................Failed Rows " + \
                           str(datetime.today()) + "...............\n"
                content += str(failed_row)
                failed_data = base64.b64encode(content.encode('utf-8'))
                vals['failed_row_file'] = failed_data
                
            if vals.get('failed_row_file'):
                self.write(vals)
            if self.failed_rows == 0:
                self.import_status = 'done'

    def update_calendar_deposite_amount(self):
        for line in self.line_ids:
            same_folio_line = self.env['control.amounts.received.line'].search_count(
                [('control_id', '!=',False),('control_id', '!=', self.id), ('folio_clc', '=', line.folio_clc)])
            if same_folio_line:
                if self.env.user.lang == 'es_MX':
                    raise ValidationError(_("Actualmente, el Folio  %s ya está registrado!")%(line.folio_clc))
                else:
                    raise ValidationError(_("Currently Folio %s is already registered!")%(line.folio_clc))
            calendar_line = self.env['calendar.assigned.amounts.lines'].search([('budgetary_program','=',line.shcp_id.name),('item_id','=',line.conpa_id.id),('calendar_assigned_amount_id.state','=','validate')],limit=1)
            
            if not calendar_line:
                budgetary_program_name =  line.shcp_id and line.shcp_id.name or ''
                item_name = line.conpa_id and line.conpa_id.federal_part or ''
                if self.env.user.lang == 'es_MX':
                    raise ValidationError(_("No se encuentra el calendario de la cantidad asignada para el programa presupuestario %s y la partida de gastos %s")%(budgetary_program_name,item_name))
                else:
                    raise ValidationError(_("Calendar of Assigned Amount not found for Budgetary Program %s and Item of Expenditure %s")%(budgetary_program_name,item_name))
            
            if calendar_line:
                if line.month_no==1:
                    calendar_line.amount_deposite_january += line.amount_deposited
                elif line.month_no==2:
                    calendar_line.amount_deposite_february += line.amount_deposited
                elif line.month_no==3:
                    calendar_line.amount_deposite_march += line.amount_deposited
                elif line.month_no==4:
                    calendar_line.amount_deposite_april += line.amount_deposited
                elif line.month_no==5:
                    calendar_line.amount_deposite_may += line.amount_deposited
                elif line.month_no==6:
                    calendar_line.amount_deposite_june += line.amount_deposited
                elif line.month_no==7:
                    calendar_line.amount_deposite_july += line.amount_deposited
                elif line.month_no==8:
                    calendar_line.amount_deposite_august += line.amount_deposited
                elif line.month_no==9:
                    calendar_line.amount_deposite_september += line.amount_deposited
                elif line.month_no==10:
                    calendar_line.amount_deposite_october += line.amount_deposited
                elif line.month_no==11:
                    calendar_line.amount_deposite_november += line.amount_deposited
                elif line.month_no==12:
                    calendar_line.amount_deposite_december += line.amount_deposited
                
                if line.bank_id:
                    calendar_line.bank_id = line.bank_id.id
                if line.bank_account_id:
                    calendar_line.bank_account_id = line.bank_account_id.id
                line.calendar_assigned_amount_line_id = calendar_line.id
                line.calendar_assigned_amount_id = calendar_line.calendar_assigned_amount_id and calendar_line.calendar_assigned_amount_id.id or False

#     def create_accured_journal_entry(self,partner_id,amount,journal,today,control_amount,company_id):
#         move_obj = self.env['account.move']
#         if not journal.accured_credit_account_id or not journal.conac_accured_credit_account_id \
#                 or not journal.accured_debit_account_id or not journal.conac_accured_debit_account_id:
#             if self.env.user.lang == 'es_MX':
#                 raise ValidationError(_("Por favor configure Devengado la cuenta UNAM y CONAC en diario!"))
#             else:
#                 raise ValidationError(_("Please configure Accured UNAM and CONAC account in journal!"))
#         unam_move_val = {'ref': self.folio, 'control_id': control_amount.id, 'conac_move': True,
#                          'date': today, 'journal_id': journal.id, 'company_id': company_id,
#                          'line_ids': [(0, 0, {
#                              'account_id': journal.accured_credit_account_id.id,
#                              'coa_conac_id': journal.conac_accured_credit_account_id.id,
#                              'credit': amount, 'control_id': control_amount.id,
#                              'partner_id': partner_id
#                          }), (0, 0, {
#                              'account_id': journal.accured_debit_account_id.id,
#                              'coa_conac_id': journal.conac_accured_debit_account_id.id,
#                              'debit': amount, 'control_id': control_amount.id,
#                              'partner_id': partner_id
#                          })]}
#         unam_move = move_obj.create(unam_move_val)
#         unam_move.action_post()
#         
#     def create_collected_journal_entry(self,partner_id,amount,journal,today,control_amount,company_id):
#         move_obj = self.env['account.move']
#         if not journal.collected_credit_account_id or not journal.conac_collected_credit_account_id \
#                 or not journal.collected_debit_account_id or not journal.conac_collected_debit_account_id:
#             if self.env.user.lang == 'es_MX':
#                 raise ValidationError(_("Por favor configure Recaudado la cuenta UNAM y CONAC en diario!"))
#             else:
#                 raise ValidationError(_("Please configure Collected UNAM and CONAC account in journal!"))
#         unam_move_val = {'ref': self.folio, 'control_id': control_amount.id, 'conac_move': True,
#                          'date': today, 'journal_id': journal.id, 'company_id': company_id,
#                          'line_ids': [(0, 0, {
#                              'account_id': journal.collected_credit_account_id.id,
#                              'coa_conac_id': journal.conac_collected_credit_account_id.id,
#                              'credit': amount, 'control_id': control_amount.id,
#                              'partner_id': partner_id
#                          }), (0, 0, {
#                              'account_id': journal.collected_debit_account_id.id,
#                              'coa_conac_id': journal.conac_collected_debit_account_id.id,
#                              'debit': amount, 'control_id': control_amount.id,
#                              'partner_id': partner_id
#                          })]}
#         unam_move = move_obj.create(unam_move_val)
#         unam_move.action_post()
        
    def create_account_journal_entry(self,partner_id,amount,journal,today,control_amount,company_id):
        move_obj = self.env['account.move']
        if not journal.default_debit_account_id or not journal.default_credit_account_id \
                or not journal.conac_debit_account_id or not journal.conac_credit_account_id:
            if self.env.user.lang == 'es_MX':
                raise ValidationError(_("Por favor configure la cuenta UNAM y CONAC en diario!"))
            else:
                raise ValidationError(_("Please configure UNAM and CONAC account in journal!"))
        if not journal.collected_credit_account_id or not journal.conac_collected_credit_account_id \
                or not journal.collected_debit_account_id or not journal.conac_collected_debit_account_id:
            if self.env.user.lang == 'es_MX':
                raise ValidationError(_("Por favor configure Recaudado la cuenta UNAM y CONAC en diario!"))
            else:
                raise ValidationError(_("Please configure Collected UNAM and CONAC account in journal!"))
        if not journal.accured_credit_account_id or not journal.conac_accured_credit_account_id \
                or not journal.accured_debit_account_id or not journal.conac_accured_debit_account_id:
            if self.env.user.lang == 'es_MX':
                raise ValidationError(_("Por favor configure Devengado la cuenta UNAM y CONAC en diario!"))
            else:
                raise ValidationError(_("Please configure Accured UNAM and CONAC account in journal!"))

        unam_move_val = {'ref': self.folio, 'control_id': control_amount.id, 'conac_move': True,
                        'journal_id': journal.id, 'company_id': company_id,'date':today,
                         'line_ids': [(0, 0, {
                             'account_id': journal.default_credit_account_id.id,
                             'coa_conac_id': journal.conac_credit_account_id.id,
                             'credit': amount, 'control_id': control_amount.id,
                             'partner_id': partner_id
                             }), 
                             (0, 0, {
                             'account_id': journal.default_debit_account_id.id,
                             'coa_conac_id': journal.conac_debit_account_id.id,
                             'debit': amount, 'control_id': control_amount.id,
                             'partner_id': partner_id
                             }),
                            (0, 0, {
                             'account_id': journal.collected_credit_account_id.id,
                             'coa_conac_id': journal.conac_collected_credit_account_id.id,
                             'credit': amount, 'control_id': control_amount.id,
                             'partner_id': partner_id
                             }), 
                             (0, 0, {
                             'account_id': journal.collected_debit_account_id.id,
                             'coa_conac_id': journal.conac_collected_debit_account_id.id,
                             'debit': amount, 'control_id': control_amount.id,
                             'partner_id': partner_id
                             }),
                            (0, 0, {
                             'account_id': journal.accured_credit_account_id.id,
                             'coa_conac_id': journal.conac_accured_credit_account_id.id,
                             'credit': amount, 'control_id': control_amount.id,
                             'partner_id': partner_id
                             }), 
                            (0, 0, {
                             'account_id': journal.accured_debit_account_id.id,
                             'coa_conac_id': journal.conac_accured_debit_account_id.id,
                             'debit': amount, 'control_id': control_amount.id,
                             'partner_id': partner_id
                             })                                 
                         ]}
        unam_move = move_obj.create(unam_move_val)
        unam_move.action_post()
                         
    def validate(self):
        self.ensure_one()
        if self.total_rows != self.success_rows:
            raise ValidationError(_("Please validate all import lines!"))
        self.update_calendar_deposite_amount()
        move_obj = self.env['account.move']
        control_amount = self
        journal = control_amount.journal_id
        today = datetime.today()
        tz = self.env.user.tz or 'UTC'
        new_tz = pytz.timezone(tz)
        today = new_tz.localize(today).date()      
        user = self.env.user
        partner_id = user.partner_id.id
        amount = sum(control_amount.line_ids.mapped('amount_deposited'))
        company_id = user.company_id.id
        self.create_account_journal_entry(partner_id,amount,journal,today,control_amount,company_id)
#         if not journal.default_debit_account_id or not journal.default_credit_account_id \
#                 or not journal.conac_debit_account_id or not journal.conac_credit_account_id:
#             if self.env.user.lang == 'es_MX':
#                 raise ValidationError(_("Por favor configure la cuenta UNAM y CONAC en diario!"))
#             else:
#                 raise ValidationError(_("Please configure UNAM and CONAC account in journal!"))
#         unam_move_val = {'ref': self.folio, 'control_id': control_amount.id, 'conac_move': True,
#                          'date': today, 'journal_id': journal.id, 'company_id': company_id,
#                          'line_ids': [(0, 0, {
#                              'account_id': journal.default_credit_account_id.id,
#                              'coa_conac_id': journal.conac_credit_account_id.id,
#                              'credit': amount, 'control_id': control_amount.id,
#                              'partner_id': partner_id
#                          }), (0, 0, {
#                              'account_id': journal.default_debit_account_id.id,
#                              'coa_conac_id': journal.conac_debit_account_id.id,
#                              'debit': amount, 'control_id': control_amount.id,
#                              'partner_id': partner_id
#                          })]}
#         unam_move = move_obj.create(unam_move_val)
#         unam_move.action_post()
#         self.create_accured_journal_entry(partner_id,amount,journal,today,control_amount,company_id)
#         self.create_collected_journal_entry(partner_id,amount,journal,today,control_amount,company_id)
        
        self.state = 'validate'

    def import_lines(self):
        return {
            'name': "Import and Validate File",
            'type': 'ir.actions.act_window',
            'res_model': 'import.control.amount.lines',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(False, 'form')],
            'target': 'new',
        }

class ControlAmountsReceivedLine(models.Model):

    _name = 'control.amounts.received.line'
    _description = 'Control of amounts received lines'
    _rec_name = 'deposit_date'

    def _get_amount_pending(self):
        for record in self:
            record.amount_pending = record.amount_assigned - record.amount_deposited

    
    month = fields.Selection([
        ('january', 'January'),
        ('february', 'February'),
        ('march', 'March'),
        ('april', 'April'),
        ('may', 'May'),
        ('june', 'June'),
        ('july', 'July'),
        ('august', 'August'),
        ('september', 'September'),
        ('october', 'October'),
        ('november', 'November'),
        ('december', 'December')], string='Month of the amount', default='january')

    
    amount_assigned = fields.Integer(string='Amount assigned')
    
    
    account_id = fields.Many2one('res.bank', string='Bank')
    amount_pending = fields.Integer(
        string='Amount pending', compute='_get_amount_pending')
    observations = fields.Text(string='Comments')
    control_id = fields.Many2one(
        'control.amounts.received', string='Control of amounts received',ondelete='cascade')
    calendar_assigned_amount_id = fields.Many2one(
        'calendar.assigned.amounts', string='Calendar of assigned amount')
    calendar_assigned_amount_line_id = fields.Many2one(
        'calendar.assigned.amounts.lines', string='Calendar of assigned amount Line')

    # ======Import Line Data ====== #
    is_imported = fields.Boolean('Imported',default=False)
    state = fields.Selection([('manual', 'Manual'), ('draft', 'Draft'), (
        'fail', 'Fail'), ('success', 'Success')], string='Status', default='manual')

    shcp_id = fields.Many2one(
        'shcp.code', string='Budgetary Program')
    amount_deposited = fields.Float(string='Amount deposited')
    branch_cr = fields.Integer('Branch CR')
    unit_cr = fields.Char('Unit CR')
    folio_clc = fields.Integer('Folio CLC')
    clc_status = fields.Char('CLC Status')
    deposit_date = fields.Date(string='Deposit date')
    application_date = fields.Date(string='Application date')
    proposed_date = fields.Date(string='Proposed date')
    #currency_name = fields.Char('Currency')
    currency_name = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id,string="Currency")

    bank_id = fields.Many2one('res.bank', string='Bank')
    bank_account_id = fields.Many2one(
        'res.partner.bank', string='Bank account', domain="['|', ('bank_id', '=', False), ('bank_id', '=', bank_id)]")
    bank_account = fields.Char('Bank account')
    year = fields.Char('Year')
    branch = fields.Integer('Branch')
    unit = fields.Char('Unit')
    month_no = fields.Integer('Month')
    line_f = fields.Integer('F')
    sfa = fields.Integer('SFA')
    sfe = fields.Integer('SFE')
    prg = fields.Integer('PRG')
    ai = fields.Integer('AI')
    ip = fields.Char('IP',Size=1)
    line_p = fields.Char('P',size=3)
    conversion_name = fields.Char(string='Conversion Name',size=5)
    conpa_id = fields.Many2one('departure.conversion','OGTO')
    tg = fields.Integer('TG')
    ff = fields.Integer('FF')
    ef = fields.Integer('EF')
    is_manual_line = fields.Boolean('Manual Add Line',default=False)
    
    @api.constrains('folio_clc')
    def check_folio_unique(self):
        if self.folio_clc: 
            same_folio_line = self.env['control.amounts.received.line'].search_count(
                    [('control_id', '!=',False),('control_id', '!=', self.control_id.id), ('folio_clc', '=', self.folio_clc)])
            if same_folio_line:
                if self.env.user.lang == 'es_MX':
                    raise ValidationError(_("Actualmente, el Folio  %s ya está registrado!")%(self.folio_clc))
                else:
                    raise ValidationError(_("Currently Folio %s is already registered!")%(self.folio_clc))

    @api.model
    def create(self,vals):
        if vals.get('line_p',False):
            line_p = vals.get('line_p',False)
            line_p = str(line_p).zfill(3)
            vals.update({'line_p':line_p})
        return super(ControlAmountsReceivedLine,self).create(vals)
    
    def write(self,vals):
        if vals.get('line_p',False):
            line_p = vals.get('line_p',False)
            line_p = str(line_p).zfill(3)
            vals.update({'line_p':line_p})
        return super(ControlAmountsReceivedLine,self).write(vals)
            
class AccountMove(models.Model):

    _inherit = 'account.move'

    control_id = fields.Many2one('control.amounts.received')

class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    control_id = fields.Many2one('control.amounts.received')
