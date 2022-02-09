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


class AgreementType(models.Model):

    _name = 'agreement.type'
    _description = 'Type of Agreement'
    _rec_name = 'number'

    type_id = fields.Many2one(
        'project.project', string='Agreement type identifier')
    name = fields.Text(string='Name')
    number = fields.Text(string='Number')

    _sql_constraints = [('number', 'unique(number)',
                         'The number must be unique.')]

    @api.constrains('type_id')
    def _check_type_id(self):
        if self.type_id and len(self.type_id.name) != 2:
            raise ValidationError(_('The type size must be two.'))

    @api.constrains('number')
    def _check_number(self):
        if self.number and len(self.number) != 6:
            raise ValidationError(_('The number size must be six.'))
