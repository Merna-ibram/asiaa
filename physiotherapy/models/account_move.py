from collections import defaultdict

from odoo import models, fields, api
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo.osv import expression
from odoo.tools import frozendict


class AccountMove(models.Model):
    _inherit = 'account.move'

    start_date = fields.Date(string="تاريخ بداية الاشتراك")
    months = fields.Integer(string="عدد أشهر الاشتراك")
    # end_date = fields.Date(string="تاريخ انتهاء الاشتراك", compute="_compute_end_date", store=True)
    doctor = fields.Many2one('hr.employee', string='الأخصائي', readonly=True)
    code = fields.Char(related='partner_id.code', readonly=1, string="الكود")
    age = fields.Integer(related='partner_id.age', string="العمر")
    gender = fields.Selection(related='partner_id.gender', string="النوع")
    national_address = fields.Text(related='partner_id.national_address', string="العنوان الوطني")
    mobile = fields.Char(related='partner_id.mobile', string="رقم الموبايل", store=True)

    invoice_created_months = fields.Integer(string="عدد الفواتير المنشأة", default=0)
    agents_name_invoice = fields.Many2many(
        'res.partner',
        string='الوكيل',
        readonly=1
    )
    agents_name = fields.One2many(
        'res.partner',
        compute='_compute_agents_from_invoice_partner_move',
        string='الوكيل',
    )

    # doctor_user_id = fields.Many2one('res.users', compute='_compute_doctor_user_id', store=True)
    #
    # @api.depends('partner_id.doctor.user_id')
    # def _compute_doctor_user_id(self):
    #     for rec in self:
    #         rec.doctor_user_id = rec.partner_id.doctor.user_id

    # search_mobile = fields.Char(string="بحث بالموبايل", compute="_compute_dummy_mobile", store=False)
    #
    # @api.depends('partner_id.mobile')
    # def _compute_dummy_mobile(self):
    #     for rec in self:
    #         rec.search_mobile = ''
    #
    # def _search_search_mobile(self, operator, value):
    #     return [('partner_id.mobile', operator, value)]

    # @api.depends('partner_id')
    # def _compute_agents_from_invoice_partner_move(self):
    #     for line in self:
    #         partner = line.partner_id
    #         if  partner:
    #             line.agents_name_invoice = partner.agent_ids
    #         else:
    #             line.agents_name_invoice = False
    # @api.depends('date', 'months')
    # def _compute_end_date(self):
    #     for record in self:
    #         if record.date and record.months:
    #             record.end_date = record.date + relativedelta(months=record.months)
    #         else:
    #             record.end_date = False

    @api.model
    def create(self, vals):
        if   not vals.get('invoice_date'):
            vals['invoice_date'] = fields.Date.today()
            vals['agents_name_invoice']=vals.get('invoice_line_ids.agents')
        return super(AccountMove, self).create(vals)

    def create_subscription_invoices(self):
        subscription_invoices = self.search([
            ('move_type', '=', 'out_invoice'),
            ('state', '!=', 'cancel'),
            ('months', '>=', 0),
            ('start_date', '!=', False),
        ])

        totals_by_partner_month = defaultdict(float)
        salary_by_partner = {}

        for record in subscription_invoices:
            months_total = record.months
            start_date = record.start_date
            end_date = start_date + relativedelta(months=months_total)
            invoice_template = record
            partner_name = record.partner_id.name
            salary = record.partner_id.salary or 0.0
            salary_by_partner[partner_name] = salary

            for month_index in range(1, months_total):
                current_invoice_date = start_date + relativedelta(months=month_index)

                existing = self.search_count([
                    ('move_type', '=', 'out_invoice'),
                    ('state', '!=', 'cancel'),
                    ('partner_id', '=', record.partner_id.id),
                    ('invoice_date', '=', current_invoice_date),
                ])

                if existing:
                    continue

                line_vals = []
                monthly_total = 0.0

                for line in invoice_template.invoice_line_ids:
                    line_total = line.quantity * line.price_unit
                    monthly_total += line_total

                    line_vals.append((0, 0, {
                        'name': line.name,
                        'quantity': line.quantity,
                        'price_unit': line.price_unit,
                        'product_id': line.product_id.id,
                        'account_id': line.account_id.id,
                        'tax_ids': [(6, 0, line.tax_ids.ids)],
                    }))

                invoice_vals = {
                    'move_type': 'out_invoice',
                    'partner_id': record.partner_id.id,
                    'start_date': current_invoice_date,
                    'invoice_date': current_invoice_date,
                    'date': current_invoice_date,
                    'months': 1,
                    'invoice_line_ids': line_vals,
                }

                self.create(invoice_vals)

                totals_by_partner_month[(partner_name, current_invoice_date.strftime('%Y-%m'))] += monthly_total

            record.invoice_created_months = months_total

        print("\n===== Monthly Totals by Partner =====")
        for (partner_name, month), total in sorted(totals_by_partner_month.items()):
            salary = salary_by_partner.get(partner_name, 0.0)
            print(f"Partner: {partner_name}, Month: {month}, Total: {total:.2f}, Salary: {salary:.2f}")
            if total == salary * 2:
                print('dd')
                self.commission_total=salary+ 0.05

                print(self.commission_total)

    # @api.model
    # def create(self, vals):
    #     move = super().create(vals)
    #     print('invoice')
    #     if vals.get("move_type") == "out_invoice":
    #         partner = self.env['res.partner'].browse(vals['partner_id'])
    #         salary = partner.salary or 0.0
    #         print(salary)
    #         print(move.start_date)
    #
    #         # Check if invoice_date exists before processing
    #         if not move.start_date:
    #             print("Invoice date is not set, skipping commission calculation")
    #             return move
    #
    #         from calendar import monthrange
    #         year = move.start_date.year
    #         month = move.start_date.month
    #
    #         # First day of the month
    #         month_start = move.start_date.replace(day=1)
    #
    #         # Last day of the month (handles varying month lengths)
    #         last_day = monthrange(year, month)[1]
    #         month_end = move.start_date.replace(day=last_day)
    #
    #         print(f"Month range: {month_start} to {month_end}")
    #
    #         domain = [
    #             ('move_type', '=', 'out_invoice'),
    #             ('state', '!=', 'cancel'),
    #             ('partner_id', '=', partner.id),
    #             ('invoice_date', '>=', month_start),
    #             ('invoice_date', '<=', month_end)
    #         ]
    #         invoices = self.search(domain)
    #         print(invoices)
    #         total_month = sum(inv.amount_total for inv in invoices)
    #         print(total_month)
    #
    #         if salary > 0 and total_month >= 2 * salary:
    #             move.commission_total = salary + (salary * 0.15)
    #             move.message_post(body="Commission Auto Set: Total invoices this month exceed 2x salary.")
    #
    #     return move
    #
    @api.model
    def search_fetch(self, domain, field_names, offset=0, limit=None, order=None):
        user = self.env.user

        # Check if user is in the doctor group
        if user.has_group('doctors_appointment.group_doctors_appointment_doctor'):
            domain = expression.AND([
                domain,
                [('partner_id.doctor.user_id', '=', user.id)]
            ])

        return super(AccountMove, self).search_fetch(
            domain, field_names, offset=offset, limit=limit, order=order
        )


    def action_post(self):

        for rec in self:
            rec.agents_name_invoice=rec.invoice_line_ids.agents
        return super(AccountMove,self).action_post()




class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def create(self, vals):
        move = self.env['account.move'].browse(vals.get('move_id'))
        partner = move.partner_id
        # لو المريض له عنوان وطني، نشيل الضرائب
        if partner and partner.national_address:
            vals['tax_ids'] = [(5, 0, 0)]
        return super().create(vals)

    def write(self, vals):
        for line in self:
            partner = line.move_id.partner_id
            if partner and partner.national_address:
                vals['tax_ids'] = [(5, 0, 0)]
        return super().write(vals)

    @api.depends('tax_ids', 'currency_id', 'partner_id', 'analytic_distribution', 'balance', 'partner_id',
                 'move_id.partner_id', 'price_unit', 'quantity')
    def _compute_all_tax(self):
        for line in self:
            sign = line.move_id.direction_sign

            if not line.tax_ids:
                line.compute_all_tax = {}
                line.compute_all_tax_dirty = False
                continue

            if line.display_type == 'tax':
                line.compute_all_tax = {}
                line.compute_all_tax_dirty = False
                continue

            if line.display_type == 'product' and line.move_id.is_invoice(True):
                amount_currency = sign * line.price_unit * (1 - line.discount / 100)
                handle_price_include = True
                quantity = line.quantity
            else:
                amount_currency = line.amount_currency
                handle_price_include = False
                quantity = 1

            compute_all_currency = line.tax_ids.compute_all(
                amount_currency,
                currency=line.currency_id,
                quantity=quantity,
                product=line.product_id,
                partner=line.move_id.partner_id or line.partner_id,
                is_refund=line.is_refund,
                handle_price_include=handle_price_include,
                include_caba_tags=line.move_id.always_tax_exigible,
                fixed_multiplicator=sign,
            )

            rate = line.amount_currency / line.balance if line.balance else 1
            line.compute_all_tax_dirty = True
            line.compute_all_tax = {
                frozendict({
                    'tax_repartition_line_id': tax['tax_repartition_line_id'],
                    'group_tax_id': tax['group'] and tax['group'].id or False,
                    'account_id': tax['account_id'] or line.account_id.id,
                    'currency_id': line.currency_id.id,
                    'analytic_distribution': (tax['analytic'] or not tax[
                        'use_in_tax_closing']) and line.analytic_distribution,
                    'tax_ids': [(6, 0, tax['tax_ids'])],
                    'tax_tag_ids': [(6, 0, tax['tag_ids'])],
                    'partner_id': line.move_id.partner_id.id or line.partner_id.id,
                    'move_id': line.move_id.id,
                    'display_type': line.display_type,
                }): {
                    'name': tax['name'] + (' ' + _('(Discount)') if line.display_type == 'epd' else ''),
                    'balance': tax['amount'] / rate,
                    'amount_currency': tax['amount'],
                    'tax_base_amount': tax['base'] / rate * (-1 if line.tax_tag_invert else 1),
                }
                for tax in compute_all_currency['taxes']
                if tax['amount']
            }

            if not line.tax_repartition_line_id:
                line.compute_all_tax[frozendict({'id': line.id})] = {
                    'tax_tag_ids': [(6, 0, compute_all_currency['base_tags'])],
                }



