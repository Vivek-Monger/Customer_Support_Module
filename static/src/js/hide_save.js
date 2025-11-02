odoo.define('customer_support_module.hide_save', function (require) {
    "use strict";

    var FormController = require('web.FormController');

    FormController.include({
        renderButtons: function($node) {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                // Hide only the default Save button
                this.$buttons.find('button[name="save"]').hide();
            }
        },
    });

    console.log('Hide Save JS loaded'); // for debugging
});
