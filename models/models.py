from odoo import fields, models, api
from odoo.exceptions import UserError
from datetime import datetime, timedelta

class CustomerSupportModule(models.Model):
    _name = "customer.support.module"
    _description = "This is Customer Support Module"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    
    # Add ticket_id field
    ticket_id = fields.Char(
        string="Ticket ID",
        readonly=True,
        copy=False,
        index=True,
        default=lambda self: self._default_ticket_id()
    )
    subject = fields.Char(required=True)
    description = fields.Text()
    date = fields.Date(default=fields.Date.context_today)
    create_date_time = fields.Datetime(string="Creation DateTime", default=lambda self: fields.Datetime.now())
    
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Urgent ')
    ], string="Priority", default='0')

    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)

    assigned_user_id = fields.Many2one(
    'res.users',
    string='Assigned To',
    help="User responsible for handling this ticket",
    domain=lambda self: [('groups_id', 'in', self.env.ref('customer_support_module.group_support_agent').id)]
    )
    
    
    
    @api.onchange('assigned_user_id')
    def _onchange_assigned_user_id(self):
        """Restrict assignment only to users in the Support Agent group."""
        agent_group = self.env.ref('customer_support_module.group_support_agent')
        return {'domain': {'assigned_user_id': [('groups_id', 'in', [agent_group.id])]}}


    agent_reply = fields.Text(string="Support Agent Reply")

    solution = fields.Text(string="Solution")

    phase_id = fields.Many2one(
        'progress.phase',
        string="Phase",
        ondelete='set null',
        group_expand='_group_expand_phases'
    )

    # image = fields.Image(max_width=128, max_height=128)
    # image_name = fields.Char()

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

    @api.model
    def _group_expand_phases(self, groups, domain):
        return self.env['progress.phase'].search([])

    @api.model
    def create(self, vals):
        # Only customers can create tickets
        if not self.env.user.has_group('customer_support_module.group_support_customer'):
            raise UserError("Only customers can create support tickets.")

        # Ensure the ticket is not assigned to an agent directly
        if vals.get('assigned_user_id'):
            raise UserError("Customers cannot assign tickets directly to agents. It will be reviewed by a manager first.")

        # Assign default phase if not set
        if not vals.get('phase_id'):
            new_phase = self.env['progress.phase'].search([('phase', '=', 'New')], limit=1)
            if new_phase:
                vals['phase_id'] = new_phase.id

        # Assign current user as the ticket creator
        vals['user_id'] = self.env.user.id

        # Assign the ticket to a manager (first available manager)
        manager_user = self.env['res.users'].search([('groups_id', 'in', self.env.ref('customer_support_module.group_support_manager').id)], limit=1)
        if not manager_user:
            raise UserError("No manager found to assign this ticket.")
        vals['assigned_user_id'] = manager_user.id

        return super(CustomerSupportModule, self).create(vals)


    def write(self, vals):
        for record in self:
            # Allow edits only within first 30 seconds after creation
            allowed_time = record.create_date + timedelta(seconds=30)
            if datetime.utcnow() > allowed_time:
                # After 30 seconds, prevent edits to subject, description, priority, image
                forbidden_fields = ['subject', 'description', 'priority', 'image']
                for field in forbidden_fields:
                    if field in vals:
                        raise UserError(f"{field.replace('_',' ').title()} cannot be edited after 30 seconds of creation.")

            # Restrict phase change (Kanban drag) for customers
            if 'phase_id' in vals:
                # If the user is NOT a support agent
                if not self.env.user.has_group('customer_support_module.group_support_agent'):
                    raise UserError("Only Support Agents can change the ticket phase (drag in Kanban view).")

        return super(CustomerSupportModule, self).write(vals)

    
    # def edit_ticket(self):
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Edit Ticket',
    #         'res_model': 'customer.support.module',
    #         'view_mode': 'form',
    #         'res_id': self.id,
    #         'target': 'current',
    #     }

    # def action_confirm_delete(self):
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'customer.support.delete.confirm',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {'default_todo_id': self.id},
    #     }
    
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
    
    def action_create_ticket(self):
        self.ensure_one()

        if not self.env.user.has_group('customer_support_module.group_support_customer'):
            raise UserError("Only customers can create tickets.")

        # Just confirm or save existing record, no need to create new one
        self.write({'date': fields.Date.context_today(self)})

        # Optional: show success message
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Ticket Submitted',
                'message': 'Your support ticket has been submitted successfully!',
                'sticky': False,
            }
        }
        
    def action_submit_reply(self):
        """Allow only Support Agents to submit replies."""
        for record in self:
            if not self.env.user.has_group('customer_support_module.group_support_agent'):
                raise UserError("Only Support Agents can submit replies.")

            if not record.agent_reply:
                raise UserError("Please enter a reply before submitting.")

            # Post the reply to the chatter
            record.message_post(
                body=f"<b>Agent Reply:</b><br/>{record.agent_reply}",
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )

            # Save the reply in the record (no clearing)
            record.write({'agent_reply': record.agent_reply})
            
    def action_assign_agent(self):
        """Allow managers to assign a support agent to the ticket."""
        for record in self:
            if not self.env.user.has_group('customer_support_module.group_support_manager'):
                raise UserError("Only Managers can assign agents.")

            if not record.assigned_user_id:
                raise UserError("Please select an agent before clicking 'Assign Agent'.")

            # Save the assignment
            record.write({'assigned_user_id': record.assigned_user_id})

            # Optional: post a message to chatter
            record.message_post(
                body=f"<b>Assigned Agent:</b> {record.assigned_user_id.name}",
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )
    def action_cancel(self):
        """Close the current form without saving"""
        return {'type': 'ir.actions.act_window_close'}
        
        
class Phase(models.Model):
    _name = "progress.phase"
    _description = "This is phase for Customer Support"
    _rec_name = "phase"

    phase = fields.Char(string="Phase Name")
    