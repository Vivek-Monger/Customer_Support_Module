from odoo import models, fields, api
from datetime import timedelta

class CustomerSupportSLARule(models.Model):
    _name = 'customer.support.sla.rule'
    _description = 'Customer Support SLA Rule'
    _rec_name = 'priority'

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string="Priority", required=True)
    
    resolution_time = fields.Float(
        string="Resolution Time (Hours)",
        required=True,
        help="Maximum allowed time to resolve tickets of this priority"
    )
    
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('priority_unique',
         'unique(priority)',
         'Only one SLA rule is allowed per priority.')
    ]

    def get_sla_deadline(self, priority, start_date):
        """Calculate SLA deadline based on priority and start date"""
        sla_rule = self.search([('priority', '=', priority), ('active', '=', True)], limit=1)
        if sla_rule:
            deadline = start_date + timedelta(hours=sla_rule.resolution_time)
            return deadline
        return None

    @api.model
    def check_sla_breaches(self):
        """Cron job method to check for SLA breaches"""
        ticket_model = self.env['customer.support.module']
        tickets = ticket_model.search([
            ('phase_id', 'not in', ['resolved', 'closed']),
            ('sla_breached', '=', False)
        ])
        
        current_time = fields.Datetime.now()
        
        for ticket in tickets:
            if ticket.sla_deadline and current_time > ticket.sla_deadline:
                ticket.write({'sla_breached': True})
                ticket._notify_sla_breach()