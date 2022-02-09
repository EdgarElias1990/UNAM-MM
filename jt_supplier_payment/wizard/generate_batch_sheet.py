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
from odoo import models, fields,_
from odoo.exceptions import UserError, ValidationError
from odoo.tools.profiler import profile

class GenerateBatchSheet(models.TransientModel):

    _name = 'generate.batch.sheet'    
    _description = 'Generate Batch Sheet'
    
    batch_line_ids = fields.One2many('generate.batch.sheet.line','batch_sheet_id','Folio')
    payment_type = fields.Selection([('supplier','Suppier'),('payroll','Payroll'),('different_payroll','Different Payroll'),('project_payment','Project Payment'),('pension_payment','Pension Payment')],string="Payent Type") 
    
    def action_generate_batch(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return ''

        line_data = []
        active_records = self.env['account.move'].browse(active_ids)
        seq_ids = self.env['ir.sequence']
        payment_type = False
        if active_records.filtered(lambda x:x.is_payment_request):
            seq_ids = self.env['ir.sequence'].search([('code', '=', 'batch.sheet.folio')], order='company_id')
            payment_type = 'supplier'
        elif active_records.filtered(lambda x:x.is_payroll_payment_request):
            seq_ids = self.env['ir.sequence'].search([('code', '=', 'payroll.payment.batch.sheet.folio')], order='company_id')
            payment_type = 'payroll'
        elif active_records.filtered(lambda x:x.is_different_payroll_request):
            seq_ids = self.env['ir.sequence'].search([('code', '=', 'different.payroll.payment.batch.sheet.folio')], order='company_id')
            payment_type = 'different_payroll'
        elif active_records.filtered(lambda x:x.is_project_payment):
            seq_ids = self.env['ir.sequence'].search([('code', '=', 'project.payroll.payment.batch.sheet.folio')], order='company_id')
            payment_type = 'project_payment'
        elif active_records.filtered(lambda x:x.is_pension_payment_request):
            seq_ids = self.env['ir.sequence'].search([('code', '=', 'pension.payroll.payment.batch.sheet.folio')], order='company_id')
            payment_type = 'pension_payment'
            
        number_next = 0
        if seq_ids:
            number_next = seq_ids[0].number_next_actual 
        
        for rec in active_ids:
            
            move_id = self.env['account.move'].browse(rec)
            line_batch_folio = move_id.batch_folio
            if move_id.invoice_sequence_number_next_prefix and  move_id.invoice_sequence_number_next:
                name = move_id.invoice_sequence_number_next_prefix + move_id.invoice_sequence_number_next
            else:
                name = move_id.name
            if not line_batch_folio:
                line_batch_folio = number_next
                
            line_data.append((0,0,{'account_move_id':move_id.id,'check_batch_folio':move_id.batch_folio,'batch_folio':line_batch_folio,'name':name}))
            
        return {
            'name': _('Generate Batch Sheet'),
            'res_model': 'generate.batch.sheet',
            'view_mode': 'form',
            'view_id': self.env.ref('jt_supplier_payment.view_generate_batch_sheet').id,
            'context': {'default_batch_line_ids':line_data,'default_payment_type':payment_type},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
    
    def update_batch_folio(self):
        line_recs = self.batch_line_ids.filtered(lambda x:x.batch_folio != x.check_batch_folio)
        if self.payment_type == 'supplier':
            folio = self.env['ir.sequence'].next_by_code('batch.sheet.folio')
        elif self.payment_type == 'payroll':
            folio = self.env['ir.sequence'].next_by_code('payroll.payment.batch.sheet.folio')
        elif self.payment_type == 'different_payroll':
            folio = self.env['ir.sequence'].next_by_code('different.payroll.payment.batch.sheet.folio')
        elif self.payment_type == 'project_payment':
            folio = self.env['ir.sequence'].next_by_code('project.payroll.payment.batch.sheet.folio')
        elif self.payment_type == 'pension_payment':
            folio = self.env['ir.sequence'].next_by_code('pension.payroll.payment.batch.sheet.folio')
        
        batch_folio_list = line_recs.mapped('batch_folio')
        batch_folio_list = list(set(batch_folio_list))
        for batch in batch_folio_list:
            new_lines = line_recs.filtered(lambda x:x.batch_folio==batch)
            if new_lines:
                move_ids = new_lines.mapped('account_move_id')
                move_ids.write({'batch_folio':batch})
                 
class GenerateBatchSheetLine(models.TransientModel):
    
    _name = 'generate.batch.sheet.line'
    
    account_move_id = fields.Many2one('account.move','Invoice')
    check_batch_folio = fields.Integer('Check Batch Folio')
    batch_folio = fields.Integer('Batch Folio')
    name = fields.Char('Name')
    batch_sheet_id = fields.Many2one('generate.batch.sheet')
    
    