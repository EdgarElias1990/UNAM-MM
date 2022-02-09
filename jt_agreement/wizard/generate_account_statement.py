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


class AccountStatement(models.TransientModel):
    _name = 'trust.account.statement'
    _description = "Trust Account Statement"

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    line_ids = fields.One2many('trust.account.statement.line',"wizard_id")
    
    def print_account_statement(self):
        lines = []
        pdf_rec = self.env['trust.account.statement'].create({'start_date':self.start_date,'end_date':self.end_date})
        for rec in self.env.context.get('active_ids'):
            base_records = self.env['agreement.trust'].browse(rec)
            
            base_records.report_start_date = self.start_date
            base_records.report_end_date = self.end_date
            
            qr_pdf = self.env.ref('jt_agreement.account_statement_report').render_qweb_pdf([rec])[0]
            qr_pdf = base64.b64encode(qr_pdf)
            lines.append((0,0,{'trust_id':rec,'file':qr_pdf,'filename':'account_statement.pdf'}))
        pdf_rec.line_ids = lines
        
        
        return {
            'name': 'Download Sample File',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'trust.account.statement',
            'domain': [],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': pdf_rec.id,
            'context':{'active_ids':self.env.context.get('active_ids')}
        }


class AccountStatementLine(models.TransientModel):
    
    _name = 'trust.account.statement.line'
    
    wizard_id = fields.Many2one('trust.account.statement')
    trust_id = fields.Many2one('agreement.trust')
    file = fields.Binary(string='File')
    filename = fields.Char(string='File name')

    def download_pdf(self):
        self.ensure_one()
        return {
                'type': 'ir.actions.act_url',
                'target':'download',
                 'url': "web/content/?model=trust.account.statement.line&id=" + str(self.id) + "&filename_field=filename&field=file&download=true&filename=" + self.filename,
            }
    
 