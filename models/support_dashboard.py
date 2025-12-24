from odoo import models, fields, api
from datetime import date

class CustomerSupportDashboard(models.TransientModel):
    _name = "customer.support.dashboard"
    _description = "Customer Support Dashboard"

    unassigned_count = fields.Integer(
        string="Unassigned Tickets",
        compute="_compute_counts"
    )
    assigned_count = fields.Integer(
        string="Assigned Tickets",
        compute="_compute_counts"
    )
    today_count = fields.Integer(
        string="Tickets Today",
        compute="_compute_counts"
    )

    ticket_ids = fields.Many2many(
        "customer.support.module",
        compute="_compute_tickets",
        string="All Tickets"
    )

    @api.depends()
    def _compute_counts(self):
        Ticket = self.env["customer.support.module"]
        today = date.today()

        for rec in self:
            rec.unassigned_count = Ticket.search_count([
                ("assigned_user_id", "=", False)
            ])
            rec.assigned_count = Ticket.search_count([
                ("assigned_user_id", "=", self.env.uid)
            ])
            rec.today_count = Ticket.search_count([
                ("create_date", ">=", today)
            ])

    @api.depends()
    def _compute_tickets(self):
        for rec in self:
            rec.ticket_ids = self.env["customer.support.module"].search(
                [], order="create_date desc", limit=20
            )
