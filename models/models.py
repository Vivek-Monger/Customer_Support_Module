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
            
    phase_id = fields.Selection(
        [
            ('new', 'New'),
            ('open', 'Open'),
            ('in_progress', 'In Progress'),
            ('resolved', 'Resolved'),
            ('closed', 'Closed'),
        ],
        string="Phase",
        default='new',
        tracking=True,
        group_expand='_group_expand_phase_id'
    )

    @api.model
    def _group_expand_phase_id(self, values, domain, order=None):
        return ['new', 'open', 'in_progress', 'resolved', 'closed']
    
    old_phase_id = fields.Selection(
        selection=lambda self: self.env['customer.support.module']._fields['phase_id'].selection,
        string="From Phase"
    )

    new_phase_id = fields.Selection(
        selection=lambda self: self.env['customer.support.module']._fields['phase_id'].selection,
        string="To Phase",
        required=True,
        default="new"
    )

    changed_by = fields.Many2one('res.users', string='Changed By')
    change_date = fields.Datetime(default=fields.Datetime.now)
    
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
        # default_phase = self._default_phase()
        records = super().create(vals_list)

        for rec in records:
            # Set assigned_date if assigned_user_id exists
            if rec.assigned_user_id and not rec.assigned_date:
                rec.assigned_date = rec.create_date

            # Set phase_date for initial phase
            if rec.phase_id and not rec.phase_date:
                rec.phase_date = rec.create_date

            # ========== NEW: Send email notification to assigned agent ==========
            if rec.assigned_user_id:
                rec._send_assignment_email()
            # ====================================================================

        return records

    def write(self, vals):
        # ========== NEW: Check if assigned_user_id is being changed ==========
        old_assigned_user = self.assigned_user_id if self else False
        # ====================================================================

        if 'phase_id' in vals:
            for ticket in self:
                self.env['customer.support.phase.history'].sudo().create({
                    'ticket_id': ticket.id,
                    'old_phase_id': ticket.phase_id,
                    'new_phase_id': vals['phase_id'],
                    'changed_by': self.env.uid,
                    'change_date': fields.Datetime.now(),
                })
            vals['phase_date'] = fields.Datetime.now()

        result = super().write(vals)

        # ========== NEW: Send email if assigned_user_id changed ==========
        if 'assigned_user_id' in vals:
            for rec in self:
                # Only send if actually changed and new agent is different from old
                if rec.assigned_user_id and rec.assigned_user_id != old_assigned_user:
                    rec._send_assignment_email()
        # ================================================================

        return result

    # ========== NEW METHOD: Send assignment email ==========
    def _send_assignment_email(self):
        """Send email notification to assigned support agent"""
        self.ensure_one()
        
        if not self.assigned_user_id or not self.assigned_user_id.email:
            return
        
        # Get priority label
        priority_dict = dict(self._fields['priority'].selection)
        priority_label = priority_dict.get(self.priority, 'Low')
        
        # Get customer name (ticket creator)
        customer_name = self.create_uid.name if self.create_uid else 'Unknown'
        
        # Get project name
        project_name = self.project_id.name if self.project_id else 'No Project'
        
        # Build ticket link
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', 'http://localhost:8069')
        ticket_url = f"{base_url}/web#id={self.id}&model=customer.support.module&view_type=form"
        
        # Email body
        mail_values = {
            'subject': f'New Ticket Assigned: {self.ticket_id} - {self.subject}',
            'body_html': f"""
                <p>Dear {self.assigned_user_id.name},</p>
                <p>A new support ticket has been assigned to you.</p>
                
                <h3>Ticket Details:</h3>
                <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background-color: #f9f9f9; font-weight: bold;">Ticket ID:</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{self.ticket_id}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background-color: #f9f9f9; font-weight: bold;">Subject:</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{self.subject or 'No Subject'}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background-color: #f9f9f9; font-weight: bold;">Customer:</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{customer_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background-color: #f9f9f9; font-weight: bold;">Project:</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{project_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background-color: #f9f9f9; font-weight: bold;">Priority:</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{priority_label}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background-color: #f9f9f9; font-weight: bold;">Description:</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{self.description or 'No description provided'}</td>
                    </tr>
                </table>
                
                <p style="margin-top: 20px;">
                    <a href="{ticket_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        View Ticket
                    </a>
                </p>
                
                <p>Please review and take action as needed.</p>
                <p>Best regards,<br>Customer Support System</p>
            """,
            'email_to': self.assigned_user_id.email,
            'email_from': '02220149.cst@rub.edu.bt',
        }
        
        self.env['mail.mail'].sudo().create(mail_values).send()
    # ======================================================


class CustomerSupportPhaseHistory(models.Model):
    _name = 'customer.support.phase.history'
    _description = 'Customer Support Phase History'

    ticket_id = fields.Many2one('customer.support.module', string='Ticket',ondelete = "cascade", required=True)
    old_phase_id = fields.Selection(
        selection=lambda self: self.env['customer.support.module']._fields['phase_id'].selection,
        string="From Phase"
    )

    new_phase_id = fields.Selection(
        selection=lambda self: self.env['customer.support.module']._fields['phase_id'].selection,
        string="To Phase",
        required=True,
        default="new"
    )

    changed_by = fields.Many2one('res.users', string='Changed By')
    change_date = fields.Datetime(default=fields.Datetime.now)