import sys

try:
    import gi
except ModuleNotFoundError:
    print("Can't import gi, please, install the dbus extra", file=sys.stderr)
    print("pip install pylils[dbus]", file=sys.stderr)
    sys.exit(1)


gi.require_version("GLib", "2.0") # noqa
from gi.repository import Gio # noqa
from gi.repository import GLib # noqa

from .ink import InkScript
from .ink import Text, Option


APPID = "net.danigm.lils"


class LilsService(Gio.Application):
    _DBUS_NAME = APPID
    _DBUS_IFACE = APPID
    _DBUS_PATH = "/" + APPID.replace(".", "/")
    _DBUS_XML = f"""
    <node>
      <interface name='{APPID}'>
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
    </node>
    """

    # Five minutes without changes
    _INACTIVITY_TIMEOUT = 5 * 60 * 1000

    def __init__(self):
        super().__init__(application_id=self._DBUS_NAME,
                         inactivity_timeout=self._INACTIVITY_TIMEOUT)
        self._dbus_id = None
        self._state = None

    def _on_method_called(self, connection, sender, path, iface,
                          method, params, invocation):
        # Call hold here, and release at the end of the method so we restart
        # the inactivity timeout for each method call.
        self.hold()

        ret = getattr(self, method)(params)
        if ret is not None:
            ret = self.convert_variant_arg(ret)
            invocation.return_value(ret)

        # Ensure release() is always called.
        self.release()

    def reset(self, params):
        self.emit("reset")
        self.emit("changed")

    def launch(self, params):
        filename = params[0]
        self._script = InkScript(filename, on_change=self._on_change)
        self._script.run()
        return self._script.output

    def choose(self, params):
        option = params[0]
        self._script.choose(option)
        return self._script.output

    def output(self, params):
        return self._script.output

    def options(self, params):
        return self._script.options

    def finished(self, params):
        return self._script.finished

    def var(self, params):
        key = params[0]
        value = self._script.var(key)
        if value is None:
            value = ""
        return GLib.Variant('(v)', (self.convert_variant_arg(value), ))

    def _on_change(self, *args):
        self.emit("changed")

    def emit(self, signal):
        self.get_dbus_connection().emit_signal(None, self._DBUS_PATH,
                                               self._DBUS_IFACE,
                                               signal, None)

    def do_dbus_register(self, connection, path):
        info = Gio.DBusNodeInfo.new_for_xml(self._DBUS_XML)
        self._dbus_id = connection.register_object(path,
                                                   info.interfaces[0],
                                                   self._on_method_called)
        return Gio.Application.do_dbus_register(self, connection, path)

    def do_dbus_unregister(self, connection, path):
        Gio.Application.do_dbus_unregister(self, connection, path)
        if not self._dbus_id:
            return
        connection.unregister_object(self._dbus_id)
        self._dbus_id = None

    def do_startup(self):
        self._script = None

        # Call hold/release here, so the inactivity-timeout is used correctly
        # (as the overridden value is only used after a release call).
        self.hold()
        self.release()

        Gio.Application.do_startup(self)

    def do_activate(self):
        self._script = None

        self.hold()
        self.release()

        Gio.Application.do_activate(self)

    def do_shutdown(self):
        Gio.Application.do_shutdown(self)

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()

        if options.contains('reload'):
            self._reload()

        return 0

    def convert_variant_arg(self, variant):
        """Convert Python object to GLib.Variant"""

        match variant:
            case GLib.Variant():
                return variant
            case bool():
                return GLib.Variant('(b)', (variant, ))
            case int():
                return GLib.Variant('(i)', (variant, ))
            case float():
                return GLib.Variant('(d)', (variant, ))
            case str():
                return GLib.Variant('(s)', (variant, ))
            case [str(), *rest]:
                return GLib.Variant('(as)', (variant, ))
            case [Text(), *rest]:
                return GLib.Variant('(as)', ([str(i) for i in variant], ))
            case [Option(), *rest]:
                return GLib.Variant('(as)', ([i.option for i in variant], ))
            case []:
                return GLib.Variant('(as)', ([], ))


def main():
    service = LilsService()
    service.run(sys.argv)


if __name__ == "__main__":
    main()
