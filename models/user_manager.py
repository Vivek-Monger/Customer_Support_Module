from odoo import models, fields, api
from odoo.exceptions import ValidationError


class UserManager(models.Model):
    _name = 'user.manager'
    _description = 'Manage Customers and Support Agents'

    name = fields.Char(required=True)
    email = fields.Char(required=True)
    role = fields.Selection([
        ('customer', 'Customer'),
        ('support_agent', 'Support Agent')
    ], required=True)
    user_id = fields.Many2one('res.users', readonly=True)

    DEFAULT_PASSWORD = 'changeme123'

    @api.model_create_multi
    def create(self, vals_list):
        records = self.env['user.manager']

        for vals in vals_list:
            name = vals.get('name')
            email = vals.get('email')
            role = vals.get('role')

            if not name or not email or not role:
                records |= super().create(vals)
                continue

            if self.env['res.users'].sudo().search([('login', '=', email)], limit=1):
                raise ValidationError(f"User with email {email} already exists.")

            # Create user (gets internal group by default)
            user = self.env['res.users'].sudo().create({
                'name': name,
                'login': email,
                'email': email,
            })

            if role == 'customer':
                partner = self.env['res.partner'].sudo().create({
                    'name': name,
                    'email': email,
                })

                user.sudo().write({
                    'partner_id': partner.id,
                    'share': True,
                })

                # Remove internal user group
                self.env.ref('base.group_user').sudo().write({
                    'user_ids': [(3, user.id)]
                })

                # Add portal group
                self.env.ref('base.group_portal').sudo().write({
                    'user_ids': [(4, user.id)]
                })

            elif role == 'support_agent':
                # Internal user → nothing else required
                pass

            else:
                raise ValidationError("Invalid role selected")

            # ✅ SET DEFAULT PASSWORD (Odoo 19 compatible)
            user.sudo().write({'password': self.DEFAULT_PASSWORD})

            vals['user_id'] = user.id
            records |= super().create(vals)

        return records
