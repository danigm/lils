Let's learn how to install and remove software in <b>openSUSE</b> Tumbleweed!


-> start

=== start ===
What do you want to learn?
-> learn

=== learn ===
 * [Install new software] -> zypper.install
 * [Remove software] -> zypper.remove
 * [Advanced usage] -> advanced
 * [Exit] -> exit

=== zypper ===
  = install
    The first thing that we'll need is a terminal. Look for you favourite
    terminal application and launch it.
    * [Ok, I go it]
      -> install2

  = install2
    Now you can try to install new software. To install new software in
    <b>openSUSE</b> we use the <b>zypper</b>, you can read more about it in
    the wiki page: https://en.opensuse.org/SDB:Zypper_manual, but today we'll
    do something simple, just install a new package.


    Write the following command in the terminal <b>sudo zypper in nyancat</b>.
    Let's see the command word by word:
      <b>sudo</b>, launch the command with root permissions, it's required to
      be able to install software in your operating system.
      <b>zypper</b>, the system management library tool, this is the one that
      does the real work.
      <b>in</b>, the command to ask zypper to install a package. It's an
      abbreviation of install, you can try to replace with that.
      <b>nyancat</b>, the name of the package to install.

    * [continue] -> install_done # wait-newfile: /usr/bin/nyancat

  = install_done
    Great! You've installed the <b>nyancat</b> package.
    * [Let's try it] -> try

  = try
    Type <b>nyancat</b> in the terminal.
    * [continue] -> congrats # wait-ps: nyancat

  = remove
    -> todo

=== advanced ===
There are other interesting topics related to <b>zypper</b> and how to handle
packages.


Let's explore other topics:
 * [Search] -> todo
 * [Update] -> todo
 * [Back] -> learn

=== exit ===
Have fun.
-> END

=== congrats ===
Great work!
What do you want to do now?
 * [Learn something else] -> start
 * [Finish]
   Ok, <>
   -> exit

=== todo ===
This section is not completed yet.


What do you want to learn?
-> learn
