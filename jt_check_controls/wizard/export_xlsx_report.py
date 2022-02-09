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
from odoo import models, fields,_,tools
import base64
import xlwt
from datetime import datetime
from PIL import Image
from resizeimage import resizeimage
import io
from xlwt import Workbook
from xlwt import easyxf
from odoo.tools.misc import xlsxwriter
from odoo.modules.module import get_resource_path

class ExportXlsxReport(models.TransientModel):
    _name = 'jt_check_controls.export.xlsx.report'
    _description = "Export Xlsx Report"

    excel_file = fields.Binary(string='File')
    filename = fields.Char(string='File name')
    test_data = fields.Binary(string='File')
    
    def print_xlsx(self):
        output = io.BytesIO()
        
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(_('Check Per Box'))
        
        header_style = workbook.add_format({'bold': True, 'align': 'center'})
        col_style = workbook.add_format({'bold': True, 'align': 'left'})
        date_style=workbook.add_format({'align': 'right','num_format': 'yyyy-mm-dd'})
        float_sytle = workbook.add_format({'align': 'right'})
        float_total_sytle = workbook.add_format({'bold': True,'align': 'right'})
        
        filename_1= 'check_per_box.xls'
        row = 0
        col = 0

        sheet.merge_range(row, col, 7, col, '',)
        if self.env.user and self.env.user.company_id and self.env.user.company_id.header_logo:
            filename = 'logo.png'
            image_data = io.BytesIO(base64.standard_b64decode(self.env.user.company_id.header_logo))
            sheet.insert_image(0,0, filename, {'image_data': image_data,'x_offset':7,'y_offset':3,'x_scale':0.5,'y_scale':0.5})
        
        string1 = ''
        string1 += 'COSTO DE CHEQUES'
        string1 += '-'
        string1 +=str(datetime.today().strftime('%Y'))
        col += 1
        sheet.merge_range(row, col,row + 7,col + 3,
                          string1, header_style)
        col+=4
        
        img_path = get_resource_path('jt_check_controls', 'static/src/img/dgf.png')
        image_2_data = base64.b64encode(open(img_path, 'rb').read())
        self.test_data = image_2_data 
        sheet.merge_range(row, col, 7, col+2, '',)    
        if self.test_data:
            filename = 'logo.png'
            image_data = io.BytesIO(base64.standard_b64decode(self.test_data))
            sheet.insert_image(0,5, filename, {'image_data': image_data,'x_offset':7,'y_offset':3,'x_scale':0.9,'y_scale':0.6})
            
        row = row + 8
        col = 0
        
        
        #=============Column======================#
        sheet.set_column(col, col,20)
        sheet.write(row,col,_('Bank'),col_style)
        col = col+1
        sheet.set_column(col, col,20)
        sheet.write(row,col,_('Bank Account'),col_style)
        col = col+1
        sheet.set_column(col, col,15)
        sheet.write(row,col,_('Checkbook No.'),col_style)
        col = col+1
        sheet.set_column(col, col,10)
        sheet.write(row,col,_('Box No.'),col_style)
        col = col+1
        sheet.set_column(col, col,12)
        sheet.write(row,col,_('Initial Folio'),col_style)
        col = col+1
        sheet.set_column(col, col,12)
        sheet.write(row,col,_('Final Folio'),col_style)
        col = col+1
        sheet.set_column(col, col,14)
        sheet.write(row,col,_('Checks Per Box'),col_style)
        col = col+1
        sheet.set_column(col, col,15)
        sheet.write(row,col,_('Cost per check'),col_style)
        col = col+1
        sheet.set_column(col, col,15)
        sheet.write(row,col,_('Total cost for checks'),col_style)
        col = col+1
        sheet.set_column(col, col,15)
        sheet.write(row,col,_('Checkbook Request Date'),col_style)
        col = col+1
        sheet.set_column(col, col,15)
        sheet.write(row,col,_('Checkbook receipt date'),col_style)
        col = col+1
        
        row = row + 1
        col = 0
        active_ids = self.env.context.get('active_ids')
        base_records = self.env['check.per.box'].browse(active_ids)
        grand_cost_check = 0
        grand_total_cost = 0
        for record in base_records:
            sheet.write(row,col,record.bank_id.name)
            sheet.write(row,col+1,record.bank_account_id.acc_number)
            sheet.write(row,col+2,record.checkbook_no)
            sheet.write(row,col+3,record.box_no)
            sheet.write(row,col+4,record.intial_folio)
            sheet.write(row,col+5,record.final_folio)
            sheet.write(row,col+6,record.check_per_box)
            sheet.write(row,col+7,record.cost_per_check,float_sytle)
            grand_cost_check += record.cost_per_check
            sheet.write(row,col+8,record.total_cost_for_checks,float_sytle)
            grand_total_cost += record.total_cost_for_checks
            sheet.write(row,col+9,record.appliaction_date,date_style)
            sheet.write(row,col+10,record.check_receipt_date,date_style)
            row = row + 1
            
        sheet.write(row,col+6,_('Total'),col_style)
        #sheet.write(row,col+7,grand_cost_check,float_total_sytle)
        sheet.write(row,col+8,grand_total_cost,float_total_sytle)
        
        row = row + 1

        workbook.close()
        xlsx_data = base64.encodestring(output.getvalue())
        
        #output.seek(0)
        #generated_file = output.read()
        #output.close()
        res_id = self.env['jt_check_controls.export.xlsx.report'].create(
        {'excel_file': xlsx_data, 'filename': filename_1})

        return {
            'name': _('Download Files'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'jt_check_controls.export.xlsx.report',
            'domain': [],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': res_id.id,
            'context': {'active_ids': self.env.context.get('active_ids')}
        }