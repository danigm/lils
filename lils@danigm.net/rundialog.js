/* exported RunDialog */

const GObject = imports.gi.GObject;
const ModalDialog = imports.ui.modalDialog;
const Dialog = imports.ui.dialog;
const Clutter = imports.gi.Clutter;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const St = imports.gi.St;


var RunDialog = GObject.registerClass(
class RunDialog extends ModalDialog.ModalDialog {
    _init() {
        super._init({
            styleClass: 'run-dialog',
            destroyOnClose: true,
        });

        let title = 'Run a LILS script';

        let content = new Dialog.MessageDialogContent({ title });
        this.contentLayout.add_actor(content);

        let entry = new St.Entry({
            style_class: 'run-dialog-entry',
            can_focus: true,
        });

        this._entryText = entry.clutter_text;
        content.add_child(entry);
        this.setInitialKeyFocus(this._entryText);

        let defaultDescriptionText = 'Press ESC to close';

        this._descriptionLabel = new St.Label({
            style_class: 'run-dialog-description',
            text: defaultDescriptionText,
        });
        content.add_child(this._descriptionLabel);
        this._commandError = false;
        this._pathCompleter = new Gio.FilenameCompleter();

        this._entryText.connect('activate', o => {
            this.popModal();
            this._run(o.get_text());
            if (!this._commandError || !this.pushModal())
                this.close();
        });
        this._entryText.connect('key-press-event', (o, e) => {
            let symbol = e.get_key_symbol();
            if (symbol === Clutter.KEY_Tab) {
                let text = o.get_text();
                let prefix;
                if (text.lastIndexOf(' ') == -1)
                    prefix = text;
                else
                    prefix = text.substr(text.lastIndexOf(' ') + 1);
                let postfix = this._getCompletion(prefix);
                if (postfix != null && postfix.length > 0) {
                    o.insert_text(postfix, -1);
                    o.set_cursor_position(text.length + postfix.length);
                }
                return Clutter.EVENT_STOP;
            }
            return Clutter.EVENT_PROPAGATE;
        });
        this._entryText.connect('text-changed', () => {
            this._descriptionLabel.set_text(defaultDescriptionText);
        });
    }

    vfunc_key_release_event(event) {
        if (event.keyval === Clutter.KEY_Escape) {
            this.close();
            return Clutter.EVENT_STOP;
        }

        return Clutter.EVENT_PROPAGATE;
    }

    _getCommandCompletion(text) {
        function _getCommon(s1, s2) {
            if (s1 == null)
                return s2;

            let k = 0;
            for (; k < s1.length && k < s2.length; k++) {
                if (s1[k] != s2[k])
                    break;
            }
            if (k == 0)
                return '';
            return s1.substr(0, k);
        }

        let paths = GLib.getenv('PATH').split(':');
        paths.push(GLib.get_home_dir());
        let someResults = paths.map(path => {
            let results = [];
            try {
                let file = Gio.File.new_for_path(path);
                let fileEnum = file.enumerate_children('standard::name', Gio.FileQueryInfoFlags.NONE, null);
                let info;
                while ((info = fileEnum.next_file(null))) {
                    let name = info.get_name();
                    if (name.slice(0, text.length) == text)
                        results.push(name);
                }
            } catch (e) {
                if (!e.matches(Gio.IOErrorEnum, Gio.IOErrorEnum.NOT_FOUND) &&
                    !e.matches(Gio.IOErrorEnum, Gio.IOErrorEnum.NOT_DIRECTORY))
                    log(e);
            }
            return results;
        });
        let results = someResults.reduce((a, b) => a.concat(b), []);

        if (!results.length)
            return null;

        let common = results.reduce(_getCommon, null);
        return common.substr(text.length);
    }

    _getCompletion(text) {
        if (text.includes('/'))
            return this._pathCompleter.get_completion_suffix(text);
        else
            return this._getCommandCompletion(text);
    }

    _run(input) {
        this._commandError = false;
        try {
            this.callback(input);
        } catch(e) {
            log(e);
        }
    }

    _showError(message) {
        this._commandError = true;
        this._descriptionLabel.set_text(message);
    }

    open(callback) {
        this._entryText.set_text('');
        this._commandError = false;
        this.callback = callback;

        return super.open();
    }
});
