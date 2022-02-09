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
from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import ValidationError


class Diot(models.Model):

    _name = 'tax.diot'
    _description = 'diot'
    _rec_name = 'folio'

    folio = fields.Integer(string='Folio')
    year = fields.Selection([(str(num), str(num)) for num in range(
        2000, (datetime.now().year) + 80)], string='Year')
    month = fields.Selection([
        ('january', 'January'),
        ('february', 'February'),
        ('march', 'March'),
        ('april', 'April'),
        ('may', 'May'),
        ('june', 'June'),
        ('july', 'July'),
        ('august', 'August'),
        ('september', 'September'),
        ('october', 'October'),
        ('november', 'November'),
        ('december', 'December')], string='Month', default='january')
    filling_date = fields.Date(string='Filling date')
    observations = fields.Char(string='Observations')
    txt_file = fields.Binary("TXT file")
    dec_file = fields.Binary("DEC file")
    diot_archive = fields.Binary("DIOT ARCHIVE")
    ackn_acceptance = fields.Binary("Acknowledgement of acceptance", attachment=True)
    shipping_ackn = fields.Binary("Shipping acknowledgement", attachment=True)
    file_name = fields.Char("File Name")

    _sql_constraints = [
        ('folio_uniq', 'unique(folio)', 'The folio must be unique.')]
    
    @api.constrains('shipping_ackn', 'file_name')
    def get_data(self):
        if self.file_name and not self.file_name.endswith('.pdf'):     # check if file pdf
            raise ValidationError('Cannot upload file different from .pdf file')
        else:
            pass