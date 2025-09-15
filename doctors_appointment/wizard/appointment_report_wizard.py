from odoo import models, fields
from datetime import datetime, time
import base64
import calendar

class AppointmentReportWizard(models.TransientModel):
    _name = 'appointment.report.wizard'
    _description = 'Doctor Monthly Appointment Report Wizard'

    doctors_id = fields.Many2one('hr.employee', string="الدكتور", required=True)
    month = fields.Selection(
        [(str(i), calendar.month_name[i]) for i in range(1, 13)],
        string="الشهر",
        required=True
    )
    year = fields.Integer(string="السنة", required=True, default=lambda self: datetime.today().year)

    make_report = fields.Binary(string="تقرير PDF", readonly=True)
    report_name = fields.Char(string="اسم الملف")

    def action_generate_report(self):
        # تحويل الشهر والسنة إلى بداية ونهاية الشهر
        month = int(self.month)
        year = self.year
        start_date = datetime(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = datetime(year, month, last_day, 23, 59, 59)
        print('start_date',start_date)
        print('end_date',end_date)

        # البحث عن المواعيد
        appointments = self.env['patient.appointment'].search([
            ('doctors_id', '=', self.doctors_id.id),
            ('appointment_date', '>=', start_date),
            ('appointment_date', '<=', end_date),
            ('is_reserved', '=', True),
        ])

        print("Selected Doctor ID:", self.doctors_id.id)
        print("Selected Doctor Name:", self.doctors_id.name)
        print('appointments',appointments)

        # إعداد البيانات للتقرير
        data = {
            'doctor_name': self.doctors_id.name,
            'selected_month': f"{calendar.month_name[month]} {year}",
            'appointments': [
                {
                    'doctor_name': appt.doctors_id.name,
                    'patient_name': appt.patient_id.name,
                    'appointment_date': appt.appointment_date.strftime('%Y-%m-%d'),
                    'appointment_type': appt.appointment_type,
                    'done': 'تم' if appt.done else 'لم يتم',
                }
                for appt in appointments
            ],
        }

        # إنشاء التقرير
        try:
            report_action = self.env.ref('doctors_appointment.report_doctor_daily_appointments_action')
            pdf_content, _ = report_action._render_qweb_pdf(self.ids, data={'data': data})
        except:
            report_template = 'doctors_appointment.report_doctor_daily_appointments_template'
            pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                report_template,
                res_ids=self.ids,
                data={'data': data}
            )

        self.make_report = base64.b64encode(pdf_content)
        self.report_name = f"تقرير-{self.doctors_id.name}-{calendar.month_name[month]}-{year}.pdf"

        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content?model=appointment.report.wizard&id={self.id}&field=make_report&filename_field=report_name&download=true",
            'target': 'new',
        }