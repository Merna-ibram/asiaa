from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    # is_specialist = fields.Boolean(string='Is Specialist')
    patient_ids = fields.One2many('res.partner', 'sales_person', string='My Patients')