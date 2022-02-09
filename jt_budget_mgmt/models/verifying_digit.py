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


class VerifyingDigit(models.Model):

    _name = 'verifying.digit'
    _description = 'Verifying Digit'
    _rec_name = 'check'

    unam_key_id = fields.Many2one('program', string='UNAM key')
    sub_program_id = fields.Many2one('sub.program', string='Sub program')
    dependency_id = fields.Many2one('dependency', string='Dependency')
    sub_dependency_id = fields.Many2one('sub.dependency', string='Sub dependency')
    item_id = fields.Many2one('expenditure.item', string='Item')
    check = fields.Integer(string='Check')

    @api.constrains('unam_key_id')
    def _check_unam_key_id(self):
        # To check size of the UNAM Key is exact 2
        if self.unam_key_id and len(str(self.unam_key_id.key_unam)) != 2 and self.unam_key_id.key_unam not in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            raise ValidationError(_('The UNAM key size must be two.'))

    @api.constrains('sub_program_id')
    def _check_sub_program_id(self):
        if self.sub_program_id and len(str(self.sub_program_id.unam_key_id.key_unam)) != 2 and self.sub_program_id.unam_key_id.key_unam not in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            raise ValidationError(_('The sub program size must be two.'))

    @api.constrains('dependency_id')
    def _check_dependency_id(self):
        if self.dependency_id and len(str(self.dependency_id.dependency)) != 3 and self.dependency_id.dependency not in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            raise ValidationError(_('The dependency size must be three.'))

    @api.constrains('sub_dependency_id')
    def _check_sub_dependency_id(self):
        if self.sub_dependency_id and len(str(self.sub_dependency_id.sub_dependency)) != 2 and self.sub_dependency_id.sub_dependency not in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            raise ValidationError(_('The sub dependency size must be two.'))

    @api.constrains('item_id')
    def _check_item_id(self):
        if self.item_id and len(str(self.item_id.item)) != 3 and self.item_id.item not in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            raise ValidationError(_('The item size must be three.'))

    @api.constrains('check')
    def _check_check(self):
        if self.check and len(str(self.check)) != 2 and self.check not in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            raise ValidationError(_('The check size must be two.'))
