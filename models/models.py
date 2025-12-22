from odoo import models, fields, api


class customer_support_module(models.Model):
    _name = 'customer.support.module'
    _description = 'customer_support_module.customer_support_module'

 
    subject = fields.Char()
    project = fields.Many2one('customer.project')
    description = fields.Text()
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string="Priority", default='0')