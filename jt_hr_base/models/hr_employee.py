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
from odoo.exceptions import ValidationError
import re


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    worker_payment_key = fields.Char('Worker Payment Key')
    # journal_id = fields.Many2one('account.journal', string='Bank Key Scatter')
    payment_place_id = fields.Many2one('payment.place', 'Payment Place')
    payment_place_description = fields.Text(related='payment_place_id.description',string='Payment Place Description')
    # Job Information Page Fields
    entry_date = fields.Date('Date of Entry')
    ss_number = fields.Integer('Social Security Number')
    worker_type = fields.Selection([('base', 'Base'), ('trust', 'Trust'),('pensioner', 'Pensioner'),
                            ('subject', 'Subject'), ('career', 'Career'), ('officials', 'Officials'), ('fee', 'Fee')],
                            string='Type of Worker')
    worker_status = fields.Selection([('active', 'Active'),
                                      ('license', 'License')],
                                     string='Worker Status')
    occ_code = fields.Selection([('commerce', 'Commerce'), ('drivers', 'Drivers'),
                                 ('admin_worker', 'Administrative Workers'),
                                 ('edu_workers', 'Education Workers'),
                                 ('trab_del', 'Trab. del Arte, Espe'),
                                 ('prot_serve', 'T. in servs of prot'),
                                 ('fab_worker', 'Fabrile Workers'),
                                 ('technician', 'Technicians'),
                                 ('salaried_proff', 'Salaried Professional'),
                                 ('independent_proff', 'Independent Professional'),
                                 ('public_off', 'Public institution or company official'),
                                 ('private_off',
                                  'Private institution or company official'),
                                 ('pensioner', 'Retirees or pensioners')],
                                string='National Occupation Code')
    registration = fields.Selection([('confirmed', 'Confirmed'), (
        'rejected', 'Rejected')], string='Registration in Financial Institution')

    # Private Information Page Fields
    emp_partner_id = fields.Many2one('res.partner','Address')
    street = fields.Char('Street')
    street2 = fields.Char('Street 2')
    colonia = fields.Char('Colonia')
    city = fields.Char('City')
    state_id = fields.Many2one('res.country.state', string='State')
    zip_code = fields.Char('Zip')
    country_id = fields.Many2one('res.country', string='Country')
    rfc = fields.Char('RFC')
    curp = fields.Char('CURP')
    housing = fields.Selection([('house', 'House'), ('building', 'Building'),
                                ('department', 'Department'),
                                ('housing_unit', 'Housing Unit'),
                                ('market', 'Market')], string='Type of housing')
    road = fields.Selection([('old_road', 'Old Road'), ('andador', 'Andador'),
                             ('highway', 'Highway'), ('avenue', 'Avenue'),
                             ('boulevard', 'Boulevard'), ('street', 'Street'),
                             ('closed', 'Closed'),('circuit','Circuit'),
                             ('alley_road', 'Alley Road'),('camino','Camino'),
                             ('high_road', 'High Road'),('calzada','Calzada'),
                             ('glorieta', 'Glorieta'),
                             ('Paseo', 'paseo'),
                             ('prolongation', 'Prolongation'),
                             ('private', 'Private'),('return','Return'),
                             ('valle', 'Valle'),('via','Via'),('villa','Villa')], string='Type of Road')

    marital = fields.Selection(
        selection_add=[('free_union', 'Free Union'), ('separate', 'Separate')])
    certificatee = fields.Selection(
        [('sin_escolaridad', 'Sin escolaridad'),
                       ('primaria', 'Primaria'), ('secundaria', 'Secundaria'),
                       ('preparatoria', 'Preparatoria'),
                       ('diplomado', 'Diplomado-especialidad'),
                       ('carrera_tecnica', 'Carrera Técnica'),
                       ('licenciatura', 'Licenciatura'),
                       ('posgrado', 'Postgrado'),
                       ('otros', 'Otros'),
                       ('sin_escolarizar', 'Sin escolarizar')], string='Escolaridad')
    profession = fields.Selection([('phy_anthropologist', 'Physical anthropologist'),
                                   ('soc_anthropologist', 'Social anthropologist'),
                                   ('architect', 'Architect'),
                                   ('biologist', 'Biologist'), ('cardinal', 'Cardinal'),
                                   ('dental', 'Dental surgeon'),
                                   ('accountant', 'Public Accountant'),
                                   ('ethnologist', 'Ethnologist'),
                                   ('physicist', 'Physicist'),
                                   ('physicist_math', 'Physicist mathematical'),
                                   ('general', 'General'), ('lieutenant', 'Lieutenant'),
                                   ('engineer', 'Engineer'), ('licensed', 'Licensed'),
                                   ('doctor', 'Doctor'), ('professor', 'Professor')],
                                  string='Profession')
    nationality = fields.Selection([('mexican', 'Mexican'),
                                    ('north_american', 'North American'),
                                    ('lebanese', 'Lebanese'),
                                    ('south_american', 'South American'),
                                    ('american_central', 'American Central'),
                                    ('europe', 'Europe'), ('israelite', 'Israelite'),
                                    ('japanese', 'Japanese'), ('canadian', 'Canadian'),
                                    ('other', 'Other')], string='Nationality')

    # HR Settings Page Fields
    worker_number = fields.Char('Worker Number')
    place_number = fields.Integer('Number of Place')
    number_of_square = fields.Char('Number Of Square')
    # Accounting Page Fields
    beneficiary_ids = fields.Many2many('res.partner', string='Beneficiary')
    bank_ids = fields.One2many("res.partner.bank", 'employee_id', string="Bank Accounts")
    account_receivable_id = fields.Many2one(
        'account.account', string='Account receivable')
    account_payable_id = fields.Many2one(
        'account.account', string='Account payable')
    
    emp_title = fields.Char("Title")
    emp_job_title = fields.Char("Job Title")
    bank_journal_id = fields.Many2one("account.journal",'Key bank dispersion')
    
    @api.constrains('number_of_square')
    def _check_key_unam(self):
        if self.number_of_square and  not str(self.number_of_square).isnumeric():
            raise ValidationError(_('The Number of square must be numeric value'))

    @api.constrains('rfc')
    def _check_unique_rfc(self):
        for rec in self:
            if rec.rfc:
                emp_id = self.env['hr.employee'].search([('id', '!=', rec.id),('rfc','=',rec.rfc)],limit=1)
                if emp_id:
                    raise ValidationError(_('The Employee RFC Value Must Be Unique'))
            if not rec.rfc:
                raise ValidationError(_('The Add Employee RFC Value'))
            
    @api.constrains('worker_payment_key')
    def _check_worker_payment_key(self):
        if self.worker_payment_key and not str(self.worker_payment_key).isnumeric():
            raise ValidationError(_('The Worker Payment Key must be numeric value'))

    @api.onchange('branch_number')
    def onchange_branch_number(self):
        if self.branch_number:
            # if not self.branch_number.isdigit():
            #     raise UserError(
            #         _('The Branch Number should only consist of digits.'))
            pattern = "^[a-zA-Z0-9_]+$"
            if not re.match(pattern, self.branch_number):
                raise UserError(_('The Branch Number value should be alphanumeric type.'))

            if len(self.branch_number) > 4:
                raise UserError(
                    _('The Branch Number should be of 4 digits only.'))
            if len(self.branch_number) < 4:
                self.branch_number = self.branch_number.zfill(4)
    @api.onchange('user_id')
    def onchange_user_partner(self):
        if self.user_id and self.user_id.partner_id:
            self.emp_partner_id =  self.user_id.partner_id.id
        else:
            self.emp_partner_id = False
    
    @api.onchange('job_id')
    def onchange_job_tags(self):
        if self.job_id and self.job_id.category_key:
            self.category_ids = [(6,0,self.job_id.category_key.ids)]
            
    _sql_constraints = [
        ('worker_number_uniq', 'unique (worker_number)', 'The Worker Number must be unique.')]

class ResPartnerBank(models.Model):

    _inherit = 'res.partner.bank'

    employee_id = fields.Many2one('hr.employee')