from datetime import date
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.osv import expression


class Registration(models.Model):
    _inherit = 'res.partner'
    _description = 'Registration'

    is_patient = fields.Boolean(string="مريض")
    code = fields.Char(default='new', readonly=1, string="الكود")
    birth_date = fields.Date(string="تاريخ الميلاد")
    age = fields.Integer(string="العمر", compute="_compute_age", store=True)
    gender = fields.Selection([
        ('m', 'Male'),
        ('f', 'Female'),
        ('unknown', 'Unknown'),
    ], string="النوع")

    tax_number = fields.Char(string="الرقم الضريبي")

    nationality_id = fields.Many2one('res.country', string="الجنسية")
    state_code = fields.Char(string="كود الدولة")
    national_address = fields.Text(string="العنوان الوطني")
    identity_info = fields.Text(string="رقم الهوية")

    doctor = fields.Many2one('hr.employee', string='الأخصائي')
    sales_person = fields.Many2one('res.users', string='الأخصائي')

    diagnosis = fields.Char(string="التشخيص", tracking=True)

    # Past History
    rta = fields.Boolean(string="RTA")
    sport_injury = fields.Boolean(string="Sport Injury")
    electrical_shock = fields.Boolean(string="Electrical Shock")
    burn = fields.Boolean(string="Burn")
    lifting_heavy_object = fields.Boolean(string="Lifting Heavy Object")
    no_history_of_trauma = fields.Boolean(string="No History of Trauma")
    duration = fields.Char(string="Duration")

    # Medical history
    htn = fields.Boolean(string="HTN")
    dm = fields.Boolean(string="D.M")
    osteoporosis = fields.Boolean(string="Osteoporosis")
    cardiac_problems = fields.Boolean(string="Cardiac Problems")
    other_medical = fields.Char(string="Other Medical")
    surgical_history = fields.Text(string="Surgical History")

    # Chief Complaint
    pain = fields.Boolean(string="Pain")
    stiffness = fields.Boolean(string="Stiffness")
    weakness = fields.Boolean(string="Weakness")
    neuro_deficit = fields.Boolean(string="Neurological Deficit")
    other_chief = fields.Text(string="Other Complaint")

    # Pain Description
    onset = fields.Char(string="Onset")
    pain_localized = fields.Boolean(string="Localized")
    pain_radiated = fields.Boolean(string="Radiated")
    pain_constant = fields.Boolean(string="Constant")
    pain_intermittent = fields.Boolean(string="Intermittent")
    aggravated_by = fields.Text(string="Aggravated By", tracking=True)
    relieved_by = fields.Text(string="Relieved By", tracking=True)

    # Patient condition on arrival
    patient_wheelchair = fields.Boolean(string="Wheelchair")
    patient_assistive = fields.Boolean(string="Walking with assistive device")
    patient_carried = fields.Boolean(string="Carried by mother")
    patient_on_bed = fields.Boolean(string="On bed")
    patient_normal = fields.Boolean(string="Walking normal")
    gait_other = fields.Char(string="Gait - Other")

    # Consciousness
    oriented = fields.Boolean(string="Oriented")
    confused = fields.Boolean(string="Confused")
    vegetated = fields.Boolean(string="Vegetated")
    conscious_other = fields.Char(string="Conscious - Other")

    # Risk of falls
    risk_time = fields.Char(string="Time (seconds)")
    risk_level = fields.Selection([
        ('no', 'No Risk'),
        ('mild', 'Mild Risk'),
        ('moderate', 'Moderate Risk'),
        ('high', 'High Risk')
    ], string="Risk of Falls")

    # Session details
    session = fields.Char(string="Session")
    lazer = fields.Char(string="Lazer")
    shock_wave = fields.Char(string="Shock Wave")
    traction = fields.Char(string="Traction")

    # Symptoms
    edema = fields.Boolean(string="Edema")
    swelling = fields.Boolean(string="Swelling")
    redness = fields.Boolean(string="Redness")
    hotness = fields.Boolean(string="Hotness")
    muscle_weakness = fields.Boolean(string="Muscle Weakness")
    muscle_spasm = fields.Boolean(string="Muscle Spasm")
    muscle_atrophy = fields.Boolean(string="Muscle Atrophy")

    deformity = fields.Text(string="Deformity")

    # Examination
    neuro_exam = fields.Text(string="Neurological Examination")
    active_rom = fields.Text(string="Active Range of Motion")
    passive_rom = fields.Text(string="Passive Range of Motion")
    muscle_test = fields.Text(string="Manual Muscle Test")
    special_test = fields.Text(string="Special Test")

    show_appointment_button = fields.Boolean(compute="_compute_show_appointment_button")

    @api.depends('is_patient')
    def _compute_show_appointment_button(self):
        for rec in self:
            rec.show_appointment_button = rec.is_patient

    # @api.constrains('is_patient', 'doctor')
    # def _check_required_fields_for_patient(self):
    #     for rec in self:
    #         if rec.is_patient:
    #             if not rec.doctor:
    #                 raise ValidationError("يجب تحديد الأخصائي للمريض.")

    def _is_reception_staff(self):
        return self.env.user.has_group('physiotherapy.group_contact_recption')

    agent_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="partner_agent_rel",
        column1="partner_id",
        column2="agent_id",
        readonly=False,
        string="Agents",
        compute='_get_agents',
        store=True
    )

    @api.depends('doctor')
    def _get_agents(self):
        for rec in self:
            partner = self.env['res.partner'].search([('name', '=', rec.doctor.name)])
            if partner:
                rec.agent_ids = [(6, 0, partner.ids)]
            else:
                rec.agent_ids = [(5, 0, 0, [])]

    @api.onchange('nationality_id')
    def _onchange_nationality(self):
        if self.nationality_id:
            self.state_code = self.nationality_id.state_code
        else:
            self.state_code = False

    @api.onchange('state_code')
    def _onchange_state_code(self):
        if self.state_code:
            country = self.env['res.country'].search([('state_code', '=', self.state_code)], limit=1)
            self.nationality_id = country if country else False
        else:
            self.nationality_id = False

    @api.model
    def create(self, vals):
        res = super(Registration, self).create(vals)

        # Generate patient code
        if res.code == 'new':
            sequence = self.env['ir.sequence'].next_by_code('registration_seq')
            if sequence:
                res.code = sequence

        # Create my.cases record automatically
        if vals.get('is_patient'):
            self.env['my.cases'].create({
                'patient_id': res.id,
                'doctor': res.doctor.id,
            })

        # if vals.get('is_patient'):
        #     self.env['patient.appointment'].create({
        #         'patient_id': res.id,
        #         'doctors_id': res.doctor.id if res.doctor else False,
        #         'appointment_date': fields.Datetime.now(),
        #         'appointment_type': 'checkup',
        #         'is_reserved': 'true',
        #     })

        return res

    def write(self, vals):
        for rec in self:
            old_doctor = rec.doctor
            res = super(Registration, rec).write(vals)
            new_doctor = rec.doctor

            # إذا تم تغيير الدكتور فعليًا وكان المريض
            if rec.is_patient and 'doctor' in vals and old_doctor != new_doctor:
                # 1. سجل جديد في my.cases
                self.env['my.cases'].create({
                    'patient_id': rec.id,
                    'doctor': new_doctor.id
                })

                # 2. إنشاء موعد جديد بناءً على آخر موعد
                # last_appointment = self.env['patient.appointment'].search(
                #     [('patient_id', '=', rec.id)],
                #     order='appointment_date desc',
                #     limit=1
                # )
                # if last_appointment:
                #     appointment_vals = last_appointment.copy_data()[0]
                #     appointment_vals.update({
                #         'doctors_id': new_doctor.id,
                #         'appointment_date': fields.Datetime.now(),
                #         'appointment_type': 'checkup',
                #         'is_reserved': True,
                #     })
                #     self.env['patient.appointment'].create(appointment_vals)

                # 3. إنشاء فاتورة جديدة بناءً على آخر فاتورة
                last_invoice = self.env['account.move'].search([
                    ('partner_id', '=', rec.id),
                    ('move_type', '=', 'out_invoice'),
                    ('state', '!=', 'cancel')
                ], order='invoice_date desc', limit=1)
                if last_invoice:
                    invoice_vals = last_invoice.copy_data()[0]
                    invoice_vals.update({
                        'doctor': new_doctor.id,
                        'invoice_date': fields.Date.today(),
                        'start_date': fields.Date.today(),
                    })
                    self.env['account.move'].create(invoice_vals)

        return res

    @api.depends('birth_date')
    def _compute_age(self):
        for rec in self:
            if rec.birth_date:
                today = date.today()
                rec.age = today.year - rec.birth_date.year - (
                        (today.month, today.day) < (rec.birth_date.month, rec.birth_date.day)
                )
            else:
                rec.age = 0

    @api.onchange('birth_date')
    def _onchange_birth_date(self):
        if self.birth_date:
            today = date.today()
            self.age = today.year - self.birth_date.year - (
                    (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        else:
            self.age = 0

    @api.model
    def search_fetch(self, domain, field_names, offset=0, limit=None, order=None):
        user = self.env.user

        # If user is reception staff, they can see all patients but limited fields
        if user.has_group('physiotherapy.module_contact_access'):
            # Reception staff can see all patients
            pass
        elif user.has_group('physiotherapy.group_contact_recption'):
            # Doctors can only see their own patients
            domain = expression.AND([
                domain,
                ['|',
                 ('is_patient', '=', False),  # عرض كل السجلات التي ليست مرضى
                 '&',
                 ('is_patient', '=', True),  # لكن إذا كانت مريض
                 ('doctor.user_id', '=', user.id)  # يشترط أن يكون الطبيب المستخدم الحالي
                 ]
            ])

        return super(Registration, self).search_fetch(domain, field_names, offset=offset, limit=limit, order=order)

    def appointment(self):
        return {
            'name': 'Doctor Appointment',
            'type': 'ir.actions.act_window',
            'res_model': 'patient.appointment',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_patient_id': self.id,
                'default_doctors_id': self.doctor.id if self.doctor else False,
                'default_appointment_type': 'checkup',  # لو فيه نوع افتراضي
            }
        }

class CountryInherit(models.Model):
    _inherit = 'res.country'

    state_code = fields.Char(string="كود الدولة", copy=False)

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.name} [{record.state_code}]" if record.state_code else record.name
            result.append((record.id, name))
        return result

    @api.model
    def create_unknown_country(self):
        """Create 'Unknown' country if not exists."""
        if not self.search([('code', '=', 'UNKN')], limit=1):
            self.create({
                'name': 'Unknown',
                'code': 'UNKN',
                'state_code': '000'
            })

    def init(self):
        """Run automatically when module is installed/updated."""
        self.create_unknown_country()

    @api.model
    def create(self, vals):
        return super(CountryInherit, self).create(vals)

    @api.model
    def assign_missing_state_codes(self):
        code = 101
        countries = self.search([], order='id')
        for country in countries:
            if not country.state_code or country.state_code == 'new':
                while str(code) in countries.mapped('state_code'):
                    code += 1
                country.state_code = str(code)
                code += 1

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = args[:]

        if name:
            domain = ['|', ('name', operator, name), ('state_code', operator, name)] + domain
        return self.search(domain, limit=limit).name_get()
