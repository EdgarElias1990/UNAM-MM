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
from datetime import datetime
class BudegtInsufficiencWiz(models.TransientModel):

    _name = 'budget.insufficien.wiz'
    _description = 'Budgetary Insufficienc'

    msg = fields.Text('Message')
    is_budget_suf = fields.Boolean(default=False)
    move_id = fields.Many2one('account.move','Move')
    move_ids = fields.Many2many('account.move', 'rel_wizard_budget_move', 'move_id', 'rel_wiz_move_id')
    insufficient_move_ids = fields.Many2many('account.move', 'rel_wizard_budget_insufficient_move', 'move_id', 'rel_wiz_move_id')
    
    def action_ok(self):
        move_str_msg_dict = self._context.get('move_str_msg_dict')
        if self.insufficient_move_ids and not self.move_id:
            for move in self.insufficient_move_ids:
                move.payment_state = 'rejected'
                move.reason_rejection = move_str_msg_dict.get(str(move.id))
            self.action_budget_allocation()
        else:
            self.move_id.payment_state = 'rejected'
            self.move_id.reason_rejection = self.msg
        
        
    def decrease_available_amount(self):
        for line in self.move_id.invoice_line_ids:
            budget_line_links = []
            if line.program_code_id and line.price_total != 0:
                amount =  0
                if line.debit:
                    amount = line.debit + line.tax_price_cr
                else: 
                    amount = line.credit + line.tax_price_cr
                
                control_amount = 0
                if line.debit:
                    control_amount = line.debit + line.tax_price_cr
                else: 
                    control_amount = line.credit + line.tax_price_cr
                
                budget_lines = self.env['expenditure.budget.line'].sudo().search(
                [('program_code_id', '=', line.program_code_id.id),
                 ('expenditure_budget_id', '=', line.program_code_id.budget_id.id),
                 ('expenditure_budget_id.state', '=', 'validate'),('available','>',0)])
                
                if self.move_id.invoice_date and budget_lines:
                    b_month = self.move_id.invoice_date.month
                    for b_line in budget_lines.sorted(key='start_date'):
                        control_assing_line = self.env['control.assigned.amounts.lines'].search([('program_code_id','=',line.program_code_id.id),('assigned_amount_id.budget_id','=',b_line.expenditure_budget_id.id),('assigned_amount_id.state','=','validated')])
                        if b_line.start_date:
                            b_s_month = b_line.start_date.month
                            if b_month in (1, 2, 3) and b_s_month in (1, 2, 3):
                                control_assing_linefilter = control_assing_line.filtered(lambda x:x.start_date.month in (1,2,3) and x.available > 0).sorted(key='start_date')
                                if control_assing_linefilter and control_amount>0:
                                    if control_assing_linefilter[0].available >= control_amount:
                                        control_assing_linefilter[0].available -= control_amount
                                        control_amount = 0
                                    else:
                                        control_amount -= control_assing_linefilter[0].available
                                        control_assing_linefilter[0].available = 0
                                
                                if b_line.available >= amount:
                                    b_line.available -= amount
                                    budget_line_links.append((0,0,{'budget_line_id':b_line.id,'account_move_line_id':line.id,'amount':amount}))
                                    break
                                else:
                                    amount -= b_line.available
                                    budget_line_links.append((0,0,{'budget_line_id':b_line.id,'account_move_line_id':line.id,'amount':b_line.available}))
                                    b_line.available = 0
                                    
                            elif b_month in (4, 5, 6) and b_s_month in (1,2,3,4, 5, 6):
                                control_assing_linefilter = control_assing_line.filtered(lambda x:x.start_date.month in (1,2,3,4,5,6) and x.available > 0).sorted(key='start_date')
                                if control_assing_linefilter and control_amount>0:
                                    if control_assing_linefilter[0].available >= control_amount:
                                        control_assing_linefilter[0].available -= control_amount
                                        control_amount = 0
                                    else:
                                        control_amount -= control_assing_linefilter[0].available
                                        control_assing_linefilter[0].available = 0
                                    
                                if b_line.available >= amount:
                                    b_line.available -= amount
                                    budget_line_links.append((0,0,{'budget_line_id':b_line.id,'account_move_line_id':line.id,'amount':amount}))
                                    break
                                else:
                                    amount -= b_line.available
                                    budget_line_links.append((0,0,{'budget_line_id':b_line.id,'account_move_line_id':line.id,'amount':b_line.available}))
                                    b_line.available = 0
                                    
                                    
                            elif b_month in (7, 8, 9) and b_s_month in (1,2,3,4,5,6,7, 8, 9):
                                control_assing_linefilter = control_assing_line.filtered(lambda x:x.start_date.month in (1,2,3,4,5,6,7, 8, 9) and x.available > 0).sorted(key='start_date')
                                if control_assing_linefilter and control_amount>0:
                                    if control_assing_linefilter[0].available >= control_amount:
                                        control_assing_linefilter[0].available -= control_amount
                                        control_amount = 0
                                    else:
                                        control_amount -= control_assing_linefilter[0].available
                                        control_assing_linefilter[0].available = 0
                                
                                if b_line.available >= amount:
                                    b_line.available -= amount
                                    budget_line_links.append((0,0,{'budget_line_id':b_line.id,'account_move_line_id':line.id,'amount':amount}))
                                    break
                                else:
                                    amount -= b_line.available
                                    budget_line_links.append((0,0,{'budget_line_id':b_line.id,'account_move_line_id':line.id,'amount':b_line.available}))
                                    b_line.available = 0
                                    
                            elif b_month in (10, 11, 12) and b_s_month in (1,2,3,4,5,6,7, 8, 9,10, 11, 12):
                                control_assing_linefilter = control_assing_line.filtered(lambda x:x.start_date.month in (1,2,3,4,5,6,7, 8, 9,10,11,12) and x.available > 0).sorted(key='start_date')
                                if control_assing_linefilter and control_amount>0:
                                    if control_assing_linefilter[0].available >= control_amount:
                                        control_assing_linefilter[0].available -= control_amount
                                        control_amount = 0
                                    else:
                                        control_amount -= control_assing_linefilter[0].available
                                        control_assing_linefilter[0].available = 0
                                    
                                if b_line.available >= amount:
                                    b_line.available -= amount
                                    budget_line_links.append((0,0,{'budget_line_id':b_line.id,'account_move_line_id':line.id,'amount':amount}))
                                    break
                                else:
                                    amount -= b_line.available
                                    budget_line_links.append((0,0,{'budget_line_id':b_line.id,'account_move_line_id':line.id,'amount':b_line.available}))
                                    b_line.available = 0
                                    
            line.budget_line_link_ids = budget_line_links
    
    def action_budget_allocation(self):
        if self.move_ids and not self.move_id:
            #self.move_ids.write({'payment_state':'approved_payment','date_approval_request':datetime.today().date(),'is_from_reschedule_payment':False})
            qq = "UPDATE account_move set payment_state='approved_payment',date_approval_request=%s,is_from_reschedule_payment='f' where id in %s" 
            self.env.cr.execute(qq,(datetime.today().date(),tuple(self.move_ids.ids)))
            program_code_ids = self.move_ids.invoice_line_ids.mapped('program_code_id')
             
            all_budget_lines = self.env['expenditure.budget.line'].search_read([('program_code_id','in',program_code_ids.ids),
                                                             ('expenditure_budget_id.state', '=', 'validate'),
                                                             ],fields=['id','program_code_id'])
            
            all_control_lines = self.env['control.assigned.amounts.lines'].search_read([('program_code_id','in',program_code_ids.ids),
                                                             ('assigned_amount_id.budget_id.state', '=', 'validate'),
                                                             ('assigned_amount_id.state', '=', 'validated')
                                                             ],fields=['id','program_code_id'])
             
            all_budget_line_dict = {}
            all_control_line_dict = {}
            
            for b_line in all_budget_lines:
                program_id = b_line.get('program_code_id')[0]
                if all_budget_line_dict.get(program_id):
                    all_budget_line_dict.update({program_id:all_budget_line_dict.get(program_id)+[b_line.get('id')]})
                else:
                    all_budget_line_dict.update({program_id:[b_line.get('id')]})

            for c_line in all_control_lines:
                program_id = b_line.get('program_code_id')[0]
                if all_control_line_dict.get(program_id):
                    all_control_line_dict.update({program_id:all_control_line_dict.get(program_id)+[c_line.get('id')]})
                else:
                    all_control_line_dict.update({program_id:[c_line.get('id')]})

            budget_line_links_list = []                                            
            for move in self.move_ids:
                for line in move.invoice_line_ids.filtered(lambda x:x.program_code_id):
                    budget_line_links = []
                    if line.program_code_id and line.price_total != 0:
                        amount = 0
                        if line.debit:
                            amount = line.debit + line.tax_price_cr
                        else:
                            amount = line.credit + line.tax_price_cr

                        control_amount = 0
                        if line.debit:
                            control_amount = line.debit + line.tax_price_cr
                        else:
                            control_amount = line.credit + line.tax_price_cr
                        
                        
#                         budget_lines = self.env['expenditure.budget.line'].sudo().search(
#                             [('program_code_id', '=', line.program_code_id.id),
#                              ('expenditure_budget_id', '=', line.program_code_id.budget_id.id),
#                              ('expenditure_budget_id.state', '=', 'validate')])
                        budget_line_new = all_budget_line_dict.get(line.program_code_id.id,[])
                        budget_lines = self.env['expenditure.budget.line'].browse(budget_line_new) 
                        
                        if move.invoice_date and budget_lines:
                            b_month = move.invoice_date.month
                            for b_line in budget_lines:
#                                 control_assing_line = self.env['control.assigned.amounts.lines'].search(
#                                     [('program_code_id', '=', line.program_code_id.id),
#                                      ('assigned_amount_id.budget_id', '=', b_line.expenditure_budget_id.id),
#                                      ('assigned_amount_id.state', '=', 'validated')])
                                control_assing_line_new = all_control_line_dict.get(line.program_code_id.id,[])
                                control_assing_line = self.env['control.assigned.amounts.lines'].browse(control_assing_line_new)
                                
                                if b_line.start_date:
                                    b_s_month = b_line.start_date.month
                                    if b_month in (1, 2, 3) and b_s_month in (1, 2, 3):
                                        control_assing_linefilter = control_assing_line.filtered(lambda x:x.start_date.month in (1,2,3) and x.available > 0).sorted(key='start_date')
                                        if control_assing_linefilter and control_amount>0:
                                            if control_assing_linefilter[0].available >= control_amount:
                                                control_assing_linefilter[0].available -= control_amount
                                                control_amount = 0
                                            else:
                                                control_amount -= control_assing_linefilter[0].available
                                                control_assing_linefilter[0].available = 0

                                        if b_line.available >= amount:
                                            b_line.available -= amount
                                            budget_line_links_list.append((b_line.id,line.id,amount))
#                                             budget_line_links.append((0, 0, {'budget_line_id': b_line.id,
#                                                                              'account_move_line_id': line.id,
#                                                                              'amount': amount}))
                                            break
                                        elif b_line.available > 0:
                                            amount -= b_line.available
                                            budget_line_links_list.append((b_line.id,line.id,b_line.available))
#                                             budget_line_links.append((0, 0, {'budget_line_id': b_line.id,
#                                                                              'account_move_line_id': line.id,
#                                                                              'amount': b_line.available}))
                                            b_line.available = 0
                                            
                                    elif b_month in (4, 5, 6) and b_s_month in (1, 2, 3, 4, 5, 6):
                                        control_assing_linefilter = control_assing_line.filtered(lambda x:x.start_date.month in (1,2,3,4,5,6) and x.available > 0).sorted(key='start_date')
                                        if control_assing_linefilter and control_amount>0:
                                            if control_assing_linefilter[0].available >= control_amount:
                                                control_assing_linefilter[0].available -= control_amount
                                                control_amount = 0
                                            else:
                                                control_amount -= control_assing_linefilter[0].available
                                                control_assing_linefilter[0].available = 0

                                        if b_line.available >= amount:
                                            b_line.available -= amount
                                            budget_line_links_list.append((b_line.id,line.id,amount))
#                                             budget_line_links.append((0, 0, {'budget_line_id': b_line.id,
#                                                                              'account_move_line_id': line.id,
#                                                                              'amount': amount}))
                                            break
                                        elif b_line.available > 0:
                                            amount -= b_line.available
                                            budget_line_links_list.append((b_line.id,line.id,b_line.available))
#                                             budget_line_links.append((0, 0, {'budget_line_id': b_line.id,
#                                                                              'account_move_line_id': line.id,
#                                                                              'amount': b_line.available}))
                                            b_line.available = 0
                                            
                                    elif b_month in (7, 8, 9) and b_s_month in (1, 2, 3, 4, 5, 6, 7, 8, 9):
                                        control_assing_linefilter = control_assing_line.filtered(lambda x:x.start_date.month in (1,2,3,4,5,6,7, 8, 9) and x.available > 0).sorted(key='start_date')
                                        if control_assing_linefilter and control_amount>0:
                                            if control_assing_linefilter[0].available >= control_amount:
                                                control_assing_linefilter[0].available -= control_amount
                                                control_amount = 0
                                            else:
                                                control_amount -= control_assing_linefilter[0].available
                                                control_assing_linefilter[0].available = 0

                                        if b_line.available >= amount:
                                            b_line.available -= amount
                                            budget_line_links_list.append((b_line.id,line.id,amount))
#                                             budget_line_links.append((0, 0, {'budget_line_id': b_line.id,
#                                                                              'account_move_line_id': line.id,
#                                                                              'amount': amount}))
                                            break
                                        elif b_line.available > 0:
                                            amount -= b_line.available
                                            budget_line_links_list.append((b_line.id,line.id,b_line.available))
#                                             budget_line_links.append((0, 0, {'budget_line_id': b_line.id,
#                                                                              'account_move_line_id': line.id,
#                                                                              'amount': b_line.available}))
                                            b_line.available = 0
                                    elif b_month in (10, 11, 12) and b_s_month in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12):
                                        control_assing_linefilter = control_assing_line.filtered(lambda x:x.start_date.month in (1,2,3,4,5,6,7, 8, 9,10,11,12) and x.available > 0).sorted(key='start_date')
                                        if control_assing_linefilter and control_amount>0:
                                            if control_assing_linefilter[0].available >= control_amount:
                                                control_assing_linefilter[0].available -= control_amount
                                                control_amount = 0
                                            else:
                                                control_amount -= control_assing_linefilter[0].available
                                                control_assing_linefilter[0].available = 0

                                        if b_line.available >= amount:
                                            b_line.available -= amount
                                            budget_line_links_list.append((b_line.id,line.id,amount))
#                                             budget_line_links.append((0, 0, {'budget_line_id': b_line.id,
#                                                                              'account_move_line_id': line.id,
#                                                                              'amount': amount}))
                                            break
                                        elif b_line.available > 0:
                                            amount -= b_line.available
                                            budget_line_links_list.append((b_line.id,line.id,b_line.available))
#                                             budget_line_links.append((0, 0, {'budget_line_id': b_line.id,
#                                                                              'account_move_line_id': line.id,
#                                                                              'amount': b_line.available}))
                                            b_line.available = 0
                                            
                    #line.budget_line_link_ids = budget_line_links
            if budget_line_links_list:
                qq = "INSERT INTO budget_line_move_line_links(budget_line_id,account_move_line_id,amount) VALUES (%s,%s,%s)" 
                self.env.cr.executemany(qq,budget_line_links_list)
            self.move_ids.create_journal_line_for_approved_payment()
        else:
            self.move_id.payment_state = 'approved_payment'
            self.move_id.date_approval_request = datetime.today().date()
            self.move_id.is_from_reschedule_payment = False
            self.decrease_available_amount()
            self.move_id.create_journal_line_for_approved_payment()
        #self.move_id.action_post()
        return self.move_id.payment_state
