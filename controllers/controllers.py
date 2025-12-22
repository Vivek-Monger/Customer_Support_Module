# from odoo import http


# class CustomerSupportModule(http.Controller):
#     @http.route('/customer_support_module/customer_support_module', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/customer_support_module/customer_support_module/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('customer_support_module.listing', {
#             'root': '/customer_support_module/customer_support_module',
#             'objects': http.request.env['customer_support_module.customer_support_module'].search([]),
#         })

#     @http.route('/customer_support_module/customer_support_module/objects/<model("customer_support_module.customer_support_module"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('customer_support_module.object', {
#             'object': obj
#         })

