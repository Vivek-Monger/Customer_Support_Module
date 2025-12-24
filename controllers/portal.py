from odoo import http
from odoo.http import request
import base64
from collections import Counter

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
        project_id = kwargs.get('project_id')
        if project_id:
            ticket_vals['project_id'] = int(project_id)  # convert from string to int


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
    
    @http.route(['/my/tickets/reporting', '/my/tickets/reporting/<string:graph_type>'], type='http', auth='user', website=True)
    def portal_customer_reporting(self, graph_type='bar', **kwargs):
        """Customer Reporting Dashboard"""

        # Fetch tickets for portal user
        tickets = request.env['customer.support.module'].sudo().search([
            ('create_uid', '=', request.env.uid)
        ])

        # Prepare chart data
        chart_data = {}
        if graph_type == 'bar':
            phases = [t.phase_id.phase if t.phase_id else 'Unknown' for t in tickets]
            chart_data = dict(Counter(phases))
        elif graph_type == 'pie':
            priorities = [t.priority for t in tickets]
            chart_data = dict(Counter(priorities))
        elif graph_type == 'line':
            dates = [str(t.create_date.date()) for t in tickets]
            chart_data = dict(Counter(dates))

        # Chart.js HTML
        chart_html = f"""
        <canvas id="tickets_chart" width="600" height="400"></canvas>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
        const ctx = document.getElementById('tickets_chart').getContext('2d');
        new Chart(ctx, {{
            type: '{graph_type}',
            data: {{
                labels: {list(chart_data.keys())},
                datasets: [{{
                    label: 'Tickets',
                    data: {list(chart_data.values())},
                    backgroundColor: 'rgba(54, 162, 235, 0.6)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
            }}
        }});
        </script>
        """

        return request.render('customer_support_module.portal_customer_reporting', {
            'chart_html': chart_html
        })
