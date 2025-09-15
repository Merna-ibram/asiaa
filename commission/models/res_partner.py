from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    agent_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="partner_agent_rel",
        column1="partner_id",
        column2="agent_id",
        domain=[("agent", "=", True)],
        readonly=False,
        string="Agents",
    )
    agent = fields.Boolean(
        string="Creditor/Agent",
        help="Check this field if the partner is a creditor or an agent.",
    )
    agent_type = fields.Selection(
        selection=[("agent", "External agent")],
        string="Type",
        default="agent",
    )
    commission_id = fields.Many2one(
        string="Commission",
        comodel_name="commission",
    )
    new_customer_commission = fields.Many2one(
        string="New Customer Commission",
        comodel_name="commission",
    )
    settlement = fields.Selection(
        selection=[
            ("biweekly", "Bi-weekly"),
            ("monthly", "Monthly"),
            ("quaterly", "Quarterly"),
            ("semi", "Semi-annual"),
            ("annual", "Annual"),
        ],
        string="Settlement period",
        default="monthly",
    )
    settlement_ids = fields.One2many(
        comodel_name="commission.settlement",
        inverse_name="agent_id",
        readonly=True,
    )
    new_customer = fields.Boolean(
        string="New Customer",
        help="Check this field if the partner is New Customer."
    )
    new_customer_count = fields.Integer(default=1)

    salary = fields.Float(string="Salary")

    res_partner_search_mode = fields.Selection(
        [('customer', 'Customer'), ('supplier', 'Supplier')],
        string='Search Mode', compute="default_partner_search_mode",
    )

    @api.depends('res_partner_search_mode')
    def default_partner_search_mode(self):
        partner_search_mode = self.env.context.get('res_partner_search_mode')
        self.res_partner_search_mode = partner_search_mode

    @api.model
    def _commercial_fields(self):
        res = super()._commercial_fields()
        res.append("agent_ids")
        return res
