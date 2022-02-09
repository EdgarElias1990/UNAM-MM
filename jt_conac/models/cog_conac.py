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
from odoo.exceptions import UserError

class COGCONAC(models.Model):
    _name = 'cog.conac'
    _description = 'COG CONAC'

    chapter = fields.Char(string='Chapter', size=4)
    name = fields.Char(string='Name')
    heading = fields.Char(string='Heading', size=3)
    concept = fields.Char(string='Concept')

    _sql_constraints = [('uniq_heading', 'unique(heading)', 'The Heading must be unique.')]

    def name_get(self):
        result = []
        for cog in self:
            if 'from_cog' in self._context:
                name = cog.name
                result.append((cog.id, name))
            else:
                name = cog.heading or cog.name
                result.append((cog.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if not args:
            args = []
        if name:
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            item_ids = []
            if operator in positive_operators:
                item_ids = self._search([('heading', '=', name)] + args, limit=limit,
                                           access_rights_uid=name_get_uid)
        else:
            item_ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        return self.browse(item_ids).name_get()

    def write(self, vals):
        res = super(COGCONAC, self).write(vals)
        for cog in self:
            heading = vals.get('heading') or cog.heading
            chap = vals.get('chapter') or cog.chapter
            if heading and chap:
                st_head = heading[:2]
                st_chap = chap[:2]
                if st_chap != st_head:
                    raise UserError(_("The Coding of the Heading field does not correspond to the chapter."))
        return res
    
    @api.model
    def create(self, vals):
        res = super(COGCONAC, self).create(vals)
        if vals.get('heading') and vals.get('chapter'):
            st_headin = vals.get('heading')[:2]
            st_chp = vals.get('chapter')[:2]
            if st_chp != st_headin:
                raise UserError(_("The Coding of the Heading field does not correspond to the chapter."))
        return res