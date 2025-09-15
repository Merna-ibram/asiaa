# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """ Model for adding pixel id in settings SEO section. """
    _inherit = 'res.config.settings'

    meta_tracking = fields.Boolean(
        config_parameter='meta_pixel_tracking.meta_tracking', default=False,
        help='For enabling meta tracking in your website.',
        string="Meta tracking.")
    pixel_id = fields.Char(
        string='Pixel ID:', help='Enter your pixel ID here.',
        config_parameter='meta_pixel_tracking.pixel_id')

    all_buttons = fields.Many2one(
        'website.menu',  # Use the appropriate model to represent buttons in Odoo
        string="Object-Type Buttons",
        help="Select a button of type 'object' to link with this setting."
    )
    # website_id = fields.Many2one(
    #     'website',  # Assuming `website_id` is a Many2one field in `ir.ui.view`
    #     string="Website",
    #     related='all_buttons.website_id',  # Fetch `website_id` from the selected button
    #     help="Website linked to the selected button."
    # )

    @api.model
    def get_values(self):
        """Getting the values of the corresponding importing items"""
        res = super(ResConfigSettings, self).get_values()
        res['meta_tracking'] = self.env[
            'ir.config_parameter'].sudo().get_param('meta_tracking')
        res['pixel_id'] = self.env[
            'ir.config_parameter'].sudo().get_param('pixel_id')
        return res

    @api.model
    def set_values(self):
        """Setting the values of the corresponding importing items"""
        self.env['ir.config_parameter'].sudo().set_param(
            'meta_tracking', self.meta_tracking)
        self.env['ir.config_parameter'].sudo().set_param(
            'pixel_id', self.pixel_id)
        super(ResConfigSettings, self).set_values()


