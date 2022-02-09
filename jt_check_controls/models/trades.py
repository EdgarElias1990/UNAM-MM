from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class Trades(models.Model):

    _name = 'trades.config'
    _description = "Configuration of Trades"
    _rec_name = 'job_template'

    job_template = fields.Selection([('check_req_1', 'Check Request 1'),
                                     ('check_req_2', 'Check Request 2'),
                                     ('register_checks', 'Register Checks'),
                                     ('payroll_payment_notice', 'Payroll Payment Notice'),
                                     ('check_delivery_document', 'Check Delivery Document')], 'Job Template')
    general_director_id = fields.Many2one("hr.employee", "Employee")
    general_director_title = fields.Char('Title', related='general_director_id.emp_title')
    general_director_job_tile = fields.Char("Job Title", related='general_director_id.emp_job_title')
    revenue_dirctor_id = fields.Many2one("hr.employee", "Employee")
    revenue_director_title = fields.Char("Title", related='revenue_dirctor_id.emp_title')
    revenue_director_job_title = fields.Char("Job Title", related='revenue_dirctor_id.emp_job_title')
    copied_employee_ids = fields.One2many('copied.employees', 'trade_config_id', string="Copied Employees")
    clerk_id = fields.Many2one('hr.employee', string="Clerk Collecting Checkbooks")
    clerk_title = fields.Char("Title", related='clerk_id.emp_title')

    @api.model
    def create(self, vals):
        trade = self.search([('job_template', '=', vals.get('job_template'))])
        if trade:
            raise ValidationError(_('Only one record have this option!'))
        return super(Trades, self).create(vals)

    def write(self, vals):
        res = super(Trades, self).write(vals)
        if vals.get('job_template'):
            for trade_rec in self:
                trade = self.search([('job_template', '=', vals.get('job_template')),
                                     ('id', '!=', trade_rec.id)])
                if trade:
                    raise ValidationError(_('Only one record have this option!'))
        return res


class CopiedEmployees(models.Model):

    _name = 'copied.employees'
    _description = "Copied Employees"

    trade_config_id = fields.Many2one('trades.config')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    title = fields.Char('Title', related='employee_id.emp_title')
    job_title = fields.Char('Job Title', related='employee_id.emp_job_title')