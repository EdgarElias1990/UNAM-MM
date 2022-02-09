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

class ProjectClose(models.TransientModel):
	_name = 'project.close'

	close_letter = fields.Binary(string='Closing Official Letter',attachment=True)
	current_id = fields.Integer(string="Current Id")
	is_papiit_project = fields.Boolean(
		'PAPIIT project', default=False, copy=False)
	project_id = fields.Many2one('project.project')
	close_label = fields.Char('Close',default='Do you want to close the project?')

	def apply_document(self):
		self.project_id.status = 'closed'
		if not self.is_papiit_project and self.close_letter:
			res = self.env['ir.attachment'].create({
				'name':"Closing Official Letter",
				'datas':self.close_letter,
				'res_model':"project.project",
				'res_id':self.current_id,
				})
			return res
		

		

		