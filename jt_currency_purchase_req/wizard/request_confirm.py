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
from odoo import models, fields,_


class RequestConfirm(models.TransientModel):
    _inherit = 'request.confirm'
    
    bank_id = fields.Many2one('res.bank','Bank')
    
    def apply_open_account(self):

        active_id = self._context.get('active_id', False)
        if active_id:
            request_account_id = self.env['request.accounts'].browse(active_id)
            request_account_id.bank_id = self.bank_id
            request_account_id.confirm_account()
    
            return {
                'name': 'Bank Account',
                'view_mode': 'form',
                'view_id': self.env.ref('account.view_account_bank_journal_form').id,
                'res_model': 'account.journal',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'context': {'default_type': 'bank','default_account_open_request_id':active_id}
            }
