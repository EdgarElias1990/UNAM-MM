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


class RejectStandardizationLine(models.TransientModel):

    _name = 'reject.standardization.line'
    _description = 'Reject Standardization Line'

    reason = fields.Char(string='Reason for rejection', required=True)

    def reject(self):
        active_id = self._context.get('parent_id')
        standardization_id = self.env['standardization'].browse(
            active_id)
        lines = standardization_id.line_ids.filtered(
            lambda l: l.state == 'cancelled' and l.selected == True)
        for line in lines:
            line.reason = self.reason
        return {'type': 'ir.actions.client', 'tag': 'reload'}
