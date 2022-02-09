from odoo import models, fields,_
from odoo.exceptions import UserError, ValidationError
import base64
from datetime import datetime, timedelta
from odoo.tools.misc import formatLang, format_date, get_lang
from babel.dates import format_datetime, format_date

class LiquidAdjustmentsManualDeposite(models.TransientModel):

    _name = 'liquid.adjustments.manual.deposite'
    _description = 'Liquid Adjustments Manual Deposite'
    
    folio = fields.Char("Folio")
    budget_id = fields.Many2one("expenditure.budget",'Expenditure Budget')
    adaptation_type = fields.Selection(
        [('compensated', 'Compensated Adjustments'), ('liquid', 'Liquid Adjustments')], default='liquid')
    journal_id = fields.Many2one('account.journal', string="Daily")
    date_of_liquid_adu = fields.Date("Affection Date",default=datetime.today())
    observation = fields.Text(string='Justification of the Movement')
    move_id = fields.Many2one("account.move",'Move')
    
    
    def generate_adequacies(self):
        
        invoice_lines = self.move_id.invoice_line_ids.filtered(lambda x:not x.program_code_id)
        if invoice_lines:
            raise ValidationError("Please add program code into invoice lines")
        program_codes = self.move_id.invoice_line_ids.mapped('program_code_id')      
        program_codes_budget = program_codes.filtered(lambda x:x.budget_id.id != self.budget_id.id)
        
        if program_codes_budget:
            str_msg = "Budget " + self.budget_id.name + " not exist For Program Code\n\n" 
            for program in program_codes_budget:
                program_name = program.program_code
                budget_name = program.budget_id and program.budget_id.name or ''
                str_msg += program_name+" Budget Name is "+ budget_name +"\n\n"
                raise ValidationError(str_msg)
        line_list = []
        for program in program_codes:
            total_lines = self.move_id.invoice_line_ids.filtered(lambda x:x.program_code_id.id==program.id)
            total_amount = sum(x.balance for x in total_lines)
            line_list.append((0,0,{'program':program.id,'line_type':'increase','creation_type':'manual','amount':abs(total_amount)}))
                             
        vals = {'budget_id':self.budget_id.id,'adaptation_type':self.adaptation_type,
                'journal_id' : self.journal_id.id,'date_of_liquid_adu' : self.date_of_liquid_adu,
                'invoice_move_id' : self.move_id.id,
                'adequacies_lines_ids' : line_list 
                }
        self.env['adequacies'].create(vals)
         