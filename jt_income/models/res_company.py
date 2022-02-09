# -*- coding: utf-8 -*-

from odoo import fields,models,api,_

class company(models.Model):
	_inherit = "res.company"

	header_logo = fields.Binary(string="Header Logo1")
	header_logo2 = fields.Binary(string="Header Logo2")
	sign = fields.Binary(string="Sign")