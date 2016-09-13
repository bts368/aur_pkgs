#!/bin/bash
set -e


## SETTINGS ##

# You can get a list of your private identities with gpg -K.
# You can get the exact string with:
# - gpg -K --fingerprint --with-colons [<your identity, e.g. joeshmoe@joe.com>] | egrep '^fpr:' | cut -f10 -d":"
GPGKEY='748231EBCBD808A14F5E85D28C004C2F93481F6B'  # https://wiki.archlinux.org/index.php/PKGBUILD#validpgpkeys
MAINTNAME='brent s. <bts[at]square-r00t[dot]net>'
PKGBUILD_DIR='/opt/dev/arch'
AUR_PKGS_DIR="${PKGBUILD_DIR}"  # should be the dir where the aur_pkgs dir lives

# Get PKGTYPE
PS3='What type of package is this?: '
options=("Release/Versioned" "VCS (Git, SVN, Mercurial, etc.)" "Quit")
select opt in "${options[@]}"
do
    case ${opt} in
        "Release/Versioned")
            PKGTYPE="release"
	    break
            ;;
        "VCS (Git, SVN, Mercurial, etc.)")
            PKGTYPE="vcs"
	    break
            ;;
        "Quit")
            exit 0
	    break
            ;;
        *) echo invalid option;;
    esac
done

# get VCSTYPE, if it's a source package
if [[ "${PKGTYPE}" == 'vcs' ]];
then
	PS3='What type of version-control?: '
	options=("Git" "Subversion" "Mercurial" "Bazaar" "(Other)" "Quit")
	select opt in "${options[@]}"
	do
	    case ${opt} in
	        "Git")
	            VCSTYPE='git'
		    break
	            ;;
	        "Subversion")
	            VCSTYPE='svn'
                    break
	            ;;
		"Mercurial")
		    VCSTYPE='hg'
		    break
		    ;;
		"Bazaar")
		    VCSTYPE='bzr'
		    break
	            ;;
		"(Other)")
		    VCSTYPE='unknown'
		    break
	            ;;
	        "Quit")
	            exit 0
		    break
	            ;;
	        *) echo invalid option;;
	    esac
	done
fi

# get PKGNAME
echo -ne "\nWhat is the NAME of the package? (Exclude VCS type if it's a source-control package,\nthat will be prepended automatically): "
read PKGNAME
echo

# check PKGNAME
set +e  # disable bail-on-error because we want a non-zero if a package name is not right, etc.
echo "${PKGNAME}" | egrep -Eq '^([a-z0-9\_])+$'
if [[ "${?}" -ne '0' ]];
then
	echo "ERROR: That does not seem to be a valid package name!"
	exit
fi
set -e
_PKGNAME="${PKGNAME}"
if [[ -n "${VCSTYPE}" && "${VCSTYPE}" != '' ]];
then
	PKGNAME="${PKGNAME}-${VCSTYPE}"
fi

# Get the version to pre-populate the PKGBUILD with, if a release.
if [[ "${PKGTYPE}" == 'release' ]];
then
	echo -n "What is the VERSION of the current release you are packaging for ${PKGNAME}? "
	read PKGVER
	set +e
	echo "${PKGVER}" | egrep -Eq '^([0-9\.])+$'
	if [[ "${?}" -ne '0' ]];
	then
		echo "ERROR: That does not seem to be a valid package version!"
		echo "Acceptable values are numbers or .'s."
		exit
	fi
	set -e
	echo
fi

# Get other bits of info.
# PKGDESC
echo -ne "What is a DESCRIPTION of ${_PKGNAME}? (Do not include the package name- e.g.:\n  Provides a library for mutating teenage turtles\n): "
read PKGDESC
echo

# PKGURL
echo -n "What is the URL for ${_PKGNAME}'s website? "
read PKGURL
echo

# SRCURL
if [[ "${PKGTYPE}" == 'vcs' ]];
then
	echo -ne "What is the CHECKOUT URL for ${_PKGNAME}?\n(Do not include the directory or VCS type prefix as per https://wiki.archlinux.org/index.php/VCS_package_guidelines#VCS_sources - this is added automatically)  e.g.:\n  https://github.com/shinnok/johnny.git\nURL: "
	read SRCURL
	echo
	SRCURL="${_PKGNAME}::${VCSTYPE}+${SRCURL}"
	SRCFILE=''
else
	echo -n "What is the URL to the source tarball for ${PKGNAME} (version ${PKGVER})? "
	read SRCURL
	echo
	SRCFILE=$(echo "${SRCURL}" | sed -re 's|^https?.*/(.*)$|\1|g')
fi

# LICENSE
echo -n "What is the LICENSE for ${_PKGNAME}? "
read LICENSE
echo

# DEPENDS
echo -n "What does ${_PKGNAME} DEPEND on (for runtime)? if no packages, just hit enter. Make sure they correspond to Arch/AUR package names. "
read PKGDEPS
echo

# OPTDEPENDS
echo -ne "What is an OPTIONAL DEPENDENCY (runtime) for ${_PKGNAME}? If no packages, just hit enter. They should match the format:\n  pkgname:reason why\nOptional deps: "
read OPTDEPS
echo

echo -e "What is a MAKE DEPEND for ${_PKGNAME}? If no packages, just hit enter. "
read BUILDDEPS
echo

echo -e "What package names, if any besides itself, does ${_PKGNAME} PROVIDE? (If a VCS package, do not include the non-VCS package- that's added by default!) "
read PROVIDES
echo

echo -e "What package names, if any besides itself, does ${_PKGNAME} CONFLICT with? (If a VCS package, do not include the non-VCS package- that's added by default!) "
read CONFLICTS
echo

## SANITY ##
mkdir -p ${PKGBUILD_DIR}
cd ${PKGBUILD_DIR}

echo "Will create a package named ${PKGNAME}. Press enter to continue, or ctrl-C to quit."
read PKGCHK


## CREATE THE REPO/PACKAGE IN AUR ##
cd /tmp
git clone aur@aur.archlinux.org:${PKGNAME}
cd /tmp/${PKGNAME}
cp ${AUR_PKGS_DIR}/_docs/PKGBUILD.templates.d/gitignore .gitignore
git add .gitignore

## DROP IN A VANILLA PKGBUILD ##
if [[ "${PKGTYPE}" == 'vcs' ]];
then
	cat ${AUR_PKGS_DIR}/_docs/PKGBUILD.templates.d/vcs/{00.*,01.*,02.*,03.*,04.*.${VCSTYPE},05.*,06.*} > PKGBUILD
else
	cat ${AUR_PKGS_DIR}/_docs/PKGBUILD.templates.d/release/* > PKGBUILD
	touch "${SRCFILE}.sig"
fi

for i in MAINTNAME GPGKEY PKGNAME PKGVER PKGDESC PKGURL SRCURL LICENSE PKGDEPS OPTDEPS BUILDDEPS _PKGNAME SRCFILE;
do
	NEWVAL=${!i}
	#echo "${i} is ${NEWVAL}"
	sed -i -re "s@%{2}${i}%{2}@${NEWVAL}@g" PKGBUILD	
done

# now we need to commit the thing since apparently we can't add empty repos as submodules...?
mksrcinfo
git add --all .
git commit -m "initial commit; setting up .gitignores and skeleton PKGBUILD"
git push origin master
cd /tmp
rm -rf ${PKGNAME}


cd ${PKGBUILD_DIR}
git submodule add --force aur@aur.archlinux.org:${PKGNAME}
#git submodule init ${PKGNAME}
#git submodule update ${PKGNAME}
cd ${PKGBUILD_DIR}/${PKGNAME}
cat >> $(git rev-parse --git-dir)/hooks/pre-commit << EOF
#!/bin/bash

/usr/bin/mksrcinfo

git add .SRCINFO
EOF
chmod 700 $(git rev-parse --git-dir)/hooks/pre-commit
