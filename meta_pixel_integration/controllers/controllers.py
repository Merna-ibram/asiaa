# -*- coding: utf-8 -*-
# from odoo import http


# class meta_pixel_integration(http.Controller):
#     @http.route('/meta_pixel_integration/meta_pixel_integration', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/meta_pixel_integration/meta_pixel_integration/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('meta_pixel_integration.listing', {
#             'root': '/meta_pixel_integration/meta_pixel_integration',
#             'objects': http.request.env['meta_pixel_integration.meta_pixel_integration'].search([]),
#         })

#     @http.route('/meta_pixel_integration/meta_pixel_integration/objects/<model("meta_pixel_integration.meta_pixel_integration"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('meta_pixel_integration.object', {
#             'object': obj
#         })

