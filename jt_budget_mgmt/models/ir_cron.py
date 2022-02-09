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


class IrCron(models.Model):

    _inherit = 'ir.cron'

    prev_cron_id = fields.Integer(string='Next CRON ID')
    nextcall_copy = fields.Datetime(string='Nextcall Copy For Budget')
    budget_id = fields.Many2one('expenditure.budget', string="Budget")
    control_assigned_id = fields.Many2one('control.assigned.amounts', string="Control of Assigned Amount")
    standardization_id = fields.Many2one('standardization', string="Re-standardization")
    adequacies_id = fields.Many2one('adequacies', string="Adequacies")