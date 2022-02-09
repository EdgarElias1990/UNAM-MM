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

class AccountMove(models.Model):

    _inherit = 'account.move'

    conac_move = fields.Boolean(string="CONAC")
    dependence_id = fields.Many2one('dependency','D')
    sub_depend_id = fields.Many2one('sub.dependency', "S")
    programatic_code = fields.Boolean('Programmatic Code')
    ie_account = fields.Boolean('IEAccount')

class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    conac_move = fields.Boolean(string="CONAC")
    coa_conac_id = fields.Many2one('coa.conac', string="CODE CONAC")
    program_code_id = fields.Many2one('program.code','Program Code')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('account_id',False) and not vals.get('coa_conac_id'):
                account_rec = self.env['account.account'].browse(vals.get('account_id',[]))
                vals.update({'coa_conac_id':account_rec.coa_conac_id and account_rec.coa_conac_id.id or False})
        lines = super(AccountMoveLine, self).create(vals_list)
        return lines
            
    def write(self,vals):
        result = super(AccountMoveLine,self).write(vals)
        if vals.get('account_id'):
            for res in self:
                if res.account_id and res.account_id.coa_conac_id:
                    res.coa_conac_id = res.account_id.coa_conac_id.id
                
        return result
        
    
