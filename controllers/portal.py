from odoo import fields, http
from odoo.http import request
import base64
from collections import Counter


class CustomerSupportPortal(http.Controller):

    def _get_phase_labels(self):
        return dict(
            request.env['customer.support.module']._fields['phase_id'].selection
        )

    @http.route(['/my/tickets'], type='http', auth='user', website=True)
    def portal_my_tickets(self, view='kanban', **kwargs):

        tickets = request.env['customer.support.module'].sudo().search(
            [('create_uid', '=', request.env.uid)],
            order='create_date desc'
        )

        phase_keys = [
            key for key, label in
            request.env['customer.support.module']._fields['phase_id'].selection
        ]

        phase_map = {}
        for phase in phase_keys:
            phase_map[phase] = tickets.filtered(lambda t: t.phase_id == phase)

        return request.render(
            'customer_support_module.portal_my_tickets',
            {
                'tickets': tickets,
                'phase_map': phase_map,
                'phase_labels': self._get_phase_labels(),
                'current_view': view,
            }
        )

    # Create Ticket (Form)

    @http.route(['/my/tickets/create'], type='http', auth='user', website=True)
    def portal_create_ticket(self, **kwargs):
        return request.render(
            'customer_support_module.portal_create_ticket'
        )

    # Create Ticket (Submit)

    @http.route(
        ['/my/tickets/create/submit'],
        type='http',
        auth='user',
        methods=['POST'],
        website=True
    )
    def portal_create_ticket_submit(self, **kwargs):

        ticket_vals = {
            'subject': kwargs.get('subject'),
            'description': kwargs.get('description'),
            'priority': kwargs.get('priority') or '0',
            'create_uid': request.env.uid,
            'phase_id': 'new',
        }

        project_id = kwargs.get('project_id')
        if project_id:
            ticket_vals['project_id'] = int(project_id)

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

    # ---------------------------------------------------------
    # Reporting Dashboard
    # ---------------------------------------------------------
    @http.route(
        ['/my/tickets/reporting', '/my/tickets/reporting/<string:graph_type>'],
        type='http',
        auth='user',
        website=True
    )
    def portal_customer_reporting(self, graph_type='bar', **kwargs):

        tickets = request.env['customer.support.module'].sudo().search(
            [('create_uid', '=', request.env.uid)]
        )

        phase_labels = self._get_phase_labels()
        chart_data = {}

        if graph_type == 'bar':
            phases = [phase_labels.get(t.phase_id, 'Unknown') for t in tickets]
            chart_data = dict(Counter(phases))

        elif graph_type == 'pie':
            priorities = [t.priority for t in tickets]
            chart_data = dict(Counter(priorities))

        elif graph_type == 'line':
            dates = [str(t.create_date.date()) for t in tickets if t.create_date]
            chart_data = dict(Counter(dates))

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

        return request.render(
            'customer_support_module.portal_customer_reporting',
            {'chart_html': chart_html}
        )
    # Ticket Overview Dashboard
 
    @http.route(['/my/tickets/overview'], type='http', auth='user', website=True)
    def portal_ticket_overview(self, **kwargs):

        Ticket = request.env['customer.support.module'].sudo()
        tickets = Ticket.search([('create_uid', '=', request.env.uid)])

        open_tickets = tickets.filtered(
            lambda t: t.phase_id not in ('resolved', 'closed')
        )

        closed_tickets = tickets.filtered(
            lambda t: t.phase_id == 'closed'
        )

        high_priority = tickets.filtered(lambda t: t.priority == '2')
        urgent_tickets = tickets.filtered(lambda t: t.priority == '3')

        today = fields.Date.today()
        today_closed = closed_tickets.filtered(
            lambda t: t.write_date and t.write_date.date() == today
        )

        values = {
            'total_tickets': len(tickets),
            'open_tickets': len(open_tickets),
            'high_priority': len(high_priority),
            'urgent_tickets': len(urgent_tickets),
            'closed_tickets': len(closed_tickets),
            'today_closed': len(today_closed),

            # SLA placeholders
            'avg_open_hours': 0.80,
            'total_hours': 2.30,
            'avg_high_priority_hours': 0.80,
            'avg_urgent_hours': 0.80,
            'sla_last_7_days': 100.0,
            'daily_target': 80.0,
            'sample_rate': 85.0,
        }

        return request.render(
            'customer_support_module.portal_ticket_overview',
            values
        )

    # Activity Log
 
    @http.route(['/my/tickets/activity-log'], type='http', auth='user', website=True)
    def portal_ticket_activity_log(self, **kwargs):

        Ticket = request.env['customer.support.module'].sudo()
        tickets = Ticket.search(
            [('create_uid', '=', request.env.uid)],
            order='create_date desc'
        )

        phase_labels = self._get_phase_labels()
        activities = []

        def get_priority_label(priority):
            return {
                '0': 'Low',
                '1': 'Medium',
                '2': 'High',
                '3': 'Urgent'
            }.get(priority, 'Unknown')

        for ticket in tickets:

            # Ticket creation
            activities.append({
                'date': ticket.create_date,
                'ticket': ticket,
                'action': 'Created',
                'details': f'Ticket created | Priority: {get_priority_label(ticket.priority)}'
            })

            # Assignment
            if ticket.assigned_user_id:
                activities.append({
                    'date': ticket.assigned_date or ticket.create_date,
                    'ticket': ticket,
                    'action': 'Assigned',
                    'details': f'Assigned to {ticket.assigned_user_id.name}'
                })

            # Phase history
            histories = request.env['customer.support.phase.history'].sudo().search(
                [('ticket_id', '=', ticket.id)],
                order='change_date'
            )

            if histories:
                for hist in histories:
                    activities.append({
                        'date': hist.change_date,
                        'ticket': ticket,
                        'action': 'Phase Changed',
                        'details': (
                            f"Phase changed from "
                            f"{phase_labels.get(hist.old_phase_id, 'New')} "
                            f"to {phase_labels.get(hist.new_phase_id)}"
                        )
                    })
            else:
                activities.append({
                    'date': ticket.phase_date or ticket.create_date,
                    'ticket': ticket,
                    'action': 'Phase Set',
                    'details': f"Initial phase: {phase_labels.get(ticket.phase_id)}"
                })

        activities = sorted(activities, key=lambda x: x['date'], reverse=True)

        return request.render(
            'customer_support_module.portal_activity_log',
            {'activities': activities}
        )
