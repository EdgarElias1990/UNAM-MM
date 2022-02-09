from odoo import models, fields, api, _

class MinimumCheck(models.Model):

    _name = 'minimum.checks'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Minimum of Checks"
    _rec_name = 'bank_id'

    checkbook_no = fields.Char("Checkbook")
    bank_id = fields.Many2one('account.journal', "Bank")
    bank_account_id = fields.Many2one("res.partner.bank", string="Bank Account")
    minimum_of_checks = fields.Integer("Mimimum of Checks")
    reorder_point = fields.Integer("Reorder Point")
    stock_checkbook_registration = fields.Integer("Checks in stock Check book registration", compute='_compute_checkbook_reg')
    stock_available_for_printing = fields.Integer("Checks in stock Available for printing", compute='_compute_available_for_printing')

    @api.onchange('bank_id')
    def onchange_bank_id(self):
        if self.bank_id and self.bank_id.bank_account_id:
            self.bank_account_id = self.bank_id.bank_account_id.id
            self.checkbook_no = self.bank_id.checkbook_no
        else:
            self.bank_account_id = False
            self.checkbook_no = False

    def min_checks_validation(self):
        min_checks = self.env['minimum.checks'].search([])
        check_log_obj = self.env['check.log']
        activity_obj = self.env['mail.activity']
        check_control_admin_group = self.env.ref('jt_check_controls.group_check_control_admin')
        check_control_admin_users = check_control_admin_group.users
        for check in min_checks:
            if check.bank_id:
                check_logs = check_log_obj.search([('bank_id', '=', check.bank_id.id),
                                                   ('status','=','Available for printing')])
                if len(check_logs) < check.reorder_point:
                    for user in check_control_admin_users:
                        activity_obj.create({
                            'activity_type_id': self.env.ref('jt_check_controls.mail_act_mininum_of_checks').id,
                            'summary': _('Ha llegado al punto de reorden'),
                            'res_id': check.id,
                            'user_id': user.id,
                            'res_model_id': self.env.ref('jt_check_controls.model_minimum_checks').id,
                        })
                if len(check_logs) < check.minimum_of_checks:
                    for user in check_control_admin_users:
                        activity_obj.create({
                            'activity_type_id': self.env.ref('jt_check_controls.mail_act_mininum_of_checks').id,
                            'summary': _('Ha llegado al límite de cheques ingresado para la chequera'),
                            'res_id': check.id,
                            'user_id': user.id,
                            'res_model_id': self.env.ref('jt_check_controls.model_minimum_checks').id,
                        })

    def _compute_checkbook_reg(self):
        check_log_obj = self.env['check.log']
        for check in self:
            stock_checkbook_registration = 0
            check_logs = check_log_obj.search_count([('bank_account_id', '=', check.bank_account_id.id),
                                                   ('status','=','Checkbook registration')])
            check.stock_checkbook_registration = check_logs

    def _compute_available_for_printing(self):
        check_log_obj = self.env['check.log']
        for check in self:
            stock_available_for_printing = 0
            check_logs = check_log_obj.search_count([('bank_account_id', '=', check.bank_account_id.id),
                                                   ('status','=','Available for printing')])
            check.stock_available_for_printing = check_logs
                
