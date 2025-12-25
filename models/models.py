from odoo import models, fields, api

class customer_support_module(models.Model):
    _name = 'customer.support.module'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'customer_support_module.customer_support_module'

    ticket_id = fields.Char(
        string="Ticket ID",
        readonly=True,
        copy=False,
        index=True,
        default=lambda self: self._default_ticket_id()
    )
    
    subject = fields.Char(required = "True")
    project_id = fields.Many2one('customer.project', string='Project')
    description = fields.Text()
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string="Priority", default='0')
    
    # Simple binary field for file upload
    # attachment_file = fields.Binary(string="Attach File")
    # attachment_filename = fields.Char(string="File Name")
    # Computed field for attachments (alternative approach)
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'customer_support_attachment_rel',
        'ticket_id',
        'attachment_id',
        string="Attachments"
    )
            
    phase_id = fields.Many2one('progress.phase', 
                               string="Phase",
                               group_expand='_group_expand_phases', tracking=True)
    
    old_phase_id = fields.Many2one('progress.phase', string='From Phase')
    new_phase_id = fields.Many2one('progress.phase', string='To Phase', required=True)
    changed_by = fields.Many2one('res.users', string='Changed By')
    change_date = fields.Datetime(string='Change Date', default=fields.Datetime.now)
    
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
    
    assigned_user_id = fields.Many2one(
        'res.users',
        string="Assigned Agent",
        tracking=True,
    )
    
    assigned_date = fields.Datetime(
        string="Assigned Date",
        readonly=True,
        tracking=True
    )

    phase_date = fields.Datetime(
        string="Phase Change Date",
        readonly=True,
        tracking=True
    )

    
    @api.model_create_multi
    def create(self, vals_list):
        default_phase = self._default_phase()
        records = super().create(vals_list)

        for rec in records:
            # Set assigned_date if assigned_user_id exists
            if rec.assigned_user_id and not rec.assigned_date:
                rec.assigned_date = rec.create_date

            # Set phase_date for initial phase
            if rec.phase_id and not rec.phase_date:
                rec.phase_date = rec.create_date

        return records

    def write(self, vals):
        if 'assigned_user_id' in vals:
            vals['assigned_date'] = fields.Datetime.now()

        if 'phase_id' in vals:
            for ticket in self:
                self.env['customer.support.phase.history'].sudo().create({
                    'ticket_id': ticket.id,
                    'old_phase_id': ticket.phase_id.id,
                    'new_phase_id': vals['phase_id'],
                    'changed_by': self.env.uid,
                    'change_date': fields.Datetime.now()
                })
            vals['phase_date'] = fields.Datetime.now()

        return super().write(vals)


class CustomerSupportPhaseHistory(models.Model):
    _name = 'customer.support.phase.history'
    _description = 'Customer Support Phase History'

    ticket_id = fields.Many2one('customer.support.module', string='Ticket', required=True)
    old_phase_id = fields.Many2one('progress.phase', string='From Phase')
    new_phase_id = fields.Many2one('progress.phase', string='To Phase', required=True)
    changed_by = fields.Many2one('res.users', string='Changed By')
    change_date = fields.Datetime(string='Change Date', default=fields.Datetime.now)

