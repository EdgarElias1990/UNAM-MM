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


class ImportAssignedAmountLine(models.TransientModel):

    _name = 'import.assigned.amount.line'
    _description = 'Import Assigned Amount Line'

    name = fields.Char(string='Name')
    folio = fields.Char(string='Folio')
    file = fields.Binary(string='File')
    filename = fields.Char(string='File name')
    record_number = fields.Integer(string='Number of records')
    dwnld_file = fields.Binary(string='Download File')
    dwnld_filename = fields.Char(string='Download File name')

    @api.model
    def default_get(self, fields):
        res = super(ImportAssignedAmountLine, self).default_get(fields)
        assigned_amount = self.env['control.assigned.amounts'].browse(
            self._context.get('active_id'))
        if assigned_amount and assigned_amount.folio:
            res['folio'] = assigned_amount.folio
        if assigned_amount and assigned_amount.name:
            res['name'] = assigned_amount.name
        return res

    @api.constrains('folio')
    def _check_folio(self):
        if not str(self.folio).isnumeric():
            if self.env.user.lang == 'es_MX':
                raise ValidationError('Folio Debe ser un valor numérico!')
            else:
                raise ValidationError('Folio Must be numeric value!')

    def download_file(self):
        file_path = get_resource_path(
            'jt_budget_mgmt', 'static/file/import_line', 'import_assigned_amount.xlsx')
        file = False
        with open(file_path, 'rb') as file_date:
            file = base64.b64encode(file_date.read())
        self.dwnld_filename = 'import_assigned_amount_line.xls'
        self.dwnld_file = file
        return {
            'name': 'Download Sample File',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'import.assigned.amount.line',
            'domain': [],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
        }

    def import_line(self):
        if not self.file:
            raise UserError(_('Please Upload File.'))

        assigned_amount = self.env['control.assigned.amounts'].browse(
            self._context.get('active_id'))
        if assigned_amount.folio != self.folio:
            raise UserError(_('Folio does not match.'))
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

                field_headers = ['year', 'program', 'subprogram', 'dependency', 'subdependency', 'item',
                                 'dv', 'origin_resource', 'ai', 'conversion_program',
                                 'departure_conversion', 'expense_type', 'location', 'portfolio',
                                 'project_type', 'project_number', 'stage', 'agreement_type',
                                 'agreement_number', 'exercise_type', 'assigned', 'start_date', 'end_date']

                result_vals = []
                for rowx, row in enumerate(map(sheet.row, range(1, sheet.nrows)), 1):
                    result_dict = {
                        'imported': True,
                        'state': 'draft',
                    }
                    counter = 0
                    for colx, cell in enumerate(row, 1):
                        value = cell.value
                        if field_headers[counter] != 'assigned':
                            if field_headers[counter] in ['year', 'dv'] and type(value) is int or type(value) is float:
                                value = int(cell.value)
                        else:
                            value = float(cell.value)

                        if field_headers[counter] == 'assigned':
                            if value < 0:
                                raise UserError(_("Assigned Amount should be greater than or 0!"))

                        if field_headers[counter] == 'start_date':
                            try:
                                start_date = False
                                if type(value) is str:
                                    start_date = datetime.strptime(str(value), '%m/%d/%Y').date()
                                elif type(value) is int or type(value) is float:
                                    start_date = datetime(*xlrd.xldate_as_tuple(value, 0)).date()
                                if start_date:
                                    value = start_date
                                else:
                                    value = False
                            except:
                                pass

                        if field_headers[counter] == 'end_date':
                            try:
                                end_date = False
                                if type(value) is str:
                                    end_date = datetime.strptime(str(value), '%m/%d/%Y').date()
                                elif type(value) is int or type(value) is float:
                                    end_date = datetime(*xlrd.xldate_as_tuple(value, 0)).date()
                                if end_date:
                                    value = end_date
                                else:
                                    value = False
                            except:
                                pass

                        result_dict.update(
                            {field_headers[counter]: value})
                        counter += 1
                    result_vals.append((0, 0, result_dict))

                data = result_vals
                if assigned_amount:
                    if self._context.get('reimport'):
                        assigned_amount.line_ids.filtered(
                            lambda l: l.state != 'manual').unlink()
                        assigned_amount.success_line_ids.filtered(
                            lambda l: l.state != 'manual').unlink()
                        assigned_amount.write({'state': 'draft'})
                    assigned_amount.write({
                        'import_status': 'in_progress',
                        'line_ids': data,
                    })
            except UserError as e:
                raise UserError(e)
