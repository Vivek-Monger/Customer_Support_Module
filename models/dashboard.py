from datetime import timedelta
from odoo import models, fields, api

class CustomerSupportDashboard(models.TransientModel):
    _name = 'customer.support.dashboard'
    _description = 'Customer Support Dashboard'

    tickets_count = fields.Integer(string="Tickets", readonly=True)
    high_priority_count = fields.Integer(string="High Priority", readonly=True)
    urgent_count = fields.Integer(string="Urgent", readonly=True)
    closed_count = fields.Integer(string="Closed", readonly=True)
    sla_success_rate = fields.Float(string="SLA Success Rate", readonly=True)

    @api.model
    def get_dashboard_data(self):
        """Compute live stats for the dashboard."""
        Ticket = self.env['customer.support.module']

        total_tickets = Ticket.search_count([])

        # High priority = '2', Urgent = '3'
        high_priority = Ticket.search_count([('priority', '=', '2')])
        urgent = Ticket.search_count([('priority', '=', '3')])

        # Closed tickets
        closed_phase = self.env['progress.phase'].search([('phase', '=', 'Closed')], limit=1)
        closed = Ticket.search_count([('phase_id', '=', closed_phase.id)]) if closed_phase else 0

        # SLA breached: tickets older than 48 hours and not closed
        sla_breached = 0
        if closed_phase:
            sla_breached = Ticket.search_count([
                ('phase_id', '!=', closed_phase.id),
                ('create_date_time', '<', fields.Datetime.now() - timedelta(hours=48))
            ])

        # SLA success rate
        sla_success = 0.0
        if total_tickets > 0:
            sla_success = ((total_tickets - sla_breached) / total_tickets) * 100

        return {
            'tickets_count': total_tickets,
            'high_priority_count': high_priority,
            'urgent_count': urgent,
            'closed_count': closed,
            'sla_success_rate': round(sla_success, 2),
        }

    @api.model
    def default_get(self, fields_list):
        """When dashboard is opened, fill data automatically."""
        res = super(CustomerSupportDashboard, self).default_get(fields_list)
        data = self.get_dashboard_data()
        res.update(data)
        return res
