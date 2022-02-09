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


class ImportAdequaciesLine(models.TransientModel):

    _name = 'import.adequacies.line'
    _description = 'Import Adequacies Line'

    folio = fields.Char(string='Folio')
    record_number = fields.Integer(string='Number of records')
    file = fields.Binary(string='File')
    filename = fields.Char(string='File name')
    dwnld_file = fields.Binary(string='Download File')
    dwnld_filename = fields.Char(string='Download File name')

    @api.model
    def default_get(self, fields):
        res = super(ImportAdequaciesLine, self).default_get(fields)
        adequacies = self.env['adequacies'].browse(
            self._context.get('active_id'))
        if adequacies and adequacies.folio:
            res['folio'] = adequacies.folio
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
            'jt_budget_mgmt', 'static/file/import_line', 'import_adequacies_line.xls')
        file = False
        with open(file_path, 'rb') as file_date:
            file = base64.b64encode(file_date.read())
        self.dwnld_filename = 'import_adequacies_line.xls'
        self.dwnld_file = file
        return {
            'name': 'Download Sample File',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'import.adequacies.line',
            'domain': [],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
        }

    def import_line(self):
        self.ensure_one()
        if not self.file:
            raise UserError(_('Please Upload File.'))
        
        adequacies = self.env['adequacies'].browse(
            self._context.get('active_id'))
        if adequacies.folio != self.folio:
            raise UserError(_('Folio does not match.'))
        elif self.file:
            try:
                data = base64.decodestring(self.file)
                book = open_workbook(file_contents=data or b'')
                sheet = book.sheet_by_index(0)

                total_rows = self.record_number + 1
                if sheet.nrows != total_rows:
                    raise UserError(_('Number of records do not match with file'))

                if adequacies:
                    adequacies_lines_ids = adequacies.adequacies_lines_ids.filtered(lambda x:x.imported)
                    if adequacies_lines_ids:
                        adequacies_lines_ids.sudo().unlink() 
                    adequacies.pointer_row = 1
                    adequacies.success_row_ids = "[]"
                    adequacies.failed_row_ids = "[]"
                    adequacies.allow_upload = False
                    adequacies.write({
                        'budget_file': self.file,
                        'filename': self.filename,
                        'import_status': 'in_progress',
                        'total_rows': self.record_number,
                    })
            except UserError as e:
                raise UserError(e)
