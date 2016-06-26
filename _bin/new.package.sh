#!/bin/bash
set -e
set -x


## SETTINGS ##

GPGKEY='748231EBCBD808A14F5E85D28C004C2F93481F6B'  # https://wiki.archlinux.org/index.php/PKGBUILD#validpgpkeys
MAINTNAME='brent s. <bts[at]square-r00t[dot]net>'
PKGBUILD_DIR='/opt/dev/arch'

# These shouldn't be touched.
PKGNAME=${1}
PKGVER="${2}"


## SANITY ##
set +e  # disable bail-on-error because we want a non-zero if a package name is not right, etc.
mkdir -p ${PKGBUILD_DIR}
cd ${PKGBUILD_DIR}
echo "${PKGNAME}" | egrep -Eq '^([a-z0-9\_]|-)+$'
if [[ "${?}" -ne '0' ]];
then
	echo "ERROR: That does not seem to be a valid package name!"
	exit
fi
echo "${PKGVER}" | egrep -Eq '^([0-9\.]|git|svn)+$'
if [[ "${?}" -ne '0' ]];
then
	echo "ERROR: That does not seem to be a valid package version!"
	echo "Acceptable values are numbers, .'s, or simply 'git'."
	exit
elif [[ "${PKGVER}" == 'git' || "${PKGVER}" == 'svn' ]];
then
	PKGVER='0.0.00001'
	GITPKG='y'
fi

if [[ -z "${2}" ]];
then
	echo "USAGE: ${0} <package name> <package version>"
	exit
fi
set -e

echo "Will create a package named ${PKGNAME} with initial version of ${PKGVER}. Press enter to continue, or ctrl-C to quit."
read PKGCHK


## CREATE THE REPO/PACKAGE IN AUR ##
cd /tmp
git clone aur@aur.archlinux.org:${PKGNAME}
cd /tmp/${PKGNAME}
cat >> .gitignore << EOF
*/
.*.swp
*.pkg.tar.xz
src/
pkg/
*.tar
*.tar.bz2
*.tar.xz
*.tar.gz
*.tgz
*.txz
*.tbz
*.tbz2
*.zip
*.run
*.7z
*.rar
*.deb
EOF
git add .gitignore

## DROP IN A VANILLA PKGBUILD ##
cat > PKGBUILD << EOF
# Maintainer: ${MAINTNAME}
# Bug reports can be filed at https://bugs.square-r00t.net/index.php?project=3
# News updates for packages can be followed at https://devblog.square-r00t.net
validpgpkeys=('${GPGKEY}')
pkgname=${PKGNAME}
pkgver=${PKGVER}
pkgrel=1
pkgdesc="%%SOME DESCRIPTION HERE%%"
arch=('i686' 'x86_64')
url="%%SOME URL HERE%%"
license=('%%SOME LICENSE(S) HERE%%')
install=
changelog=
noextract=()
#depends=('%%RUNTIME DEPENDENCIES HERE%%')
#optdepends=('%%OPTIONAL DEPENDENCIES HERE (pkg: why needed)%%')
#makedepends=('%%BUILDTIME DEPENDENCIES HERE%%')
EOF

if [[ -n "${GITPKG}" ]];
then
	STRIPPKG=$(echo "${PKGNAME}" | sed -re 's/-(git|svn)//g')
else
	STRIPPKG="${PKGNAME}"
fi

cat >> PKGBUILD << EOF
_pkgname=${STRIPPKG}
#_pkgname2='%%OPTIONAL SHORTHAND PACKAGE NAME%%'
EOF


if [[ -n "${GITPKG}" ]];
then
	cat >> PKGBUILD << EOF
source=("\${_pkgname}::git+https://github.com/\${_pkgname}/\${_pkgname}.git")
sha512sums=('SKIP')
EOF
else
	cat >> PKGBUILD << EOF
source=("https://\${pkgname}.com/\${_pkgname}/\${_pkgname}-\${pkgver}.tar.gz"
	"\${_pkgname}-\${pkgver}.tar.gz.sig")
sha512sums=('cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e'
	    'SKIP')
EOF
fi

cat >> PKGBUILD << EOF
provides=("\${_pkgname}")
#conflicts=("\${_pkgname}")
EOF

if [[ -n "${GITPKG}" ]];
then
	cat >> PKGBUILD << EOF
pkgver() {
  cd "\${srcdir}/\${_pkgname}"
  (
     printf "r%s.%s" "\$(git rev-list --count HEAD)" "\$(git rev-parse --short HEAD)"
  #( set -o pipefail
  #  git describe --long --tags 2>/dev/null | sed 's/\\([^-]*-g\\)/r\\1/;s/-/./g' ||
  #  printf "r%s.%s" "\$(git rev-list --count HEAD)" "\$(git rev-parse --short HEAD)"
  #)
  )
}
EOF
fi

cat >> PKGBUILD << EOF

build() {
	cd "\${srcdir}/\${_pkgname}/src"
	make prefix=\${pkgdir}/usr
}

package() {
	install -D -m755 \${srcdir}/\${_pkgname}/src/\${_pkgname2} \${pkgdir}/usr/bin/\${_pkgname2}
	install -D -m644 \${srcdir}/\${_pkgname}/docs/README.html.en \${pkgdir}/usr/share/doc/\${_pkgname}/README.html
}
EOF

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
