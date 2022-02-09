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

class AdjustmentCases(models.Model):

    _name = 'adjustment.cases'
    _description = "AdjustmentCases"
    _rec_name = 'case'


    case = fields.Selection([('A','A'),('D','D'),('R','R'),('F','F'),('H','H'),('B','B'),('V','V'),('C','C'),('E','E'),('P','P'),('Z','Z'),('S','S')],string="Case")
    description = fields.Text('Description')

#     def name_get(self):
#         if 'show_from_payroll' in self._context:
#             res = []
#             for case in self:
#                 name = case.description
#                 res.append((case.id, name))
#         else:
#             res = super(AdjustmentCases, self).name_get()
#         return res


    
    