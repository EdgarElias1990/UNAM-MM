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
from odoo.exceptions import ValidationError

class ExpenditureItem(models.Model):

    _name = 'expenditure.item'
    _description = 'Item of Expenditure'
    _rec_name = 'item'

    item = fields.Char(string='Item', size=3)
    item_group = fields.Integer(compute='get_item_group',store=True)
    exercise_type = fields.Selection(
        [('r', 'R'), ('c', 'C'), ('d', 'D')], string='Exercise type')
    description = fields.Text(string='Item description')
    unam_account_id = fields.Many2one('account.account', string='UNAM account')
    shcp = fields.Char(string='Expenditure Item SHCP')
    desc_shcp = fields.Char(string='Description of expenditure item of SHCP')
    cog_id = fields.Many2one('coa.conac', string='CONAC Code')
    cog_desc = fields.Char(string='Account name COG CONAC')
    assigned_account = fields.Char(string='Assigned account')
    heading = fields.Many2one('cog.conac', string="Heading")
    cog_conac = fields.Char(string='COG CONAC')
    des_cog_conac = fields.Char(string='Description of COG CONAC')
    concept_cog_conac = fields.Char(string='Concept COG CONAC')

    _sql_constraints = [('item', 'unique(item)', 'The item must be unique.')]

    @api.depends('item')
    def get_item_group(self):
        for rec in self:
            if rec.item:
                rec.item_group =int(rec.item[0])
            else:
                rec.item_group = 0
                 
    @api.constrains('item')
    def _check_item(self):
        if not str(self.item).isnumeric():
            raise ValidationError(_('The Item value must be numeric value'))

    def fill_zero(self, code):
        return str(code).zfill(3)

    @api.model
    def create(self, vals):
        if vals.get('item') and len(vals.get('item')) != 3:
            vals['item'] = self.fill_zero(vals.get('item'))
        item = self.search([('item', '=', vals.get('item'))])
        if item:
            raise ValidationError(_("The item must be unique."))
        return super(ExpenditureItem, self).create(vals)

    def write(self, vals):
        if vals.get('item'):
            if len(vals.get('item')) != 3:
                vals['item'] = self.fill_zero(vals.get('item'))
            item = self.search([('item', '=', vals.get('item'))])
            if item:
                raise ValidationError(_("The item must be unique."))
        return super(ExpenditureItem, self).write(vals)

    @api.onchange('heading')
    def onchange_item(self):
        if self.heading:
            heading = self.heading
            self.cog_conac = heading.chapter or ''
            self.des_cog_conac = heading.name or ''
            self.concept_cog_conac = heading.concept or ''

    @api.onchange('unam_account_id')
    def _onchange_unam_account_id(self):
        if self.unam_account_id and len(self.unam_account_id.tag_ids.ids) > 0:
            # Prepare Expenditure Item SHCP and Description of expenditure item of SHCP From Account tags
            tag_code = ''
            tag_name = ''
            for tag in self.unam_account_id.tag_ids:
                split_list = str(tag.name).split(' ')
                if len(split_list) > 0:
                    tag_code += split_list[0]
                if len(split_list) > 1:
                    tag_name += ' '.join(split_list[1:])
            # Set Expenditure Item SHCP
            self.shcp = tag_code
            # Set Description of expenditure item of SHCP
            self.desc_shcp = tag_name
            # Set COG CONAC
            if self.unam_account_id.coa_conac_id:
                self.cog_id = self.unam_account_id.coa_conac_id.id
            else:
                self.cog_id = False
            # Set Description of COG CONAC
            if self.unam_account_id.conac_name:
                self.cog_desc = self.unam_account_id.conac_name
            else:
                self.cog_desc = False
            # Set Assign Account
            if self.unam_account_id.name:
                self.assigned_account = self.unam_account_id.name
            else:
                self.assigned_account = False

    def unlink(self):
        for item in self:
            program_code = self.env['program.code'].search([('item_id', '=', item.id)], limit=1)
            if program_code:
                raise ValidationError('You can not delete item which are mapped with program code!')
        return super(ExpenditureItem, self).unlink()

    def validate_item(self, item_string, typee):
        if len(str(item_string)) > 2:
            item_str = str(item_string).zfill(3)
            typee = str(typee).lower()
            if typee not in ['r', 'c', 'd']:
                typee = 'r'
            if item_str.isnumeric():
                item = self.search(
                    [('item', '=', item_str), ('exercise_type', '=', typee)], limit=1)
                if not item:
                    item = self.search(
                        [('item', '=', item_str)], limit=1)
                if item:
                    return item
        return False
