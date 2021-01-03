#!/usr/bin/env python3

import argparse
import os
import shutil
##
import git


repo_dir = '/opt/dev/arch'

class Remover(object):
    def __init__(self, pkgnm, force = False):
        self.pkg = pkgnm
        self.force = force
        rdir = os.path.abspath(os.path.expanduser(repo_dir))
        self.dir = os.path.join(rdir, self.pkg)
        # TODO: automatically check out?
        if not os.path.isdir(self.dir):
            raise FileNotFoundError('Package directory does not exist. Is it checked out?')
        self.repo = git.Repo(rdir)
        self.sub = self.repo.submodule(self.pkg)

    def remove(self):
        self.sub.remove(force = self.force)
        return(None)

    def push(self):
        self.repo.remotes.origin.push()
        return(None)


def parseArgs():
    args = argparse.ArgumentParser(description = 'Remove a package from repository (disowned, promoted to [community], etc.)')
    args.add_argument('-f', '--force',
                      action = 'store_true',
                      help = 'Delete even if it contains changes not yet committed')
    args.add_argument('pkgnm',
                      help = 'The package name. An error will be thrown if it is not checked out locally')
    return(args)


def main():
    args = parseArgs().parse_args()
    r = Remover(**vars(args))
    r.remove()
    r.push()
    return(None)


if __name__ == '__main__':
    main()

