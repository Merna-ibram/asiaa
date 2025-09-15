/** @odoo-module **/

import { Component } from "@odoo/owl";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class addBookmark extends Component {
    static template = "main_menu.AddBookmark";
    static components = { DropdownItem };
    static props = {};

    setup() {
        this.action = useService("action");
        this.rpc = useService("rpc");
    }

    addBookmark() {
        this.rpc("/web/menu_bookmark/add", {
            name: window.document.title,
            url: window.location.href,
        });
    }
}

registry.category("cogMenu").add("add-bookmark", { Component: addBookmark }, { sequence: 1 });
