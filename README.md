## Project Description

Immersive system to run interactive tutorials, hacking learning lessons or just
games that integrates with your system. The main idea is to have an
[INK](https://www.inklestudios.com/ink/) language engine to process the
**tutorial** scripts and provide an interactive user interface to the user. The
system should be able to listen to different Linux events (like filesystem
changes, process is running, the current date, etc) and modify the **tutorial**
state depending on that.

Example:
 * We've a tutorial to learn about how to use the linux terminal, a bash
   introduction
 * The tutorial gives to the user a brief explanation about how to create a
   directory and waits for the directory to be created
 * Once the system detects that directory, it automatically go forwards, says
   congrats to the user and continues with the next step

The main idea is to build the base system with Python and provide a generic
interface (dbus, socket, cli) to be able to extend and use from different
languages.

This idea is based on the [Hack Computer](https://www.hack-computer.com/)
concept, but trying to make it simpler and not tied to the desktop. It's a
simple concept to have a way to create a more fun learning experience using a
[Choose Your Own Adventure](https://en.wikipedia.org/wiki/Choose_Your_Own_Adventure)
like tutorial flow, with different user input that can happen in a different
process.


## Goal for this Hackweek

This is the full list of goals that will be great to have, in order of
importance:

 1. Build a basic python Ink language interpreter
 1. Create the base system that runs the tutorial, keep the state and provide
    an API to be used
 1. Make the base system extensible with **listeners** that can wait for
    different kind of events:
    * user option selection
    * user text input
    * new file
    * date change
    * launch program, close program
    * system reboot?
    * ...
 1. Create initial tutorial about how to write **lils** tutorials / games
 1. Create different graphical user interfaces (GNOME shell plugin, desktop
    application, web interface...)

## Resources

 * [Hack Computer](https://www.hack-computer.com/)
 * [Hack Web interface](https://try.hack-computer.com/)
 * [INK](https://www.inklestudios.com/ink/)
