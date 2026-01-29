from odoo import models, fields, api
from datetime import timedelta

class CustomerProject(models.Model):
    _name = 'customer.project'
    _description = 'Customer Projects with Warranty Management'
    _rec_name = "project_name"
    _order = 'create_date desc'

    # Basic Information
    project_name = fields.Char(string="Project Name", required=True)
    project_code = fields.Char(
        string="Project Code",
        readonly=True,
        copy=False,
        default=lambda self: self._default_project_code()
    )
    description = fields.Text(string="Description")
    customer_id = fields.Many2one(
        'res.users',
        string="Customer",
        required=False,  # ← Now optional
        domain=[('share', '=', True)],
        ondelete='set null'  # ← Changed from cascade
    )
    customer_name = fields.Char(related='customer_id.name', string="Customer Name", store=True)
    
    # Warranty Management
    start_date = fields.Date(
        string="Warranty Start Date",
        default=fields.Date.today,
        required=True
    )
    warranty_months = fields.Integer(
        string="Warranty Period (Months)",
        default=6,
        required=True
    )
    warranty_end_date = fields.Date(
        string="Warranty End Date",
        compute='_compute_warranty_end_date',
        store=True
    )
    
    # Status Fields
    is_warranty_active = fields.Boolean(
        string="Warranty Active",
        compute='_compute_warranty_status',
        store=True
    )
    warranty_status = fields.Selection([
        ('active', 'Active'),
        ('expiring_soon', 'Expiring Soon'),
        ('expired', 'Expired')
    ], string="Warranty Status", compute='_compute_warranty_status', store=True)
    
    days_remaining = fields.Integer(
        string="Days Remaining",
        compute='_compute_warranty_status'
    )
    
    # Additional Info
    notes = fields.Text(string="Notes")
    
    # Ticket Count
    ticket_count = fields.Integer(
        string="Tickets",
        compute='_compute_ticket_count'
    )
    
    @api.model
    def _default_project_code(self):
        """Generate default project code in format PRJ-XXXX"""
        existing_projects = self.search([
            ('project_code', 'like', '#PRJ-%')
        ])
        
        if existing_projects:
            max_seq = 0
            for project in existing_projects:
                try:
                    seq_part = project.project_code.split('-')[-1]
                    seq_num = int(seq_part)
                    if seq_num > max_seq:
                        max_seq = seq_num
                except (IndexError, ValueError):
                    continue
            next_seq = max_seq + 1
        else:
            next_seq = 1
            
        return f"#PRJ-{next_seq:04d}"
    
    @api.depends('start_date', 'warranty_months')
    def _compute_warranty_end_date(self):
        """Calculate warranty end date based on start date and warranty months"""
        for record in self:
            if record.start_date and record.warranty_months:
                # Calculate end date by adding months
                record.warranty_end_date = record.start_date + timedelta(days=record.warranty_months * 30)
            else:
                record.warranty_end_date = False
    
    @api.depends('warranty_end_date')
    def _compute_warranty_status(self):
        """Compute warranty status and days remaining"""
        today = fields.Date.today()
        
        for record in self:
            if not record.warranty_end_date:
                record.is_warranty_active = False
                record.warranty_status = 'expired'
                record.days_remaining = 0
                continue
            
            days_diff = (record.warranty_end_date - today).days
            record.days_remaining = days_diff if days_diff > 0 else 0
            
            if days_diff > 30:
                record.is_warranty_active = True
                record.warranty_status = 'active'
            elif days_diff > 0:
                record.is_warranty_active = True
                record.warranty_status = 'expiring_soon'
            else:
                record.is_warranty_active = False
                record.warranty_status = 'expired'
    
    def _compute_ticket_count(self):
        """Count tickets related to this project"""
        for record in self:
            record.ticket_count = self.env['customer.support.module'].search_count([
                ('project_id', '=', record.id)
            ])
    
    def action_view_tickets(self):
        """Smart button action to view tickets"""
        self.ensure_one()
        return {
            'name': f'Tickets - {self.project_name}',
            'type': 'ir.actions.act_window',
            'res_model': 'customer.support.module',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id}
        }
    
    def action_extend_warranty(self):
        """Action to extend warranty - opens wizard"""
        self.ensure_one()
        return {
            'name': 'Extend Warranty',
            'type': 'ir.actions.act_window',
            'res_model': 'customer.project',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }