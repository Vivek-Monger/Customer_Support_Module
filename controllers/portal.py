from odoo import http
from odoo.http import request
import base64

class CustomerSupportPortal(http.Controller):

    @http.route(['/my/tickets'], type='http', auth='user', website=True)
    def portal_my_tickets(self, view='kanban', **kwargs):
        # Fetch customer tickets
        tickets = request.env['customer.support.module'].sudo().search(
            [('create_uid', '=', request.env.uid)],
            order='phase_id'
        )

        # Fetch all phases
        phases = request.env['progress.phase'].sudo().search([], order='id')

        # Group tickets by phase (for kanban)
        phase_map = {}
        for phase in phases:
            phase_map[phase] = tickets.filtered(lambda t: t.phase_id == phase)

        return request.render(
            'customer_support_module.portal_my_tickets',
            {
                'tickets': tickets,
                'phase_map': phase_map,
                'current_view': view,   # list | kanban
            }
        )

    @http.route(['/my/tickets/create'], type='http', auth='user', website=True)
    def portal_create_ticket(self, **kwargs):
        return request.render(
            'customer_support_module.portal_create_ticket'
        )

    @http.route(['/my/tickets/create/submit'], type='http', auth='user', methods=['POST'], website=True)
    def portal_create_ticket_submit(self, **kwargs):

        ticket_vals = {
            'subject': kwargs.get('subject'),
            'description': kwargs.get('description'),
            'priority': kwargs.get('priority') or '0',
            'create_uid': request.env.uid,
        }

        default_phase = request.env['progress.phase'].sudo().search(
            [('phase', '=', 'New')], limit=1
        )
        if default_phase:
            ticket_vals['phase_id'] = default_phase.id

        ticket = request.env['customer.support.module'].sudo().create(ticket_vals)

        files = request.httprequest.files.getlist('attachment')
        attachments = []
        for f in files:
            if f.filename:
                attachment = request.env['ir.attachment'].sudo().create({
                    'name': f.filename,
                    'type': 'binary',
                    'datas': base64.b64encode(f.read()),
                    'res_model': 'customer.support.module',
                    'res_id': ticket.id,
                    'mimetype': f.content_type,
                })
                attachments.append(attachment.id)

        if attachments:
            ticket.write({'attachment_ids': [(6, 0, attachments)]})

        return request.redirect('/my/tickets')
