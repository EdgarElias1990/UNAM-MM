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
from odoo import models, fields, api


class StatementOfIncome(models.Model):
    _name = 'income.statement'
    _description = 'Statement of Income'
    # _rec_name = 'name'

    name = fields.Char(string='Nombre')
    estimated_amt = fields.Float(string='Estimado')
    exp_and_red_amt = fields.Float(string='Ampliaciones y Reducciones')
    modified_amt = fields.Float(string='Modificado')
    accrued_amt = fields.Float(string='Devengado')
    raised_amt = fields.Float(string='Recaudado')
    difference_amt = fields.Float(string='Diferencia')
    parent_id = fields.Many2one('income.statement', string='Parent')
    coa_conac_ids = fields.Many2many('coa.conac', string="CODE CONAC")
    # accounts_ids = fields.Many2many("account.account",'rel_conac_income_account','income_id','account_id','Estimated Accounts')
    # collected_accounts_ids = fields.Many2many("account.account",'rel_conac_income_collected_account','income_id','account_id','Collected Accounts')

    # conac_accounts_ids = fields.Many2many("coa.conac",'rel_conac_chart_income_account','income_id','account_id','Estimated Accounts')
    # conac_collected_accounts_ids = fields.Many2many("coa.conac",'rel_conac_chart_income_collected_account','income_id','account_id','Collected Accounts')
    
    