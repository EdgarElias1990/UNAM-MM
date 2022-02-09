from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class DistributionModules(models.TransientModel):
    _name = 'apply.distribution.modules'
    _description = "Apply Distribution Of modules"

    line_ids = fields.One2many('apply.distribution.modules.lines', 'distribution_id', string="Lines")
    checkbook_req_id = fields.Many2one('checkbook.request', string="Checkbook Request")

    def apply(self):
        logs = []
        active_id = self._context.get('active_id')
        blank_check = self.env['blank.checks.request'].browse(active_id)
        if self.checkbook_req_id and blank_check:
            for rec in self.line_ids:
                check_logs = self.env['check.log'].search(
                    [('checklist_id.checkbook_req_id', '=', self.checkbook_req_id.id),
                     ('folio', '>=', rec.intial_filio.folio),
                     ('folio', '<=', rec.final_folio.folio)])
                for log in check_logs:
                    if log.id not in logs:
                        logs.append(log.id)
                        log.module = rec.module
                    else:
                        raise ValidationError(_('You cannot assign module in same folio!'))
                blank_check.distribution_of_module_ids = [(0, 0, {
                    'module': rec.module,
                    'intial_filio': rec.intial_filio.id,
                    'final_folio': rec.final_folio.id,
                    'amounts_of_checks': rec.amounts_of_checks
                })]


class DistributionModulesLines(models.TransientModel):
    _name = 'apply.distribution.modules.lines'
    _description = "Apply Distribution Of modules"

    distribution_id = fields.Many2one('apply.distribution.modules')
    module = fields.Selection([('ACATLAN', 'ACATLAN'),
                               ('ARAGON', 'ARAGON'), ('CUAUTITLAN', 'CUAUTITLAN'),
                               ('CUERNAVACA', 'CUERNAVACA'),
                               ('COVE', 'COVE'), ('IZTACALA', 'IZTACALA'),
                               ('JURIQUILLA', 'JURIQUILLA'), ('LION', 'LION'),
                               ('MORELIA', 'MORELIA'), ('YUCATAN', 'YUCATAN')], string="Module")
    intial_filio = fields.Many2one('check.log', "Intial Folio")
    final_folio = fields.Many2one('check.log', "Final Folio")
    amounts_of_checks = fields.Integer("Amounts of Checks")

    @api.onchange('intial_filio', 'final_folio')
    def onchange_folios(self):
        if self.final_folio and self.intial_filio:
            amount_of_checks = self.final_folio.folio - self.intial_filio.folio
            if amount_of_checks == 0:
                self.amounts_of_checks = 1
            else:
                self.amounts_of_checks = amount_of_checks + 1