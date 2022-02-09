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
import base64
import xlrd
from datetime import datetime
from odoo.modules.module import get_resource_path
from xlrd import open_workbook
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import ustr

class ImportCalendarAssignAmountLines(models.TransientModel):

    _name = 'import.calendar.assign.amount.lines'
    _description = 'Import Calendar Assign Amount Lines'

    record_number = fields.Integer(string='Number of records')
    file = fields.Binary(string='File')
    filename = fields.Char(string='File name')
    dwnld_file = fields.Binary(string='Download File')
    dwnld_filename = fields.Char(string='Download File name')

 
    def download_file(self):
        file_path = get_resource_path(
            'jt_finance', 'static/file/import_line', 'calendar_assign_amount_line.xlsx')
        file = False
        with open(file_path, 'rb') as file_date:
            file = base64.b64encode(file_date.read())
        self.dwnld_filename = 'import_calendar_assigned_amount_line.xls'
        self.dwnld_file = file
        return {
            'name': 'Download Sample File',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'import.calendar.assign.amount.lines',
            'domain': [],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
        }

    def import_line(self):
        user_lang = self.env.user.lang
        self.ensure_one()
        control_amount = self.env['calendar.assigned.amounts'].browse(
            self._context.get('active_id'))
        if self.file:
            try:
                data = base64.decodestring(self.file)
                book = open_workbook(file_contents=data or b'')
                sheet = book.sheet_by_index(0)

                total_rows = self.record_number + 1
                if sheet.nrows != total_rows:
                    raise UserError(
                        _('The number of imported lines is not equal to the number of records'))

                headers = []
                for rowx, row in enumerate(map(sheet.row, range(1)), 1):
                    for colx, cell in enumerate(row, 1):
                        headers.append(cell.value)

                field_headers = ['year', 'branch', 'unit', 'purpose', 'function', 
                                 'sub_function', 'program','institution_activity', 'project_identification', 'project', 'item_char',
                                 'expense_type', 'funding_source', 'federal','key_wallet' ,'january', 'february',
                                 'march', 'april', 'may', 'june','july','august','september','october','november','december','annual_amount']

                result_vals = []
                for rowx, row in enumerate(map(sheet.row, range(1, sheet.nrows)), 1):
                    counter = 0
                    result_dict = { 
                        'is_imported': True,
                        'state': 'draft',
                        }
                    for colx, cell in enumerate(row, 1):
                        value = cell.value
                        if field_headers[counter] in ('year','branch','purpose','function','sub_function','program','institution_activity','project','expense_type','funding_source') and type(value) is int or type(value) is float:
                            value = int(cell.value)
                                                
                        result_dict.update(
                            {field_headers[counter]: value})
                        counter += 1
                    result_vals.append((0, 0, result_dict))
                data = result_vals
                
                if control_amount:
                    control_amount.line_ids.unlink()
                    if self._context.get('reimport'):
                        control_amount.line_ids.filtered(
                            lambda l: l.state != 'manual').unlink()
                        control_amount.import_line_ids.filtered(
                            lambda l: l.state != 'manual').unlink()
                        control_amount.write({'state': 'draft'})
                    try:
                        control_amount.write({
                            'line_ids': data,
                            'import_status' : 'in_progress',
                           # 'import_date' : fields.Datetime.now(),
                        })

                    except ValueError as e:
                        raise ValidationError(_("Column  contains incorrect values. Error: %s")% (ustr(e)))
                    except ValidationError as e:
                        raise ValidationError(_("Column  contains incorrect values. Error: %s")% (ustr(e)))
                    except UserError as e:
                        raise ValidationError(_("Column  contains incorrect values. Error: %s")% (ustr(e)))            

            except ValueError as e:
                raise ValidationError(_("Column  contains incorrect values. Error: %s")% (ustr(e)))
            except ValidationError as e:
                raise ValidationError(_("Column  contains incorrect values. Error: %s")% (ustr(e)))
            except UserError as e:
                raise ValidationError(_("Column  contains incorrect values. Error: %s")% (ustr(e)))            
        
