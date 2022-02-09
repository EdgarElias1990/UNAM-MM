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


class StatesAndProgram(models.Model):
    _name = 'states.program'
    _description = 'States and Program'
    _rec_name = 'concept'

    code = fields.Char(string='Code')
    concept = fields.Char(string='Concepto')
    approved_amt = fields.Float(string='Aprobado')
    ext_and_red_amt = fields.Float(string='Ampliaciones/ (Reducciones)')
    modified_amt = fields.Float(string='Modificado')
    accrued_amt = fields.Float(string='Devengado')
    paid_out_amt = fields.Float(string='Pagado')
    sub_exercise = fields.Char(string='Subejercicio')
    parent_id = fields.Many2one('states.program', string='Parent')
