from odoo import http
from odoo.http import request
import base64


class CustomerSupportTicketConfirmation(http.Controller):

    def _priority_label(self, priority):
        return {
            '0': 'Low',
            '1': 'Medium',
            '2': 'High',
            '3': 'Urgent'
        }.get(priority, 'Low')

    # ---------------------------------------
    # Confirmation Page
    # ---------------------------------------
    @http.route(
        ['/my/tickets/create/confirm'],
        type='http',
        auth='user',
        methods=['POST'],
        website=True
    )
    def portal_ticket_confirm(self, **post):

        values = {
            'subject': post.get('subject'),
            'description': post.get('description'),
            'priority': post.get('priority') or '0',
            'priority_label': self._priority_label(post.get('priority')),
            'project_id': post.get('project_id'),
        }

        return request.render(
            'customer_support_module.portal_ticket_confirmation',
            values
        )

    # ---------------------------------------
    # Final Ticket Creation
    # ---------------------------------------
    @http.route(
        ['/my/tickets/create/final'],
        type='http',
        auth='user',
        methods=['POST'],
        website=True
    )
    def portal_ticket_create_final(self, **post):

        ticket_vals = {
            'subject': post.get('subject'),
            'description': post.get('description'),
            'priority': post.get('priority') or '0',
            'create_uid': request.env.uid,
            'phase_id': 'new',
        }

        project_id = post.get('project_id')
        if project_id:
            ticket_vals['project_id'] = int(project_id)

        ticket = request.env['customer.support.module'].sudo().create(ticket_vals)

        return request.redirect('/my/tickets')
