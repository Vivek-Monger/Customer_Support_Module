from odoo import models

class ResUsers(models.Model):
    _inherit = 'res.users'

    def _get_login_redirect_url(self):
        self.ensure_one()

        if self.has_group('customer_support_module.group_customer'):
            return '/web#action=customer_support_module.action_my_tickets'

        if self.has_group('customer_support_module.group_support_agent'):
            return '/web#action=customer_support_module.action_my_tickets'

        return super()._get_login_redirect_url()
