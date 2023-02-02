/* extension.js
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later
 */

const St = imports.gi.St;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;

const Main = imports.ui.main;
const PanelMenu = imports.ui.panelMenu;
const PopupMenu = imports.ui.popupMenu;

const ExtensionUtils = imports.misc.extensionUtils;
const Me = ExtensionUtils.getCurrentExtension();

const Service = Me.imports.service;
const RunDialog = Me.imports.rundialog;
const Message = Me.imports.message;


class Extension {
    constructor() {
        this._indicator = null;
        this._menu = null;
        this._lils = null;
        this._messages = [];
        this._currentMessage = null;
    }

    launchGame() {
        const runDialog = new RunDialog.RunDialog();
        runDialog.open((path) => {
            this._messages = this._lils.launch(path);
            this.showMessages();
        });
    }

    destroyMessage() {
        this._currentMessage.destroy();
        this._currentMessage = null;
    }

    showMessages() {
        let message = this._messages.shift();
        if (typeof message === 'undefined')
            return;

        const options = this._lils.options();
        const hasNext = this._messages.length > 0;

        this._currentMessage = new Message.Message(message, options, hasNext);
        this._currentMessage.connect('next', () => {
            this.destroyMessage();
            this.showMessages();
        });
        this._currentMessage.connect('option-selected', (button, option) => {
            this.destroyMessage();
            this.chooseOption(option);
        });
        this._currentMessage.present();
    }

    chooseOption(option) {
        this._messages = this._lils.choose(option);
        this.showMessages();
    }

    createMenu() {
        this._menu = this._indicator.menu;
        this._menu.removeAll();

        const section = new PopupMenu.PopupMenuSection();
        section.addMenuItem(new PopupMenu.PopupMenuItem("Linux Immersive Learning System", {reactive: false}));
        section.addAction("Launch Game", () => {
            this.launchGame();
        });
        this._menu.addMenuItem(section);

    }

    enable() {
        let indicatorName = `${Me.metadata.name} Indicator`;

        // Create a panel button
        this._indicator = new PanelMenu.Button(0.0, indicatorName, false);
        this.createMenu();

        // Add an icon
        let icon = new St.Icon({
            gicon: new Gio.ThemedIcon({name: 'dialog-information-symbolic', }),
            style_class: 'system-status-icon'
        });
        this._indicator.add_child(icon);
        Main.panel.addToStatusArea(indicatorName, this._indicator);

        this._lils = new Service.LilsDbus();

        // TODO: remove this line
        // this.debug();
    }

    disable() {
        this._indicator.destroy();
        this._indicator = null;
        this._menu = null;
        this._lils = null;
        this.destroyMessage();
    }


    debug() {
        this._timeoutId = GLib.timeout_add(GLib.PRIORITY_LOW, 1000, () => {
            this._messages = this._lils.launch('/tmp/basic.ink');
            this.showMessages();
            return GLib.SOURCE_REMOVE;
        });
    }
}


function init() {
    return new Extension();
}
