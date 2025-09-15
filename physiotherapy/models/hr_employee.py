from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    user_id = fields.Many2one('res.users', string="User")

    # @api.model
    # def create(self, vals):
    #     employee = super(HrEmployee, self).create(vals)
    #
    #     if employee.work_email and employee.name:
    #         user_vals = {
    #             'name': employee.name,
    #             'login': employee.work_email,
    #             'email': employee.work_email,
    #             'employee_id': employee.id,
    #         }
    #         user = self.env['res.users'].create(user_vals)
    #         employee.user_id = user.id
    #
    #     else:
    #         raise ValidationError("يجب إدخال اسم وبريد إلكتروني للموظف لإنشاء مستخدم مرتبط.")
    #
    #     return employee
    #
    # @api.model
    # def create(self, vals):
    #     employee = super().create(vals)
    #
    #     # Create user if not exists
    #     user = self.env['res.users'].create({
    #         'name': employee.name,
    #         'login': employee.work_email or f"emp_{employee.id}@example.com",
    #         'email': employee.work_email or f"emp_{employee.id}@example.com",
    #     })
    #
    #     employee.user_id = user.id
    #     return employee
