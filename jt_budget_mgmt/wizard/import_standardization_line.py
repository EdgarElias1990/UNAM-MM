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
from odoo.modules.module import get_resource_path
from xlrd import open_workbook
from odoo.exceptions import UserError, ValidationError


class ImportStandardizationLine(models.TransientModel):

    _name = 'import.standardization.line'
    _description = 'Import Standardization Line'

    folio = fields.Char(string='Folio')
    record_number = fields.Integer(string='Number of records')
    file = fields.Binary(string='File')
    filename = fields.Char(string='File name')
    dwnld_file = fields.Binary(string='Download File')
    dwnld_filename = fields.Char(string='Download File name')
    
    _sql_constraints = [
         ('folio_uniq', 'unique(id)', 'The ID must be unique.')]

    @api.constrains('folio')
    def _check_folio(self):
        if not str(self.folio).isnumeric():
            if self.env.user.lang == 'es_MX':
                raise ValidationError('Folio Debe ser un valor numérico!')
            else:
                raise ValidationError('Folio Must be numeric value!')

    def download_file(self):
        file_path = get_resource_path(
            'jt_budget_mgmt', 'static/file/import_line', 'import_standardization_line.xls')
        file = False
        with open(file_path, 'rb') as file_date:
            file = base64.b64encode(file_date.read())
        self.dwnld_filename = 'import_standardization_line.xls'
        self.dwnld_file = file
        return {
            'name': 'Download Sample File',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'import.standardization.line',
            'domain': [],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
        }

    @api.model
    def default_get(self, fields):
        res = super(ImportStandardizationLine, self).default_get(fields)
        standardization = self.env['standardization'].browse(
            self._context.get('active_id'))
        if standardization and standardization.folio:
            res['folio'] = standardization.folio
        return res

    def import_line(self):

        if not self.file:
            raise UserError(_('Please Upload File.'))
        
        standardization = self.env['standardization'].browse(
            self._context.get('active_id'))
        if standardization.folio != self.folio:
            raise UserError(_('Folio does not match.'))
        elif self.file:
            try:
                data = base64.decodestring(self.file)
                book = open_workbook(file_contents=data or b'')
                sheet = book.sheet_by_index(0)
                total_rows = self.record_number + 1
                if sheet.nrows != total_rows:
                    raise UserError(_('Number of records do not match with file'))

                headers = []
                for rowx, row in enumerate(map(sheet.row, range(1)), 1):
                    for colx, cell in enumerate(row, 1):
                        headers.append(cell.value)

                field_headers = ['year', 'program', 'subprogram', 'dependency', 'subdependency', 'item',
                                 'dv', 'origin_resource', 'ai', 'conversion_program',
                                 'departure_conversion', 'expense_type', 'location', 'portfolio',
                                 'project_type', 'project_number', 'stage', 'agreement_type',
                                 'agreement_number', 'exercise_type','folio','budget' ,'amount', 'origin', 'quarter_data']

                result_vals = []
                for rowx, row in enumerate(map(sheet.row, range(1, sheet.nrows)), 1):
                    result_dict = {
                        'imported': True,
                        'state': False,
                        'line_state' : 'draft',
                    }
                    counter = 0
                    for colx, cell in enumerate(row, 1):
                        value = cell.value
                       
                        if field_headers[counter] != 'amount':
                            if field_headers[counter] in ['year', 'dv'] and type(value) is int or type(value) is float:
                                value = int(cell.value)
                        else:
                            value = float(cell.value)
                        result_dict.update(
                            {field_headers[counter]: value})
                        counter += 1
                    result_vals.append((0, 0, result_dict))

                data = result_vals
                if standardization:
                    if self._context.get('reimport'):
                        standardization.line_ids.filtered(
                            lambda l:l.imported == True).unlink()
                        #standardization.write({'state': 'draft'})
                    standardization.write({
                        'import_status': 'in_progress',
                        'line_ids': data,
                        'total_rows': self.record_number,
                    })
                
            except UserError as e:
                raise UserError(e)
