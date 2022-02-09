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
from odoo import models, fields
class ApplicationRequest(models.Model):

    _name = 'application.request'

    currency_id = fields.Many2one('res.currency','Currency')
    date = fields.Date('Date')
    no_of_currencies = fields.Float('Number Of Currencies')
    reg_denomination = fields.Char('Register denomination')
    status = fields.Selection([('draft','Draft'),('request','Request')],string='Status',default='draft')
    user_id = fields.Many2one('res.users','Prepared by',default=lambda self:self.env.user.id)
    
    def request(self):

    	for record in self:

    		record.status = 'request'