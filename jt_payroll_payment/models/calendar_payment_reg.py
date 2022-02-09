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
from odoo.exceptions import UserError,ValidationError

class CalendarPaymentRegistration(models.Model):

    _name = 'calendar.payment.regis'
    _description = "Calendar for Payment Registration"
    _rec_name = 'type_pay'

    type_pay = fields.Selection([('Non Business Day', 'Non Business Day'),
                                 ('Payment schedule', 'Payment schedule')], string="Type")
    type_of_payment = fields.Selection([('payroll', 'Payroll'),
                                        ('pay_contr', 'Payment of Contributions'),
                                        ('pay_commi', 'Payment of Commissions and Interests')], string="Payment Type")
    provider_id = fields.Many2one("res.partner", "Provider")
    date = fields.Date("Date")
    cause = fields.Selection([('saturday', 'Saturday'), ('sunday', 'Sunday'),
                              ('unam', 'UNAM'), ('official', 'Official'),
                              ('financ_inst', 'Financial Institution')], string="Cause")
    fornight_does = fields.Selection([('01', '01'), ('02', '02'), ('03', '03'), ('04', '04'), ('05', '05'),
                                      ('06', '06'), ('07', '07'), ('08', '08'), ('09', '09'), ('10', '10'),
                                      ('11', '11'), ('12', '12'), ('13', '13'), ('14', '14'), ('15', '15'),
                                      ('16', '16'), ('17', '17'), ('18', '18'), ('19', '19'), ('20', '20'),
                                      ('21', '21'), ('22', '22'), ('23', '23'), ('24', '24')],
                                     string="Fornight Does")
    
    @api.constrains('date')
    def _check_date(self):
        for rec in self:
            if rec.date:
                calendar_id = self.search([('id', '!=', rec.id), ('date', '=', rec.date)], limit=1)
                if calendar_id:
                    raise ValidationError(_('The system should not allow the same date to be used again'))
