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

    @api.constrains('check')
    def _check_check(self):
        if not str(self.check).isnumeric():
            raise ValidationError(_('The Check value must be numeric value'))

    def check_digit(self):
        if self.unam_key_id and self.sub_program_id and self.dependency_id and self.sub_dependency_id and self.item_id:
            pr = self.unam_key_id.key_unam or ''
            sp = self.sub_program_id.sub_program or ''
            dep = self.dependency_id.dependency or ''
            sd = self.sub_dependency_id.sub_dependency or ''
            par = self.item_id.item or ''
            combined_digits = '' + pr + sp + dep + sd + par

            odd = 0
            even = 0
            counter = 0
            for digit in combined_digits:
                counter += 1
                if counter % 2 == 0:
                    even += int(digit)
                else:
                    odd += int(digit)
            result_odd = odd * 7
            result_even = even * 3
            result_odd_even = result_odd + result_even
            vd = '0' + str(result_odd_even)[-1:]
            return vd

    def check_digit_from_codes(self, program_id, sub_program_id, dependency_id, sub_dependency_id, item_id):
        if program_id and sub_program_id and dependency_id and sub_dependency_id and item_id:
            pr = program_id.key_unam or ''
            sp = sub_program_id.sub_program or ''
            dep = dependency_id.dependency or ''
            sd = sub_dependency_id.sub_dependency or ''
            par = item_id.item or ''
            combined_digits = '' + pr + sp + dep + sd + par

            odd = 0
            even = 0
            counter = 0
            for digit in combined_digits:
                counter += 1
                if counter % 2 == 0:
                    even += int(digit)
                else:
                    odd += int(digit)
            result_odd = odd * 7
            result_even = even * 3
            result_odd_even = result_odd + result_even
            vd = '0' + str(result_odd_even)[-1:]
            return vd
        else:
            return '00'

    def _compute_check(self):
        for dv in self:
            dv.check = '00'
            result = dv.check_digit()
            if result:
                dv.check = result

    check = fields.Char(string='Check', size=2, compute='_compute_check')
