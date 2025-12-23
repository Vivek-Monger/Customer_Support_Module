from odoo import http
from odoo.http import request
import base64

class CustomerSupportPortal(http.Controller):

    @http.route(['/my/tickets'], type='http', auth='user', website=True)
    def portal_my_tickets(self):
        """Display tickets created by the logged-in customer"""
        tickets = request.env['customer.support.module'].sudo().search([
            ('create_uid', '=', request.env.uid)
        ])
        return request.render(
            'customer_support_module.portal_my_tickets',
            {'tickets': tickets}
        )

    @http.route(['/my/tickets/create'], type='http', auth='user', website=True)
    def portal_create_ticket(self, **kwargs):
        """Display the create ticket form"""
        return request.render(
            'customer_support_module.portal_create_ticket'
        )

    @http.route(['/my/tickets/create/submit'], type='http', auth='user', methods=['POST'], website=True)
    def portal_create_ticket_submit(self, **kwargs):
        """Handle ticket creation with optional file attachment"""

        # Step 1: Create ticket
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

        ticket = request.env['customer.support.module'].sudo().create(ticket_vals)

        # Step 2: Handle file attachment(s)
        # attachments = []

        # if 'attachment' in request.httprequest.files:
        #     uploaded_files = request.httprequest.files.getlist('attachment')
        #     for file in uploaded_files:
        #         attachments.append((
        #             file.filename,
        #             base64.b64encode(file.read())
        #         ))

        # if attachments:
        #     ticket.sudo().message_post(
        #         body="Attachments uploaded by customer",
        #         attachments=attachments
        #     )
        
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



        # Step 3: Redirect to the portal ticket list
        return request.redirect('/my/tickets')
