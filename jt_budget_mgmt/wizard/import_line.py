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

class ImportLine(models.TransientModel):

    _name = 'import.line'
    _description = 'Import Line'

    budget_name = fields.Text(string='Name of the budget')
    total_budget = fields.Float(string='Total budget')
    record_number = fields.Integer(string='Number of records')
    file = fields.Binary(string='File')
    filename = fields.Char(string='File name')
    dwnld_file = fields.Binary(string='Download File')
    dwnld_filename = fields.Char(string='Download File name')

    @api.model
    def default_get(self, fields):
        res = super(ImportLine, self).default_get(fields)
        budget = self.env['expenditure.budget'].browse(
            self._context.get('active_id'))
        if budget and budget.name:
            res['budget_name'] = budget.name
        return res

    def download_file(self):
        file_path = get_resource_path(
            'jt_budget_mgmt', 'static/file/import_line', 'import_line_sample.xlsx')
        file = False
        with open(file_path, 'rb') as file_date:                
            file = base64.b64encode(file_date.read())
        self.dwnld_filename = 'import_line.xlsx'
        self.dwnld_file = file
        return {
            'name': 'Download',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'import.line',
            'domain': [],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
        }

    def import_line(self):
        budget = self.env['expenditure.budget'].browse(
            self._context.get('active_ids'))
        if not self.file:
            raise UserError(_('Please Upload File.'))
        if budget.name != self.budget_name:
            raise UserError(_('Budget name does not match.'))
        elif self.file:
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

                field_headers = ['year', 'program', 'subprogram', 'dependency', 'subdependency', 'item', 'dv',
                                 'origin_resource', 'ai', 'conversion_program', 'departure_conversion',
                                 'expense_type', 'location', 'portfolio', 'project_type', 'project_number',
                                 'stage', 'agreement_type', 'agreement_number', 'exercise_type',
                                 'authorized', 'start_date', 'end_date']

                total_budget_amount = 0
                result_vals = []
                for rowx, row in enumerate(map(sheet.row, range(1, sheet.nrows)), 1):
                    result_dict = {
                        'imported': True,
                        'state': 'draft',
                    }
                    if budget:
                        if budget.from_date:
                            result_dict.update({'start_date':budget.from_date})
                        if budget.to_date:
                            result_dict.update({'end_date':budget.to_date})
                    counter = 0
                    for colx, cell in enumerate(row, 1):
                        value = cell.value
                        if field_headers[counter] not in ('authorized', 'assigned'):
                            if field_headers[counter] in ('year', 'dv') and type(value) is int or type(value) is float:
                                value = int(cell.value)

                        if field_headers[counter] == 'start_date':
                            msg = ''
                            try:
                                start_date = False
                                if type(value) is str:
                                    start_date = datetime.strptime(str(value), '%m/%d/%Y').date()
                                elif type(value) is int or type(value) is float:
                                    start_date = datetime(*xlrd.xldate_as_tuple(value, 0)).date()
                                if start_date:
                                    if start_date.day !=1 or start_date.month != 1:
                                        if self.env.user.lang == 'es_MX':
                                            msg = "de fechas:Las fechas colocadas en el archivo no coinciden con las fechas colocadas en el Presupuesto 01/01/YYYY"
                                            raise ValidationError(_("de fechas:Las fechas colocadas en el archivo no coinciden con las fechas colocadas en el Presupuesto 01/01/YYYY"))
                                        else:
                                            raise ValidationError(_("Start Date Format must be 01/01/YYYY"))
                                    value = start_date
                                else:
                                    value = False
                            except ValueError as e:
                                raise ValidationError(_("Start Date Format Does Not match : %s")% (ustr(e)))
                            except ValidationError as e:
                                if msg and self.env.user.lang == 'es_MX':
                                    raise ValidationError(_("de fechas:Las fechas colocadas en el archivo no coinciden con las fechas colocadas en el Presupuesto 01/01/YYYY"))
                                else:
                                    raise ValidationError(_("Start Date Format Does Not match : %s")% (ustr(e)))
                            except UserError as e:
                                raise ValidationError(_("Start Date Format Does Not match : %s")% (ustr(e)))            

                        if field_headers[counter] == 'end_date':
                            msg = ''
                            try:
                                end_date = False
                                if type(value) is str:
                                    end_date = datetime.strptime(str(value), '%m/%d/%Y').date()
                                elif type(value) is int or type(value) is float:
                                    end_date = datetime(*xlrd.xldate_as_tuple(value, 0)).date()
                                if end_date:
                                    if end_date.day != 31 or end_date.month != 12:
                                        if self.env.user.lang == 'es_MX':
                                            msg = 'de fechas:Las fechas colocadas en el archivo no coinciden con las fechas colocadas en el Presupuesto 31/12/YYYY'
                                            raise ValidationError(_("de fechas:Las fechas colocadas en el archivo no coinciden con las fechas colocadas en el Presupuesto 31/12/YYYY"))
                                        else:
                                            raise ValidationError(_("End Date Format must be 01/01/YYYY"))
                                    value = end_date
                                else:
                                    value = False
                            except ValueError as e:
                                raise ValidationError(_("End Date Format Does Not match : %s")% (ustr(e)))
                            except ValidationError as e:
                                if msg and self.env.user.lang == 'es_MX':
                                    raise ValidationError(_("de fechas:Las fechas colocadas en el archivo no coinciden con las fechas colocadas en el Presupuesto 31/12/YYYY"))
                                else:
                                    raise ValidationError(_("End Date Format Does Not match :%s")% (ustr(e)))
                            except UserError as e:
                                raise ValidationError(_("End Date Format Does Not match : %s")% (ustr(e)))            
                        result_dict.update(
                            {field_headers[counter]: value})
                        counter += 1

                    if 'authorized' in result_dict:
                        amt = result_dict.get('authorized', 0)
                        if float(amt) < 0:
                            raise UserError(_("Authorized Amount should be greater than 0!"))
                        total_budget_amount += float(amt)
                    if 'assigned' in result_dict:
                        amt = result_dict.get('assigned', 0)
                        if float(amt) < 0:
                            raise UserError(_("Assigned Amount should be greater than or 0!"))
                        
                    result_vals.append((0, 0, result_dict))
                if round(total_budget_amount, 2) != self.total_budget:
                    if self.env.user.lang=='es_MX':
                        raise UserError(
                            _('La suma de los montos Autorizados %s no es igual al total del presupuesto %s')%(round(total_budget_amount, 2),self.total_budget))
                    else:
                        raise UserError(
                            _('The sum of the Authorized amounts %s is not equal to the total of the budget %s')%(round(total_budget_amount, 2),self.total_budget))

                data = result_vals
                if budget:
                    if self._context.get('reimport'):
                        budget.line_ids.filtered(
                            lambda l: l.state != 'manual').unlink()
                        budget.success_line_ids.filtered(
                            lambda l: l.state != 'manual').unlink()
                        budget.write({'state': 'draft'})
                    try:
                        budget.write({
                            'import_status': 'in_progress',
                            'line_ids': data,
                        })

                    except ValueError as e:
                        if self.env.user.lang == 'es_MX':
                            raise ValidationError(_("La columna contiene valores incorrectos. Error: %s")% (ustr(e)))
                        else:
                            raise ValidationError(_("Column  contains incorrect values. Error: %s")% (ustr(e)))
                    except ValidationError as e:
                        if self.env.user.lang == 'es_MX':
                            raise ValidationError(_("La columna contiene valores incorrectos. Error: %s")% (ustr(e)))
                        else:                        
                            raise ValidationError(_("Column  contains incorrect values. Error: %s")% (ustr(e)))
                    except UserError as e:
                        if self.env.user.lang == 'es_MX':
                            raise ValidationError(_("La columna contiene valores incorrectos. Error: %s")% (ustr(e)))
                        else:                        
                            raise ValidationError(_("Column  contains incorrect values. Error: %s")% (ustr(e)))            

            except ValueError as e:
                if self.env.user.lang == 'es_MX':
                    raise ValidationError(_("La columna contiene valores incorrectos. Error %s")% (ustr(e)))
                else:
                    raise ValidationError(_("Column  contains incorrect values. Error %s")% (ustr(e)))
            except ValidationError as e:
                if self.env.user.lang == 'es_MX':
                    raise ValidationError(_("La columna contiene valores incorrectos. Error: %s")% (ustr(e)))
                else:
                    raise ValidationError(_("Column  contains incorrect values. Error %s")% (ustr(e)))
            except UserError as e:
                if self.env.user.lang == 'es_MX':
                    raise ValidationError(_("La columna contiene valores incorrectos. Error: %s")% (ustr(e)))
                else:                
                    raise ValidationError(_("Column  contains incorrect values. Error %s")% (ustr(e)))            
