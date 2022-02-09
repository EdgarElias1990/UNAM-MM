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


class ControlAmountsReceived(models.Model):

    _name = 'control.amounts.received'
    _description = 'Control of amounts received'
    _rec_name = 'folio'

    folio = fields.Integer(string='Folio')
    budget_id = fields.Many2one('expenditure.budget', string='Budget')
    made_by_id = fields.Many2one('res.users', string='Made by')
    import_date = fields.Date(string='Import date')
    observations = fields.Text(string='Observations')
    line_ids = fields.One2many('control.amounts.received.line',
                               'control_id', string='Control of amounts received lines')


class ControlAmountsReceivedLine(models.Model):

    _name = 'control.amounts.received.line'
    _description = 'Control of amounts received lines'
    _rec_name = 'deposit_date'

    amount_assigned = fields.Integer(string='Amount assigned')
    deposit_date = fields.Date(string='Deposit date')
    amount_deposited = fields.Integer(string='Amount deposited')
    account_id = fields.Many2one('account.account', string='Account')
    amount_pending = fields.Integer(string='Amount pending')
    observations = fields.Text(string='Observations')
    control_id = fields.Many2one(
        'control.amounts.received', string='Control of amounts received')
