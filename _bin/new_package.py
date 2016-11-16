#!/usr/bin/env python3

import re
import os
import shutil
import subprocess
import hashlib
import datetime
import gnupg
import git  # python-gitpython in AUR
import menu3  # python-menu3 in AUR
import jinja2  # python-jinja in community
from tempfile import gettempdir
from urllib.request import urlopen

import pprint

## SETTINGS ##
gpgkey = ['748231EBCBD808A14F5E85D28C004C2F93481F6B']  # https://wiki.archlinux.org/index.php/PKGBUILD#validpgpkeys
maintname = 'brent s. <bts[at]square-r00t[dot]net>'  # your name and email address, feel free to obfuscate though
pkgbuild_dir = '/opt/dev/arch'  # what dir do the pkgbuilds/AUR checkouts live?
aur_pkgs_dir = pkgbuild_dir  # should be the dir where the aur_pkgs repo checkout lives. it's recommended you keep this the same as pkgbuild_dir
git_name = 'brent s.'  # the name to use in AUR git commits
git_email = 'bts@square-r00t.net'  # the email to use in AUR git commits

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
        pkg['name'] = input("\nWhat is the name of your package? (Exclude the '-git' etc. suffix, that will be added automatically later on)\n").lower()
        srcurl = input("\nWhat is the checkout URL for {0}?\n" +
                        "(Do not include the directory or VCS type prefix as per\n" +
                        "https://wiki.archlinux.org/index.php/VCS_package_guidelines#VCS_sources ...\n" +
                        "it will be added automatically)\n".format(pkg['name']))
        pkg['vcstype'] = ["git",
                "svn",
                "hg",
                "bzr"]
        pkg['srcurl'] = pkg['name'] + "::" + pkg['vcstype'][vcs_menu-1] + srcurl
        pkg['name'] = pkg['name'] + "-" + pkg['vcstype']
        pkg['type'] = 'vcs'
        pkg['srcfile'] = False
        pkg['ver'] = False
        pkg['srchash'] = 'SKIP'
        pkg['src_dl'] = False

    # If they're adding a release package...
    elif add_menu == 1:
        pkg['vcstype'] = False
        pkg['name'] = input("\nWhat is the name of your package?\n").lower()
        pkg['ver'] = input("\nWhat is the version of the release you are packaging for {0}?\n".format(pkg['name']))
        pkg['srcurl'] = input("\nWhat is the full URL for the tarball/zip file/etc. for {0} (version {1})?\n".format(pkg['name'], pkg['ver']))
        pkg['srcfile'] = re.sub('^\s*(https?|ftp).*/(.*)\s*$', '\\2', pkg['srcurl'], re.IGNORECASE)
        pkg['type'] = 'release'
        # And here's where we download the source file for hashing
        pkg['src_dl'] = "{0}/.aur_pkgs/{1}".format(gettempdir(), pkg['srcfile'])
        print("Please wait while we download {0} to {1}...\n".format(pkg['srcfile'], pkg['src_dl']))
        datastream = urlopen(pkg['srcurl'])
        data_in = datastream.read()
        with open(pkg['src_dl'], "wb") as data_dl:
            data_dl.write(data_in)
        pkg['srchash'] = hashlib.sha512(open(pkg['src_dl'],'rb').read()).hexdigest()

    # And this is stuff shared by both types.
    pkg['desc'] = input("\nWhat is a short description of {0}?\n".format(pkg['name']))
    pkg['site'] = input("\nWhat is {0}'s website?\n".format(pkg['name']))
    pkg['license'] = []
    license_raw = input(("\nWhat is {0}'s license(s)? (See https://wiki.archlinux.org/index.php/PKGBUILD#license)\n" +
                        "If you have more than one, separate them by spaces.\n").format(pkg['name'])).upper()
    pkg['license'] = list(map(str, license_raw.split()))
    pkg['deps'] = []
    deps_raw = input(("\nWhat does {0} depend on for runtime? if no packages, just hit enter.\n" +
                    "Make sure they correspond to Arch/AUR package names.\n" +
                    "If you have more than one, separate them by spaces.\n").format(pkg['name']))
    if deps_raw:
        pkg['deps'] = list(map(str, deps_raw.split()))
    pkg['optdeps'] = []
    optdeps_raw = input(("\nWhat does {0} optionally depend on (runtime)? if no packages, just hit enter.\n" +
                        "Make sure they correspond to Arch/AUR package names.\n" +
                        "If you have more than one, separate them by COMMAS.\n" + 
                        "They should follow this format:\n" +
                        "pkgname: some reason why it should be installed\n").format(pkg['name']))
    if optdeps_raw:
        pkg['optdeps'] = list(map(str, optdeps_raw.split(',')))
    pkg['makedeps'] = []
    makedeps_raw = input(("\nWhat dependencies are required for building/making {0}? If no packages, just hit enter.\n" +
                        "Make sure they correspond to Arch/AUR package names.\n" +
                        "If you have more than one, separate them by spaces.\n").format(pkg['name']))
    if makedeps_raw:
        pkg['makedeps'] = list(map(str, makedeps_raw.split()))
    if pkg['type'] == 'vcs':
        pkg['provides'] = [pkg['name'].split('-')[0]]
    else:
        pkg['provides'] = [pkg['name']]
    pkg['provides'] = []
    provides_raw = input(("\nWhat package names, if any besides itself, does {0} provide?\n" +
                        "(If {0} is a VCS package, do NOT include the non-VCS package name- that's added by default!)\n" +
                        "If you have more than one, separate them by spaces.\n").format(pkg['name']))
    if provides_raw:
        provides_list = list(map(str, provides_raw.split()))
        pkg['provides'] = pkg['provides'] + provides_list
    if pkg['type'] == 'vcs':
        pkg['conflicts'] = [pkg['name'].split('-')[0]]
    else:
        pkg['conflicts'] = [pkg['name']]
    conflicts_raw = input(("\nWhat package names, if any, does {0} conflict with?\n" +
                        "(If {0} is a VCS package, do NOT include the non-VCS package name- that's added by default!)\n" +
                        "If you have more than one, separate them by spaces.\n").format(pkg['name']))
    if conflicts_raw:
        conflicts_list = list(map(str, conflicts_raw.split()))
        pkg['conflicts'] = pkg['conflicts'] + conflicts_list
    return(pkg)

## MAKE SURE SOME PREREQS HAPPEN ##
def sanity_checks():
    os.makedirs(pkgbuild_dir, exist_ok = True)

## REGISTER IN THE AUR AND MAKE FIRST COMMIT ##
def aur_create(pkg):
    # git clone from AUR to create repository, add .gitignore
    tmpcheckout = os.path.join(gettempdir(), '.aur_pkgs')
    repo_dir = tmpcheckout + '/' + pkg['name']
    if os.path.exists(repo_dir):
        shutil.rmtree(repo_dir)
    git_repo_dir = git.osp.join(tmpcheckout, pkg['name'])
    # oops. originally had branch='master', which causes it to die since we're cloneing an empty repo
    aur_repo = git.Repo.clone_from('aur@aur.archlinux.org:' + pkg['name'], git_repo_dir)
    repo_dir = aur_repo.working_tree_dir
    shutil.copy2(aur_pkgs_dir + "/_docs/PKGBUILD.templates.d/gitignore", repo_dir + "/.gitignore")
    aur_repo.index.add(['.gitignore'])
    # Create the initial PKGBUILD
    tpl_dir = aur_pkgs_dir + '/_docs/PKGBUILD.templates.d.python'
    tpl_meta = aur_pkgs_dir + '/_docs/PKGBUILD.templates.d.python' + '/' + pkg['type'] + '.all'
    tpl_fsloader = jinja2.FileSystemLoader(searchpath = tpl_dir, followlinks = True)
    tpl_fsloader2 = jinja2.FileSystemLoader(searchpath = tpl_dir + '/' + pkg['type'], followlinks = True)
    pkgbuild_list = tpl_fsloader2.list_templates()
    pkgbuild_list[:] = [pkg['type'] + '/' + s for s in pkgbuild_list]
    tpl_env = jinja2.Environment(loader = tpl_fsloader)
    pkgbuild_out = tpl_env.get_template(pkg['type'] + '.all.j2').render(pkg = pkg,
                                                                        maintname = maintname,
                                                                        gpgkey = gpgkey,
                                                                        pkgbuild_list = pkgbuild_list)
    with open(repo_dir + "/PKGBUILD", "w+") as pkgbuild_file:
        pkgbuild_file.write(pkgbuild_out)
    # Move the source file
    if pkg['srcfile']:
        # sign with GPG
        gpg = gnupg.GPG()
        datastream = open(pkg['src_dl'], 'rb')
        print("If you see an error about 'KEY_CONSIDERED', you most likely can ignore it.")
        gpg.sign_file(datastream, keyid = gpgkey[0], detach = True, clearsign = False, output = repo_dir + '/' + pkg['srcfile'] + '.sig')
        datastream.close()
        aur_repo.index.add([pkg['srcfile'] + '.sig'])
    aur_repo.index.add(['PKGBUILD'])
    # TODO: SRCINFO!
    now = datetime.datetime.utcnow().strftime("%a %b %d %H:%M:%S UTC %Y")
    srcinfo_out = tpl_env.get_template('srcinfo.j2').render(pkg = pkg, now = now )
    with open(repo_dir + "/.SRCINFO", "w+") as srcinfo_file:
        srcinfo_file.write(srcinfo_out)
    aur_repo.index.add(['.SRCINFO'])
    # commit to git
    aur_repo.index.commit("initial commit; setting up .gitignores and skeleton PKGBUILD")
    # and push...
    aur_repo.remotes.origin.push()
    # and delete the repo and source file
    shutil.rmtree(repo_dir)
    if pkg['srcfile']:
        os.remove(pkg['src_dl'])

## ADD THE SUBMODULE TO THE MAIN AUR TREE ##
def aur_submodule(pkg):
    aur_pkgs_repo = git.Repo(aur_pkgs_dir)
    aur_pkgs_repo.create_submodule(pkg['name'], aur_pkgs_dir + '/' + pkg['name'], url='aur@aur.archlinux.org:' + pkg['name'])
    aur_pkgs_repo.index.commit("adding {0}".format(pkg['name']))
    # Comment me out if you don't have access to upstream:
    aur_pkgs_repo.remotes.origin.push()
    # And don't forget to add the hook to make life easier for us in the future.
    # WARNING: HERE BE POSSIBLE RACE CONDITIONS
    mod_gitdir = aur_pkgs_repo.submodules[-1].module().git_dir
    if not aur_pkgs_repo.submodules[-1].module().git_dir.endswith(pkg['name']):
        exit('SOMETHING FUCKED UP BADLY. Do not run this thing in parallel.')
    else:
        pass
    shutil.copy2(aur_pkgs_dir + '/_docs/PKGBUILD.templates.d.python/pre-commit.hook.sh', mod_gitdir + '/hooks/pre-commit', follow_symlinks = True)
    print()

#pprint.pprint(gui_init())

#aur_create(gui_init())

if __name__ ==  "__main__":
    pkg = gui_init()
    sanity_checks()
    aur_create(pkg)
    aur_submodule(pkg)
    print("Done! Successfully added {0} to the AUR and your local AUR meta-repository.".format(pkg['name'])
