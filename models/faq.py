from odoo import models, fields, api

class CustomerSupportFAQ(models.Model):
    _name = 'customer.support.faq'
    _description = 'Customer Support FAQ'
    _order = 'sequence, id'

    name = fields.Char(string='Question', required=True)
    answer = fields.Html(string='Answer', required=True)
    sequence = fields.Integer(string='Sequence', default=10, help="Order of display")
    
    category_id = fields.Many2one(
        'customer.support.faq.category',
        string='Category',
        required=True
    )
    
    active = fields.Boolean(default=True, help="Uncheck to hide this FAQ from portal")
    
    view_count = fields.Integer(string='View Count', default=0, readonly=True)
    
    created_by = fields.Many2one(
        'res.users',
        string='Created By',
        default=lambda self: self.env.user,
        readonly=True
    )
    
    last_updated = fields.Datetime(
        string='Last Updated',
        default=fields.Datetime.now,
        readonly=True
    )
    
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record.last_updated = fields.Datetime.now()
        return records
    
    def write(self, vals):
        vals['last_updated'] = fields.Datetime.now()
        return super().write(vals)


class CustomerSupportFAQCategory(models.Model):
    _name = 'customer.support.faq.category'
    _description = 'FAQ Category'
    _order = 'sequence, name'

    name = fields.Char(string='Category Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(default=True)
    
    faq_ids = fields.One2many(
        'customer.support.faq',
        'category_id',
        string='FAQs'
    )
    
    faq_count = fields.Integer(
        string='FAQ Count',
        compute='_compute_faq_count'
    )
    
    @api.depends('faq_ids')
    def _compute_faq_count(self):
        for category in self:
            category.faq_count = len(category.faq_ids.filtered(lambda f: f.active))