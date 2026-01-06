from odoo import models, fields, api

class CustomerSupportNotification(models.Model):
    _name = 'customer.support.notification'
    _description = 'Customer Support Notification'
    _order = 'create_date desc'

    ticket_id = fields.Many2one(
        'customer.support.module',
        string='Ticket',
        required=True,
        ondelete='cascade'
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        ondelete='cascade'
    )
    
    title = fields.Char(string='Title', required=True)
    message = fields.Text(string='Message', required=True)
    
    notification_type = fields.Selection([
        ('phase_change', 'Phase Change'),
        ('assignment', 'Assignment'),
        ('comment', 'Comment'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ], string='Type', default='phase_change')
    
    is_read = fields.Boolean(string='Read', default=False)
    read_date = fields.Datetime(string='Read Date', readonly=True)
    
    def action_mark_as_read(self):
        """Mark notification as read"""
        self.ensure_one()
        if not self.is_read:
            self.write({
                'is_read': True,
                'read_date': fields.Datetime.now()
            })
    
    def action_mark_all_as_read(self, user_id):
        """Mark all notifications as read for a user"""
        notifications = self.search([
            ('user_id', '=', user_id),
            ('is_read', '=', False)
        ])
        notifications.write({
            'is_read': True,
            'read_date': fields.Datetime.now()
        })


# Modify the existing customer_support_module class to add notification creation
# Add this to your existing customer_support_module class in models.py

class customer_support_module(models.Model):
    _inherit = 'customer.support.module'
    
    def _create_notification(self, user_id, title, message, notification_type='phase_change'):
        """Helper method to create notifications"""
        self.env['customer.support.notification'].sudo().create({
            'ticket_id': self.id,
            'user_id': user_id,
            'title': title,
            'message': message,
            'notification_type': notification_type,
        })
    
    def write(self, vals):
        """Override write to create notifications on phase change"""
        # Store old phase for each ticket
        old_phases = {}
        for ticket in self:
            old_phases[ticket.id] = ticket.phase_id
        
        # Call parent write
        result = super(customer_support_module, self).write(vals)
        
        # Create notifications for phase changes
        if 'phase_id' in vals:
            for ticket in self:
                old_phase = old_phases.get(ticket.id)
                new_phase = ticket.phase_id
                
                if old_phase != new_phase:
                    # Get phase labels
                    phase_labels = dict(self._fields['phase_id'].selection)
                    old_phase_label = phase_labels.get(old_phase, 'Unknown')
                    new_phase_label = phase_labels.get(new_phase, 'Unknown')
                    
                    # Create notification for ticket creator
                    if ticket.create_uid:
                        title = f'Ticket {ticket.ticket_id} Status Updated'
                        message = f'Your ticket "{ticket.subject}" has been moved from {old_phase_label} to {new_phase_label}.'
                        
                        ticket._create_notification(
                            user_id=ticket.create_uid.id,
                            title=title,
                            message=message,
                            notification_type='phase_change'
                        )
        
        return result