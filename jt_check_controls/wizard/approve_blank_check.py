from odoo import fields, models, api,_
from odoo.exceptions import ValidationError, UserError

class ApproveBlankCheck(models.TransientModel):
    _name = 'approve.blank.check'
    _description = 'Approve Blank Check'

    department = fields.Selection([('General Directorate of Personnel', 'General Directorate of Personnel'),
                                   ('Payment coordination', 'Payment coordination'),
                                   ('Financial transaction', 'Financial transaction'),
                                   ('ACATLAN', 'ACATLAN'),
                                   ('ARAGON', 'ARAGON'),
                                   ('CUAUTITLAN', 'CUAUTITLAN'),
                                   ('CUERNAVACA','CUERNAVACA'),('COVE','COVE'),
                                   ('IZTACALA','IZTACALA'),('JURIQUILLA', 'JURIQUILLA'),
                                   ('LION', 'LION'),('MORELIA','MORELIA'),('YUCATAN','YUCATAN')])
    bank_account_id = fields.Many2one('account.journal', "Bank Account")
    checkbook_req_id = fields.Many2one("checkbook.request", "Checkbook No")
    number_of_checks_auth = fields.Integer("Number of checks authorized")
    checkbook_no = fields.Char(related='checkbook_req_id.checkbook_no')
    intial_folio = fields.Integer("Intial Folio")
    final_folio = fields.Integer("Final Folio")

#     @api.constrains('intial_folio', 'final_folio')
#     def _check_amount(self):
#         if ((self.final_folio - self.intial_folio) + 1) != self.number_of_checks_auth:
#             raise ValidationError(_('The folios registered do not match the number of checks authorized'))

    @api.onchange('bank_account_id')
    def onchange_bank_account_id(self):
        if self.bank_account_id:
            self.checkbook_no = self.bank_account_id.checkbook_no

    def apply(self):
        check_req = self.env['blank.checks.request'].browse(self._context.get('active_id'))
        if check_req:
            amount_checks = check_req.amount_checks
            if amount_checks < self.number_of_checks_auth:
                raise ValidationError(_('The total amount of checks authorized cannot be greater than the total amount of checks requested.'))

            if ((self.final_folio - self.intial_folio) + 1) != self.number_of_checks_auth:
                raise ValidationError(_('The folios registered do not match the number of checks authorized'))
            
            check_req.department = self.department
            check_req.bank_account_id = self.bank_account_id.id
            check_req.checkbook_req_id = self.checkbook_req_id.id
            check_req.number_of_checks_auth = self.number_of_checks_auth
            check_req.intial_folio = self.intial_folio
            check_req.final_folio = self.final_folio
            check_req.state = 'approved'
            check_logs = self.env['check.log'].search([('checklist_id.checkbook_req_id', '=', self.checkbook_req_id.id),
                                                ('folio', '>=', self.intial_folio),
                                                ('folio', '!=', int(self.checkbook_req_id.print_sample_folio_number)),
                                                ('folio', '<=', self.final_folio)])
            if not check_logs:
                raise ValidationError(_('The folios entered are not registered or are not available within the indicated checkbook, please verify.'))
            
            check_vals = {'status':'Assigned for shipping',
                          'dependence_id' : check_req.dependence_id and check_req.dependence_id.id or False,
                          'subdependence_id' : check_req.subdependence_id and check_req.subdependence_id.id or False,
                          
                          }
            check_logs.write(check_vals)
            check_req.log_ids = [(6, 0, check_logs.ids)]
            
#             for log in check_logs:
#                 log.status = 'Assigned for shipping'
#                 log.dependence_id = check_req.dependence_id and check_req.dependence_id.id or False
#                 log.subdependence_id = check_req.subdependence_id and check_req.subdependence_id.id or False
#                 check_req.log_ids = [(4, log.id)]
