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
from odoo import models, fields, api,_
from odoo.exceptions import ValidationError

class AccountMove(models.Model):

    _inherit = 'account.move'

    def show_conac_move(self):
        for record in self:
            record.conac_line_ids = record.line_ids.filtered(lambda x:x.conac_move)
             
    budget_id = fields.Many2one('expenditure.budget')
    adequacy_id = fields.Many2one('adequacies')
    budget_standardization_id = fields.Many2one('standardization')
    dependancy_id = fields.Many2one('dependency', string='Dependency')
    sub_dependancy_id = fields.Many2one('sub.dependency', 'Sub Dependency')
    payment_place_id = fields.Many2one('payment.place', 'Payment Place')
    conac_line_ids = fields.One2many('account.move.line', 'move_id', string='Journal Items',
                                     compute="show_conac_move")


    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        if res.dependancy_id and res.sub_dependancy_id:
            if res.sub_dependancy_id.dependency_id and res.sub_dependancy_id.dependency_id.id != res.dependancy_id.id:
                res.sub_dependancy_id = self.env['sub.dependency'].get_sub_dep_records(res.sub_dependancy_id.sub_dependency,res.dependancy_id.id)
        return res
    
    @api.onchange('dependancy_id','sub_dependancy_id','is_payroll_payment_request')        
    def onchange_dep_sub_dep(self):
        if self.is_payroll_payment_request:
            if self.dependancy_id and self.sub_dependancy_id:
                payment_place_id = self.env['payment.place'].search([('dependancy_id','=',self.dependancy_id.id),('sub_dependancy_id','=',self.sub_dependancy_id.id)],limit=1)
                if payment_place_id:
                    self.payment_place_id = payment_place_id.id
                else:
                    self.payment_place_id = False
            else:
                self.payment_place_id = False

    @api.onchange('payment_place_id','is_different_payroll_request','is_payment_request')        
    def onchange_payment_place_id(self):
        #if self.is_different_payroll_request or self.is_payment_request:
        if self.payment_place_id:
            self.dependancy_id = self.payment_place_id.dependancy_id and self.payment_place_id.dependancy_id.id or False
            self.sub_dependancy_id = self.payment_place_id.sub_dependancy_id and self.payment_place_id.sub_dependancy_id.id or False
        else:  
            self.dependancy_id = False
            self.sub_dependancy_id = False
                
    def action_register(self):
        for move in self.filtered(lambda x:not x.is_different_payroll_request and not x.is_pension_payment_request):
            invoice_lines = move.invoice_line_ids.filtered(lambda x:not x.program_code_id and x.price_unit > 0)
            if invoice_lines.filtered(lambda x:x.account_id and not x.account_id.code in ('220.003.001','115.001.001')):
                raise ValidationError("Please add program code into invoice lines")
        return super(AccountMove,self).action_register()

    def validate_multiple_budgets(self):
        
        if any(self.filtered(lambda x:x.payment_state != 'registered')):
            raise ValidationError("Only allowed to validate registered payment")
        
        str_msg = "Budgetary Insufficiency For Program Code\n\n"
        if self.env.user.lang == 'es_MX':
            str_msg = "Insuficiencia Presupuestal para el código del programa\n\n"
        
        is_check = False
        budget_msg = "Budget sufficiency"
        if self.env.user.lang == 'es_MX':
            budget_msg = "Suficiencia Presupuestal"
        
        insufficient_move_ids = []
        sufficient_move_ids = []
        budget_line_obj = self.env['expenditure.budget.line']
        move_str_msg_dict = {} # Msg Dict for insufficient move and its program code list that will help to save
                                # rejection message
        code_dict = {} # To minus available balance if same program code with different request
        # For e.g. Procom code 1 is added in two requests with amount 3000 & 4000 and available balance is 5000
        # So when checking second request need to minus first request amount otherwise in both we get suffient
        for request in self:
            if request.payment_state == 'registered':
                move_str_msg = "Budgetary Insufficiency For Program Code\n\n"
                if self.env.user.lang == 'es_MX':
                    move_str_msg = "Insuficiencia Presupuestal para el código del programa\n\n"
                
                sufficient_move_ids.append(request.id)
                for line in request.invoice_line_ids.filtered(lambda x:x.program_code_id):
                    total_available_budget = 0
                    if line.program_code_id:
                        budget_line = self.env['expenditure.budget.line']
                        budget_lines = budget_line_obj.sudo().search(
                            [('program_code_id', '=', line.program_code_id.id),
                             ('expenditure_budget_id', '=', line.program_code_id.budget_id.id),
                             ('expenditure_budget_id.state', '=', 'validate')])

                        if request.invoice_date and budget_lines:
                            b_month = request.invoice_date.month
                            for b_line in budget_lines:
                                if b_line.start_date:
                                    b_s_month = b_line.start_date.month
                                    if b_month in (1, 2, 3) and b_s_month in (1, 2, 3):
                                        budget_line += b_line
                                    elif b_month in (4, 5, 6) and b_s_month in (1, 2, 3, 4, 5, 6):
                                        budget_line += b_line
                                    elif b_month in (7, 8, 9) and b_s_month in (1, 2, 3, 4, 5, 6,7, 8, 9):
                                        budget_line += b_line
                                    elif b_month in (10, 11, 12) and b_s_month in (1, 2, 3, 4, 5, 6,7, 8, 9,10, 11, 12):
                                        budget_line += b_line
                            total_available_budget = sum(x.available for x in budget_line)

                            # Minus if same programcode exits in another request which is also selected
                            if line.program_code_id.id in code_dict.keys():
                                exit_lines = code_dict.get(line.program_code_id.id)
                                for exit_line in exit_lines:
                                    if exit_line.move_id.invoice_date.month == b_month:
                                        if exit_line.debit:
                                            total_available_budget -= exit_line.debit + exit_line.tax_price_cr
                                        else:
                                            total_available_budget -= exit_line.credit + exit_line.tax_price_cr 

                            # Preparing code_dict purpose added where defined
                            if line.program_code_id.id in code_dict.keys():
                                code_dict.update({line.program_code_id.id: code_dict.get(line.program_code_id.id) + [line]})
                            else:
                                code_dict.update({line.program_code_id.id: [line]})
                    line_amount = 0
                    if line.debit:
                        line_amount = line.debit + line.tax_price_cr
                    else:
                        line_amount = line.credit + line.tax_price_cr
                    if total_available_budget < line_amount:
                        is_check = True
                        program_name = ''
                        if line.program_code_id:
                            program_name = line.program_code_id.program_code
                            avl_amount = " Available Amount Is "
                            if self.env.user.lang == 'es_MX':
                                avl_amount = " Disponible Monto "
                            
                            str_msg += program_name + avl_amount + str(total_available_budget) + "\n\n"
                            move_str_msg += program_name + avl_amount + str(total_available_budget) + "\n\n"
                            insufficient_move_ids.append(request.id)
                if request.id in insufficient_move_ids:
                    move_str_msg_dict.update({request.id: move_str_msg})
        if is_check:
            new_sufficient_move_ids = list(set(sufficient_move_ids)-set(insufficient_move_ids))
            print ("sufficient_move_ids===",new_sufficient_move_ids)
            print ("insufficient_move_ids===",insufficient_move_ids)
            return {
                'name': _('Budgetary Insufficiency'),
                'type': 'ir.actions.act_window',
                'res_model': 'budget.insufficien.wiz',
                'view_mode': 'form',
                'view_type': 'form',
                'views': [(False, 'form')],
                'target': 'new',
                'context': {'default_msg': str_msg, 'default_is_budget_suf': False,
                            'move_str_msg_dict': move_str_msg_dict,
                            'default_move_ids': [(4, move) for move in new_sufficient_move_ids],
                            'default_insufficient_move_ids': [(4, move) for move in insufficient_move_ids]
                            }
            }
        else:
            return {
                'name': _('Budget sufficiency'),
                'type': 'ir.actions.act_window',
                'res_model': 'budget.insufficien.wiz',
                'view_mode': 'form',
                'view_type': 'form',
                'views': [(False, 'form')],
                'target': 'new',
                'context': {'default_msg': budget_msg, 'default_is_budget_suf': True,
                            'default_move_ids': [(4, move) for move in sufficient_move_ids]}
            }

    def action_validate_budget(self):
        self.ensure_one()
        str_msg = "Budgetary Insufficiency For Program Code\n\n"
        if self.env.user.lang == 'es_MX':
            str_msg = "Insuficiencia Presupuestal para el código del programa\n\n"
        is_check = False
        budget_msg = "Budget sufficiency"
        if self.env.user.lang == 'es_MX':
            budget_msg = "Suficiencia Presupuestal"
            
        for line in self.invoice_line_ids.filtered(lambda x:x.program_code_id):
            total_available_budget = 0
            if line.program_code_id:
                budget_line = self.env['expenditure.budget.line']
                budget_lines = self.env['expenditure.budget.line'].sudo().search(
                [('program_code_id', '=', line.program_code_id.id),
                 ('expenditure_budget_id', '=', line.program_code_id.budget_id.id),
                 ('expenditure_budget_id.state', '=', 'validate')])
                
#                 invoice_lines = self.env['account.move.line']
#                 invoice_lines_exist = self.env['account.move.line'].search([('program_code_id', '=', line.program_code_id.id),
#                                                                             ('move_id.payment_state', '=', 'approved_payment')
#                                                                            ])
                if self.invoice_date and budget_lines:
                    b_month = self.invoice_date.month
                    for b_line in budget_lines:
                        if b_line.start_date:
                            b_s_month = b_line.start_date.month
                            if b_month in (1, 2, 3) and b_s_month in (1, 2, 3):
                                budget_line += b_line
                            elif b_month in (4, 5, 6) and b_s_month in (1, 2, 3, 4, 5, 6):
                                budget_line += b_line
                            elif b_month in (7, 8, 9) and b_s_month in (1, 2, 3, 4, 5, 6, 7, 8, 9):
                                budget_line += b_line
                            elif b_month in (10, 11, 12) and b_s_month in (1, 2, 3, 4, 5, 6, 7, 8, 9,10, 11, 12):
                                budget_line += b_line
                    
                    total_available_budget = sum(x.available for x in budget_line)
#                 if self.invoice_date and invoice_lines_exist: 
#                     invoice_month = self.invoice_date.month
#                     for b_line in invoice_lines_exist:
#                         if b_line.move_id.invoice_date:
#                             b_s_month = b_line.move_id.invoice_date.month
#                             if invoice_month in (1, 2, 3) and b_s_month in (1, 2, 3):
#                                 invoice_lines += b_line
#                             elif invoice_month in (4, 5, 6) and b_s_month in (4, 5, 6):
#                                 invoice_lines += b_line
#                             elif invoice_month in (7, 8, 9) and b_s_month in (7, 8, 8):
#                                 invoice_lines += b_line
#                             elif invoice_month in (10, 11, 12) and b_s_month in (10, 11, 12):
#                                 invoice_lines += b_line
#                     total_assign_budget = sum(x.price_total for x in invoice_lines)
#                     total_available_budget = total_available_budget - total_assign_budget
                    
            line_amount =  0
            if line.debit:
                line_amount = line.debit + line.tax_price_cr
            else: 
                line_amount = line.credit + line.tax_price_cr
            
            
            if total_available_budget < line_amount:
                is_check = True
                program_name = ''
                if line.program_code_id:
                    program_name = line.program_code_id.program_code
                    avl_amount = " Available Amount Is "
                    if self.env.user.lang == 'es_MX':
                        avl_amount = " Disponible Monto "
                    str_msg += program_name+avl_amount+str(total_available_budget)+"\n\n"
                    
        if is_check:
            return {
                        'name': _('Budgetary Insufficiency'),
                        'type': 'ir.actions.act_window',
                        'res_model': 'budget.insufficien.wiz',
                        'view_mode': 'form',
                        'view_type': 'form',
                        'views': [(False, 'form')],
                        'target': 'new',
                        'context':{'default_msg':str_msg,'default_move_id':self.id,'default_is_budget_suf':False}
                    }
        else:
            return {
                        'name': _('Budget sufficiency'),
                        'type': 'ir.actions.act_window',
                        'res_model': 'budget.insufficien.wiz',
                        'view_mode': 'form',
                        'view_type': 'form',
                        'views': [(False, 'form')],
                        'target': 'new',
                        'context':{'default_msg':budget_msg,'default_move_id':self.id,'default_is_budget_suf':True}
                    }

    def add_budget_available_amount(self): 
        for line in self.invoice_line_ids:
            if line.budget_line_link_ids:
                for b_line in line.budget_line_link_ids:
                    if b_line.budget_line_id:
                        b_line.budget_line_id.available += b_line.amount
                        control_assing_line = self.env['control.assigned.amounts.lines'].search([
                            ('program_code_id','=',b_line.budget_line_id.program_code_id.id),
                            ('assigned_amount_id.budget_id','=',b_line.budget_line_id.expenditure_budget_id.id),
                            ('assigned_amount_id.state','=','validated'),
                            ('start_date','=',b_line.budget_line_id.start_date),
                            ('end_date','=',b_line.budget_line_id.end_date)
                            ])
                        if control_assing_line:
                            control_assing_line[0].available += b_line.amount
                            
                line.budget_line_link_ids.unlink()
                   
    def action_draft_budget(self):
        self.ensure_one()
        self.payment_state = 'draft'
        self.button_draft()
        conac_move = self.line_ids.filtered(lambda x:x.conac_move)
        conac_move.sudo().unlink()
        for line in self.line_ids:
            line.coa_conac_id = False 
        
        self.add_budget_available_amount()
        return self.payment_state
    
    def cancel_payment_revers_entry(self):
        revers_list = []
        for line in self.line_ids:
            revers_list.append((0, 0, {
                                     'account_id': line.account_id.id,
                                     'coa_conac_id': line.coa_conac_id and line.coa_conac_id.id or False,
                                     'credit': line.debit,
                                     'debit':line.credit, 
                                     'exclude_from_invoice_tab': True,
                                     'conac_move' : line.conac_move,
                                     'name' : 'Reversa',
                                     'currency_id' : line.currency_id and line.currency_id.id or False,
                                     'amount_currency' : -line.amount_currency,
                                 }))
        self.line_ids = revers_list 

    def button_cancel(self):
        for record in self:
            if record.is_payment_request or record.is_payroll_payment_request or record.is_project_payment:
                if record.payment_state == 'cancel':
                    record.cancel_payment_revers_entry()
                    record.add_budget_available_amount()
        return super(AccountMove,self).button_cancel()
    
    def action_cancel_budget(self):
        self.ensure_one()
        self.payment_state = 'cancel'
        self.button_cancel()
        
    # def action_reschedule(self):
    #     res = super(AccountMove,self).action_reschedule()
    #     for move in self:
    #         move.add_budget_available_amount()
    #     return res
    
              
    def create_journal_line_for_approved_payment(self):
        all_line_list = []
        for move in self:
            if move.journal_id and (not move.journal_id.default_credit_account_id or not \
                move.journal_id.default_debit_account_id):
                raise ValidationError(_("Configure Default Debit and Credit Account in %s!" % \
                                        move.journal_id.name))
            
            amount_total = sum(x.price_total for x in move.invoice_line_ids.filtered(lambda x:x.program_code_id))    
            if move.currency_id != move.company_id.currency_id:
                amount_currency = abs(amount_total)
                balance = move.currency_id._convert(amount_currency, move.company_currency_id, move.company_id, move.date)
                currency_id = move.currency_id and move.currency_id.id or False
            else:
                balance = abs(amount_total)
                amount_currency = 0.0
                currency_id = False
                
            all_line_list.append({
                                         'account_id': move.journal_id.default_credit_account_id.id,
                                         'coa_conac_id': move.journal_id.conac_credit_account_id.id,
                                         'credit': balance, 
                                         'amount_currency' : -amount_currency,
                                         'exclude_from_invoice_tab': True,
                                         'conac_move' : True,
                                         'currency_id' : currency_id,
                                         'partner_id':move.partner_id and move.partner_id.id or False,
                                         'is_for_approved_payment' : True,
                                         'move_id':move.id
                                     })
             
            all_line_list.append({
                                         'account_id': move.journal_id.default_debit_account_id.id,
                                         'coa_conac_id': move.journal_id.conac_debit_account_id.id,
                                         'debit': balance,
                                         'amount_currency' : amount_currency,
                                         'exclude_from_invoice_tab': True,
                                         'conac_move' : True,
                                         'currency_id' : currency_id,
                                         'partner_id':move.partner_id and move.partner_id.id or False,
                                         'is_for_approved_payment' : True,
                                         'move_id':move.id
                                     })
        self.env['account.move.line'].create(all_line_list)
        self.env.cr.execute("UPDATE account_move set conac_move=%s where id in %s", ('t',tuple(self.ids)))
        #self.write({'conac_move':True})
        
class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    budget_id = fields.Many2one('expenditure.budget')
    adequacy_id = fields.Many2one('adequacies')
    budget_standardization_id = fields.Many2one('standardization')
    program_code_id = fields.Many2one('program.code')
    budget_line_link_ids = fields.One2many('budget.line.move.line.links','account_move_line_id')
    
    @api.onchange('program_code_id')
    def onchange_program_code(self):
        if self.program_code_id and self.program_code_id.item_id and self.program_code_id.item_id.unam_account_id:
            self.account_id = self.program_code_id.item_id.unam_account_id.id
            

#     @api.model
#     def _get_default_tax_account(self, repartition_line):
#         account = super(AccountMoveLine,self)._get_default_tax_account(repartition_line)
#         if self.program_code_id and self.program_code_id.item_id and self.program_code_id.item_id.unam_account_id:
#             return self.program_code_id.item_id.unam_account_id
#         return account

class BudgetLineMoveLinelinks(models.Model):
    
    _name = 'budget.line.move.line.links'
    
    budget_line_id = fields.Many2one('expenditure.budget.line','Budget Line')
    account_move_line_id = fields.Many2one('account.move.line','Budget Line')
    amount = fields.Float('Amount')
       
    
           
