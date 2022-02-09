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
class AccountJournal(models.Model):

    _inherit = 'account.journal'

    account_type = fields.Selection(selection_add=[('fixed', 'Fixed'), ('operational_fund', 'Operational Fund')],
                                    string='Account Type')
    dependency_id = fields.Many2one('dependency', "Dependency Key")
    auth_sign_ids = fields.One2many('auth.sign','journal_id')
    account_open_request_id = fields.Many2one('request.accounts','Account Request')
    
class  AuthorizedSign(models.Model):

	_name = 'auth.sign'
	_description = 'Authorized Signature'

	journal_id = fields.Many2one('account.journal')
	employee_id = fields.Many2one('hr.employee','Name')
	poistion = fields.Many2one('hr.job','Position')
	movement = fields.Selection([('high','High'),('low','Low')],string='Movement')
	type_of_signature = fields.Char('Type Of Signature')
	ownership = fields.Char('Ownership')