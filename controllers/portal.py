from odoo import fields, http
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
        
    @http.route(['/my/tickets/overview'], type='http', auth='user', website=True)
    def portal_ticket_overview(self, **kwargs):
        """Customer Ticket Overview Dashboard"""

        Ticket = request.env['customer.support.module'].sudo()

        # Only customer's tickets
        domain = [('create_uid', '=', request.env.uid)]
        tickets = Ticket.search(domain)

        open_tickets = tickets.filtered(lambda t: t.phase_id.phase != 'Done')
        failed_tickets = tickets.filtered(lambda t: t.phase_id.phase == 'Failed')

        high_priority = tickets.filtered(lambda t: t.priority == '2')
        urgent_tickets = tickets.filtered(lambda t: t.priority == '3')

        high_priority_failed = failed_tickets.filtered(lambda t: t.priority == '2')
        urgent_failed = failed_tickets.filtered(lambda t: t.priority == '3')

        today = fields.Date.today()
        today_closed = tickets.filtered(
            lambda t: t.phase_id.phase == 'Done'
            and t.write_date
            and t.write_date.date() == today
        )

        values = {
            'total_tickets': len(tickets),
            'open_tickets': len(open_tickets),

            'high_priority': len(high_priority),
            'urgent_tickets': len(urgent_tickets),

            'failed_tickets': len(failed_tickets),
            'failed_rate': (len(failed_tickets) / len(tickets) * 100) if tickets else 0,

            'high_priority_failed': len(high_priority_failed),
            'urgent_failed': len(urgent_failed),

            'today_closed': len(today_closed),

            # Placeholder SLA values (same as internal)
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
        
    @http.route(['/my/tickets/activity-log'], type='http', auth='user', website=True)
    def portal_ticket_activity_log(self, **kwargs):
        Ticket = request.env['customer.support.module'].sudo()
        tickets = Ticket.search([('create_uid', '=', request.env.uid)], order='create_date desc')

        activities = []

        # Local function to get readable priority
        def get_priority_label(priority):
            return {
                '0': 'Low',
                '1': 'Medium',
                '2': 'High',
                '3': 'Urgent'
            }.get(priority, 'Unknown')

        for ticket in tickets:
            # 1️⃣ Ticket creation
            activities.append({
                'date': ticket.create_date,
                'ticket': ticket,
                'action': 'Created',
                'details': f'Ticket created with priority {get_priority_label(ticket.priority)}'
            })

            # 2️⃣ Assignment
            if ticket.assigned_user_id:
                activities.append({
                    'date': ticket.assigned_date or ticket.create_date,
                    'ticket': ticket,
                    'action': 'Assigned',
                    'details': f'Ticket assigned to {ticket.assigned_user_id.name} | Priority: {get_priority_label(ticket.priority)}'
                })

            # 3️⃣ Phase changes from history
            phase_histories = request.env['customer.support.phase.history'].sudo().search(
                [('ticket_id', '=', ticket.id)],
                order='change_date'
            )


            if phase_histories:
                for hist in phase_histories:
                    activities.append({
                        'date': hist.change_date,
                        'ticket': ticket,
                        'action': 'Phase Changed',
                        'details': f'Phase changed from {hist.old_phase_id.phase if hist.old_phase_id else "New"} to {hist.new_phase_id.phase} | Priority: {get_priority_label(ticket.priority)}'
                    })
            else:
                # Initial phase fallback
                if ticket.phase_id:
                    activities.append({
                        'date': ticket.phase_date or ticket.create_date,
                        'ticket': ticket,
                        'action': 'Phase Changed',
                        'details': f'Initial phase: {ticket.phase_id.phase} | Priority: {get_priority_label(ticket.priority)}'
                    })

        # Sort all activities by date descending
        activities = sorted(activities, key=lambda x: x['date'], reverse=True)

        return request.render(
            'customer_support_module.portal_activity_log',
            {'activities': activities}
        )

            