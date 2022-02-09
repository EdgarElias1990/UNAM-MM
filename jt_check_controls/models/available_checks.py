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
from odoo import models, fields, api, _,tools
from datetime import datetime, timedelta,date
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT, format_date

class AvailableCheck(models.Model):
    
    _name = 'available.check'
    _description = 'Available Check'
    _auto = False
    _rec_name='check_folio_id'
    
    check_folio_id = fields.Many2one('check.log',"Check number")
    
    dependence_id = fields.Many2one('dependency', "Dependence")
    subdependence_id = fields.Many2one('sub.dependency', "Subdependence")
    checkbook_no = fields.Char("Checkbook No")
    general_status = fields.Selection([('available', 'Available'),
                                       ('assigned', 'Assigned'),
                                       ('cancelled', 'Cancelled'),
                                       ('paid', 'Paid')])

    reason_cancellation = fields.Text(related='check_folio_id.reason_cancellation')
    is_physical_check = fields.Boolean(related='check_folio_id.is_physical_check')
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr,self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
                select cl.id as id,
                cl.id as check_folio_id,
                cl.dependence_id as dependence_id,
                cl.subdependence_id as subdependence_id,
                cl.checkbook_no as checkbook_no,
                cl.general_status as general_status
                from check_log cl                
                where cl.general_status = 'available'
                            )'''% (self._table) 
        )    
    
    def action_cancel_checks(self):
        return {
            'name': _('Cancel Available Check'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'cancel.available.check',
            'domain': [],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_check_folio_ids': self.ids},
        }
