# Copyright 2020 Tecnativa - Manuel Calero
# Copyright 2014-2022 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from collections import defaultdict

from lxml import etree

from odoo import _, api, exceptions, fields, models, Command


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends('partner_id')
    def _compute_new_customer(self):
        for rec in self:
            rec.new_customer = rec.partner_id.new_customer
    commission_total = fields.Float(
        string="Commissions",readonly=1
    )
    partner_agent_ids = fields.Many2many(
        string="Agents",
        comodel_name="res.partner",
        compute="_compute_agents",
        search="_search_agents",
    )
    settlement_count = fields.Integer(compute="_compute_settlement")
    settlement_ids = fields.One2many(
        "commission.settlement",
        string="Settlements",
        compute="_compute_settlement",
    )
    new_customer = fields.Boolean(compute="_compute_new_customer", store=True)

    def action_view_settlement(self):
        xmlid = "commission.action_commission_settlement"
        action = self.env["ir.actions.actions"]._for_xml_id(xmlid)
        action["context"] = {}
        settlements = self.mapped("settlement_ids")
        if not settlements or len(settlements) > 1:
            action["domain"] = [("id", "in", settlements.ids)]
        elif len(settlements) == 1:
            res = self.env.ref("commission.view_settlement_form", False)
            action["views"] = [(res and res.id or False, "form")]
            action["res_id"] = settlements.id
        return action

    def _compute_settlement(self):
        for invoice in self:
            settlements = invoice.invoice_line_ids.settlement_id
            invoice.settlement_ids = settlements
            invoice.settlement_count = len(settlements)

    @api.depends("partner_agent_ids", "invoice_line_ids.agent_ids.agent_id")
    def _compute_agents(self):
        for move in self:
            move.partner_agent_ids = [
                (6, 0, move.mapped("invoice_line_ids.agent_ids.agent_id").ids)
            ]

    @api.model
    def _search_agents(self, operator, value):
        ail_agents = self.env["account.invoice.line.agent"].search(
            [("agent_id", operator, value)]
        )
        return [("id", "in", ail_agents.mapped("object_id.move_id").ids)]

    # @api.depends("line_ids.agent_ids.amount")
    # def _compute_commission_total(self):
    #     for record in self:
    #         record.commission_total = 0.0
    #         for line in record.line_ids:
    #             record.commission_total += sum(x.amount for x in line.agent_ids)

    def action_post(self):
        """Put settlements associated to the invoices in invoiced state."""
        if self.partner_id.new_customer:
            self.partner_id.new_customer = False
            self.partner_id.agent_ids.new_customer_count = self.partner_id.agent_ids.new_customer_count + 1
        self.mapped("line_ids.settlement_id").write({"state": "invoiced"})
        return super().action_post()

    def button_cancel(self):
        """Check settled lines and put settlements associated to the invoices in
        exception.
        """
        if any(self.mapped("invoice_line_ids.any_settled")):
            raise exceptions.ValidationError(
                _("You can't cancel an invoice with settled lines"),
            )
        self.mapped("line_ids.settlement_id").write({"state": "except_invoice"})
        return super().button_cancel()

    def recompute_lines_agents(self):
        self.mapped("invoice_line_ids").recompute_agents()

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        """Inject in this method the needed context for not removing other
        possible context values.
        """
        res = super(AccountMove, self).fields_view_get(
            view_id=view_id,
            view_type=view_type,
            toolbar=toolbar,
            submenu=submenu,
        )
        if view_type == "form":
            invoice_xml = etree.XML(res["arch"])
            invoice_line_fields = invoice_xml.xpath("//field[@name='invoice_line_ids']")
            if invoice_line_fields:
                invoice_line_field = invoice_line_fields[0]
                context = invoice_line_field.attrib.get("context", "{}").replace(
                    "{",
                    "{'partner_id': partner_id, ",
                    1,
                )
                invoice_line_field.attrib["context"] = context
                res["arch"] = etree.tostring(invoice_xml)
        return res



    def action_post(self):
        # First call the original action_post
        res = super().action_post()

        # Now apply our commission logic
        for move in self:
            print('Invoice posted')
            agents = move.invoice_line_ids.mapped('agents')
            if agents:
                move.agents_name_invoice = [(6, 0, agents.ids)]

            if move.move_type == "out_invoice" and move.partner_id:
                partner = move.partner_id

                # Loop through all agents for the partner
                for agent in partner.agent_ids:
                    print(f"\nAgent: {agent.name}")
                    print(f"Salary: {agent.salary}")

                    # Get all customers with this agent
                    customers = self.env['res.partner'].search([
                        ('agent_ids', 'in', agent.id)
                    ])

                    print(move.agents_name_invoice)

                    # Make sure the current partner is included in customers
                    if partner.id not in customers.ids:
                        customers |= partner

                    # Get all posted invoices for these customers including the current one
                    invoices = self.env['account.move'].search([
                        ('move_type', '=', 'out_invoice'),
                        ('agents_name_invoice', 'in', move.agents_name_invoice.ids),
                        ('state', 'in', ['posted']),
                        ('invoice_date', '!=', False),
                    ])
                    print(invoices)

                    # Group totals by month name
                    monthly_totals = defaultdict(float)
                    for inv in invoices:
                        if inv.invoice_date:
                            month_name = inv.invoice_date.strftime('%B')  # January, February, etc.
                            monthly_totals[month_name] += inv.amount_untaxed

                    # Ordered month names for display
                    ordered_months = [
                        'January', 'February', 'March', 'April', 'May', 'June',
                        'July', 'August', 'September', 'October', 'November', 'December'
                    ]

                    # Get current invoice details
                    invoice_date = move.invoice_date or fields.Date.today()
                    current_month_name = invoice_date.strftime('%B')
                    current_invoice_total = move.amount_untaxed
                    monthly_invoice_total = monthly_totals.get(current_month_name, 0.0)
                    salary_threshold = move.agents_name_invoice.salary * 2
                    print('salary_threshold', salary_threshold)

                    # Display monthly totals for debugging
                    for month in ordered_months:
                        total = monthly_totals.get(month, 0.0)
                        print(f"Agent: {agent.name}, Month: {month}, Total: {total:.2f}")
                        if month == current_month_name:
                            print(f"?? Current Invoice Total This Month: {monthly_invoice_total:.2f}")

                    print(f"Current invoice amount: {current_invoice_total:.2f}")
                    print(f"Monthly total: {monthly_invoice_total:.2f}")
                    print(f"Salary threshold (salary * 2): {salary_threshold:.2f}")
                    print('all invoice', current_invoice_total + monthly_invoice_total)

                    # Commission calculation logic
                    commission_calculated = False

                    # Check if monthly total >= salary * 2
                    if monthly_invoice_total == salary_threshold:
                        move.commission_total = salary_threshold * 0.05
                        commission_calculated = True
                        print(f"? Commission triggered by monthly total: {move.commission_total:.2f}")
                        print(f"   Monthly total ({monthly_invoice_total:.2f}) >= Threshold ({salary_threshold:.2f})")

                    if monthly_invoice_total > salary_threshold:
                        move.commission_total = (monthly_invoice_total)* 0.05
                        commission_calculated = True
                        print(f"? Commission triggered by monthly total: {move.commission_total:.2f}")
                        print(f"   Monthly total ({monthly_invoice_total:.2f}) >= Threshold ({salary_threshold:.2f})")

                    # Check if current invoice alone >= salary * 2
                    if current_invoice_total == salary_threshold and monthly_invoice_total < salary_threshold :
                        move.commission_total = salary_threshold * 0.05
                        commission_calculated = True
                        print(f"? Commission triggered by single invoice: {move.commission_total:.2f}")
                        print(f"   Invoice amount ({current_invoice_total:.2f}) >= Threshold ({salary_threshold:.2f})")


                    if current_invoice_total > salary_threshold:
                        move.commission_total = (current_invoice_total) * 0.05
                        commission_calculated = True
                        print(f"? Commission triggered by single invoice: {move.commission_total:.2f}")
                        print(f"   Invoice amount ({current_invoice_total:.2f}) >= Threshold ({salary_threshold:.2f})")

                    if not commission_calculated:
                        move.commission_total = 0.0
                        print(f"?? No commission triggered.")
                        print(
                            f"   Monthly total: {monthly_invoice_total:.2f}, Invoice amount: {current_invoice_total:.2f}")
                        print(f"   Both are less than threshold: {salary_threshold:.2f}")

        return res

    def unlink(self):
        """Put 'invoiced' settlements associated to the invoices back in settled state."""
        self.invoice_line_ids.settlement_id.filtered(
            lambda s: s.state == "invoiced"
        ).write({"state": "settled"})
        return super().unlink()


    @api.depends('invoice_line_ids.price_total')
    def _amount_all(self):
        """Compute the total amounts of the invoice."""
        for move in self:
            if move.state == 'posted' and any(move.line_ids.matched_debit_ids) or any(move.line_ids.matched_credit_ids):
                continue

            
            amount_price = amount_untaxed = amount_tax = amount_discount = 0.0
            for line in move.invoice_line_ids:
                amount_price += line.quantity * line.price_unit
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_total - line.price_subtotal
                amount_discount += (line.quantity * line.price_unit * line.discount) / 100
            move.update({
                'amount_price': amount_price,
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_discount': amount_discount,
                # 'amount_total': amount_untaxed + amount_tax, issu register payment not work
            })

    amount_price = fields.Float(string='Amount', store=True, readonly=True, compute='_amount_all')
    amount_untaxed = fields.Monetary(string='Total after discount', store=True, readonly=True, compute='_amount_all')
    amount_discount = fields.Float(string='Discount', store=True, readonly=True, compute='_amount_all')


class AccountMoveLine(models.Model):
    _inherit = [
        "account.move.line",
        "commission.mixin",
    ]
    _name = "account.move.line"

    agent_ids = fields.One2many(comodel_name="account.invoice.line.agent")
    any_settled = fields.Boolean(compute="_compute_any_settled")
    agents = fields.One2many(
        'res.partner',
        compute='_compute_agents_from_invoice_partner',
        string='Agent',
    )

    settlement_id = fields.Many2one(
        comodel_name="commission.settlement",
        help="Settlement that generates this invoice line",
        copy=False,
    )

    @api.depends('move_id.partner_id')
    def _compute_agents_from_invoice_partner(self):
        for line in self:
            if line.move_id and line.move_id.partner_id:
                partner = line.move_id.partner_id
                # Assume agent_ids is a One2many(Many2many) of res.partner
                line.agents = partner.agent_ids
            else:
                line.agents = False

    @api.depends("agent_ids", "agent_ids.settled")
    def _compute_any_settled(self):
        for record in self:
            record.any_settled = any(record.mapped("agent_ids.settled"))

    @api.depends("move_id.partner_id")
    def _compute_agent_ids(self):
        self.agent_ids = False  # for resetting previous agents
        for record in self:
            if (
                record.move_id.partner_id
                and record.move_id.move_type[:3] == "out"
                and not record.commission_free
                and record.product_id
            ):
                record.agent_ids = record._prepare_agents_vals_partner(
                    record.move_id.partner_id, settlement_type="sale_invoice"
                )

    def _copy_data_extend_business_fields(self, values):
        """We don't want to loose the settlement from the line when reversing the line
        if it was a refund. We need to include it, but as we don't want change it
        everytime, we will add the data when a context key is passed.
        """
        res = super()._copy_data_extend_business_fields(values)
        if self.settlement_id and self.env.context.get("include_settlement", False):
            values["settlement_id"] = self.settlement_id.id
        return res


class AccountInvoiceLineAgent(models.Model):
    _inherit = "commission.line.mixin"
    _name = "account.invoice.line.agent"
    _description = "Agent detail of commission line in invoice lines"

    object_id = fields.Many2one(comodel_name="account.move.line")
    invoice_id = fields.Many2one(
        string="Invoice",
        comodel_name="account.move",
        related="object_id.move_id",
        store=True,
    )
    invoice_date = fields.Date(
        string="Invoice date",
        related="invoice_id.invoice_date",
        store=True,
        readonly=True,
    )
    settlement_line_ids = fields.One2many(
        comodel_name="commission.settlement.line",
        inverse_name="invoice_agent_line_id",
    )
    settled = fields.Boolean(compute="_compute_settled", store=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        compute="_compute_company",
        store=True,
    )
    currency_id = fields.Many2one(
        related="object_id.currency_id",
    )

    @api.depends(
        "object_id.price_subtotal",
        "object_id.commission_free",
        "commission_id",
    )
    def _compute_amount(self):
        for line in self:
            inv_line = line.object_id
            print('hello', line.object_id.partner_id.new_customer)
            if inv_line.partner_id.new_customer:
                commission_id = line.agent_id.new_customer_commission
                count = line.agent_id.new_customer_count
                print("subtotallllll",inv_line.price_subtotal)
                line.amount = line._get_new_customer_commission_amount(
                    commission_id,
                    inv_line.price_subtotal,
                    inv_line.product_id,
                    inv_line.quantity,
                    count,
                )

            else:
                line.amount = line._get_commission_amount(
                line.commission_id,
                inv_line.price_subtotal,
                inv_line.product_id,
                inv_line.quantity,
                )

            # Refunds commissions are negative
            if line.invoice_id.move_type and "refund" in line.invoice_id.move_type:
                line.amount = -line.amount
        #self.object_id.partner_id.new_customer = False

    @api.depends(
        "settlement_line_ids",
        "settlement_line_ids.settlement_id.state",
        "invoice_id",
        "invoice_id.state",
    )
    def _compute_settled(self):
        # Count lines of not open or paid invoices as settled for not
        # being included in settlements
        for line in self:
            line.settled = any(
                x.settlement_id.state != "cancel" for x in line.settlement_line_ids
            )

    @api.depends("object_id", "object_id.company_id")
    def _compute_company(self):
        for line in self:
            line.company_id = line.object_id.company_id

    @api.constrains("agent_id", "amount")
    def _check_settle_integrity(self):
        for record in self:
            if any(record.mapped("settled")):
                raise exceptions.ValidationError(
                    _("You can't modify a settled line"),
                )

    def _skip_settlement(self):
        """This function should return False if the commission can be paid.

        :return: bool
        """
        self.ensure_one()
        return (
            self.commission_id.invoice_state == "paid"
            and self.invoice_id.payment_state not in ["in_payment", "paid", "reversed"]
        ) or self.invoice_id.state != "posted"
