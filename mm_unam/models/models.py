# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import re

class BankAccountConcept(models.Model):
    _inherit = 'bank.account.concept'

    def unlink(self):
        a = self.env["account.journal"].search([])
        lista = list()
        for ac in self:
            for i in range(len(a)):
                lista.append(a[i].concept_id.name)
                if ac.name in lista:
                    raise UserError(_("Concepto de Cuenta Bancaria en Uso"))

        return super(BankAccountConcept, self).unlink()
