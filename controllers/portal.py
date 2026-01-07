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

    @http.route(
        '/my/tickets/create',
        type='http',
        auth='user',
        website=True,
        methods=['GET', 'POST']
    )
    def portal_create_ticket(self, **post):
        
        # Check if coming from confirmation page
        from_confirm = post.get('from_confirm') or request.params.get('from_confirm')
        
        if from_confirm:
            # Retrieve data from session
            ticket_data = request.session.get('temp_ticket_data', {})
            file_data_list = request.session.get('temp_ticket_files', [])
            
            return request.render(
                'customer_support_module.portal_create_ticket',
                {
                    'subject': ticket_data.get('subject'),
                    'description': ticket_data.get('description'),
                    'priority': ticket_data.get('priority'),
                    'project_id': ticket_data.get('project_id'),
                    'file_count': len(file_data_list),
                    'files': file_data_list,
                    'from_confirm': True,
                }
            )
        
        # Normal create (not from confirmation)
        return request.render(
            'customer_support_module.portal_create_ticket',
            {
                'subject': post.get('subject'),
                'description': post.get('description'),
                'priority': post.get('priority'),
                'project_id': post.get('project_id'),
            }
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
            'new_phase_id':'new',
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
    # Add these routes to your existing CustomerSupportPortal class in portal.py

    @http.route(['/my/faq', '/my/faq/category/<int:category_id>'], type='http', auth='user', website=True)
    def portal_faq(self, category_id=None, search=None, **kwargs):
        """Display FAQ page with categories and questions"""
        
        FAQ = request.env['customer.support.faq'].sudo()
        Category = request.env['customer.support.faq.category'].sudo()
        
        # Get all active categories with active FAQs
        categories = Category.search([('active', '=', True)])
        
        # Filter FAQs based on category or search
        domain = [('active', '=', True)]
        
        if category_id:
            domain.append(('category_id', '=', category_id))
        
        if search:
            domain.append('|')
            domain.append(('name', 'ilike', search))
            domain.append(('answer', 'ilike', search))
        
        faqs = FAQ.search(domain)
        
        # Group FAQs by category
        faq_by_category = {}
        for category in categories:
            category_faqs = faqs.filtered(lambda f: f.category_id.id == category.id)
            if category_faqs:
                faq_by_category[category] = category_faqs
        
        values = {
            'categories': categories,
            'faq_by_category': faq_by_category,
            'selected_category_id': category_id,
            'search_term': search or '',
            'total_faqs': len(faqs),
        }
        
        return request.render('customer_support_module.portal_faq', values)


    @http.route(['/my/faq/view/<int:faq_id>'], type='http', auth='user', website=True)
    def portal_faq_view(self, faq_id, **kwargs):
        """Display single FAQ with expanded answer and increment view count"""
        
        FAQ = request.env['customer.support.faq'].sudo()
        Category = request.env['customer.support.faq.category'].sudo()
        
        faq = FAQ.browse(faq_id)
        
        if not faq.exists() or not faq.active:
            return request.redirect('/my/faq')
        
        # Increment view count
        faq.write({'view_count': faq.view_count + 1})
        
        # Get all categories for sidebar
        categories = Category.search([('active', '=', True)])
        
        # Get all FAQs in the same category
        category_faqs = FAQ.search([
            ('active', '=', True),
            ('category_id', '=', faq.category_id.id)
        ])
        
        values = {
            'categories': categories,
            'selected_faq': faq,
            'category_faqs': category_faqs,
            'selected_category_id': faq.category_id.id,
        }
        
        return request.render('customer_support_module.portal_faq_detail', values)
    
    # Ticket Details
    @http.route(['/my/tickets/<int:ticket_id>'], type='http', auth='user', website=True)
    def portal_ticket_detail(self, ticket_id, **kwargs):
        """Display detailed view of a single ticket"""
        
        Ticket = request.env['customer.support.module'].sudo()
        
        # Get the ticket and verify ownership
        ticket = Ticket.browse(ticket_id)
        
        if not ticket.exists() or ticket.create_uid.id != request.env.uid:
            return request.redirect('/my/tickets')
        
        # Get phase labels
        phase_labels = self._get_phase_labels()
        
        # Get phase history
        phase_history = request.env['customer.support.phase.history'].sudo().search(
            [('ticket_id', '=', ticket.id)],
            order='change_date desc'
        )
        
        # Get priority label
        priority_labels = {
            '0': 'Low',
            '1': 'Medium',
            '2': 'High',
            '3': 'Urgent'
        }
        
        values = {
            'ticket': ticket,
            'phase_labels': phase_labels,
            'priority_label': priority_labels.get(ticket.priority, 'Unknown'),
            'phase_history': phase_history,
            'page_name': 'ticket_detail',
        }
        
        return request.render('customer_support_module.portal_ticket_detail', values)
    
    # Notification

    @http.route(['/my/notifications'], type='http', auth='user', website=True)
    def portal_notifications(self, **kwargs):
        """Display all notifications for the current user"""
        
        Notification = request.env['customer.support.notification'].sudo()
        
        # Get all notifications for current user
        notifications = Notification.search(
            [('user_id', '=', request.env.uid)],
            order='create_date desc'
        )
        
        # Separate read and unread
        unread_notifications = notifications.filtered(lambda n: not n.is_read)
        read_notifications = notifications.filtered(lambda n: n.is_read)
        
        values = {
            'notifications': notifications,
            'unread_notifications': unread_notifications,
            'read_notifications': read_notifications,
            'unread_count': len(unread_notifications),
        }
        
        return request.render('customer_support_module.portal_notifications', values)


    @http.route(['/my/notifications/mark-read/<int:notification_id>'], type='http', auth='user', website=True)
    def portal_notification_mark_read(self, notification_id, **kwargs):
        """Mark a single notification as read and redirect to ticket"""
        
        import logging
        _logger = logging.getLogger(__name__)
        
        try:
            Notification = request.env['customer.support.notification'].sudo()
            notification = Notification.browse(notification_id)
            
            _logger.info(f"Processing notification ID: {notification_id}")
            
            if not notification.exists():
                _logger.warning(f"Notification {notification_id} does not exist")
                return request.redirect('/my/notifications')
            
            if notification.user_id.id != request.env.uid:
                _logger.warning(f"User {request.env.uid} tried to access notification {notification_id} owned by {notification.user_id.id}")
                return request.redirect('/my/notifications')
            
            # Mark as read
            notification.action_mark_as_read()
            _logger.info(f"Marked notification {notification_id} as read")
            
            # Redirect to ticket details if ticket exists
            if notification.ticket_id and notification.ticket_id.exists():
                ticket_id = notification.ticket_id.id
                _logger.info(f"Redirecting to ticket {ticket_id}")
                return request.redirect(f'/my/tickets/{ticket_id}')
            else:
                _logger.info("No ticket associated with notification")
                return request.redirect('/my/notifications')
                
        except Exception as e:
            _logger.error(f"Error in portal_notification_mark_read: {str(e)}")
            import traceback
            _logger.error(traceback.format_exc())
            return request.redirect('/my/notifications')


    @http.route(['/my/notifications/mark-all-read'], type='http', auth='user', website=True)
    def portal_notification_mark_all_read(self, **kwargs):
        """Mark all notifications as read"""
        
        Notification = request.env['customer.support.notification'].sudo()
        Notification.action_mark_all_as_read(request.env.uid)
        
        return request.redirect('/my/notifications')


    @http.route(['/my/notifications/count'], type='json', auth='user')
    def portal_notification_count(self, **kwargs):
        """Get unread notification count (for AJAX calls if needed)"""
        
        Notification = request.env['customer.support.notification'].sudo()
        count = Notification.search_count([
            ('user_id', '=', request.env.uid),
            ('is_read', '=', False)
        ])
        
        return {'count': count}


    @http.route(['/my/notifications/delete/<int:notification_id>'], type='http', auth='user', website=True)
    def portal_notification_delete(self, notification_id, **kwargs):
        """Delete a notification"""
        
        Notification = request.env['customer.support.notification'].sudo()
        notification = Notification.browse(notification_id)
        
        if notification.exists() and notification.user_id.id == request.env.uid:
            notification.unlink()
        
        return request.redirect('/my/notifications')
