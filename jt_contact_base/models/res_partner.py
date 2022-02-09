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


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Registration of supplier / beneficiaries
    person_type = fields.Selection(
        [('physics', 'Physics'), ('moral', 'Moral')], string='Person type')
    beneficiary_type = fields.Selection([('employee','Employee'),('alimony', 'Alimony'), (
        'scholar', 'Scholar'), ('national_provider', 'National provider'),
        ('foreign_supplier','Foreign supplier'),('fixed_fund','Fixed Fund')
        ],
                                        string='Beneficiary type')
    password_beneficiary = fields.Char('Password of the beneficiary of the payment')
    #rfc = fields.Char('RFC')
    #curp = fields.Char('CURP')
    instruction = fields.Selection([('high', 'High'), ('low', 'Low'), (
        'change', 'Change')], string='Instruction with the banking institution')
    dob = fields.Date('Date of birth')
    nationality = fields.Char('Nationality')
    tax_email = fields.Char('Tax email')

    # Recording of Scholarship
    scholar_key_payment = fields.Char('Scholar key payment')
    scholarship_id = fields.Many2one('scholarship.type', string='Type of Scholarship')
    scholarship_approved_month = fields.Char(string='Scholarship approved month')
    period = fields.Char('Period')

    #Boolean fields
    is_ISSSTE_supplier = fields.Boolean('Is ISSSTE supplier')
    is_FOVISSSTE_supplier = fields.Boolean('Is FOVISSSTE supplier')

    _sql_constraints = [
        ('password_beneficiary_uniq', 'unique (password_beneficiary)',
         'The Password of the beneficiary of the payment must be unique.'),
        ('scholar_key_payment_uniq', 'unique (scholar_key_payment)',
         'The scholar key payment must be unique.')]

    def supplier_registration(self):
        return {
            'name': (_('Supplier Registration')),
            'type': 'ir.actions.act_window',
            'res_model': 'supplier.registration',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref(
                'jt_contact_base.supplier_registration_form_view').id,
            'target': 'new',
            'context': self._context
        }
