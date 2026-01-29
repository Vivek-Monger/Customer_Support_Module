from odoo import models, fields, api

class ProjectAssignmentWizard(models.TransientModel):
    _name = 'project.assignment.wizard'
    _description = 'Assign Projects to Customer'

    customer_id = fields.Many2one('res.users', string='Customer', required=True)
    project_ids = fields.Many2many(
        'customer.project',
        string='Projects to Assign',
        domain="[('customer_id', '=', False)]"  # Only unassigned projects
    )

    def action_assign_projects(self):
        """Assign selected projects to the customer"""
        self.ensure_one()
        if self.project_ids:
            self.project_ids.write({'customer_id': self.customer_id.id})
        return {'type': 'ir.actions.act_window_close'}