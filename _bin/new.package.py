#!/usr/bin/env python3

import re
import os
import shutil
import subprocess
import git # python-gitpython in AUR
import menu3 # python-menu3 in AUR
from tempfile import gettempdir

import pprint

## SETTINGS ##
gpgkey = '748231EBCBD808A14F5E85D28C004C2F93481F6B'  # https://wiki.archlinux.org/index.php/PKGBUILD#validpgpkeys
maintname = 'brent s. <bts[at]square-r00t[dot]net>'  # your name and email address, feel free to obfuscate though
pkgbuild_dir = '/opt/dev/arch'  # what dir do the pkgbuilds/AUR checkouts live?
aur_pkgs_dir = pkgbuild_dir  # should be the dir where the aur_pkgs repo checkout lives. it's recommended you keep this the same as pkgbuild_dir

## BUILD THE GUI ##
def gui_init():
    m = menu3.Menu(True)
    pkgname = False

    base_options = ["Add a new package to the AUR...",
                    "Sign a package's sources",
                    "Update/initialize submodules from your AUR account"]
    base_menu = m.menu("How might I assist you today?", base_options, "Select an operation ('q' to quit):")
    pkg = {}
    if base_menu == 1:
        add_options = ["Release/versioned",
                        "VCS (Git, SVN, Mercurial, etc.)"]
        add_menu = m.menu("What type of package is this?", add_options, "Package type ('q' to quit):")
    elif base_menu == 2:
        pkg['oper'] = 'sign'
    elif base_menu == 3:
        pkg['oper'] = 'submodule'

    # If they selected to add a package and it's a VCS package...
    if add_menu == 2:
        vcs_options = ["Git",
                    "Subversion (svn)",
                    "Mercurial (hg)",
                    "Bazaar (bzr)"]
        vcs_menu = m.menu("What type of VCS system?", vcs_options, "VCS type ('q' to quit):")
        pkg['name'] = input("\nWhat is the name of your package? (Exclude the '-git' etc. suffix)\n").lower()
        srcurl = input("\nWhat is the checkout URL for {0}?\n(Do not include the directory or VCS type prefix as per\nhttps://wiki.archlinux.org/index.php/VCS_package_guidelines#VCS_sources ...\nit will be added automatically)\n".format(pkg['name']))
        pkg['vcstype'] = ["git",
                "svn",
                "hg",
                "bzr"]
        pkg['srcurl'] = pkg['name'] + "::" + pkg['vcstype'][vcs_menu-1] + srcurl
        pkg['srcfile'] = False
        pkg['ver'] = False

    # If they're adding a release package...
    elif add_menu == 1:
        pkg['vcstype'] = False
        pkg['name'] = input("\nWhat is the name of your package?\n").lower()
        pkg['ver'] = input("\nWhat is the version of the release you are packaging for {0}?\n".format(pkg['name']))
        pkg['srcurl'] = input("\nWhat is the full URL for the tarball/zip file/etc. for {0} (version {1})?\n".format(pkg['name'], pkg['ver']))
        pkg['srcfile'] = re.sub('^\s*(https?|ftp).*/(.*)\s*$', '\\2', pkg['srcurl'], re.IGNORECASE)

    # And this is stuff shared by both types.
    pkg['desc'] = input("\nWhat is a short description of {0}?\n".format(pkg['name']))
    pkg['site'] = input("\nWhat is {0}'s website?\n".format(pkg['name']))
    pkg['license'] = []
    license_raw = input("\nWhat is {0}'s license(s)? (See https://wiki.archlinux.org/index.php/PKGBUILD#license)\nIf you have more than one, separate them by spaces.\n".format(pkg['name']).upper())
    pkg['license'] = list(map(str, license_raw.split()))
    pkg['deps'] = []
    deps_raw = input("\nWhat does {0} depend on for runtime? if no packages, just hit enter.\nMake sure they correspond to Arch/AUR package names.\nIf you have more than one, separate them by spaces.\n".format(pkg['name']))
    pkg['deps'] = list(map(str, deps_raw.split()))
    pkg['optdeps'] = []
    optdeps_raw = input("\nWhat does {0} optionally depend on (runtime)? if no packages, just hit enter.\nMake sure they correspond to Arch/AUR package names.\nIf you have more than one, separate them by COMMAS.\nThey should follow this format:\npkgname: some reason why it should be installed\n".format(pkg['name']))
    pkg['optdeps'] = list(map(str, optdeps_raw.split(',')))
    pkg['makedeps'] = []
    makedeps_raw = input("\nWhat dependencies are required for building/making {0}? If no packages, just hit enter.\nMake sure they correspond to Arch/AUR package names.\nIf you have more than one, separate them by spaces.\n".format(pkg['name']))
    pkg['makedeps'] = list(map(str, makedeps_raw.split()))
    pkg['provides'] = []
    provides_raw = input("\nWhat package names, if any besides itself, does {0} provide?\n(If {0} is a VCS package, do NOT include the non-VCS package name- that's added by default!)\nIf you have more than one, separate them by spaces.\n".format(pkg['name']))
    pkg['provides'] = list(map(str, provides_raw.split()))
    pkg['conflicts'] = []
    conflicts_raw = input("\nWhat package names, if any, does {0} conflict with?\n(If {0} is a VCS package, do NOT include the non-VCS package name- that's added by default!)\nIf you have more than one, separate them by spaces.\n".format(pkg['name']))
    pkg['conflicts'] = list(map(str, conflicts_raw.split()))
    return(pkg)

## MAKE SURE SOME PREREQS HAPPEN ##
def sanity_checks(pkg):
    try:
        os.makedirs(pkgbuild_dir)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def aur_create(pkg):
    tmpcheckout = os.path.join(gettempdir(), '.aur_pkgs.{}'.format(pkg['name']))
    pygit2.clone_repository('aur@aur.archlinux.org:' + pkg['name'], tmpcheckout, bare=False, repository=None, remote=None, checkout_branch=None, callbacks=None)
    shutil.copy2(aur_pkgs_dir + "/_docs/PKGBUILD.templates.d/gitignore", tmpcheckout + "/.gitignore")


pprint.pprint(gui_init())


