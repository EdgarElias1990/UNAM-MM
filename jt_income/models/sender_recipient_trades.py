from odoo import models, fields, api

class SenderRecipientTrades(models.Model):

    _name = 'sender.recipient.trades'
    _description = "Sender Recipient Trades"
    _rec_name = 'template'
    
    template = fields.Selection([('application_form_20','Application form 20%'),
                                 ('format_forgiveness','Format Forgiveness'),
                                 ('format_notice_change','Format notice change form of payment to transfer'),
                                 ('2nd application_form_20','2nd Application form 20%'),
                                 ('format_remission_20','Format remission 20%'),
                                 ('reporting_format_returned_check','Reporting format returned check'),
                                 ],string="Template")
    
    
    recipient_emp_id = fields.Many2one('hr.employee','Employee')
    recipient_title = fields.Char(related="recipient_emp_id.emp_title",string='Title')
    recipient_professional_title = fields.Char(related="recipient_emp_id.emp_job_title",string='Professional Title')

    sender_emp_id = fields.Many2one('hr.employee','Employee')
    sender_title = fields.Char(related="sender_emp_id.emp_title",string='Title')
    sender_professional_title = fields.Char(related="sender_emp_id.emp_job_title",string='Professional Title')
    
    employee_ids = fields.Many2many('hr.employee','rel_employee_sender_recipient_trades','sender_id','emp_id','EMPLOYEES COPIED')
    
    def name_get(self):
        result = []
        for rec in self:
            name = rec.template or ''
            if rec.template: 
                name = dict(rec._fields['template'].selection).get(rec.template)
                if self.env.user.lang == 'es_MX':
                    if name=='Application form 20%':
                        name = 'Formato de aplicación 20%'
                    elif name=='Format Forgiveness':
                        name = 'Formato de condonación'
                    elif name=='Format notice change form of payment to transfer':
                        name = 'Formato de aviso cambio forma de cobro a transferencia'
                    elif name=='2nd Application form 20%':
                        name = '2° formato de aplicación 20%'
                    elif name=='Format remission 20%':
                        name = 'Formato de condonación 20%'
                    elif name=='Reporting format returned check':
                        name = 'Formato de notificación de cheque devuelto'
                        
            result.append((rec.id, name))
        return result        