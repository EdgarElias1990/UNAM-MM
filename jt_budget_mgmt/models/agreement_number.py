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


class AgreementNumber(models.Model):

    _name = 'agreement.number'
    _description = 'Agreement Number'
    _rec_name = 'code'

    code = fields.Char(string='Abbreviation for program code')
    description = fields.Text(string='Description of program code')
    # number_id = fields.Many2one('', string='Agreement number')
    # desc_id = fields.Many2one('', string='Description')

    # _sql_constraints = [('number_id', 'unique(number_id)',
    #                      'The number must be unique.')]

    @api.constrains('code')
    def _check_code(self):
        if self.code and not len(self.code) == 2:
            raise ValidationError(_('The code size must be two.'))

    # @api.constrains('number_id')
    # def _check_number_id(self):
    #     if self.number_id and not len(str(self.number_id)) == 6:
    #         raise ValidationError(_('The number size must be six.'))
