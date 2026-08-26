/** @odoo-module **/

import { Component, useState, onWillUnmount } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class WorkItemSystrayItem extends Component {
    static components = { Dropdown, DropdownItem };
    static props = [];
    static template = "work_item_systray.WorkItemSystrayItem";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.busService = this.env.services.bus_service;
        this.busService.subscribe("work_item_systray.session_updated", (data) => this._applyData(data));
        this.state = useState({
            status: "break",
            workItemModel: false,
            workItemId: false,
            name: "",
            icon: "",
            cssClass: "",
            description: "",
            startDatetime: false,
            elapsed: "00:00:00",
            timeColorClass: "o_work_item_time-neutral",
            pomodoroDeadline: false,
            isPomodoroBlinking: false,
            workItems: [],
            extra: {},
        });
        this._loadState();
        this._timer = setInterval(() => this._tick(), 1000);
        onWillUnmount(() => clearInterval(this._timer));
    }

    async _loadState() {
        const data = await this.orm.call("work.item.session", "get_systray_state", []);
        this._applyData(data);
    }

    _applyData(data) {
        this.state.status = data.state;
        this.state.workItemModel = data.work_item_model;
        this.state.workItemId = data.work_item_id;
        this.state.name = data.name || _t("Sin actividad");
        this.state.icon = data.icon || "";
        this.state.cssClass = data.css_class || "";
        this.state.description = data.description || "";
        this.state.startDatetime = data.start_datetime;
        this.state.pomodoroDeadline = data.pomodoro_deadline || false;
        this.state.workItems = data.work_items || [];
        // Datos extra específicos de cada proveedor (p. ej. allocated_hours):
        // el core los guarda tal cual para que solo los lea quien los patchea.
        this.state.extra = data;
    }

    /**
     * Por defecto el cronómetro siempre cuenta hacia adelante. Los
     * proveedores que necesiten cuenta regresiva (p. ej. contra un
     * presupuesto de horas) pisan este método con patch() desde su propio
     * addon, leyendo this.state.extra.
     */
    _tick() {
        if (this.state.status !== "active" || !this.state.startDatetime) {
            this.state.elapsed = "00:00:00";
            this.state.timeColorClass = "o_work_item_time-neutral";
            this.state.isPomodoroBlinking = false;
            return;
        }
        const start = new Date(this.state.startDatetime.replace(" ", "T") + "Z");
        const liveSeconds = Math.max(0, Math.floor((Date.now() - start.getTime()) / 1000));
        this.state.elapsed = this._formatDuration(liveSeconds);
        this.state.timeColorClass = "o_work_item_time-neutral";
        this.state.isPomodoroBlinking = this._computePomodoroBlinking();
    }

    /**
     * true desde que se vence el período activo de 25' hasta que se
     * confirma "seguir" o el cron server-side cierra la sesión (backstop
     * si se cierra la pestaña o la laptop suspende) — ver
     * work.item.session._cron_close_expired_pomodoros.
     */
    _computePomodoroBlinking() {
        if (!this.state.pomodoroDeadline) {
            return false;
        }
        const deadline = new Date(this.state.pomodoroDeadline.replace(" ", "T") + "Z");
        return Date.now() >= deadline.getTime();
    }

    async onConfirmPomodoro() {
        const data = await this.orm.call("work.item.session", "action_confirm_pomodoro", []);
        this._applyData(data);
    }

    _formatDuration(seconds) {
        const sign = seconds < 0 ? "+" : "";
        const abs = Math.abs(Math.round(seconds));
        const h = String(Math.floor(abs / 3600)).padStart(2, "0");
        const m = String(Math.floor((abs % 3600) / 60)).padStart(2, "0");
        const s = String(abs % 60).padStart(2, "0");
        return `${sign}${h}:${m}:${s}`;
    }

    get todayItems() {
        return this.state.workItems.filter((item) => item.is_today);
    }

    get otherItems() {
        return this.state.workItems.filter((item) => !item.is_today);
    }

    onSelectWorkItem(model, resId) {
        // El wizard postea la nota de cierre/inicio y llama a switch_work_item
        // en el backend; este último ya notifica por bus, así que no hace
        // falta refrescar el estado acá.
        this._openSwitchWizard({ default_mode: "switch", default_target_ref: `${model},${resId}` });
    }

    onOpenWizardBlank() {
        this._openSwitchWizard({ default_mode: "switch" });
    }

    onTakeBreak() {
        this._openSwitchWizard({ default_mode: "break" });
    }

    _openSwitchWizard(context) {
        this.action.doAction(
            "work_item_systray.action_work_item_session_switch_wizard",
            { additionalContext: context }
        );
    }

    onOpenWorkItem() {
        this.openWorkItemRecord(this.state.workItemModel, this.state.workItemId);
    }

    openWorkItemRecord(model, resId) {
        if (!model || !resId) {
            return;
        }
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: model,
            res_id: resId,
            views: [[false, "form"]],
            target: "new",
        });
    }
}

export const workItemSystrayItem = {
    Component: WorkItemSystrayItem,
};

registry
    .category("systray")
    .add("work_item_systray.WorkItemSystrayItem", workItemSystrayItem, { sequence: 20 });
