# from odoo import models, fields, api
#
# class DoctorAppointment(models.Model):
#     _name = 'doctor.appointment'
#     _description = 'Doctor Appointment'
#     _order = 'appointment_date desc'
#
#     # name = fields.Char(string="وصف الموعد", required=True)
#     patient_id = fields.Many2one('res.partner', string="Patient")
#     appointment_id = fields.Many2one(
#         'patient.appointment',
#         string="موعد المريض",
#         domain="[('patient_id', '=', patient_id)]"
#     )
#     appointment_date = fields.Datetime(string="تاريخ ووقت الموعد")
#
#     # patient_id = fields.Many2one('res.partner', string="Patient")
#
#     doctors_id = fields.Many2one('hr.employee', string="الاخصائي",related='patient_id.doctor', store=True)
#
#     notes = fields.Text(string="ملاحظات")
#     is_reserved = fields.Boolean(string="محجوز؟", default=False)

from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

from odoo import models, fields, api


class DoctorAppointment(models.Model):
    _name = 'doctor.appointment'
    _description = 'Doctor Appointment'
    _order = 'appointment_date desc'

    patient_id = fields.Many2one('res.partner', string="المريض")
    appointment_id = fields.Many2one(
        'patient.appointment',
        string="موعد المريض",
        domain="[('patient_id', '=', patient_id)]"
    )
    appointment_date = fields.Datetime(string="تاريخ ووقت الموعد")

    doctors_id = fields.Many2one('hr.employee', string="الأخصائي", related='patient_id.doctor', store=True)
    notes = fields.Text(string="ملاحظات")
    is_reserved = fields.Boolean(string="محجوز؟", default=False)

    is_this_week = fields.Boolean(string="هذا الأسبوع", compute='_compute_is_this_week', store=False)

    @api.depends('appointment_date')
    def _compute_is_this_week(self):
        today = fields.Date.context_today(self)
        start_of_week = today - timedelta(days=today.weekday())  # يوم الاثنين
        end_of_week = start_of_week + timedelta(days=6)  # الأحد

        for rec in self:
            if rec.appointment_date:
                date_only = rec.appointment_date.date()
                rec.is_this_week = start_of_week <= date_only <= end_of_week
            else:
                rec.is_this_week = False








