from odoo import models, fields, api
from datetime import date


class CustomerSupportDashboard(models.TransientModel):
    _name = "customer.support.dashboard"
    _description = "Customer Support Dashboard"

    unassigned_count = fields.Integer(readonly=True)
    assigned_count = fields.Integer(readonly=True)
    today_count = fields.Integer(readonly=True)

    ticket_ids = fields.Many2many(
        "customer.support.module",
        string="All Tickets",
        readonly=True
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        Ticket = self.env["customer.support.module"]
        tickets = Ticket.search([], order="create_date desc")

        today = date.today()

        res.update({
            "ticket_ids": [(6, 0, tickets.ids)],
            "unassigned_count": len(tickets.filtered(lambda t: not t.assigned_user_id)),
            "assigned_count": len(tickets.filtered(lambda t: t.assigned_user_id)),
            "today_count": len(
                tickets.filtered(
                    lambda t: t.create_date and t.create_date.date() == today
                )
            ),
        })
        return res
