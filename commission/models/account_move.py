from odoo import _, api, fields, models
from datetime import datetime
from odoo.exceptions import ValidationError
from datetime import date

import logging


class AccountMove(models.Model):
    _inherit = "account.move"

    agent_id = fields.Many2one(
        'res.partner',
        string='Agent',
        compute='_compute_agent_id',
        store=True
    )
    target = fields.Integer()
    target_amount = fields.Integer()
    creation_check = fields.Boolean(default=False)

    def action_post(self):
        """Inherit to check its first invoice for that agent in this month also set target invoice count and target amount"""
        res = super(AccountMove, self).action_post()
        target_id = self.env['agent.target'].search(
            [('name', '=', self.agent_id.name), ('date_from', '<=', self.invoice_date),
             ('date_to', '>=', self.invoice_date), ('state', '=', 'approve')],limit=1)
        if target_id:
            self.creation_check = True
            self.target = target_id.target_invoice
            self.target_amount = target_id.target_amount
        else:
            self.target_amount = 0
            self.target = 0
        return res

    @api.depends('partner_id', 'partner_id.agent_ids')
    def _compute_agent_id(self):
        """ Assign the first agent from the partner's agent_ids Many2many field"""
        for move in self:
            # Assign the first agent from the partner's agent_ids Many2many field
            move.agent_id = move.partner_id.agent_ids[:1].id if move.partner_id.agent_ids else False

    def is_first_invoice_of_month(self):
        """If first invoice of that month pass target invoice count and target amount flag true else false"""
        for record in self:
            start_of_month = datetime(record.invoice_date.year, record.invoice_date.month, 1)
            end_of_month = datetime(record.invoice_date.year, record.invoice_date.month + 1,
                                    1) if record.invoice_date.month < 12 else datetime(record.invoice_date.year + 1, 1,
                                                                                       1)
            invoice_count = self.search_count([
                ('agent_id', '=', record.agent_id.id),
                ('invoice_date', '>=', start_of_month),
                ('invoice_date', '<', end_of_month),
                ('id', '!=', record.id),  # Exclude the current record if it has already been created
                ('state', '!=', 'cancel'),  # Exclude canceled invoices
            ])

            return invoice_count == 0  # Return True if first invoice of the month, else False
        return False

    def _update_commission_agent_history(self, history_record, paid_amount, amount_due, total_amount):
            """Update the existing commission agent history record with new payment details"""
            history_record.sudo().write({

                'pad': paid_amount,
                'amount_due': amount_due,
                'total': total_amount,
                'status': 'partial' if amount_due >= 0 else self.payment_state,
            })
    def _create_commission_agent_history(self):
        """Method used to create agent commission history"""
        self.ensure_one()
        # Flag to track the first record creation
        for record in self:
            first_record = record.is_first_invoice_of_month()
        for invoice in self:
            paid_amount = invoice.amount_total_signed - invoice.amount_residual_signed
            amount_due = invoice.amount_residual_signed
            total_amount = invoice.amount_total_signed
            # Check if a history record already exists for this invoice
            history_record = self.env['commission.agent.history'].search([('invoice_no', '=', invoice.name)], limit=1)

            if history_record:
                # Update the existing history record if partial payment was made before
                self._update_commission_agent_history(history_record, paid_amount, amount_due, total_amount)
            else:
                # Calculate target percentage
                target_percentage = (
                                                total_amount / self.target_amount) * 100 if self.target_amount != 0 else 0  # Calculate the record count before using it
                comm_history_ids = self.env['account.move'].search(
                    [('name', '=', self.agent_id.name), ('invoice_date', '=', self.invoice_date)])
                record_count = self.env['account.move'].search_count([
                    ('agent_id', '=', self.agent_id.id),
                    ('invoice_date', '=', self.invoice_date),
                    ('state', '!=', 'cancel')
                ])
                agent_target= self.env['agent.target'].search(
                    [('name', '=', self.agent_id.name), ('date_from', '<=', self.invoice_date),
                     ('date_to', '>=', self.invoice_date), ('state', '=', 'approve')],limit=1)


                record_count = len(comm_history_ids)
                # Create the commission agent history record
                self.env['commission.agent.history'].sudo().create({
                    'name': self.agent_id.name,
                    'agent_id': self.agent_id.id,
                    'commission_id': self.agent_id.commission_id.id,
                    'customer_name': invoice.partner_id.name,
                    'invoice_no': invoice.name,
                    'pad': paid_amount,
                    'amount_due': amount_due,
                    'total': total_amount,
                    'target': agent_target.target_invoice if agent_target else 0,
                    'target_amount': agent_target.target_amount if agent_target else 0,
                    'target_percentage': target_percentage,
                    'status': invoice.payment_state,
                    'count_invoice': record_count + 1,
                    'invoice_date': invoice.invoice_date,
                })
                print("self.target", self.target)





class CommissionAgentHistory(models.Model):
    _name = 'commission.agent.history'
    _description = 'Commission Agent History'

    name = fields.Char(string="Name", required=True)
    agent_id = fields.Many2one('res.partner', string='Agent', )
    commission_id = fields.Many2one('commission', string="Commission Type")
    invoice_no = fields.Char(string="Invoice No", required=True)
    customer_name = fields.Char(string='Customer Name')
    pad = fields.Float(string="Paid")
    amount_due = fields.Float(string="Amount Due")
    total = fields.Float(string="Total")
    target_amount = fields.Float(string="Target Amount")
    target_percentage = fields.Float(string="Target Percentage")
    status = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'), ('partial', 'Partially Paid'), ('reversed', 'Reversed'),
        ('invoicing_legacy', 'Invoicing App Legacy')
    ], string="Status", default='pending')
    count_invoice = fields.Integer('Count Invoice')
    target = fields.Integer('Target')
    invoice_date = fields.Date('Invoice Date')


class AgentTarget(models.Model):
    _name = 'agent.target'
    _description = 'Agent Target'

    name = fields.Many2one('res.partner', name='Agent', domain=[('agent', '=', True)])
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    target_invoice = fields.Integer('Target Invoice')
    target_amount = fields.Float('Targe Amount')
    btn_invisible = fields.Boolean(default=False)
    state = fields.Selection([('draft', 'Draft'), ('approve', 'Approved'), ('done', 'Done')], default='draft')
    web_reb = fields.Selection([('not_created', 'Agent History Not Created'), ('create', 'Agent History Created')],
                               default='not_created')

    def action_send(self):
        if self.state == 'draft':
            self.state = 'approve'
        elif self.state == 'approve':
            self.state = 'done'

    @api.constrains('date_from', 'date_to')
    def _check_date_range(self):
        today = date.today()
        first_day_of_current_month = today.replace(day=1)
        for record in self:
            if record.date_from < first_day_of_current_month:
                raise ValidationError('The start date cannot be earlier than the first day of the current month.')
            if record.date_from.month != today.month or record.date_from.year != today.year:
                raise ValidationError('The start date must be within the current month.')
            if record.date_from > record.date_to:
                raise ValidationError('The start date must be before the end date.')


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def action_create_payments(self):
        print("action_create_payments")
        res = super(AccountPaymentRegister, self).action_create_payments()
        invoices = self.env['account.move'].browse(self._context.get('active_id', []))
        for invoice in invoices:
            if invoice.creation_check:

                invoice._create_commission_agent_history()
        return res
