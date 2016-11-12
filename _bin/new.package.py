#!/usr/bin/env python3

import curses
import os
import subprocess
import pygit2

## SETTINGS ##
gpgkey = '748231EBCBD808A14F5E85D28C004C2F93481F6B'  # https://wiki.archlinux.org/index.php/PKGBUILD#validpgpkeys
maintname = 'brent s. <bts[at]square-r00t[dot]net>'  # your name and email address, feel free to obfuscate though
pkgbuild_dir = '/opt/dev/arch'  # what dir do the pkgbuilds/AUR checkouts live?
aur_pkgs_dir = pkgbuild_dir  # should be the dir where the aur_pkgs repo checkout lives. it's recommended you keep this the same as pkgbuild_dir

## BUILD THE GUI ##
def gui_init():
    # props to https://gist.github.com/abishur/2482046
    screen = curses.initscr()
    curses.noecho()
    curses.cbreak()
    curses.start_color()
    screen.keypad(True)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # might change this. black text, white BG
    h = curses.color_pair(1)
    n = curses.A_NORMAL
    MENU = "menu"
    COMMAND = "command"
    EXITMENU = "exitmenu"

    menu_data = {'title': "AUR_Pkgs Packaging Menu", 'type': MENU, 'subtitle': "How might I assist you today?",
    'options':[
        { 'title': "Add a new package to the AUR...", 'type': MENU, 'subtitle': 'Use this submenu to add new packages.',
        'options': [
            { '
        },
        { 'title': "Sign a package's sources", 'type': COMMAND, 'command': 'sign_pkg' },
        { 'title': "Update/initialize submodules from the AUR", 'type': COMMAND, 'command': 'fetch_aur' }
        ]
    }

gui_init()



# Get the package type
def get_pkgtype():
    pkgtype = True
    while pkgtype:
        print("""
            What type of package is this?
            1 Release/Versioned
            2 VCS (Git, SVN, Mercurial, etc.)
            3 Quit
            """)
        pkgtype = input()
        #if pkgtype == 

# Get the package name
def get_pkgname():
    pkgname = input('What is the name of this package?')
