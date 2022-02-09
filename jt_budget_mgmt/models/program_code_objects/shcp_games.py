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


class SHCPGame(models.Model):

    _name = 'shcp.game'
    _description = 'Conversion Key with Item'
    _rec_name = 'conversion_key'

    conversion_key = fields.Char('Conversion Key')
    conversion_key_desc = fields.Text(string="Description of Conversion Key")
    
    _sql_constraints = [('conversion_key', 'unique(conversion_key)', 'The  Conversion Key must be unique.')]
    
    @api.constrains('conversion_key')
    def _check_name(self):
        if self.conversion_key:
            if not str(self.conversion_key).isnumeric():
                raise ValidationError(_('The Conversion Key must be numeric value'))
            
            if len(self.conversion_key) != 5:
                raise ValidationError(_('The Conversion Key size must be five.'))
