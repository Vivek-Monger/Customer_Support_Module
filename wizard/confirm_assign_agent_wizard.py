from odoo import models, fields, api
from odoo.exceptions import UserError

class ConfirmAssignAgentWizard(models.TransientModel):
    _name = 'confirm.assign.agent.wizard'
    _description = 'Confirm Agent Assignment'

    ticket_id = fields.Many2one('customer.support.module', string="Ticket", required=True)
    assigned_user_id = fields.Many2one('res.users', string="Agent", required=True, readonly=True)

    def action_confirm_assignment(self):
        """Confirm and assign the selected agent"""
        self.ensure_one()
        ticket = self.ticket_id

        # Verify manager role
        if not self.env.user.has_group('customer_support_module.group_support_manager'):
            raise UserError("Only Managers can assign agents.")

        # Write the assignment
        ticket.write({'assigned_user_id': self.assigned_user_id.id})

        # Post message in chatter
        ticket.message_post(
            body=f"<b>Assigned Agent:</b> {self.assigned_user_id.name}",
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )

        # Close the wizard and return to list view
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'customer.support.module',
            'view_mode': 'list,kanban,form',
            'target': 'current',
        }

    def action_cancel(self):
        """Cancel and close popup"""
        return {'type': 'ir.actions.act_window_close'}
