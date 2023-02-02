/* exported LilsDbus */

const { Gio, Shell } = imports.gi;


const DEFAULT_ID = 'net.danigm.lils';
const DEFAULT_PATH = '/net/danigm/lils';
const DEFAULT_IFACE = `
        <node>
          <interface name='net.danigm.lils'>
            <method name='launch'>
              <arg type='s' name='filename' direction='in'/>
              <arg type='as' name='output' direction='out'/>
            </method>
            <method name='choose'>
              <arg type='u' name='option' direction='in'/>
              <arg type='as' name='output' direction='out'/>
            </method>
            <method name='output'>
              <arg type='as' name='output' direction='out'/>
            </method>
            <method name='options'>
              <arg type='as' name='output' direction='out'/>
            </method>
            <method name='var'>
              <arg type='s' name='name' direction='in'/>
              <arg type='v' name='value' direction='out'/>
            </method>
            <method name='finished'>
              <arg type='b' name='output' direction='out'/>
            </method>

            <method name='reset'></method>
            <signal name='changed'></signal>
            <signal name='reset'></signal>
          </interface>
        </node>`

var LilsDbus = class LilsDbus {
    constructor(onChange) {
        this._id = DEFAULT_ID;
        this._path = DEFAULT_PATH;
        this._iface = DEFAULT_IFACE;

        const Proxy = Gio.DBusProxy.makeProxyWrapper(this._iface);
        this._proxy = new Proxy(Gio.DBus.session, this._id, this._path);
        this._proxy.connectSignal('changed', () => {
            onChange();
        });
    }

    grouped(messages) {
        // Group by paragraph
        let grouped = [];
        let group = "";
        messages.forEach(str => {
            if (!str || /^\s*$/.test(str)) {
                grouped.push(group);
                group = "";
            } else {
                group = `${group}${str}\n`;
            }
        });
        // The last one
        grouped.push(group);

        return grouped;
    }

    launch(path) {
        return this.grouped(this._proxy.launchSync(path)[0]);
    }

    choose(index) {
        return this.grouped(this._proxy.chooseSync(index)[0]);
    }

    output() {
        return this.grouped(this._proxy.outputSync()[0]);
    }

    options() {
        return this._proxy.optionsSync()[0];
    }

    getvar(name) {
        return this._proxy.varSync(name)[0];
    }

    finished() {
        return this._proxy.finishedSync()[0];
    }

    reset() {
        return this._proxy.resetSync()[0];
    }
};
