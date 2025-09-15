from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime
import base64
import calendar

class DoctorInvoiceWizard(models.TransientModel):
    _name = 'doctor.invoice.wizard'
    _description = 'Doctor Invoice Report Wizard'

    month = fields.Selection(
        [(str(i), calendar.month_name[i]) for i in range(1, 13)],
        string="الشهر",
        required=True,
        default=lambda self: str(datetime.today().month)
    )
    year = fields.Integer(
        string="السنة",
        required=True,
        default=lambda self: datetime.today().year
    )
    make_report = fields.Binary(string="تقرير PDF", readonly=True)
    report_name = fields.Char(string="اسم الملف")

    def action_generate_report_invoice(self):
        month = int(self.month)
        year = self.year

        start_date = datetime(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = datetime(year, month, last_day, 23, 59, 59)

        # جلب الدكتور المرتبط بالمستخدم الحالي
        current_user = self.env.user
        doctor = current_user.employee_id or current_user.employee_ids[:1]
        if not doctor:
            raise ValidationError("⚠️ لا يوجد دكتور مرتبط بالمستخدم الحالي.")

        # البحث عن فواتير الدكتور
        invoices = self.env['account.move'].search([
            ('agents_name_invoice', '=', doctor.id),
            ('invoice_date', '>=', start_date),
            ('invoice_date', '<=', end_date),
            ('state', '=', 'posted'),
            ('move_type', '=', 'out_invoice')
        ])

        # حساب الإجماليات
        total_amount = sum(invoices.mapped('amount_untaxed'))
        total_commission = total_amount * 0.05
        invoices_count = len(invoices)
        doctor_salary = getattr(doctor, 'salary', 0)

        agents_data = [{
            'agent_name': doctor.name,
            'total_amount': total_amount,
            'total_commission': total_commission,
            'doctor_salary': doctor_salary,
            'invoices_count': invoices_count,
        }]

        data = {
            'selected_month': f"{calendar.month_name[month]} {year}",
            'total_amount': total_amount,
            'total_commission': total_commission,
            'doctor_salary': doctor_salary,
            'invoices_count': invoices_count,
            'has_data': bool(invoices),
            'agents_data': agents_data,
        }

        # إنشاء التقرير PDF
        report_template = 'appointments.doctor_report_invoices_template'
        pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
            report_template,
            res_ids=self.ids,
            data={'data': data}
        )

        self.make_report = base64.b64encode(pdf_content)
        self.report_name = f"تقرير-{calendar.month_name[month]}-{year}.pdf"

        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content?model=doctor.invoice.wizard&id={self.id}&field=make_report&filename_field=report_name&download=true",
            'target': 'new',
        }
