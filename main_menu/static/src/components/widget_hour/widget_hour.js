/** @odoo-module **/

import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class WidgetHour extends Component {
    static props = {
        userIsAdmin: Boolean,
        announcement: String,
    };
    static template = "main_menu.WidgetHour";

    setup() {
        this.user = useService("user");
        this.getDateTime();
        this.updateHour = setInterval(() => {
            this.getDateTime();
            this.render();
        }, 1000);
    }

    getDateTime(){
        const lang = this.user.context.lang.replace("_", "-");
        this.currentTime = new Date().toLocaleTimeString();
        try {
            this.currentDate = new Date().toLocaleDateString(lang, {
                weekday: "long",
                year: "numeric",
                month: "long",
                day: "numeric"
            });
        }
        catch (e) {
            this.currentDate = new Date().toLocaleDateString();
        }
    }

    destroy(){
        clearInterval(this.updateHour);
    }
}
