from datetime import datetime
from odoo.exceptions import ValidationError, UserError
from odoo import models, fields, api, _


class ReissueOfChecks(models.Model):
    _name = 'reissue.checks'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Reissue Of Checks'
    _rec_name = 'application_folio'
    
    @api.depends('check_log_id','check_log_id.date_protection','check_log_id.date_printing','type_of_batch')
    def _get_date_protection(self):
        for rec in self:
            date_protection = False
            if rec.check_log_id and rec.type_of_batch in ('nominal','pension'):
                date_protection = rec.check_log_id.date_printing
            if rec.check_log_id and rec.type_of_batch in ('supplier','project'):
                date_protection = rec.check_log_id.date_protection
             
            rec.date_protection = date_protection 
            
    application_folio = fields.Char('Application sheet')
    type_of_request = fields.Selection([('check_reissue','Check Reissue'),('check_cancellation','Check Cancellation')],
                                       string='Type of Request')
    # reissue_type = fields.Selection([('revocation','Revocación'),('reexped','Reexpedición o Reimpresión')],copy=False)
    type_of_request_payroll = fields.Selection(
        [('check_reissue', 'Check Reissue'), ('check_cancellation', 'Check Cancellation'),
         ('check_adjustments', 'Check Adjustments')], string='Type of Request')
    checkbook_req_id = fields.Many2one("checkbook.request", "Checkbook")
    check_log_id = fields.Many2one('check.log','Check Folio')
    check_log_ids = fields.Many2many('check.log','rel_reissue_check_log','log_id','reissue_id',compute="get_check_log_ids")
    
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.user.company_id.currency_id, string="Currency")
    check_amount = fields.Monetary(related='check_log_id.check_amount', currency_field='currency_id')
    status = fields.Selection(related='check_log_id.status')
    bank_id = fields.Many2one(related='check_log_id.bank_id')
    bank_account_id = fields.Many2one(related='check_log_id.bank_account_id')
    
    move_id = fields.Many2one('account.move','Payment request')
    folio_against_receipt = fields.Many2one('account.move','Folio against Receipt')
    folio_against_receipt_name = fields.Char(related='folio_against_receipt.folio',string='Folio')
   # move_ids = fields.Many2many('account.move','rel_reissue_account_move','move_id','reissue_id',compute="get_move_ids")
    
    reason_reissue = fields.Text("Reason for Reissue")
    reason_cancellation = fields.Text("Reason for Cancellation")
    reason_rejection = fields.Text("Reason for rejection")
    reason_adjustments = fields.Text("Reason for Adjustment")
    description_layout = fields.Text("Description for Layout")
    
    is_physical_check = fields.Boolean("Do you have the physical check?")
    observations = fields.Text("Observations")
    partner_id = fields.Many2one(related='move_id.partner_id',string='Beneficiary')
    general_status = fields.Selection(related='check_log_id.general_status')
    
    dependence_id = fields.Many2one(related='folio_against_receipt.dependancy_id')
    subdependence_id = fields.Many2one(related='folio_against_receipt.sub_dependancy_id')
    date_protection = fields.Date(compute=_get_date_protection,string="Expedition date",store=True)
    
    state = fields.Selection([('draft','Draft'),('request','Request'),('approved','Approved'),('rejected','Rejected')],default='draft',string='Status')
    type_of_batch = fields.Selection([('supplier','Supplier'),('project','Project'),
                                      ('nominal','Nominal'),('pension','Pension')],string="Type Of Batch")

    type_of_reissue_id = fields.Many2one('type.of.reissue','Reissue type')
    fornight = fields.Selection(related='move_id.fornight',string='Fornight')
    employee_number = fields.Char(string='Employee number',compute='get_employee_number')
    layout_generated = fields.Boolean(default=False, copy=False,string="Layout Generated")
    
    @api.onchange('type_of_request')
    def onchange_compute_type_of_request(self):
        for rec in self:
            if not rec.type_of_request:
                if rec.type_of_request_payroll == 'check_reissue':
                    rec.type_of_request = 'check_reissue'
                elif rec.type_of_request_payroll == 'check_cancellation':
                    rec.type_of_request = 'check_cancellation'

    def get_employee_number(self):
        for rec in self:
            emp_no = False
            if rec.partner_id:
                user_id = self.env['res.users'].search([('partner_id','=',rec.partner_id.id)],limit=1)
                if user_id:
                    emp_id = self.env['hr.employee'].search([('user_id','=',user_id.id)],limit=1)
                    if emp_id:
                        emp_no = emp_id.worker_number
            rec.employee_number = emp_no

    def unlink(self):
        for check in self:
            if check.state != 'draft':
                raise UserError(_('Cannot delete a record that has already been processed.'))
        return super(ReissueOfChecks, self).unlink()

              
    @api.onchange('move_id')
    def onchange_move_id(self):
        if self.move_id:
            self.folio_against_receipt = self.move_id.id
            if not self.check_log_id:
                self.check_log_id = self.move_id.check_folio_id and self.move_id.check_folio_id.id or False

    @api.onchange('folio_against_receipt')
    def onchange_folio_against_receipt(self):
        if self.folio_against_receipt:
            self.move_id = self.folio_against_receipt.id
            if not self.check_log_id:
                self.check_log_id = self.folio_against_receipt.check_folio_id and self.folio_against_receipt.check_folio_id.id or False

    @api.onchange('check_log_id')
    def onchange_check_log_id(self):
        if self.check_log_id:
            move_id = self.env['account.move'].search([('check_folio_id','=',self.check_log_id.id)],limit=1)
            if move_id:
                self.move_id = move_id.id
                self.folio_against_receipt = move_id.id
            else:
                move_id = self.env['account.move'].search([('related_check_folio_ids','in',self.check_log_id.id)],limit=1)
                if move_id:
                    self.move_id = move_id.id
                    self.folio_against_receipt = move_id.id
                
            self.checkbook_req_id = self.check_log_id.checklist_id and self.check_log_id.checklist_id.checkbook_req_id and self.check_log_id.checklist_id.checkbook_req_id.id or False 

#     @api.depends('type_of_request','type_of_request_payroll','type_of_batch')
#     def get_move_ids(self):                        
#         for rec in self:
#             move_list = []
#             domain = [('payment_state','in',('payment_method_cancelled','assigned_payment_method')),('type', '=', 'in_invoice')]
#             if rec.type_of_request_payroll == 'check_reissue':
#                 if rec.type_of_batch == 'nominal':
#                     domain.append(('check_status','in',()))
#             if domain:
#                 move_rec_ids = self.env['account.move'].search([domain])
#                 move_list = move_rec_ids.ids
#             rec.move_ids= [(6, 0, move_list)]
                
    @api.depends('type_of_request','checkbook_req_id', 'type_of_request_payroll')
    def get_check_log_ids(self):
        for rec in self:
            log_list = []
            if rec.type_of_request=='check_reissue':
                check_ids = self.env['check.log'].search([('status','in',('Delivered','Protected and in transit',
                                                                          'Cancelled'))])
                if rec.checkbook_req_id:
                    check_ids = check_ids.filtered(lambda x:x.checklist_id.checkbook_req_id.id==rec.checkbook_req_id.id)
                move_ids = self.env['account.move'].search(['|',('related_check_folio_ids','in',check_ids.ids),('check_folio_id','in',check_ids.ids),
                                    ('payment_state','in',('payment_method_cancelled','assigned_payment_method'))])
                
                if rec.type_of_batch == 'supplier':
                    move_ids = move_ids.filtered(lambda x:x.is_payment_request)
                elif rec.type_of_batch == 'project':
                    move_ids = move_ids.filtered(lambda x:x.is_project_payment)
                elif rec.type_of_batch == 'nominal':
                    move_ids = move_ids.filtered(lambda x:x.is_payroll_payment_request or x.is_different_payroll_request)
                elif rec.type_of_batch == 'pension':
                    move_ids = move_ids.filtered(lambda x:x.is_pension_payment_request)
                
                new_check_ids = move_ids.mapped('check_folio_id').filtered(lambda x:x.id in check_ids.ids)
                new_check_ids += move_ids.mapped('related_check_folio_ids').filtered(lambda x:x.id in check_ids.ids)
                    
                log_list = new_check_ids.ids
                
            elif rec.type_of_request_payroll == 'check_reissue':
                check_ids = self.env['check.log'].search([('status', 'in', ('In transit', 'Protected',
                                                                            'Cancelled'))])
                if rec.checkbook_req_id:
                    check_ids = check_ids.filtered(
                        lambda x: x.checklist_id.checkbook_req_id.id == rec.checkbook_req_id.id)
                move_ids = self.env['account.move'].search(['|',('related_check_folio_ids','in',check_ids.ids),('check_folio_id', 'in', check_ids.ids),
                                                            ('payment_state', 'in',
                                                             ('payment_method_cancelled', 'assigned_payment_method'))])
                if rec.type_of_batch == 'nominal':
                    move_ids = move_ids.filtered(
                        lambda x: x.is_payroll_payment_request or x.is_different_payroll_request)
                elif rec.type_of_batch == 'pension':
                    move_ids = move_ids.filtered(lambda x: x.is_pension_payment_request)

                new_check_ids = move_ids.mapped('check_folio_id').filtered(lambda x:x.id in check_ids.ids)
                new_check_ids += move_ids.mapped('related_check_folio_ids').filtered(lambda x:x.id in check_ids.ids)
                    
                log_list = new_check_ids.ids
                
            elif rec.type_of_request=='check_cancellation':
                check_ids = self.env['check.log'].search([('status','in',('Protected and in transit','Printed',
                                                                          'Detained','Withdrawn from circulation'))])
                if rec.checkbook_req_id:
                    check_ids = check_ids.filtered(lambda x:x.checklist_id.checkbook_req_id.id==rec.checkbook_req_id.id)
                    move_ids = self.env['account.move'].search([('check_folio_id','in',check_ids.ids)])
                    if rec.type_of_batch == 'supplier':
                        move_ids = move_ids.filtered(lambda x:x.is_payment_request)
                    elif rec.type_of_batch == 'project':
                        move_ids = move_ids.filtered(lambda x:x.is_project_payment)
                    elif rec.type_of_batch == 'nominal':
                        move_ids = move_ids.filtered(lambda x:x.is_payroll_payment_request or x.is_different_payroll_request)
                    elif rec.type_of_batch == 'pension':
                        move_ids = move_ids.filtered(lambda x: x.is_pension_payment_request)

                    check_ids = move_ids.mapped('check_folio_id')
                log_list = check_ids.ids
            elif rec.type_of_request_payroll == 'check_cancellation':
                check_ids = self.env['check.log'].search([('status', 'in', ('Protected', 'Printed',
                                                                        'Detained', 'Withdrawn from circulation'))])
                if rec.checkbook_req_id:
                    check_ids = check_ids.filtered(
                        lambda x: x.checklist_id.checkbook_req_id.id == rec.checkbook_req_id.id)
                    move_ids = self.env['account.move'].search([('check_folio_id', 'in', check_ids.ids)])
                    if rec.type_of_batch == 'nominal':
                        move_ids = move_ids.filtered(
                            lambda x: x.is_payroll_payment_request or x.is_different_payroll_request)
                    elif rec.type_of_batch == 'pension':
                        move_ids = move_ids.filtered(lambda x: x.is_pension_payment_request)

                    check_ids = move_ids.mapped('check_folio_id')
                log_list = check_ids.ids
            elif rec.type_of_request_payroll == 'check_adjustments':
                if rec.checkbook_req_id:
                    check_ids = self.env['check.log'].search([('status', '=', 'Printed')])
                    check_ids = check_ids.filtered(
                        lambda x: x.checklist_id.checkbook_req_id.id == rec.checkbook_req_id.id)
                    if self.type_of_batch == 'nominal':
                        move_ids = self.env['account.move'].search([('check_folio_id', 'in', check_ids.ids),
                                                                    '|', ('is_payroll_payment_request', '=', True),
                                                                    ('is_different_payroll_request', '=', True)])
                        check_ids = move_ids.mapped('check_folio_id')
                    elif self.type_of_batch == 'pension':
                        move_ids = self.env['account.move'].search([('check_folio_id', 'in', check_ids.ids),
                                                                    ('is_pension_payment_request', '=', True)])
                        check_ids = move_ids.mapped('check_folio_id')
                    log_list = check_ids.ids
            rec.check_log_ids= [(6, 0, log_list)]
                
    @api.model
    def create(self, vals):
        res = super(ReissueOfChecks, self).create(vals)
        application_no = self.env['ir.sequence'].next_by_code('reissue.check.folio')
        res.application_folio = application_no
        return res
    
    def action_mass_request(self):
        for rec in self:
            rec.action_request()
            
    def action_request(self):
        self.state = 'request'
        check_control_admin_group = self.env.ref('jt_check_controls.group_check_control_admin')
        finance_admin_group = self.env.ref('jt_finance.group_finance_admin')
        check_control_admin_users = check_control_admin_group.users
        finance_admin_users = finance_admin_group.users
        activity_type = self.env.ref('mail.mail_activity_data_todo').id
        summary = "Approve '" + self.application_folio + "' Request for changes to the check"
        if self.type_of_batch == 'supplier':
            summary += " (Suppliers)"
        elif self.type_of_batch == 'project':
            summary += " (Project)"
        elif self.type_of_batch == 'nominal':
            summary += " (Payroll)"
        elif self.type_of_batch == 'pension':
            summary += " (Pension Payment)"
        activity_obj = self.env['mail.activity']
        model_id = self.env['ir.model'].sudo().search([('model', '=', 'reissue.checks')]).id
        user_list = []
        # if self.type_of_reissue_id and self.type_of_reissue_id.name == 'Revocación':
        for user in check_control_admin_users:
            if user.id not  in user_list:
                activity_obj.create({'activity_type_id': activity_type,
                                   'res_model': 'reissue.checks', 'res_id': self.id,
                                   'res_model_id':model_id,
                                   'summary': summary, 'user_id': user.id})
                user_list.append(user.id)
        for user in finance_admin_users:
            if user.id not in user_list:
                activity_obj.create({'activity_type_id': activity_type,
                                   'res_model': 'reissue.checks', 'res_id': self.application_folio,
                                   'res_model_id':model_id,
                                   'summary': summary, 'user_id': user.id})
                user_list.append(user.id)

    def create_check_printing_reverse_entry(self):
        batch_line = self.env['check.payment.req'].search([('check_folio_id','=',self.check_log_id.id)],limit=1)
        if batch_line and batch_line.payment_batch_id:
            batch = batch_line.payment_batch_id
            journal = batch.get_check_printing_journal(batch.type_of_batch)
            if not journal.execercise_credit_account_id or not journal.conac_exe_credit_account_id \
                or not journal.execercise_debit_account_id or not journal.conac_exe_debit_account_id :
                raise ValidationError(_("Please configure UNAM and CONAC Exercised account in %s journal!" %
                                      journal.name))
    
            today = datetime.today().date()
            user = self.env.user
            partner_id = user.partner_id.id
            name = "Payment Batch "+str(batch.type_of_batch)+" "+str(batch.batch_folio)
            move_lines = []
            for line in batch_line:
                amount = line.amount_to_pay
                line_name = line.check_folio_id and line.check_folio_id.folio_ch or ''
                move_lines.append((0,0,{
                                 'account_id': journal.execercise_credit_account_id.id,
                                 'coa_conac_id': journal.conac_exe_credit_account_id.id,
                                 'debit': amount,
                                 'partner_id': partner_id,
                                 'payment_batch_check_id' : batch.id,
                                 'check_payment_req_id' : line.id,
                                 'name' : line_name,
                    }))
                move_lines.append((0,0,{
                                 'account_id': journal.execercise_debit_account_id.id,
                                 'coa_conac_id': journal.conac_exe_debit_account_id.id,
                                 'credit': amount,
                                 'partner_id': partner_id,
                                 'payment_batch_check_id' : batch.id,
                                 'check_payment_req_id' : line.id,
                                 'name' : line_name,
                    }))
                
            unam_move_val = { 'ref': name,  'conac_move': True,
                             'date': today, 'journal_id': journal.id, 'company_id': self.env.user.company_id.id,
                             'payment_batch_check_id' : batch.id,
                             'line_ids': move_lines}
            move_obj = self.env['account.move']
            unam_move = move_obj.create(unam_move_val)
            unam_move.action_post()

    def create_check_protection_reverse_entry(self):
        batch_line = self.env['check.payment.req'].search([('check_folio_id','=',self.check_log_id.id)],limit=1)
        if batch_line and batch_line.payment_batch_id:
            batch = batch_line.payment_batch_id
            journal = batch.get_check_protection_journal(batch.type_of_batch)
            if not journal.paid_credit_account_id or not journal.conac_paid_credit_account_id \
                or not journal.paid_debit_account_id or not journal.conac_paid_debit_account_id :
                raise ValidationError(_("Please configure UNAM and CONAC Paid account in %s journal!" %
                                      journal.name))
    
            today = datetime.today().date()
            user = self.env.user
            partner_id = user.partner_id.id
            name = "Payment Batch "+str(batch.type_of_batch)+" "+str(batch.batch_folio)
            move_lines = []
            for line in batch_line:
                amount = line.amount_to_pay
                line_name = line.check_folio_id and line.check_folio_id.folio_ch or ''
                move_lines.append((0,0,{
                                 'account_id': journal.paid_credit_account_id.id,
                                 'coa_conac_id': journal.conac_paid_credit_account_id.id,
                                 'debit': amount,
                                 'partner_id': partner_id,
                                 'payment_batch_check_id' : batch.id,
                                 'check_payment_req_id' : line.id,
                                 'name' : line_name,
                    }))
                move_lines.append((0,0,{
                                 'account_id': journal.paid_debit_account_id.id,
                                 'coa_conac_id': journal.conac_paid_debit_account_id.id,
                                 'credit': amount,
                                 'partner_id': partner_id,
                                 'payment_batch_check_id' : batch.id,
                                 'check_payment_req_id' : line.id,
                                 'name' : line_name,
                    }))
                
            unam_move_val = { 'ref': name,  'conac_move': True,
                             'date': today, 'journal_id': journal.id, 'company_id': self.env.user.company_id.id,
                             'payment_batch_check_id' : batch.id,
                             'line_ids': move_lines}
            move_obj = self.env['account.move']
            unam_move = move_obj.create(unam_move_val)
            unam_move.action_post()
            
    def action_mass_approve(self):
        for rec in self:
            rec.action_approve()
            
    def action_approve(self):
        self.state = 'approved'
        if self.check_log_id:
            check_status = self.check_log_id.status 
            self.check_log_id.status = 'Reissued'
            moves = self.env['account.move'].search([('check_folio_id', '=', self.check_log_id.id)])
            for move in moves:
                payment_ids = self.env['account.payment'].search([('payment_state', '=', 'for_payment_procedure'),
                                                                  ('payment_request_id', '=', move.id)])
                for payment in payment_ids:
                    payment.cancel()
                move.payment_state = 'payment_method_cancelled'
            self.create_check_printing_reverse_entry()
            if check_status!='Printed':
                self.create_check_protection_reverse_entry()
            
        if self.check_log_id and (self.type_of_request=='check_cancellation' or
                                  self.type_of_request_payroll=='check_cancellation'):
            self.check_log_id.status = 'Cancelled'
            self.check_log_id.date_cancellation = datetime.now().today()
            self.check_log_id.reason_cancellation = self.reason_cancellation
            
        if self.check_log_id and self.type_of_request_payroll=='check_adjustments':
            self.check_log_id.status = 'Detained'
            self.check_log_id.general_status = 'cancelled'
            self.check_log_id.reason_retention = self.reason_adjustments
        
        if self.check_log_id:
            moves = self.env['account.move'].search([('check_folio_id', '=', self.check_log_id.id)])
            if moves:
                for move in moves:
                    move.cancel_payment_method()
    def action_mass_reject(self):
        return {
            'name': _('Reject Reason'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'reissue.reject.reason.wizard',
            'domain': [],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': self.env.context,
        }
                    
    def action_reject(self):
        return {
            'name': _('Reject Reason'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'reissue.reject.reason.wizard',
            'domain': [],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_reissue_checks_id': self.id},
        }
    def action_set_reject(self):
        self.state = 'rejected'

    def action_layout_check_cancel(self):
        layout = False
        bank_ids = self.mapped('bank_id.bank_id')
        if bank_ids and len(bank_ids) > 1:
            raise ValidationError(_('Please select same bank for layout'))
        if self:
            if self[0].bank_id and self[0].bank_id.bank_id and self[0].bank_id.bank_id.name:
                if self[0].bank_id.bank_id.name.upper() == 'Banamex'.upper():
                    layout = 'Banamex'
                elif self[0].bank_id.bank_id.name.upper() == 'BBVA Bancomer'.upper():
                    layout = 'BBVA Bancomer'
                elif self[0].bank_id.bank_id.name.upper() == 'Scotiabank'.upper():
                    layout = 'Scotiabank'
                    
        return {
            'name': _('Generate Cancel Check Layout'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'generate.cancel.check.layout',
            'domain': [],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_reissue_ids': [(6,0,self.ids)],'default_layout':layout},
        }

    def action_request_attach_file(self):
        return {
            'name': _('Attach File'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'reissue.check.attach.file',
            'domain': [],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context':self.env.context,
        }

class ReissueCheckAttachFile(models.TransientModel):
    
    _name = 'reissue.check.attach.file'
    
    file_data= fields.Binary(string='Attachment For Check Cancellation')
    file_name = fields.Char('Attachment For Check Cancellation')
    
    def action_attach(self):
        if self.env.context and self.env.context.get('active_ids'):
            check_ids = self.env['reissue.checks'].browse(self.env.context.get('active_ids',[]))
            for batch in check_ids: 
                atc_create = self.env['ir.attachment'].create({'datas':self.file_data,'name':self.file_name,'type':'binary','res_model':'reissue.checks','res_id':batch.id})


class Dependency(models.Model):
    _inherit = 'dependency'

    def name_get(self):
        result = []
        for rec in self:
            name = rec.dependency or ''
            if rec.description:
                name += ' ' + rec.description
            result.append((rec.id, name))

        return result


class SubDependency(models.Model):
    _inherit = 'sub.dependency'

    def name_get(self):
        result = []
        for rec in self:
            name = rec.sub_dependency or ''
            if rec.description:
                name += ' ' + rec.description
            result.append((rec.id, name))
        return result
