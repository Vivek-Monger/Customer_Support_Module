/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { MenuItem } from "@web/webclient/navbar/menu_item";

patch(MenuItem.prototype, "customer_support_module.MenuItemHighlight", {
    /**
     * After menu item click, add active class and remove from others
     */
    async onClick(ev) {
        // Call original behavior first
        await super.onClick(ev);

        // Remove active class from all menu items
        document.querySelectorAll(".o_menu_entry").forEach((item) => {
            item.classList.remove("active_menu");
        });

        // Add active class to clicked one
        const currentMenu = ev.currentTarget;
        if (currentMenu) {
            currentMenu.classList.add("active_menu");
        }
    },
});
