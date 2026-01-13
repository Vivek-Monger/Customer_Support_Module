from odoo import models, fields, api
from datetime import datetime, timedelta


class CustomerSupportActivityLog(models.Model):
    _name = 'customer.support.activity.log'
    _description = 'Customer Support Activity Log'
    _order = 'activity_date desc'
    _rec_name = 'activity_type'

    ticket_id = fields.Many2one(
        'customer.support.module',
        string='Ticket',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    activity_type = fields.Selection([
        ('created', 'Ticket Created'),
        ('assigned', 'Ticket Assigned'),
        ('reassigned', 'Ticket Reassigned'),
        ('phase_change', 'Phase Changed'),
        ('priority_change', 'Priority Changed'),
        ('comment', 'Comment Added'),
        ('attachment', 'Attachment Added'),
        ('sla_breach', 'SLA Breach'),
        ('resolved', 'Ticket Resolved'),
        ('closed', 'Ticket Closed'),
        ('reopened', 'Ticket Reopened'),
    ], string='Activity Type', required=True, index=True)
    
    activity_date = fields.Datetime(
        string='Activity Date',
        default=fields.Datetime.now,
        required=True,
        index=True
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Performed By',
        default=lambda self: self.env.user,
        required=True
    )
    
    description = fields.Text(string='Description')
    
    # Additional fields for specific activity types
    old_value = fields.Char(string='Old Value')
    new_value = fields.Char(string='New Value')
    
    old_user_id = fields.Many2one('res.users', string='Previous User')
    new_user_id = fields.Many2one('res.users', string='New User')
    
    # Related fields for easy filtering
    ticket_subject = fields.Char(related='ticket_id.subject', store=True, string='Ticket Subject')
    ticket_priority = fields.Selection(related='ticket_id.priority', store=True, string='Priority')
    ticket_phase = fields.Selection(related='ticket_id.phase_id', store=True, string='Phase')
    customer_id = fields.Many2one(related='ticket_id.create_uid', store=True, string='Customer')
    
    @api.model
    def log_activity(self, ticket_id, activity_type, description, **kwargs):
        """
        Helper method to create activity log entries
        
        Usage:
            self.env['customer.support.activity.log'].log_activity(
                ticket_id=ticket.id,
                activity_type='assigned',
                description='Ticket assigned to John Doe',
                old_user_id=old_user.id,
                new_user_id=new_user.id
            )
        """
        vals = {
            'ticket_id': ticket_id,
            'activity_type': activity_type,
            'description': description,
        }
        
        # Add optional fields if provided
        if 'old_value' in kwargs:
            vals['old_value'] = kwargs['old_value']
        if 'new_value' in kwargs:
            vals['new_value'] = kwargs['new_value']
        if 'old_user_id' in kwargs:
            vals['old_user_id'] = kwargs['old_user_id']
        if 'new_user_id' in kwargs:
            vals['new_user_id'] = kwargs['new_user_id']
        if 'user_id' in kwargs:
            vals['user_id'] = kwargs['user_id']
            
        return self.create(vals)
    
    @api.model
    def get_activity_stats(self, date_from=None, date_to=None):
        """Get activity statistics for dashboard"""
        domain = []
        
        if date_from:
            domain.append(('activity_date', '>=', date_from))
        if date_to:
            domain.append(('activity_date', '<=', date_to))
        
        activities = self.search(domain)
        
        # Group by activity type
        activity_counts = {}
        for activity in activities:
            if activity.activity_type not in activity_counts:
                activity_counts[activity.activity_type] = 0
            activity_counts[activity.activity_type] += 1
        
        # Get most active users
        user_counts = {}
        for activity in activities:
            user_name = activity.user_id.name
            if user_name not in user_counts:
                user_counts[user_name] = 0
            user_counts[user_name] += 1
        
        # Sort users by activity count
        top_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_activities': len(activities),
            'activity_counts': activity_counts,
            'top_users': top_users,
        }
    
    @api.model
    def get_recent_activities(self, limit=10):
        """Get recent activities for dashboard widget"""
        return self.search([], order='activity_date desc', limit=limit)
    
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            activity_dict = dict(self._fields['activity_type'].selection)
            name = f"{record.ticket_id.ticket_id} - {activity_dict.get(record.activity_type)}"
            result.append((record.id, name))
        return result


class CustomerSupportModuleInherit(models.Model):
    _inherit = 'customer.support.module'
    
    activity_log_ids = fields.One2many(
        'customer.support.activity.log',
        'ticket_id',
        string='Activity Logs'
    )
    
    activity_count = fields.Integer(
        string='Activity Count',
        compute='_compute_activity_count'
    )
    
    @api.depends('activity_log_ids')
    def _compute_activity_count(self):
        for record in self:
            record.activity_count = len(record.activity_log_ids)
    
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        
        # Log ticket creation
        for record in records:
            priority_dict = dict(self._fields['priority'].selection)
            priority_label = priority_dict.get(record.priority, 'Unknown')
            
            self.env['customer.support.activity.log'].log_activity(
                ticket_id=record.id,
                activity_type='created',
                description=f'Ticket created with priority: {priority_label}',
                new_value=record.phase_id,
                user_id=record.create_uid.id
            )
            
            # Log assignment if assigned during creation
            if record.assigned_user_id:
                self.env['customer.support.activity.log'].log_activity(
                    ticket_id=record.id,
                    activity_type='assigned',
                    description=f'Ticket assigned to {record.assigned_user_id.name}',
                    new_user_id=record.assigned_user_id.id
                )
        
        return records
    
    def write(self, vals):
        # Store old values before write
        old_values = {}
        for record in self:
            old_values[record.id] = {
                'phase_id': record.phase_id,
                'priority': record.priority,
                'assigned_user_id': record.assigned_user_id,
            }
        
        result = super().write(vals)
        
        # Log activities after write
        ActivityLog = self.env['customer.support.activity.log']
        
        for record in self:
            old_vals = old_values.get(record.id, {})
            
            # Log phase changes
            if 'phase_id' in vals and old_vals.get('phase_id') != record.phase_id:
                phase_dict = dict(self._fields['phase_id'].selection)
                old_phase = phase_dict.get(old_vals.get('phase_id'), 'Unknown')
                new_phase = phase_dict.get(record.phase_id, 'Unknown')
                
                activity_type = 'phase_change'
                if record.phase_id == 'resolved':
                    activity_type = 'resolved'
                elif record.phase_id == 'closed':
                    activity_type = 'closed'
                elif old_vals.get('phase_id') in ['resolved', 'closed']:
                    activity_type = 'reopened'
                
                ActivityLog.log_activity(
                    ticket_id=record.id,
                    activity_type=activity_type,
                    description=f'Phase changed from {old_phase} to {new_phase}',
                    old_value=old_vals.get('phase_id'),
                    new_value=record.phase_id
                )
            
            # Log priority changes
            if 'priority' in vals and old_vals.get('priority') != record.priority:
                priority_dict = dict(self._fields['priority'].selection)
                old_priority = priority_dict.get(old_vals.get('priority'), 'Unknown')
                new_priority = priority_dict.get(record.priority, 'Unknown')
                
                ActivityLog.log_activity(
                    ticket_id=record.id,
                    activity_type='priority_change',
                    description=f'Priority changed from {old_priority} to {new_priority}',
                    old_value=old_vals.get('priority'),
                    new_value=record.priority
                )
            
            # Log assignment/reassignment
            if 'assigned_user_id' in vals:
                old_user = old_vals.get('assigned_user_id')
                new_user = record.assigned_user_id
                
                if old_user and new_user and old_user != new_user:
                    # Reassignment
                    ActivityLog.log_activity(
                        ticket_id=record.id,
                        activity_type='reassigned',
                        description=f'Ticket reassigned from {old_user.name} to {new_user.name}',
                        old_user_id=old_user.id,
                        new_user_id=new_user.id
                    )
                elif not old_user and new_user:
                    # Initial assignment
                    ActivityLog.log_activity(
                        ticket_id=record.id,
                        activity_type='assigned',
                        description=f'Ticket assigned to {new_user.name}',
                        new_user_id=new_user.id
                    )
            
            # Log SLA breach
            if 'sla_breached' in vals and vals['sla_breached']:
                ActivityLog.log_activity(
                    ticket_id=record.id,
                    activity_type='sla_breach',
                    description=f'SLA deadline breached at {fields.Datetime.now()}'
                )
        
        return result
    
    def action_view_activity_log(self):
        """Action to view activity log for this ticket"""
        self.ensure_one()
        return {
            'name': f'Activity Log - {self.ticket_id}',
            'type': 'ir.actions.act_window',
            'res_model': 'customer.support.activity.log',
            'view_mode': 'tree,form',
            'domain': [('ticket_id', '=', self.id)],
            'context': {'default_ticket_id': self.id},
            'target': 'current',
        }