from odoo import models, fields, api


class customer_support_module(models.Model):
    _name = 'customer.support.module'
    _description = 'customer_support_module.customer_support_module'

 
    ticket_id = fields.Char(
        string="Ticket ID",
        readonly=True,
        copy=False,
        index=True,
        default=lambda self: self._default_ticket_id()
    )
    
    subject = fields.Char()
    project = fields.Many2one('customer.project')
    description = fields.Text()
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string="Priority", default='0')
    
    # Simple binary field for file upload
    attachment_file = fields.Binary(string="Attach File")
    attachment_filename = fields.Char(string="File Name")
    # Computed field for attachments (alternative approach)
    attachment_ids = fields.One2many(
        'ir.attachment', 
        'res_id', 
        string='Attachments',
        domain=[('res_model', '=', 'customer.support.module')]
    )
    
    phase_id = fields.Many2one('progress.phase', 
                               string="Phase",
                               group_expand='_group_expand_phases')
    
    @api.model
    def _default_ticket_id(self):
        """Generate default ticket ID in format DC-XXXX"""
        
        # Find the highest sequence number for today
        existing_tickets = self.search([
            ('ticket_id', 'like', f'#DC-%')
        ])
        
        if existing_tickets:
            # Extract the highest sequence number
            max_seq = 0
            for ticket in existing_tickets:
                try:
                    seq_part = ticket.ticket_id.split('-')[-1]
                    seq_num = int(seq_part)
                    if seq_num > max_seq:
                        max_seq = seq_num
                except (IndexError, ValueError):
                    continue
            next_seq = max_seq + 1
        else:
            next_seq = 1
            
        return f"#DC-{next_seq:04d}"
    
    @api.model
    def _group_expand_phases(self, groups, domain):
        return self.env['progress.phase'].search([])
    
    @api.model
    def _default_phase(self):
        return self.env['progress.phase'].search(
            [('phase', '=', 'New')],
            limit=1
        )

    @api.model_create_multi
    def create(self, vals_list):
        default_phase = self._default_phase()

        for vals in vals_list:
            if not vals.get('phase_id'):
                vals['phase_id'] = default_phase.id if default_phase else False

        return super().create(vals_list)

