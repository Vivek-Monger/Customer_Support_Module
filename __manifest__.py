{
    'name': "customer_support_module",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'mail', 'web', 'portal'],

    'data': [
    'security/groups.xml',
    'security/security.xml',
    'security/ir.model.access.csv',
    'views/views.xml',
    'views/projects.xml',
    'views/project_assignment_wizard.xml',  
    'views/user_manager.xml',               
    'views/portal_menu.xml',
    'views/portal_my_tickets.xml',
    'views/portal_create_ticket.xml',
    'views/portal_reporting.xml',
    'views/sla_rule.xml',
    'views/support_dashboard_view.xml',
    'views/overview.xml',
    'views/portal_ticket_overview.xml',
    'views/portal_activity_log.xml',
    'views/portal_ticket_confirmation.xml',
    'views/portal_faq.xml',
    'views/faq_views.xml',
    ],
    

    'installable': True,
    'application': True,
    'auto_install': False,
}