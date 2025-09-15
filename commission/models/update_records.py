from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class CreateCommissionHistoryAction(models.Model):
    _inherit = 'account.move'
    _description = 'Create Commission History Action'

    @api.model
    def create_commission_history(self):
        try:
            print("Create Commission History")
            """Action to create commission agent history for existing invoices"""
            # Get all posted invoices that have an agent_id and don't have commission history
            invoices = self.env['account.move'].search([
                ('state', '=', 'posted'),('payment_state', '!=', 'not_paid'),
                ('agent_id', '!=', False),
                ('move_type', 'in', ['out_invoice', 'out_refund'])
            ])




            for invoice in invoices:
                # Check if history already exists for this invoice
                existing_history = self.env['commission.agent.history'].search([
                    ('invoice_no', '=', invoice.name)
                ], limit=1)

                if not existing_history:
                    # Calculate required values
                    paid_amount = invoice.amount_total_signed - invoice.amount_residual_signed
                    amount_due = invoice.amount_residual_signed
                    total_amount = invoice.amount_total_signed

                    # Get agent target for the invoice date
                    agent_target = self.env['agent.target'].search([
                        ('name', '=', invoice.agent_id.name),
                        ('date_from', '<=', invoice.invoice_date),
                        ('date_to', '>=', invoice.invoice_date),
                        ('state', '=', 'approve')
                    ], limit=1)

                    # Calculate target percentage
                    target_percentage = (total_amount / agent_target.target_amount) * 100 if agent_target and agent_target.target_amount != 0 else 0

                    # Get invoice count for the day
                    record_count = self.env['account.move'].search_count([
                        ('agent_id', '=', invoice.agent_id.id),
                        ('invoice_date', '=', invoice.invoice_date),
                        ('state', '!=', 'cancel')
                    ])

                    # Create commission history record
                    self.env['commission.agent.history'].sudo().create({
                        'name': invoice.agent_id.name,
                        'agent_id': invoice.agent_id.id,
                        'commission_id': invoice.agent_id.commission_id.id,
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
            return True

        except Exception as e:
            raise UserError(_('Error creating commission history: %s') % str(e))