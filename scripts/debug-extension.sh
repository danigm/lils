#!/bin/bash
#
MUTTER_DEBUG_DUMMY_MODE_SPECS=1920x1080 dbus-run-session -- gnome-shell --nested --wayland

# Alt F2
# xwininfo -root -tree | grep gnome-shell
# xdotool keydown Alt key F2 keyup Alt 0x1a00005
