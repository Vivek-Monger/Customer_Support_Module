from odoo import models, fields, api
from odoo.exceptions import UserError

class ConfirmCreateTicketWizard(models.TransientModel):
    _name = 'confirm.create.ticket.wizard'
    _description = 'Confirm Ticket Creation Wizard'

    # Fields to display in popup (readonly)
    subject = fields.Char(string="Subject", readonly=True)
    description = fields.Text(string="Description", readonly=True)
    date = fields.Date(string="Date", readonly=True)
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string="Priority", readonly=True)

    # Pre-fill wizard fields from active ticket
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id:
            ticket = self.env['customer.support.module'].browse(active_id)
            res.update({
                'subject': ticket.subject,
                'description': ticket.description,
                'date': ticket.date,
                'priority': ticket.priority,
            })
        return res

    def action_confirm_create(self):
        """Create the ticket and return to list view"""
        active_id = self.env.context.get('active_id')
        ticket = self.env['customer.support.module'].browse(active_id)

        if not ticket:
            raise UserError("No active ticket found.")

        # Call the existing ticket creation logic
        ticket.action_create_ticket()

        # Explicitly specify tree and form views
        list_view = self.env.ref('customer_support_module.view_customer_support_tree_customer').id
        form_view = self.env.ref('customer_support_module.customer_support_module_form_view').id

        return {
            'type': 'ir.actions.act_window',
            'name': 'My Tickets',
            'res_model': 'customer.support.module',
            'views': [(list_view, 'list'), (form_view, 'form')],
            'target': 'current',
            'domain': [('user_id', '=', self.env.user.id)],
        }
