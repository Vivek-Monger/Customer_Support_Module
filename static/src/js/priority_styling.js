odoo.define('customer_support_module.priority_styling', function (require) {
    "use strict";

    var ListRenderer = require('web.ListRenderer');

    ListRenderer.include({
        _renderRow: function (record) {
            var $row = this._super.apply(this, arguments);
            var self = this;

            // Style priority field
            var priorityCell = $row.find('.o_priority_cell');
            if (priorityCell.length) {
                var priorityValue = priorityCell.text().trim().toLowerCase();
                var badgeClass = '';
                
                switch(priorityValue) {
                    case 'urgent':
                        badgeClass = 'priority-urgent';
                        break;
                    case 'high':
                        badgeClass = 'priority-high';
                        break;
                    case 'medium':
                        badgeClass = 'priority-medium';
                        break;
                    case 'low':
                        badgeClass = 'priority-low';
                        break;
                }
                
                if (badgeClass) {
                    priorityCell.html('<span class="priority-badge ' + badgeClass + '">' + priorityValue.charAt(0).toUpperCase() + priorityValue.slice(1) + '</span>');
                }
            }

            return $row;
        }
    });
});