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

    DEFAULT_PASSWORD = '123'

    @api.model_create_multi
    def create(self, vals_list):
        records = self.env['user.manager']

        portal_group = self.env.ref('base.group_portal')
        internal_group = self.env.ref('base.group_user')

        for vals in vals_list:
            name = vals.get('name')
            email = vals.get('email')
            role = vals.get('role')

            if not name or not email or not role:
                records |= super().create(vals)
                continue

            # Prevent duplicate users
            if self.env['res.users'].sudo().search([('login', '=', email)], limit=1):
                raise ValidationError(f"User with email {email} already exists.")

            # --------------------------------------------------
            # CUSTOMER → PORTAL USER
            # --------------------------------------------------
            if role == 'customer':
                partner = self.env['res.partner'].sudo().create({
                    'name': name,
                    'email': email,
                })

                user = self.env['res.users'].sudo().create({
                    'name': name,
                    'login': email,
                    'email': email,
                    'partner_id': partner.id,
                    'share': True,
                })

                # ✅ Odoo 19 way: manage groups from res.groups
                internal_group.sudo().write({
                    'user_ids': [(3, user.id)]
                })
                portal_group.sudo().write({
                    'user_ids': [(4, user.id)]
                })

            # --------------------------------------------------
            # SUPPORT AGENT → INTERNAL USER
            # --------------------------------------------------
            elif role == 'support_agent':
                user = self.env['res.users'].sudo().create({
                    'name': name,
                    'login': email,
                    'email': email,
                    'share': False,
                })

                portal_group.sudo().write({
                    'user_ids': [(3, user.id)]
                })
                internal_group.sudo().write({
                    'user_ids': [(4, user.id)]
                })

            else:
                raise ValidationError("Invalid role selected")

            # Set default password
            user.sudo().write({'password': self.DEFAULT_PASSWORD})

            # Send welcome email to customer
            if role == 'customer':
                mail_values = {
                    'subject': 'Welcome to Customer Support Portal',
                    'body_html': f"""
                        <p>Dear {name},</p>
                        <p>Welcome to our Customer Support Portal!</p>
                        <p>Your account has been created successfully.</p>
                        <p><strong>Login Details:</strong></p>
                        <ul>
                            <li>Email: {email}</li>
                            <li>Password: {self.DEFAULT_PASSWORD}</li>
                        </ul>
                        <p>Please log in and change your password for security.</p>
                        <p>Best regards,<br>Customer Support Team</p>
                    """,
                    'email_to': email,
                    'email_from': '02220149.cst@rub.edu.bt',
                }
                self.env['mail.mail'].sudo().create(mail_values).send()

            vals['user_id'] = user.id
            records |= super().create(vals)

        return records