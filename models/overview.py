from odoo import models, fields, api
from datetime import datetime, timedelta


class CustomerSupportDashboard(models.Model):
    _name = 'customer.support.overview'
    _description = 'Customer Support Dashboard'

    # -------------------------
    # Ticket Analytics
    # -------------------------
    open_tickets = fields.Integer(compute="_compute_metrics", store=False)
    total_tickets = fields.Integer(compute="_compute_metrics", store=False)

    high_priority = fields.Integer(compute="_compute_metrics", store=False)
    urgent_tickets = fields.Integer(compute="_compute_metrics", store=False)

    avg_open_hours = fields.Float(compute="_compute_metrics", store=False)
    total_hours = fields.Float(compute="_compute_metrics", store=False)

    avg_high_priority_hours = fields.Float(compute="_compute_metrics", store=False)
    avg_urgent_hours = fields.Float(compute="_compute_metrics", store=False)

    failed_tickets = fields.Integer(compute="_compute_metrics", store=False)
    failed_rate = fields.Float(compute="_compute_metrics", store=False)

    high_priority_failed = fields.Integer(compute="_compute_metrics", store=False)
    urgent_failed = fields.Integer(compute="_compute_metrics", store=False)

    # -------------------------
    # Performance
    # -------------------------
    today_closed = fields.Integer(compute="_compute_metrics", store=False)
    sla_last_7_days = fields.Float(compute="_compute_metrics", store=False)

    daily_target = fields.Float(default=80.0)
    sample_rate = fields.Float(default=85.0)

    # -------------------------
    # Core Compute
    # -------------------------
    @api.depends(
        'daily_target',  # dummy dependency to allow recompute
    )
    def _compute_metrics(self):
        Ticket = self.env['customer.support.module']

        now = fields.Datetime.now()
        today_start = fields.Datetime.to_datetime(now.date())
        last_7_days = now - timedelta(days=7)

        tickets = Ticket.search([])
        open_tickets = Ticket.search([('phase_id.phase', '!=', 'Done')])
        failed = Ticket.search([('phase_id.phase', '=', 'Failed')])

        high_priority = Ticket.search([('priority', '=', '2')])
        urgent = Ticket.search([('priority', '=', '3')])

        today_closed = Ticket.search([
            ('phase_id.phase', '=', 'Done'),
            ('write_date', '>=', today_start)
        ])

        for rec in self:
            # Counts
            rec.total_tickets = len(tickets)
            rec.open_tickets = len(open_tickets)

            rec.high_priority = len(high_priority)
            rec.urgent_tickets = len(urgent)

            rec.failed_tickets = len(failed)
            rec.failed_rate = (len(failed) / len(tickets) * 100) if tickets else 0.0

            rec.high_priority_failed = len(failed.filtered(lambda t: t.priority == '2'))
            rec.urgent_failed = len(failed.filtered(lambda t: t.priority == '3'))

            rec.today_closed = len(today_closed)

            # SLA / Hours (replace later with real logic)
            rec.total_hours = 2.30
            rec.avg_open_hours = 0.80
            rec.avg_high_priority_hours = 0.80
            rec.avg_urgent_hours = 0.80

            rec.sla_last_7_days = 100.0
