from odoo import models

class ResUsers(models.Model):
    _inherit = 'res.users'

    def _get_login_redirect_url(self):
        self.ensure_one()

        # Portal customers → Portal tickets page
        if self.has_group('base.group_portal'):
            return '/my/tickets'

        # Internal support agents → Backend action
        if self.has_group('base.group_user'):
            return '/web#action=customer_support_module.action_my_tickets'

        return super()._get_login_redirect_url()
