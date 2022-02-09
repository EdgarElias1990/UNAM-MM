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
from odoo.exceptions import UserError

class PaymentPlace(models.Model):

    _name = 'payment.place'
    _description = 'Place of Payment'

    name = fields.Char('Name', size=8)
    description = fields.Text('Description')
    place = fields.Char('Place', size=3)
    
    @api.constrains('name')
    def _check_name(self):
        if not str(self.name).isnumeric():
            raise UserError(_('The name must be numeric value'))

    @api.constrains('place')
    def _check_place(self):
        if self.place and not str(self.place).isnumeric():
            raise UserError(_('The place must be numeric value'))
    
    _sql_constraints = [('name_unique', 'unique(name)', 'Name must be unique.')]
