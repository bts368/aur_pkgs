#!/usr/bin/env python3

## SETTINGS ##
gpgkey = '748231EBCBD808A14F5E85D28C004C2F93481F6B'  # https://wiki.archlinux.org/index.php/PKGBUILD#validpgpkeys
maintname = 'brent s. <bts[at]square-r00t[dot]net>'  # your name and email address, feel free to obfuscate though
pkgbuild_dir = '/opt/dev/arch'  # what dir do the pkgbuilds/AUR checkouts live?
aur_pkgs_dir = pkgbuild_dir  # should be the dir where the aur_pkgs repo checkout lives. it's recommended you keep this the same as pkgbuild_dir

def get_pkgname():
    
