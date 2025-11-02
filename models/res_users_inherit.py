from odoo import models, fields, api

class ResUsersInherit(models.Model):
    _inherit = 'res.users'

    user_role = fields.Selection([
        ('customer', 'Customer'),
        ('agent', 'Support Agent'),
    ], string="User Role", default='customer', required=True)

    @api.model
    def create(self, vals):
        user = super(ResUsersInherit, self).create(vals)
        try:
            if vals.get('user_role') == 'agent':
                group = self.env.ref('customer_support_module.group_support_agent', raise_if_not_found=False)
                if group:
                    user.groups_id = [(4, group.id)]
            elif vals.get('user_role') == 'customer':
                group = self.env.ref('customer_suppor_modulet.group_support_customer', raise_if_not_found=False)
                if group:
                    user.groups_id = [(4, group.id)]
        except Exception:
            pass
        return user

    def write(self, vals):
        res = super(ResUsersInherit, self).write(vals)
        if 'user_role' in vals:
            for user in self:
                try:
                    group_agent = self.env.ref('customer_support_module.group_support_agent', raise_if_not_found=False)
                    group_customer = self.env.ref('customer_support_module.group_support_customer', raise_if_not_found=False)

                    if vals['user_role'] == 'agent' and group_agent:
                        user.groups_id = [(3, group_customer.id), (4, group_agent.id)]
                    elif vals['user_role'] == 'customer' and group_customer:
                        user.groups_id = [(3, group_agent.id), (4, group_customer.id)]
                except Exception:
                    pass
        return res
