from odoo import models, fields

class TodoDeleteConfirm(models.TransientModel):
    _name = 'customer.support.delete.confirm'
    _description = 'Confirm To-Do Deletion'

    todo_id = fields.Many2one('customer.support.module', string='To-Do', required=True)

    def action_confirm_delete(self):
        """Deletes the selected record when user clicks 'Yes'."""
        if self.todo_id:
            self.todo_id.unlink()
        return {'type': 'ir.actions.act_window_close'}
