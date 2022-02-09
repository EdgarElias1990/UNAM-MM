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

class AgreementBasesCollabration(models.TransientModel):
    _name = 'jt_agreement.bases.collaboration'
    _description = "Bases of collaboration"

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    line_ids = fields.One2many('jt_agreement.bases.collaboration.line',"wizard_id")
    is_hide_button = fields.Boolean(default=False)
        
    def print_bases_collaboration(self):
        lines = []
        pdf_rec = self.env['jt_agreement.bases.collaboration'].create({'is_hide_button':True,
                                'start_date':self.start_date,'end_date':self.end_date})
        for rec in self.env.context.get('active_ids'):
            base_records = self.env['bases.collaboration'].browse(rec)
            
            base_records.report_start_date = self.start_date
            base_records.report_end_date = self.end_date
            today = datetime.today().date() 
            qr_pdf = self.env.ref('jt_agreement.bases_collaboration_report').render_qweb_pdf([rec])[0]
            qr_pdf = base64.b64encode(qr_pdf)
            
            filename = 'CON'
            if base_records.dependency_id and base_records.dependency_id.dependency:
                filename += "_"+str(base_records.dependency_id.dependency)
            if base_records.subdependency_id and base_records.subdependency_id.sub_dependency:
                filename += "_"+str(base_records.subdependency_id.sub_dependency)
            filename += "_"+str(today.month).zfill(2)+"_"+str(today.year)
            
            if base_records.convention_no:
                filename += "_"+str(base_records.convention_no)
            
            
            filename += ".pdf"
            lines.append((0,0,{'bases_id':rec,'file':qr_pdf,'filename':filename}))
        pdf_rec.line_ids = lines
        
        
        return {
            'name': 'Generate Bases collaboration',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'jt_agreement.bases.collaboration',
            'domain': [],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': pdf_rec.id,
            'context':{'active_ids':self.env.context.get('active_ids')}
        }

    def download_all(self):

        attch_obj = self.env['ir.attachment']
        attach_ids = attch_obj.sudo().search([
            ('res_model', '=', 'jt_agreement.bases.collaboration')])
        if attach_ids:
            try:
                attach_ids.sudo().unlink()
            except:
                pass
        
        rec = self.env.context.get('active_ids')
        pdf_rec = self.env['jt_agreement.bases.collaboration'].create({'start_date':self.start_date,'end_date':self.end_date})
        base_records = self.env['bases.collaboration'].browse(rec)
        tab_id = []
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
            if base.dependency_id and base.dependency_id.dependency:
                filename += "_"+str(base_records.dependency_id.dependency)
            if base.subdependency_id and base.subdependency_id.sub_dependency:
                filename += "_"+str(base.subdependency_id.sub_dependency)
            filename += "_"+str(today.month).zfill(2)+"_"+str(today.year)
            
            if base.convention_no:
                filename += "_"+str(base.convention_no)
            
            
            filename += ".pdf"
            pdf = self.env.ref('jt_agreement.bases_collaboration_report').render_qweb_pdf(base.id)[0]
        
            # Store report as PDF so user can download
            out = base64.b64encode(pdf)
            vals = {'name': filename,
                    'datas': out,
                    'res_model': 'jt_agreement.bases.collaboration',
                    'res_id':base.id,
                    'name': filename}
            doc_id = attch_obj.create(vals)
            tab_id.append(doc_id.id)
        self._cr.commit()
        url = '/web/binary/download_document?tab_id=%s' % tab_id
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }
            
#         return {
#             'type': 'ir.actions.act_url',
#             'url': 'web/content/%s?download=true' % (doc_id.id),
#             'target': 'current',
#             'tag': 'close',
#         }





class AccountStatementLine(models.TransientModel):
    
    _name = 'jt_agreement.bases.collaboration.line'
    
    wizard_id = fields.Many2one('jt_agreement.bases.collaboration')
    bases_id = fields.Many2one('bases.collaboration')
    file = fields.Binary(string='File')
    filename = fields.Char(string='File name')

    def download_pdf(self):
        self.ensure_one()
        return {
                'type': 'ir.actions.act_url',
                'target':'download',
                 'url': "web/content/?model=jt_agreement.bases.collaboration.line&id=" + str(self.id) + "&filename_field=filename&field=file&download=true&filename=" + self.filename,
            }
    
 