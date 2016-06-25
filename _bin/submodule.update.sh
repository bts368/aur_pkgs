#!/bin/bash

PKGBUILD_DIR='/opt/dev/arch'


cd "${PKGBUILD_DIR}"
if [ ! -d "${PKGBUILD_DIR}" ];
then
	mkdir -p $(dirname "${PKGBUILD_DIR}")
	git init "${PKGBUILD_DIR}"
elif [ ! -d "${PKGBUILD_DIR}/.git" ];
then
	echo "ERROR: ${PKGBUILD_DIR} does not seem to be a git directory."
	exit
fi

if [ -n "${1}" ];
then
	PKGNAME="${1}"
	echo "This script will delete ${PKGNAME} and pull a fresh copy of it from the AUR, adding it as a submodule to this directory."
	echo "Hit enter to continue, or ctrl-c to exit."
	read DELCHK
else
	PKGNAME='ALL'
	echo "This script will delete ANY/ALL existing working tree directories that match the name of an existing repository you have access to in the AUR!"
	echo "Hit enter to continue, or ctrl-c to exit."
	read DELCHK
fi

URI='aur@aur.archlinux.org'

function freshenrepo () {

	REPO="${1}"

	# Check to see if it exists. https://stackoverflow.com/questions/12641469/list-submodules-in-a-git-repository
	# We COULD use 'if git submodule status "${REPO}"' but we don't because regexes are cooler. so there. deal with it. /me puts on cool guy sunglasses.
	git config --file .gitmodules --get-regexp path | awk '{ print $2 }' | egrep -Eq "^${REPO}$"
	if [[ "${?}" -eq '0' ]];
	then
		# We remove it so we can grab a fresh copy directly from the AUR.
		#https://stackoverflow.com/questions/1260748/how-do-i-remove-a-submodule and others
		git submodule deinit -f "${REPO}"
		git rm -f "${REPO}"
		git config -f .gitmodules --remove-section "submodule.${REPO}" > /dev/null 2>&1  # probably not necessary,...
		rm -rf .git/modules/${REPO}
	fi
	touch .gitmodules
	git add .gitmodules
	git submodule add ${URI}:${REPO}
	cat >> .git/modules/${REPO}/hooks/pre-commit << EOF
#!/bin/bash
/usr/bin/mksrcinfo

git add .SRCINFO
EOF
	chmod 700 .git/modules/${REPO}/hooks/pre-commit

}

if [[ "${PKGNAME}" =~ [Aa][Ll]{2} ]];
then
	for i in $(ssh aur@aur.archlinux.org list-repos | sed -e 's/[[:space:]]*//g' | sort);
	do
		freshenrepo ${i}
	done
elif [ -n "${PKGNAME}" ];
then
	freshenrepo ${PKGNAME}
fi

git submodule update
