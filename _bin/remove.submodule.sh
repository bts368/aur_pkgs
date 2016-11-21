#!/bin/bash

# TODO- incorporate into python script

if [[ -z "${1}" ]];
then
	echo "USAGE: ${0} <SUBMODULENAME.TO.REMOVE>"
	exit 1
fi

PKG=${1}
PROJPATH='/opt/dev/arch'

cd ${PROJPATH}

# .gitmodules string to match:
#[submodule "bdisk-git"]
#	url = aur@aur.archlinux.org:bdisk-git
#	path = bdisk-git
sed -i -e "/^[[:space:]]*\[submodule \"${PKG}\"\]$/d" -e "/^[[:space:]]*path[[:space:]]*=[[:space:]]*${PKG}$/d" .gitmodules
git add .gitmodules

# .git/config string to match:
#[submodule "bdisk-git"]
#	url = aur@aur.archlinux.org:bdisk-git
sed -i -e "/^[[:space:]]*\[submodule \"${PKG}\"\]$/d" -e "/^[[:space:]]*url[[:space:]]*=[[:space:]]*aur@aur\.archlinux\.org:${PKG}$/d" .git/config

git rm --cached ${PKG}

rm -rf .git/modules/${PKG}

git commit -m "removed ${PKG} submodule"
rm -rf ${PKG}
