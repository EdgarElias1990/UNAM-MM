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

class AgreementFund(models.Model):

    _name = 'agreement.fund'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Funds"

    fund_key = fields.Char("Fund Key")
    name = fields.Char("Fund Name")

    @api.constrains('fund_key')
    def _check_fund_key(self):
        for rec in self:
            if rec.fund_key:
                result = self.search([('id', '!=', rec.id), ('fund_key', '=', rec.fund_key)], limit=1)
                if result:
                    raise ValidationError(_('The Fund Key must be unique'))
    
    @api.constrains('name')
    def _check_name(self):
        for rec in self:
            if rec.name:
                result = self.search([('id', '!=', rec.id), ('name', '=', rec.name)], limit=1)
                if result:
                    raise ValidationError(_('The Fund name must be unique'))    