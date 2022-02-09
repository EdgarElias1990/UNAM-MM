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


class CalendarAssignedAmounts(models.Model):

    _name = 'calendar.assigned.amounts'
    _description = 'Calendar of assigned amounts'
    _rec_name = 'date'

    date = fields.Date(string='Date')
    amount_to_receive = fields.Integer(string='Amount to receive')
    amount_received = fields.Integer(string='Amount received')
    amount_pending = fields.Integer(string='Amount pending')
    observations = fields.Text(string='Observations')
    line_ids = fields.One2many('calendar.assigned.amounts.lines',
                               'calendar_assigned_amount_id', string='Calendar of assigned amount lines')


class CalendarAssignedAmountsLines(models.Model):

    _name = 'calendar.assigned.amounts.lines'
    _description = 'Calendar of assigned amounts lines'
    _rec_name = 'date'

    date = fields.Date(string='Deposit date')
    observations = fields.Text(string='Observations')
    amount_deposited = fields.Integer(string='Amount deposited')
    bank_id = fields.Many2one('res.bank', string='Bank')
    bank_account_id = fields.Many2one('res.partner.bank', string='Bank account')
    calendar_assigned_amount_id = fields.Many2one(
        'calendar.assigned.amounts', string='Calendar of assigned amount')
