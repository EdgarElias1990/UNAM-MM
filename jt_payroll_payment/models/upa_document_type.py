# -*- coding: utf-8 -*-
##############################################################################
#
#    Jupical Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Jupical Technologies(<http://www.jupical.com>).
#    Author: Jupical Technologies Pvt. Ltd.(<http://www.jupical.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class UPADocumentType(models.Model):

    _name = 'upa.document.type'
    _description = 'UPA Document Type'
    _rec_name = "document_number"

    name = fields.Char('Name')
    document_number = fields.Char('Consecutive')

    @api.constrains('document_number')
    def _check_key_unam(self):
        if not str(self.document_number).isnumeric():
            raise ValidationError(_('The Consecutive must be numeric value'))

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, '%s-%s' % (rec.name, rec.document_number)))
        return res

    def fill_zero(self, code):
        return str(code).zfill(2)

    @api.model
    def create(self, vals):
        if vals.get('document_number') and len(vals.get('document_number')) != 2:
            vals['document_number'] = self.fill_zero(
                vals.get('document_number'))
        return super(UPADocumentType, self).create(vals)

    def write(self, vals):
        if vals.get('document_number') and len(vals.get('document_number')) != 2:
            vals['document_number'] = self.fill_zero(
                vals.get('document_number'))
        return super(UPADocumentType, self).write(vals)
