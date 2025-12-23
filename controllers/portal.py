from odoo import http
from odoo.http import request

class CustomerSupportPortal(http.Controller):

    @http.route(['/my/tickets'], type='http', auth='user', website=True)
    def portal_my_tickets(self):
        tickets = request.env['customer.support.module'].sudo().search([
            ('create_uid', '=', request.env.uid)
        ])
        return request.render(
            'customer_support_module.portal_my_tickets',
            {'tickets': tickets}
        )

    @http.route(['/my/tickets/create'], type='http', auth='user', website=True)
    def portal_create_ticket(self, **kwargs):
        """Display form for creating a new ticket"""
        return request.render(
            'customer_support_module.portal_create_ticket'
        )

    @http.route(['/my/tickets/create/submit'], type='http', auth='user', methods=['POST'], website=True)
    def portal_create_ticket_submit(self, **kwargs):
        """Handle ticket creation"""
        ticket_vals = {
            'subject': kwargs.get('subject'),
            'description': kwargs.get('description'),
            'priority': kwargs.get('priority') or '0',
            'create_uid': request.env.uid,
        }

        # Optional: set default phase
        default_phase = request.env['progress.phase'].sudo().search([('phase', '=', 'New')], limit=1)
        if default_phase:
            ticket_vals['phase_id'] = default_phase.id

        request.env['customer.support.module'].sudo().create(ticket_vals)
        return request.redirect('/my/tickets')
