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
from odoo.exceptions import UserError, ValidationError

class PolicyKeys(models.Model):

    _name = 'policy.keys'
    _description = 'UPA Catalog'
    _rec_name = 'organization'

    origin = fields.Char('Origination of the movement')
    organization = fields.Char('Organization and Control', size=3)
    description = fields.Text('Description')

    _sql_constraints = [('organization', 'unique(organization)', 'La Organización debe ser única.')]

    def name_get(self):
        result = []
        for rec in self:
            name = rec.origin or ''
            if rec.organization and self.env.context and self.env.context.get('show_for_supplier_payment',False): 
                name = rec.organization
            result.append((rec.id, name))
        return result

    @api.model
    def create(self, vals):
        res = super(PolicyKeys, self).create(vals)
        if vals.get('organization'):
            len_org = len(vals.get('organization'))
            if len_org != 3:
                raise UserError(
                    _('The Organization and Control must be of 3 characters only.'))
        return res

    @api.constrains('organization')
    def check_organization(self):
        if self.organization and len(self.organization) != 3:
            raise UserError(
                _('The Organization and Control must be of 3 characters only.'))

    @api.onchange('organization')
    def onchange_organization(self):
        lista = []
        e = self.env['policy.keys'].search([])
        for i in range(len(e)):
            lista.append(e[i].organization)
        if self.organization in lista:
            raise ValidationError('La Organización debe ser única.')