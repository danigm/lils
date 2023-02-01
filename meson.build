# keep version in sync with pyproject.toml
project('lils-dbus', version: '0.1.0')
id = 'net.danigm.lils'

dbus_dep = dependency ('dbus-1')
session_bus_services_dir = dbus_dep.get_pkgconfig_variable('session_bus_services_dir')

conf = configuration_data()
conf.set('bindir', join_paths(get_option('prefix'), get_option('bindir')))

configure_file(
    input: id + '.service.in',
    output: id + '.service',
    install: true,
    install_dir: session_bus_services_dir,
    configuration: conf
)
