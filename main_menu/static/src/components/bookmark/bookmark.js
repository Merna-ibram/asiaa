/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted } from "@odoo/owl";
import { Deferred } from "@web/core/utils/concurrency";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { useDiscussSystray } from "@mail/utils/common/hooks";

export class Bookmark extends Component {
    static components = { Dropdown, DropdownItem };
    static props = [];
    static template = "main_menu.Bookmark";

    setup() {
        this.discussSystray = useDiscussSystray();
        this.action = useService("action");
        this.rpc = useService("rpc");
        this.fetchDeferred = new Deferred();
        this.bookmarks = [];

        onMounted(() => {
            this.fetchBookmarks();
        });
    }

    openMyBookmarks() {
        this.action.doAction("main_menu.menu_bookmark_action_my_bookmarks", { clearBreadcrumbs: true });
    }

    openBookmark(bookmark) {
        window.open(bookmark.url, bookmark.target);
    }

    onBeforeOpen() {
        const fetchDeferred = this.fetchDeferred;
        this.fetchBookmarks();
        return fetchDeferred;
    }

    async fetchBookmarks() {
        const fetchDeferred = this.fetchDeferred;
        this.rpc("/web/menu_bookmark/data").then(
            (data) => {
                this.bookmarks = data;
                fetchDeferred.resolve(data);
            },
            (error) => {
                fetchDeferred.reject(error);
            }
        );
        this.fetchDeferred = new Deferred();
    }
}

registry
    .category("systray")
    .add("main_menu.bookmark", { Component: Bookmark }, { sequence: 10 });
