from datetime import datetime, timedelta
from odoo import models, fields, api

class CustomerSupportDashboard(models.TransientModel):
    _name = 'customer.support.dashboard'
    _description = 'Customer Support Dashboard'

    # Column 1 Fields
    tickets_count = fields.Integer(string="Open Tickets", readonly=True)
    avg_open_hours = fields.Float(string="Avg Open Hours", readonly=True)
    failed_tickets_count = fields.Integer(string="Failed Tickets", readonly=True)
    
    # Column 2 Fields  
    total_tickets = fields.Integer(string="Total Tickets", readonly=True)
    total_hours = fields.Float(string="Total Hours", readonly=True)
    failed_rate = fields.Float(string="Failed Rate", readonly=True)
    
    # Column 3 Fields
    high_priority_count = fields.Integer(string="High Priority", readonly=True)
    avg_high_priority_hours = fields.Float(string="Avg High Priority Hours", readonly=True)
    high_priority_failed = fields.Integer(string="High Priority Failed", readonly=True)
    
    # Column 4 Fields
    urgent_count = fields.Integer(string="Urgent", readonly=True)
    avg_urgent_hours = fields.Float(string="Avg Urgent Hours", readonly=True)
    urgent_failed = fields.Integer(string="Urgent Failed", readonly=True)
    
    # Performance Card Fields
    closed_today_count = fields.Integer(string="Closed Today", readonly=True)
    avg_last_7_days = fields.Float(string="Avg Last 7 Days", readonly=True)
    daily_target = fields.Float(string="Daily Target", readonly=True)

    @api.model
    def get_dashboard_data(self):
        """Compute live stats for the dashboard."""
        Ticket = self.env['customer.support.module']
        now = datetime.now()
        
        # Helper function to safely compute hours
        def safe_hours(create_date):
            if not create_date:
                return 0.0
            if isinstance(create_date, str):
                create_date = fields.Datetime.from_string(create_date)
            return float((now - create_date).total_seconds() / 3600)

        # Get all tickets
        all_tickets = Ticket.search([])
        total_tickets = len(all_tickets)
        
        # Open Tickets (all non-closed tickets)
        closed_phase = self.env['progress.phase'].search([('phase', '=', 'Closed')], limit=1)
        if closed_phase:
            open_tickets_records = Ticket.search([('phase_id', '!=', closed_phase.id)])
        else:
            open_tickets_records = all_tickets
        
        open_tickets = len(open_tickets_records)
        
        # Failed tickets: open > 48 hours
        failed_tickets = 0
        for ticket in open_tickets_records:
            hours_open = safe_hours(ticket.create_date)
            if hours_open > 48:  # SLA threshold
                failed_tickets += 1

        # Priority counts
        high_priority_tickets = Ticket.search([('priority', '=', '2')])
        urgent_tickets = Ticket.search([('priority', '=', '3')])
        high_priority = len(high_priority_tickets)
        urgent = len(urgent_tickets)

        # Calculate total hours and average open hours
        total_hours_calculated = sum([safe_hours(t.create_date) for t in open_tickets_records])
        avg_open_hours_calculated = round(total_hours_calculated / open_tickets, 1) if open_tickets else 0.0

        # Failed rate
        failed_rate_calculated = round((failed_tickets / total_tickets) * 100, 1) if total_tickets else 0.0

        # High priority calculations
        total_high_priority_hours = sum([safe_hours(t.create_date) for t in high_priority_tickets])
        high_priority_failed_count = sum([1 for t in high_priority_tickets if safe_hours(t.create_date) > 48])
        avg_high_priority_hours_calculated = round(total_high_priority_hours / high_priority, 1) if high_priority else 0.0

        # Urgent calculations
        total_urgent_hours = sum([safe_hours(t.create_date) for t in urgent_tickets])
        urgent_failed_count = sum([1 for t in urgent_tickets if safe_hours(t.create_date) > 24])  # SLA 24h
        avg_urgent_hours_calculated = round(total_urgent_hours / urgent, 1) if urgent else 0.0

        # Performance Card Calculations
        # Closed Today
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        if closed_phase:
            closed_today = Ticket.search_count([
                ('phase_id', '=', closed_phase.id),
                ('write_date', '>=', today_start),
                ('write_date', '<=', today_end)
            ])
        else:
            closed_today = 0

        # Avg Last 7 Days (SLA Success Rate)
        seven_days_ago = now - timedelta(days=7)
        tickets_last_7_days = Ticket.search_count([
            ('create_date', '>=', seven_days_ago),
            ('create_date', '<=', now)
        ])
        
        if tickets_last_7_days > 0:
            successful_tickets_7_days = tickets_last_7_days - failed_tickets
            avg_last_7_days_calculated = round((successful_tickets_7_days / tickets_last_7_days) * 100, 2)
        else:
            avg_last_7_days_calculated = 100.0

        # Daily Target (Achievement Rate)
        daily_target_calculated = 80.0  # Default target as shown in image

        return {
            # Column 1
            'tickets_count': int(open_tickets),
            'avg_open_hours': float(avg_open_hours_calculated),
            'failed_tickets_count': int(failed_tickets),
            
            # Column 2
            'total_tickets': int(total_tickets),
            'total_hours': float(round(total_hours_calculated, 1)),
            'failed_rate': float(failed_rate_calculated),
            
            # Column 3
            'high_priority_count': int(high_priority),
            'avg_high_priority_hours': float(avg_high_priority_hours_calculated),
            'high_priority_failed': int(high_priority_failed_count),
            
            # Column 4
            'urgent_count': int(urgent),
            'avg_urgent_hours': float(avg_urgent_hours_calculated),
            'urgent_failed': int(urgent_failed_count),
            
            # Performance Card
            'closed_today_count': int(closed_today),
            'avg_last_7_days': float(avg_last_7_days_calculated),
            'daily_target': float(daily_target_calculated),
        }

    @api.model
    def default_get(self, fields_list):
        """When dashboard is opened, fill data automatically."""
        res = super().default_get(fields_list)
        res.update(self.get_dashboard_data())
        return res