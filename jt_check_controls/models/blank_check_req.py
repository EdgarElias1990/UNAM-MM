from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError, UserError



class BlankCheckRequest(models.Model):

    _name = 'blank.checks.request'
    _description = "Blank Check Requests"
    _rec_name = "application_no"

    application_no = fields.Char("Application No")
    dependence_id = fields.Many2one('dependency', "Dependence")
    subdependence_id = fields.Many2one('sub.dependency', "Subdependence")
    amount_checks = fields.Integer("Amount of Checks")
    reason_request = fields.Text("Reason for Request")
    applicant_id = fields.Many2one(
        'res.users', default=lambda self: self.env.user.id)
    are_test_prin_formats_sent = fields.Boolean("Are test print formats sent?")
    area = fields.Char("Area")
    number_of_folios = fields.Integer("Number of Folios")
    print_sample_folio_number = fields.Integer("Print Sample Folio Number")
    delivery_of_checks = fields.Binary(
        "Office of delivery of checks to dependency")
    # check_request = fields.Binary("Check Request")
    state = fields.Selection([('draft', 'Draft'), ('requested', 'Requested'),
                              ('approved', 'Approved'),
                              ('confirmed', 'Confirmed'),
                              ('rejected', 'Rejected'), ('cancelled', 'Cancelled')
                              ], string="Status", default='draft')

    department = fields.Selection([('General Directorate of Personnel', 'General Directorate of Personnel'),
                                   ('Payment coordination',
                                    'Payment coordination'),
                                   ('Financial transaction',
                                    'Financial transaction'),
                                   ('ACATLAN', 'ACATLAN'),
                                   ('ARAGON', 'ARAGON'),
                                   ('CUAUTITLAN', 'CUAUTITLAN'),
                                   ('CUERNAVACA', 'CUERNAVACA'), ('COVE', 'COVE'),
                                   ('IZTACALA', 'IZTACALA'), ('JURIQUILLA',
                                                              'JURIQUILLA'),
                                   ('LION', 'LION'), ('MORELIA', 'MORELIA'), ('YUCATAN', 'YUCATAN')])
    bank_account_id = fields.Many2one('account.journal', "Bank Account")
    checkbook_req_id = fields.Many2one('checkbook.request', "Checkbook no")
    number_of_checks_auth = fields.Integer("Number of checks authorized")
    intial_folio = fields.Integer("Intial Folio")
    final_folio = fields.Integer("Final Folio")
    distribution_of_module_ids = fields.One2many(
        'check.distribution.modules', 'request_id')
    log_ids = fields.Many2many('check.log', string="Logs", copy=False)
    is_process_done = fields.Boolean("Is Process Done",copy=False,default=False)
    
    @api.model
    def create(self, vals):
        res = super(BlankCheckRequest, self).create(vals)
        application_no = self.env['ir.sequence'].next_by_code(
            'blank.check.application')
        year = datetime.today().year
        res.application_no = "DIOF / CTRLCHEQ / " + \
            str(application_no) + "/" + str(year)
        return res

    def unlink(self):
        for check_req in self:
            if check_req.state != 'draft':
                raise UserError(_('Cannot delete a record that has already been processed.'))
        return super(BlankCheckRequest, self).unlink()


    @api.constrains('amount_checks')
    def _check_amount_checks(self):
        if self.dependence_id and self.subdependence_id:
            auth = self.env['check.authorized.dependency'].search([('dependency_id', '=', self.dependence_id.id),
                                                                   ('subdependency_id', '=', self.subdependence_id.id)], limit=1)
            if auth and self.amount_checks > auth.checks_remaining_to_auth:
                raise ValidationError(
                    _('Value of Amount of checks does not more than authorized.'))

    @api.constrains('dependence_id', 'subdependence_id')
    def _check_dependence_checks(self):
        if self.dependence_id and self.subdependence_id:
            auth = self.env['check.authorized.dependency'].search([('dependency_id', '=', self.dependence_id.id),
                                                                   ('subdependency_id', '=', self.subdependence_id.id)], limit=1)
            if not auth:
                if self.env.user.lang == 'es_MX':
                    raise ValidationError(
                        _('La dependencia no está autorizada para solicitar cheques'))                    
                else:
                    raise ValidationError(
                        _('The dependency is not authorized to request checks'))

    def action_request(self):
        self.ensure_one()
        self.state = 'requested'

    def get_date(self):
        today = datetime.today().date()
        day = today.day
        month = today.month
        month_name = ''
        if month == 1:
            month_name = 'Enero'
        elif month == 2:
            month_name = 'Febrero'
        elif month == 3:
            month_name = 'Marzo'
        elif month == 4:
            month_name = 'Abril'
        elif month == 5:
            month_name = 'Mayo'
        elif month == 6:
            month_name = 'Junio'
        elif month == 7:
            month_name = 'Julio'
        elif month == 8:
            month_name = 'Agosto'
        elif month == 9:
            month_name = 'Septiembre'
        elif month == 10:
            month_name = 'Octubre'
        elif month == 11:
            month_name = 'Noviembre'
        elif month == 12:
            month_name = 'Diciembre'
        year = today.year
        return str(day) + ' de ' + month_name + ' de ' + str(year)

    def get_trade_configuration(self):
        trade = self.env['trades.config'].search(
            [('job_template', '=', 'check_delivery_document')], limit=1)
        return trade

    def action_reject(self):
        self.ensure_one()
        self.state = 'rejected'

    def action_approve(self):
        self.ensure_one()
        return {
            'name': _('Check Authorization'),
            'type': 'ir.actions.act_window',
            'res_model': 'approve.blank.check',
            'view_mode': 'form',
            'target': 'new',
            'context': {'from_approve_check': 1}
        }

    def action_confirm(self):
        self.ensure_one()
        self.state = 'confirmed'
        check_logs = self.env['check.log'].search([('checklist_id.checkbook_req_id', '=', self.checkbook_req_id.id),
                                                   ('folio', '>=',
                                                    self.intial_folio),
                                                   ('folio', '<=', self.final_folio)])
        check_logs.write({'module':self.department})
        
        check_log = self.env['check.log'].search([('checklist_id.checkbook_req_id', '=', self.checkbook_req_id.id),
                                                  ('folio', '=', self.print_sample_folio_number)])
        if check_log:
            check_log.status = 'Cancelled'
            check_log.module = self.department
            
    def change_status_suthorized_checks(self):
        for rec in self:
            if rec.state == 'confirmed':
                if rec.is_process_done:
                    raise ValidationError(_("The status change of this request has already been processed"))
                check_logs = self.env['check.log'].search(
                    [('checklist_id.checkbook_req_id', '=', self.checkbook_req_id.id),
                     ('folio', '>=', self.intial_folio),
                     ('folio', '!=', self.print_sample_folio_number),
                     ('folio', '!=', int(self.checkbook_req_id.print_sample_folio_number)),
                     ('folio', '<=', self.final_folio)])
                check_logs.write({'status':'Available for printing'})
                rec.is_process_done = True
        self.env.user.notify_success(message=_('The checks in this application have been changed to Available for printing status successfully.'),sticky=True)
        
    def action_apply_distribution(self):
        self.ensure_one()
        log_ids = self.log_ids.ids if self.log_ids else []
        check_log_obj = self.env['check.log']
        if log_ids:
            for line in self.distribution_of_module_ids:
                check_logs = check_log_obj.search(
                    [('checklist_id.checkbook_req_id', '=', self.checkbook_req_id.id),
                     ('folio', '>=', line.intial_filio.folio),
                     ('folio', '<=', line.final_folio.folio)])
                for log in check_logs:
                    log_ids.remove(log.id)
        return {
            'name': _('Apply Distribution'),
            'view_mode': 'form',
            'view_id': self.env.ref('jt_check_controls.apply_distribution_form').id,
            'res_model': 'apply.distribution.modules',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'log_ids': log_ids,
                        'default_checkbook_req_id': self.checkbook_req_id.id if self.checkbook_req_id else False}
        }

class DistributionModules(models.Model):
    _name = 'check.distribution.modules'
    _description = "Distribution Of modules"

    request_id = fields.Many2one('blank.checks.request')
    checkbook_req_id = fields.Many2one(
        'checkbook.request', related='request_id.checkbook_req_id', store=True)
    module = fields.Selection([('ACATLAN', 'ACATLAN'),
                               ('ARAGON', 'ARAGON'), ('CUAUTITLAN', 'CUAUTITLAN'),
                               ('CUERNAVACA', 'CUERNAVACA'),
                               ('COVE', 'COVE'), ('IZTACALA', 'IZTACALA'),
                               ('JURIQUILLA', 'JURIQUILLA'), ('LION', 'LION'),
                               ('MORELIA', 'MORELIA'), ('YUCATAN', 'YUCATAN')], string="Module")
    intial_filio = fields.Many2one('check.log', "Intial Folio")
    final_folio = fields.Many2one('check.log', "Final Folio")
    amounts_of_checks = fields.Integer("Amounts of Checks")