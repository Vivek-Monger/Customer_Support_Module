from odoo import models, fields, api

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
