/** @odoo-module **/

import { Component, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { WidgetHour } from "@main_menu/components/widget_hour/widget_hour";
import { WidgetAnnouncement } from "@main_menu/components/widget_announcement/widget_announcement";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

class MenuAction extends Component {
    static components = { WidgetHour, WidgetAnnouncement };
    static props = {...standardActionServiceProps};
    static template = "main_menu.MainMenu";

    setup() {
        this.orm = useService("orm");
        this.user = useService("user");
        this.menuService = useService("menu");
        const companyService = useService("company");
        this.currentCompanyId = companyService.currentCompany.id
        this.apps = this.menuService.getApps()
                        .filter(app => app.xmlid != "main_menu.main_menu_root")
                        .sort((a, b) => a.name.localeCompare(b.name));
        this.deg = `${90 + 180 * Math.atan(window.innerHeight / window.innerWidth) / Math.PI}deg`;

        onWillStart(async () => {
            try {
                this.userIsAdmin = await this.user.hasGroup("base.group_system");
                const res = await this.orm.searchRead(
                    "res.company",
                    [["id", "=", this.currentCompanyId]],
                    ["announcement", "show_widgets"]
                );
                this.announcement = res[0].announcement;
                this.showWidgets = res[0].show_widgets;
            } catch (error) {
                console.error("Error loading data:", error);
            }
        });
    }

    onClickModule(menu){
        menu && this.menuService.selectMenu(menu);
    }

    onChangeAnnouncement(value){
        this.announcement = value;
    }

    async onSaveAnnouncement(){
        try {
            await this.orm.write("res.company", [this.currentCompanyId], {
                "announcement": this.announcement
            });
        } catch (error) {
            console.error("Error saving data:", error);
        }
    }
}

registry
    .category("actions")
    .add("main_menu.action_open_main_menu", MenuAction);
