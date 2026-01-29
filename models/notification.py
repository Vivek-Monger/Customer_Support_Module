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
        ('sla_breach', 'SLA Breach'), 
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