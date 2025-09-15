from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    announcement = fields.Char(size=140)
    show_widgets = fields.Boolean()
