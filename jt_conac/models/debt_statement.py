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


class StatementOfDebt(models.Model):
    _name = 'debt.statement'
    _description = 'Statement of Debt'
    _rec_name = 'denomination'

    denomination = fields.Char(string='Denomination of Debts')
    currency_id = fields.Many2one(
        'res.currency', string='Contracting Currency')
    country_id = fields.Many2one(
        'res.country', string='Institution or Creditor Country')
    init_balance = fields.Float(string='Initial Balance of the Period')
    end_balance = fields.Float(string='End Balance of the Period')
    parent_id = fields.Many2one('debt.statement', string='Parent')
    coa_conac_ids = fields.Many2many('coa.conac', string="CODE CONAC")
    