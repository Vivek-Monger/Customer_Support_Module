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

    # ------------------------------
    # Fetch the latest tickets
    # ------------------------------
    @api.depends()
    def _compute_tickets(self):
        Ticket = self.env["customer.support.module"]
        latest_tickets = Ticket.search([], order="create_date desc", limit=20)
        for rec in self:
            rec.ticket_ids = latest_tickets

    # ------------------------------
    # Compute ticket counts for admin
    # ------------------------------
    @api.depends('ticket_ids')
    def _compute_counts(self):
        today = date.today()
        tickets = self.env["customer.support.module"].search([], order="create_date desc")

        for rec in self:
            rec.ticket_ids = tickets[:20]  # keep only latest 20 tickets
            rec.unassigned_count = len([t for t in tickets if not t.assigned_user_id])
            rec.assigned_count = len([t for t in tickets if t.assigned_user_id])
            rec.today_count = len([t for t in tickets if t.create_date.date() == today])
