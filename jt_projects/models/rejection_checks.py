from odoo import models, fields


class RejectionChecks(models.Model):

    _name = 'rejection.checks'
    _description = "Rejections for CONACYT checks"
    _rec_name = 'key'

    def name_get(self):
        result = []
        for rec in self:
            if rec.key and rec.description:
                result.append((rec.id, '%s. %s' % (rec.key, rec.description)))
        return result

    key = fields.Char("Key")
    description = fields.Char("Description")
