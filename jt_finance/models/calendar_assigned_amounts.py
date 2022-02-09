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
from odoo.exceptions import ValidationError
from odoo import models, fields, api, _
from datetime import datetime
import base64
import io

class CalendarAssignedAmounts(models.Model):

    _name = 'calendar.assigned.amounts'
    _description = 'Calendar of assigned amounts'
    _rec_name = 'date'

    def _get_amount(self):
        for record in self:
            record.amount_to_receive = sum(
                record.line_ids.mapped('annual_amount'))
            record.amount_received = sum(
                record.line_ids.mapped('annual_amount_received'))
            record.amount_pending = record.amount_to_receive - record.amount_received

    # Fields for control of amount received
    folio = fields.Char(string='Folio')
    budget_id = fields.Many2one('expenditure.budget', domain=[
                                ('state', '=', 'validate')])
    user_id = fields.Many2one('res.users', string='Made By',
                              default=lambda self: self.env.user, tracking=True, copy=False)
    file = fields.Binary(string='Seasonal File', copy=False)
    filename = fields.Char(string="File Name", copy=False)
    import_date = fields.Date(string='Import Date', copy=False,default=datetime.today())
    obs_cont_amount = fields.Text(string='Observations')
    total_rows = fields.Integer(string='Total Rows', copy=False)
    diff = fields.Text(string='Difference', copy=False)

    # Fields for Calender of assigned amounts
    date = fields.Date(string='Date')
    amount_to_receive = fields.Float(
        string='Amount to receive', compute='_get_amount')
    amount_received = fields.Float(
        string='Amount received', compute='_get_amount')
    amount_pending = fields.Float(
        string='Amount pending', compute='_get_amount')
    obs_calender_amount = fields.Text(string='Observations')

    @api.depends('date')
    def _compute_month_int(self):
        for record in self:
            record.month_int = 0
            if record.date:
                record.month_int = record.date.month

    month_int = fields.Integer(string='Month Integer', store=True, compute='_compute_month_int')

    line_ids = fields.One2many('calendar.assigned.amounts.lines',
                               'calendar_assigned_amount_id', string='Calendar of assigned amount lines',domain=[('state', 'in', ('success','manual'))])
    import_line_ids = fields.One2many('calendar.assigned.amounts.lines',
                               'calendar_assigned_amount_id', string='Imported Lines',domain=[('state', 'in', ('draft','fail'))])

    journal_id = fields.Many2one("account.journal", string="Journal")
    state = fields.Selection([('draft', 'Draft'), ('validate', 'Validated')], default='draft',string='Status')
    move_line_ids = fields.One2many('account.move.line', 'calender_id', string="Journal Items")

    import_status = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Completed')], default='draft', copy=False)

    def _compute_total_rows(self):
        for budget in self:
            budget.failed_rows = self.env['calendar.assigned.amounts.lines'].search_count(
                [('calendar_assigned_amount_id', '=', budget.id), ('state', '=', 'fail')])
            budget.success_rows = self.env['calendar.assigned.amounts.lines'].search_count(
                [('calendar_assigned_amount_id', '=', budget.id), ('state', '=', 'success')])
            budget.total_rows = self.env['calendar.assigned.amounts.lines'].search_count(
                [('calendar_assigned_amount_id', '=', budget.id),('state', '!=', 'manual')])

    failed_rows = fields.Integer(
        string='Failed Rows', compute="_compute_total_rows")
    success_rows = fields.Integer(
        string='Success Rows', compute="_compute_total_rows")
    total_rows = fields.Integer(
        string="Total Rows", compute="_compute_total_rows")

    failed_row_file = fields.Binary(string='Failed Rows File')
    fialed_row_filename = fields.Char(
        string='File name', default=lambda self: _("Failed_Rows.txt"))

    def unlink(self):
        for calendar in self:
            if calendar.state in ('validate'):
                if self.env.user.lang == 'es_MX':
                    raise ValidationError(_("No puedes eliminar un Registro del Subsidio Federal en estatus Validado."))
                else:
                    raise ValidationError('You cannot delete a Registration of Federal Subsidy in Validated status!')
            
        return super(CalendarAssignedAmounts, self).unlink()
        
    @api.model
    def default_get(self, fields):
        res = super(CalendarAssignedAmounts, self).default_get(fields)
        daily_income_jour = self.env.ref('jt_conac.daily_income_jour')
        if daily_income_jour:
            res.update({'journal_id': daily_income_jour.id})
        return res

    def validate_import_line(self):
        if len(self.import_line_ids.ids) > 0:

            counter = 0
            failed_row = ""
            failed_line_ids = []
            success_line_ids = []
            departure_conversion_obj = self.env['departure.conversion'].search_read([], fields=['id', 'federal_part'])
            for line in self.import_line_ids:
                counter += 1
                line_vals = [line.year, line.branch, line.unit, line.purpose, line.function, 
                                 line.sub_function, line.program,line.institution_activity, line.project_identification, line.project, line.item_char,
                                 line.expense_type, line.funding_source, line.federal,line.key_wallet ,line.january, line.february,
                                 line.march, line.april, line.may, line.june,line.july,line.august,line.september,line.october,line.november,line.december,line.annual_amount]
                
                # Validate  Item
                item_id = False
                if line.item_char:
                    item_id = list(filter(lambda prog: prog['federal_part'] == line.item_char, departure_conversion_obj))
                    item_id = item_id[0]['id'] if item_id else False
                if not item_id:
                    failed_row += str(line_vals) + \
                                  "------>> Invalid SHCP Games(CONPA) Format\n"
                    failed_line_ids.append(line.id)
                    continue
                line.item_id = item_id
                success_line_ids.append(line.id)

            failed_lines = self.env['calendar.assigned.amounts.lines'].search(
                [('calendar_assigned_amount_id', '=', self.id), ('id', 'in', failed_line_ids)])
            success_lines = self.env['calendar.assigned.amounts.lines'].search(
                [('calendar_assigned_amount_id', '=', self.id), ('id', 'in', success_line_ids)])
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
            
    def action_validate_calendar_assing(self):
        self.ensure_one()
        if self.total_rows != self.success_rows:
            raise ValidationError(_("Please validate all import lines!"))
        for line in self.line_ids:
            months_amounts = line.january + line.february+line.march+line.april+line.may+line.june+line.july+line.august+line.september+line.october+line.november+line.december
            if months_amounts != line.annual_amount:
                if self.env.user.lang == 'es_MX':
                    raise ValidationError(_("La cantidad anual ingresada no es correcta."))
                else:
                    raise ValidationError(_("The annual amount entered is not correct."))
                
        move_obj = self.env['account.move']
        control_amount = self
        journal = control_amount.journal_id
        today = datetime.today().date()
        user = self.env.user
        partner_id = user.partner_id.id
        amount = sum(control_amount.line_ids.mapped('annual_amount'))
        company_id = user.company_id.id
        if not journal.estimated_credit_account_id or not journal.estimated_debit_account_id \
                or not journal.conac_estimated_credit_account_id or not journal.conac_estimated_debit_account_id:
            if self.env.user.lang == 'es_MX':
                raise ValidationError(_("Por favor configure estimada la cuenta UNAM y CONAC en diario!"))
            else:
                raise ValidationError(_("Please configure Estimated UNAM and CONAC account in journal!"))
        unam_move_val = {'ref': self.folio, 'calender_id': control_amount.id, 'conac_move': True,
                         'date': today, 'journal_id': journal.id, 'company_id': company_id,
                         'line_ids': [(0, 0, {
                             'account_id': journal.estimated_credit_account_id.id,
                             'coa_conac_id': journal.conac_estimated_credit_account_id.id,
                             'credit': amount, 'calender_id': control_amount.id,
                             'partner_id': partner_id
                         }), (0, 0, {
                             'account_id': journal.estimated_debit_account_id.id,
                             'coa_conac_id': journal.conac_estimated_debit_account_id.id,
                             'debit': amount, 'calender_id': control_amount.id,
                             'partner_id': partner_id
                         })]}
        unam_move = move_obj.create(unam_move_val)
        unam_move.action_post()
        self.state = 'validate'
        
    def import_lines(self):
        return {
            'name': "Import and Validate File",
            'type': 'ir.actions.act_window',
            'res_model': 'import.calendar.assign.amount.lines',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(False, 'form')],
            'target': 'new',
        }


#     @api.constrains('date', 'line_ids')
#     def _check_lines(self):
#         if self.date:
#             date_month = self.date.month
#             months = list(self.line_ids.mapped('month'))
#             month_dict = {
#                 1: 'january',
#                 2: 'february',
#                 3: 'march',
#                 4: 'april',
#                 5: 'may',
#                 6: 'june',
#                 7: 'july',
#                 8: 'august',
#                 9: 'september',
#                 10: 'october',
#                 11: 'november',
#                 12: 'december',
#             }
#             if any(month != month_dict.get(date_month) for month in months):
#                 raise ValidationError("You can only add selected date's month in lines")


class CalendarAssignedAmountsLines(models.Model):

    _name = 'calendar.assigned.amounts.lines'
    _description = 'Calendar of assigned amounts lines'
    _rec_name = 'date'

    date = fields.Date(string='Deposit date')
    shcp_id = fields.Many2one(
        'shcp.code', string='Budgetary Program')
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

    bank_id = fields.Many2one('res.bank', string='Bank')
    bank_account_id = fields.Many2one(
        'res.partner.bank', string='Bank account', domain="['|', ('bank_id', '=', False), ('bank_id', '=', bank_id)]")
    observations = fields.Text(string='Observations')
    calendar_assigned_amount_id = fields.Many2one(
        'calendar.assigned.amounts', string='Calendar of assigned amount',ondelete='cascade')

    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id)

    @api.depends('project_identification','project')
    def get_budgetary_program(self):
        for line in self:
            budgetary_program = ''
            if line.project_identification:
                budgetary_program += line.project_identification
            if line.project:
                budgetary_program += line.project.zfill(3)
            line.budgetary_program = budgetary_program
            
    #==== New fields ======#

    is_imported = fields.Boolean('Imported',default=False)
    state = fields.Selection([('manual', 'Manual'), ('draft', 'Draft'), (
        'fail', 'Fail'), ('success', 'Success')], string='Status', default='manual')
    is_manual_line = fields.Boolean('Manual Add Line',default=False)
    
    year = fields.Char('Year',size=4)
    branch = fields.Integer('Branch')
    unit = fields.Char('Unit')
    purpose = fields.Integer('Purpose')
    function = fields.Integer('Function')
    sub_function = fields.Integer('Subfunction')
    program = fields.Char('Program')
    institution_activity = fields.Integer('Institution Activity')
    project_identification = fields.Char('Project Identification',size=1)
    project = fields.Char('Project',size=3)
    budgetary_program = fields.Char(string='Budgetary Program',compute='get_budgetary_program',store=True)
    item_id = fields.Many2one('departure.conversion','Expense Item')
    item_char = fields.Char('Field_item',size=5)
    expense_type = fields.Integer('Expense Type')
    funding_source = fields.Char('Funding Source')
    federal = fields.Integer('Federal')
    key_wallet = fields.Char('Key Wallet')
    january = fields.Float(string='January')
    amount_deposite_january = fields.Float(string='Amount deposited January')
    february = fields.Float(string='February')
    amount_deposite_february = fields.Float(string='Amount deposited February')
    march = fields.Float(string='March')
    amount_deposite_march = fields.Float(string='Amount deposited March')
    april = fields.Float(string='April')
    amount_deposite_april = fields.Float(string='Amount deposited April')
    may = fields.Float(string='May')
    amount_deposite_may = fields.Float(string='Amount deposited May')
    june = fields.Float(string='June')
    amount_deposite_june = fields.Float(string='Amount deposited June')
    july = fields.Float(string='July')
    amount_deposite_july = fields.Float(string='Amount deposited July')
    august = fields.Float(string='August')
    amount_deposite_august = fields.Float(string='Amount deposited August')
    september = fields.Float(string='September')
    amount_deposite_september = fields.Float(string='Amount deposited September')
    october = fields.Float(string='October')
    amount_deposite_october = fields.Float(string='Amount deposited October')
    november = fields.Float(string='November')
    amount_deposite_november = fields.Float(string='Amount deposited November')
    december = fields.Float(string='December')
    amount_deposite_december = fields.Float(string='Amount deposited December')
    
    annual_amount = fields.Float(string='Annual Amount')
    
    @api.depends('amount_deposite_january','amount_deposite_february','amount_deposite_march',
                 'amount_deposite_april','amount_deposite_may','amount_deposite_june',
                 'amount_deposite_july','amount_deposite_august','amount_deposite_september',
                 'amount_deposite_october','amount_deposite_november','amount_deposite_december'
                 )
    def cal_annual_amount_received(self):
        for line in self:
            line.annual_amount_received = line.amount_deposite_january+line.amount_deposite_february+line.amount_deposite_march  \
                                          + line.amount_deposite_april + line.amount_deposite_may + line.amount_deposite_june \
                                          + line.amount_deposite_july + line.amount_deposite_august + line.amount_deposite_september \
                                          + line.amount_deposite_october + line.amount_deposite_november + line.amount_deposite_december
                                            
    annual_amount_received = fields.Float(string='Annual Amount Received',compute='cal_annual_amount_received',store=True,copy=False)

    @api.depends('item_id')
    def get_item_data(self):
        for line in self:
            if line.item_id and line.item_id.federal_part:
                line.item_id_first = line.item_id.federal_part[0]
                if len(line.item_id.federal_part) > 1:
                    line.item_id_second = line.item_id.federal_part[1]
                
    item_id_first = fields.Char('Item First',compute='get_item_data',store=True)
    item_id_second = fields.Char('Item Second',compute='get_item_data',store=True)
    
    @api.model
    def create(self,vals):
        if vals.get('project',False):
            line_p = vals.get('project',False)
            line_p = str(line_p).zfill(3)
            vals.update({'project':line_p})
        return super(CalendarAssignedAmountsLines,self).create(vals)
     
    def write(self,vals):
        if vals.get('project',False):
            line_p = vals.get('project',False)
            line_p = str(line_p).zfill(3)
            vals.update({'project':line_p})
        return super(CalendarAssignedAmountsLines,self).write(vals)
    
class AccountMove(models.Model):

    _inherit = 'account.move'

    calender_id = fields.Many2one('calendar.assigned.amounts')

class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    calender_id = fields.Many2one('calendar.assigned.amounts')
