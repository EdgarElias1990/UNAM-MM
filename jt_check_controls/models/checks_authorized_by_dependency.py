from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class CheckAuthorizedByDependency(models.Model):

    _name = 'check.authorized.dependency'
    _description = "Check Authorized By Dependency"
    _rec_name = 'dependency_id'

    dependency_id = fields.Many2one('dependency', string="Dependence")
    subdependency_id = fields.Many2one('sub.dependency', string="Subdependence")
    area = fields.Char("Area")
    max_authorized_checks = fields.Integer("Maximum authorized checks")
    checks_authorized_on_previous_app = fields.Integer("Checks authorized on previous applications",
                                                       compute='_compute_checks')
    checks_remaining_to_auth = fields.Integer("Checks remaining to authorize", compute='_compute_checks')

    def _compute_checks(self):
        check_req_obj = self.env['blank.checks.request']
        for rec in self:
            if rec.dependency_id and rec.subdependency_id:
                check_reqs = check_req_obj.search([('dependence_id', '=', rec.dependency_id.id),
                                                   ('subdependence_id', '=', rec.subdependency_id.id),
                                                                   ('state', '=', 'confirmed')])
                rec.checks_authorized_on_previous_app = sum(x.amount_checks for x in check_reqs)
                rec.checks_remaining_to_auth = rec.max_authorized_checks - rec.checks_authorized_on_previous_app



    @api.constrains('dependency_id', 'subdependency_id')
    def _check_dependence(self):
        for rec in self:
            if rec.dependency_id and rec.subdependency_id:
                auth = self.env['check.authorized.dependency'].search([('dependency_id', '=', rec.dependency_id.id),
                                                                       ('subdependency_id', '=', rec.subdependency_id.id),('id','!=',rec.id)], limit=1)
                print('auth',auth)
                if auth:
                    if self.env.user.lang == 'es_MX':
                        raise ValidationError(
                            _('La dependencia y subdependencia que intenta guardar ya se encuentra registrada'))                    
                    else:
                        raise ValidationError(
                            _('The dependency and subdependency you are trying to save is already registered'))
