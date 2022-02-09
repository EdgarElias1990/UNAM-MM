# -*- coding: utf-8 -*-
# from odoo import http


# class MmUnam(http.Controller):
#     @http.route('/mm_unam/mm_unam/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mm_unam/mm_unam/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mm_unam.listing', {
#             'root': '/mm_unam/mm_unam',
#             'objects': http.request.env['mm_unam.mm_unam'].search([]),
#         })

#     @http.route('/mm_unam/mm_unam/objects/<model("mm_unam.mm_unam"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mm_unam.object', {
#             'object': obj
#         })
