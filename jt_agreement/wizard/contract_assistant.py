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

class contractAssistant(models.TransientModel):
    _name = 'jt_agreement.contract.assistant'
    _description = "Contract Assistant"

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    line_ids = fields.One2many('jt_agreement.contract.assistant.line',"wizard_id")
    is_hide_button = fields.Boolean(default=False)
        
    def print_bases_collaboration(self):
        lines = []
        pdf_rec = self.env['jt_agreement.contract.assistant'].create({'is_hide_button':True,
                                'start_date':self.start_date,'end_date':self.end_date})
        for rec in self.env.context.get('active_ids'):
            base_records = self.env['bases.collaboration'].browse(rec)
            
            base_records.report_start_date = self.start_date
            base_records.report_end_date = self.end_date
            today = datetime.today().date() 
            qr_pdf = self.env.ref('jt_agreement.contract_assistant_report').render_qweb_pdf([rec])[0]
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
            'name': 'Download Sample File',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'jt_agreement.contract.assistant',
            'domain': [],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': pdf_rec.id,
            'context':{'active_ids':self.env.context.get('active_ids')}
        }


class ContractAssistantLine(models.TransientModel):
    
    _name = 'jt_agreement.contract.assistant.line'
    
    wizard_id = fields.Many2one('jt_agreement.contract.assistant')
    bases_id = fields.Many2one('bases.collaboration')
    file = fields.Binary(string='File')
    filename = fields.Char(string='File name')

    def download_pdf(self):
        self.ensure_one()
        return {
                'type': 'ir.actions.act_url',
                'target':'download',
                 'url': "web/content/?model=jt_agreement.contract.assistant.line&id=" + str(self.id) + "&filename_field=filename&field=file&download=true&filename=" + self.filename,
            }
    
 