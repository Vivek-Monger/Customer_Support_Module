# -*- coding: utf-8 -*-
{
    'name': "Customer_Support_Module",

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
    'depends': ['base','mail'],

    # always loaded
    'data': [
        'security/customer_support_security.xml',
        'security/record_rules.xml',
        'security/ir.model.access.csv',
        
        'views/views.xml',
        'views/phase.xml',
        #'views/delete_confirm_view.xml',
        'views/res_users_inherit_view.xml',
        'views/dashboard_view.xml',
        'wizard/views.xml',
        'wizard/confirm_assign_agent_wizard_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo/demo.xml',
    ],
    'assets': {
    'web.assets_backend': [
        'customer_support_module/static/src/js/priority_styling.js',
        'customer_support_module/static/src/css/dashboard.css',
        'customer_support_module/static/src/css/customer_support_form.css',
        'customer_support_module/static/src/css/customer_support_list.css',
        #'customer_support_module/static/src/priority_styling.js',
        'customer_support_module/static/src/css/confirm_ticket.css',
    ],
    },
    'installable': True,
    'application': True,
}

