from odoo import api, models, fields
from datetime import datetime, timedelta
from odoo.osv import expression
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from pytz import timezone, UTC

class PatientAppointment(models.Model):
    _name = "patient.appointment"
    _description = "Patient Records"

    patient_id = fields.Many2one('res.partner', string="المريض")
    doctors_id = fields.Many2one('hr.employee', string="الأخصائي")
    appointment_date = fields.Datetime(string="تاريخ ووقت الموعد")
    appointment_type = fields.Selection([
        ('checkup', 'فحص'),
        ('treatment', 'علاج'),
        ('consultation', 'استشارة')
    ], string='نوع الموعد')

    observation = fields.Text(string="الملاحظات الطبية")
    pharmacy_line_ids = fields.One2many('patient.pharmacy.lines', 'appointment_id', string='بنود الصيدلية')
    patient_prescription_line_ids = fields.One2many('patient.prescription.line', 'prescription_id',
                                                    string='بنود الروشتة')
    total_amount = fields.Float(string="إجمالي المبلغ", compute="_compute_total_amount", store=True)
    done = fields.Boolean(string="تم", default=False)
    notes = fields.Text(string="ملاحظات")
    is_reserved = fields.Boolean(string="محجوز؟", default=False)
    is_this_week = fields.Boolean(string="هذا الأسبوع", compute='_compute_is_this_week', store=False)

    @api.onchange('patient_id')
    def _onchange_patient_id(self):
        if self.patient_id and self.patient_id.doctor:
            self.doctors_id = self.patient_id.doctor
        else:
            self.doctors_id = False

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

    @api.depends('pharmacy_line_ids.total')
    def _compute_total_amount(self):
        for appointment in self:
            appointment.total_amount = sum(line.total for line in appointment.pharmacy_line_ids)

    def patient_report_sheet(self):
        data = {
            'patient_id': self.patient_id,
            'appointment_type': self.appointment_type,
            'appointment_date': self.appointment_date,
            'observation': self.observation,
            'total_amount': self.total_amount,
            'doctors_id': self.doctors_id,
        }

    @api.model
    def search_fetch(self, domain, field_names, offset=0, limit=None, order=None):
        user = self.env.user
        if user.has_group('doctors_appointment.group_doctors_appointment_doctor'):
            domain = expression.AND([
                domain,
                [('doctors_id.user_id', '=', user.id)]])
        return super(PatientAppointment, self).search_fetch(
            domain, field_names, offset=offset, limit=limit, order=order)

    def write(self, vals):
        for rec in self:
            if 'doctors_id' in vals and vals['doctors_id'] != rec.doctors_id.id:
                new_vals = rec.copy_data()[0]
                new_vals['doctors_id'] = vals['doctors_id']
                self.env['patient.appointment'].create(new_vals)
                return True
        return super(PatientAppointment, self).write(vals)

    @api.constrains('doctors_id', 'appointment_date')
    def _check_doctor_appointment_conflict(self):
        user_tz = self.env.user.tz or 'UTC'
        tz = timezone(user_tz)

        for rec in self:
            if rec.doctors_id and rec.appointment_date:
                start_range = rec.appointment_date - timedelta(minutes=29)
                end_range = rec.appointment_date + timedelta(minutes=29)

                conflict_appointments = self.search([
                    ('id', '!=', rec.id),
                    ('doctors_id', '=', rec.doctors_id.id),
                    ('appointment_date', '>=', start_range),
                    ('appointment_date', '<=', end_range)
                ])
                if conflict_appointments:
                    conflict_info = "\n".join(
                        f"• عند {UTC.localize(appt.appointment_date).astimezone(tz).strftime('%Y-%m-%d %H:%M')}"
                        for appt in conflict_appointments
                    )
                    raise ValidationError(
                        f"⚠ لا يمكن حجز ميعاد لنفس الدكتور خلال 30 دقيقة من ميعاد آخر.\nالمواعيد المتعارضة:\n{conflict_info}"
                    )
class PatientPharmacyLines(models.Model):
    _name = "patient.pharmacy.lines"
    _description = "Patient Pharmacy Lines"

    medicine_id = fields.Many2one('product.product', string="Medicine")
    quantity = fields.Integer(string="Quantity")
    unit_price = fields.Float(string="Unit Price")
    total = fields.Float(string="Total", compute="_compute_total", store=True)
    appointment_id = fields.Many2one('patient.appointment', string="Appointment")
    in_prescription = fields.Boolean(default=False, string='In Prescription')

    @api.depends('quantity', 'unit_price')
    def _compute_total(self):
        for line in self:
            line.total = line.quantity * line.unit_price

    def addto_prescription(self):
        return {
            'name': 'Add Medicine to Prescription',
            'view_mode': 'form',
            'res_model': 'patient.prescription.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_medicine_id': self.medicine_id.id,
                'default_appointment_id': self.appointment_id.id,
                'default_treatment_id': self.id,
            }
        }

    def action_remove_from_prescription(self):
        prescription_lines = self.env['patient.prescription.line'].search([
            ('medicine_id', '=', self.medicine_id.id),
            ('prescription_id', '=', self.appointment_id.id)
        ])
        if prescription_lines:
            prescription_lines.unlink()
            self.in_prescription = False
        return {'type': 'ir.actions.act_window_close'}

class PatientPrescriptionLine(models.Model):
    _name = 'patient.prescription.line'
    _description = 'Patient Prescription Line'

    medicine_id = fields.Many2one('product.product', string="Medicine")
    prescription_id = fields.Many2one('patient.appointment', string="Appointment")
    dosage = fields.Char(string="Dosage")
