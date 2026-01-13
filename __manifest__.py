{
    'name': "customer_support_module",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mail','web','portal'],

    # always loaded
    'data': [
        'security/groups.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/projects.xml',
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
        'views/notification_views.xml',
        'views/portal_notification.xml',
        'views/portal_ticket_detail.xml',
        'views/sla_cron.xml',
        'views/activity_log_dashboard.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'customer_support_module/static/src/css/kanban.css',
            'customer_support_module/static/src/css/overview_dashboard.css',
            'customer_support_module/static/src/css/navbar.css',
            'customer_support_module/static/src/css/list.css',
            'customer_support_module/static/src/js/faq_dashboard.js',
            'customer_support_module/static/src/xml/faq_dashboard.xml',
        ],
    }

}