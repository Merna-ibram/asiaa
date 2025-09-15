from odoo import http
from odoo.http import request, route


class MenuBookmark(http.Controller):

    @route('/web/menu_bookmark/data', methods=['POST'], type='json', auth='user')
    def menu_bookmark_data(self, **kwargs):
        return request.env['menu.bookmark'].search_read([('user_id', '=', request.session.uid)], [])

    @route('/web/menu_bookmark/add', methods=['POST'], type='json', auth='user')
    def menu_bookmark_add(self, **kwargs):
        new_bookmark = {
            'name': kwargs.get('name'),
            'url': kwargs.get('url'),
            'user_id': request.session.uid,
        }
        return request.env['menu.bookmark'].create(new_bookmark).id
