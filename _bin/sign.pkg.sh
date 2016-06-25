#!/bin/bash



GPGKEY='748231EBCBD808A14F5E85D28C004C2F93481F6B'
PKGBUILD_DIR='/opt/dev/arch'


if [[ -n "${1}" ]];
then
	PKGNAME="${1}"
else
	PKGNAME="$(pwd | sed -e 's@^.*/@@g')"
fi

if [ ! -d "${PKGBUILD_DIR}/${PKGNAME}" ];
then
	echo "ERROR: ${PKGNAME} is not a package directory in ${PKGBUILD_DIR}!"
	exit
fi

if [ ! -f "${PKGBUILD_DIR}/${PKGNAME}/PKGBUILD" ];
then
	echo "ERROR: ${PKGNAME} is a package directory in ${PKGBUILD_DIR}, but it is missing a PKGBUILD file!"
fi

cd "${PKGBUILD_DIR}/${PKGNAME}"

rm *.sig  # don't delete sigs, we want to keep them in case they exist for co-maintainers...? see line 34
updpkgsums

for i in $(find ./ -maxdepth 1 -type f | egrep -Ev '(*\.install|PKGBUILD|Changelog|\.gitignore)');
do
	# i need a better way of dealing with sigs from co-maintainers.
	# when i think of something, comment out line 29 and uncomment the commented lines below to add sigs
	#cp ${i}.sig ${i}.sig.old
	gpg -u 0x${GPGKEY} --detach-sign ${i}
	#cat ${i}.sig.old >> ${i}.sig
	#rm ${i}.sig.old
done

updpkgsums

git add --all .
git commit -m "version bump, etc."
