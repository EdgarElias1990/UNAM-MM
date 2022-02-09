from datetime import datetime
from odoo.exceptions import ValidationError, UserError
from odoo import models, fields, api, _


class CancelChecks(models.Model):
    _name = 'cancel.checks'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'check_folio'
    _description = "Cancel Checks"

    check_folio = fields.Integer(string="Check Folio")
    check_log_id = fields.Many2one('check.log')
    check_status = fields.Selection([('Checkbook registration', 'Checkbook registration'),
                                     ('Assigned for shipping', 'Assigned for shipping'),
                                     ('Available for printing', 'Available for printing'),
                                     ('Printed', 'Printed'), ('Delivered', 'Delivered'),
                                     ('In transit', 'In transit'), ('Sent to protection', 'Sent to protection'),
                                     ('Protected and in transit', 'Protected and in transit'),
                                     ('Protected', 'Protected'), ('Detained', 'Detained'),
                                     ('Withdrawn from circulation', 'Withdrawn from circulation'),
                                     ('Cancelled', 'Cancelled'),
                                     ('Canceled in custody of Finance', 'Canceled in custody of Finance'),
                                     ('On file', 'On file'), ('Destroyed', 'Destroyed'),
                                     ('Reissued', 'Reissued'), ('Charged', 'Charged')], related='check_log_id.status',
                                    store=True, string='Check Status')
    dependency_id = fields.Many2one('dependency', string="Dependency")
    bank_id = fields.Many2one('account.journal', string="Bank")
    bank_account_id = fields.Many2one('res.partner.bank', string="Bank Account")
    checkbook_no = fields.Char(string="Checkbook")
    observation = fields.Char(string="Observation")
    status = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'), ('rejected', 'Rejected')
    ], default='draft', string="Status")
    batch_folio = fields.Integer(string="Batch Folio")

    def action_reject(self):
        self.ensure_one()
        self.status = 'rejected'

    def unlink(self):
        for check in self:
            if check.status != 'draft':
                raise UserError(_('Cannot delete a record that has already been processed.'))
        return super(CancelChecks, self).unlink()


    def action_approve(self):
        self.ensure_one()
        attachment = self.env['ir.attachment'].search([('res_model', '=', 'cancel.checks'), ('res_id', '=', self.id)])
        if attachment:
            self.status = 'approved'
            if self.check_log_id:
                self.check_log_id.status = 'Canceled in custody of Finance'
                self.check_status = 'Canceled in custody of Finance'
        else:
            raise ValidationError(_('It is necessary to attach the corresponding document.'))

    def action_mass_approve(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return ''

        active_records = self.browse(active_ids)
        for rec in active_records.filtered(lambda x:x.status=='draft'):
            rec.action_approve()
            
             
    def action_generate_batch_folio(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return ''

        active_records = self.browse(active_ids)
        if active_records and active_records.filtered(lambda x:not x.batch_folio):
            folio = self.env['ir.sequence'].next_by_code('batch.folio')
            for rec in active_records.filtered(lambda x:not x.batch_folio):
                if rec.check_status == 'Canceled in custody of Finance':
                    rec.batch_folio = folio

    def action_request_send_checks(self):
        send_checks = self.env['send.checks']
        batch_folio_dict = {}
        for rec in self:
            if rec.batch_folio:
                if rec.batch_folio in batch_folio_dict.keys():
                    batch_folio_dict.update({
                        rec.batch_folio: batch_folio_dict.get(rec.batch_folio) + [rec]
                    })
                else:
                    batch_folio_dict.update({rec.batch_folio: [rec]})

        for folio, recs in batch_folio_dict.items():
            lines_vals = []
            for line in recs:
                lines_vals.append({
                    'check_log_id': line.check_log_id.id if line.check_log_id else False,
                    'dependency_id': line.dependency_id.id if line.dependency_id else False,
                })
            send_checks.create({
                'batch_folio': folio,
                'total_checks': len(recs),
                'date': datetime.today().date(),
                'check_line_ids': [(0, 0, val) for val in lines_vals]
            })
    def action_request_attach_file(self):
        return {
            'name': _('Attach Supporting File'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'cancel.check.attach.file',
            'domain': [],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context':self.env.context,
        }
        


class CancelCheckAttachFile(models.TransientModel):
    
    _name = 'cancel.check.attach.file'
    
    file_data= fields.Binary(string='Please attach the verification file')
    file_name = fields.Char('Please attach the verification file')
    
    def action_attach(self):
        if self.env.context and self.env.context.get('active_ids'):
            cancel_check_ids = self.env['cancel.checks'].browse(self.env.context.get('active_ids',[]))
            for check in cancel_check_ids: 
                atc_create = self.env['ir.attachment'].create({'datas':self.file_data,'name':self.file_name,'type':'binary','res_model':'cancel.checks','res_id':check.id})
        
    

        