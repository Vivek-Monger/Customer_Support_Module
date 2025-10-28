# -*- coding: utf-8 -*-
# from odoo import http


# class CustomerSupportModule(http.Controller):
#     @http.route('/customer__support__module/customer__support__module', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/customer__support__module/customer__support__module/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('customer__support__module.listing', {
#             'root': '/customer__support__module/customer__support__module',
#             'objects': http.request.env['customer__support__module.customer__support__module'].search([]),
#         })

#     @http.route('/customer__support__module/customer__support__module/objects/<model("customer__support__module.customer__support__module"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('customer__support__module.object', {
#             'object': obj
#         })

