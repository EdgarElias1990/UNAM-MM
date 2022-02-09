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
import base64
from odoo.http import request, content_disposition
from datetime import datetime, timedelta
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta

class AgreementBasesCollabrationResemble(models.TransientModel):
    _name = 'jt_agreement.bases.resemble'
    _description = "Bases of collaboration Resemble"

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    line_ids = fields.One2many('jt_agreement.bases.collaboration.line',"wizard_id")
    is_hide_button = fields.Boolean(default=False)
        
    def print_pdf(self):

        attch_obj = self.env['ir.attachment']
        rec = self.env.context.get('active_ids')
        pdf_rec = self.env['jt_agreement.bases.collaboration'].create({'start_date':self.start_date,'end_date':self.end_date})
        base_records = self.env['bases.collaboration'].browse(rec)
        for base in base_records:
            base.report_start_date = self.start_date
            base.report_end_date = self.end_date
        start_date = str(self.start_date)
        end_date = str(self.end_date)
        today = datetime.today().date()
        ctx = {
            'start': self.start_date,
            'end': self.end_date,
        }
        filename = 'CON'
        pdf = self.env.ref('jt_agreement.bases_collaboration_view_report').render_qweb_pdf(rec)[0]
        
        # Store report as PDF so user can download
        out = base64.b64encode(pdf)
        vals = {'name': filename,
                'datas': out,
                'res_model': 'jt_agreement.bases.resemble',
                'name': filename}
        attach_ids = attch_obj.search([
            ('res_model', '=', 'jt_agreement.bases.resemble')])
        if attach_ids:
            try:
                attach_ids.unlink()
            except:
                pass
        doc_id = attch_obj.create(vals)
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/%s?download=true' % (doc_id.id),
            'target': 'current',
            'tag': 'close',
        }


