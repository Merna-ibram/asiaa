from odoo import models, fields, api
from odoo.osv import expression

class AccountMove(models.Model):
    _inherit = "account.move"

    doctor = fields.Many2one('hr.employee', string='الأخصائي', readonly=True)



    @api.model
    def search_fetch(self, domain, field_names, offset=0, limit=None, order=None):
        user = self.env.user

        if user.has_group('invoice.group_doctor'):
            domain = expression.AND([
                domain,
                [('doctor.user_id', '=', user.id)]
            ])

        return super(AccountMove, self).search_fetch(domain, field_names, offset=offset, limit=limit, order=order)
