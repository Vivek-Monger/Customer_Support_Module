from odoo import models, fields


class customer_support_module(models.Model):
    _name = 'customer.project'
    _description = 'List of Projects'
    _rec_name = "project"

    project = fields.Char(required = "True")
    description = fields.Text()
    