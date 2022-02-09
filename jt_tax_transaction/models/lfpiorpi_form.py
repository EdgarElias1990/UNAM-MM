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

class LfpiorpiForm(models.Model):

    _name = 'declaration.lfpiorpi'
    _description = 'lfpiorpi'
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
    application_office = fields.Binary("Application Office")
    dgpu_file = fields.Binary("DGPU file")
    statement_draft = fields.Binary("Statement draft")
    shipping_ack = fields.Binary("Shipping acknowledgement")

    _sql_constraints = [
        ('folio_uniq', 'unique(folio)', 'The folio must be unique.')]
    