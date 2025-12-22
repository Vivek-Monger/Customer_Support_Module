from odoo import models, fields, api


class customer_support_module(models.Model):
    _name = 'customer.support.module'
    _description = 'customer_support_module.customer_support_module'

 
    subject = fields.Char()
    project = fields.Char()
    description = fields.Text()
    priority = fields.Char()