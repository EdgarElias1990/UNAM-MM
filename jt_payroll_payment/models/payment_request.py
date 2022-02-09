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

class PaymentRequest(models.Model):

    _name = 'payment.request'
    _description = "Payment Request"

    name = fields.Char("Document Sequence")
    employee_id = fields.Many2one('hr.employee', "Alimony Employee / Beneficiary")
    employee_number = fields.Char(related='employee_id.identification_id', string="Employee Number")
    batch_folio = fields.Integer("Batch Folio")
    amount = fields.Float("Amount to Pay")
    request_type = fields.Selection([('university', 'Payment to University Worker'),
                                     ('add_benifit', 'Additional Benifit'),
                                     ('alimony', 'Payment Special payroll'),
                                     ('payment', 'Payment')], "Type of request for payroll payment")
    bank_receiving_payment_id = fields.Many2one('res.bank', string="Bank Receiving Payment")
    payment_receipt_bank_id = fields.Many2one("account.journal", string="Payment Receipt Bank Account")
    receipt_date = fields.Date("Receipt Date")
    register_user_id = fields.Many2one('res.users', "Registering User")
    send_user_id = fields.Many2one('res.users', "User who Sends")
    payment_method = fields.Selection([('check', 'Check'), ('cash', 'Cash'),
                                       ('elec_trans', 'Electronic Transfer')])
    payroll_origin_id = fields.Many2one('employee.payroll.file', "Payroll Origin")
    bank_acc_payment_insur_id = fields.Many2one('account.journal', string="Bank account of payment issuance")
    payment_issuing_bank_id = fields.Many2one("account.journal", string="Payment Issuing Bank")
    fornight = fields.Selection([('01', '01'), ('02', '02'), ('03', '03'), ('04', '04'), ('05', '05'),
                                 ('06', '06'), ('07', '07'), ('08', '08'), ('09', '09'), ('10', '10'),
                                 ('11', '11'), ('12', '12'), ('13', '13'), ('14', '14'), ('15', '15'),
                                 ('16', '16'), ('17', '17'), ('18', '18'), ('19', '19'), ('20', '20'),
                                 ('21', '21'), ('22', '22'), ('23', '23'), ('24', '24')],
                                string="Fornight")
    journal_id = fields.Many2one("account.journal", "Journal")

