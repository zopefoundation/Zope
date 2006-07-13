##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import os
import sys
import optparse
import tarfile
from distutils import filelist

INCLUDES = tuple('.*'.split())
EXCLUDES = tuple(r""".*.svn\\ .*CVS\\ .*.tgz
                     .*makefile$ .*Makefile$
                     .*inst\\tmp\\.* .*inst\\src\\.*
                     .*build-base\\ .*build\\
                     .*~ .*.#.*""".split())

def collect(top_dir, includes=INCLUDES, excludes=EXCLUDES):
    old_dir = os.getcwd()
    os.chdir(top_dir)
    try:
        fl = filelist.FileList()
        fl.findall()

        for inc in includes:
            fl.include_pattern(inc, is_regex=1)

        for exc in excludes:
            fl.exclude_pattern(exc, is_regex=1)

        return fl.files
    finally:
        os.chdir(old_dir)

def tar_it_up(dest, files):
    tar = tarfile.open(dest, mode='w:gz')
    basename = os.path.splitext(os.path.basename(dest))[0]
    for fname in files:
        tar.add(fname, os.path.join(basename, fname), recursive=False)
    tar.close()

def main(options, args):
    dest, top_dir = args
    includes = options.include
    excludes = options.exclude
    excludes.append('.*%s.*' % os.path.basename(dest))

    files = collect(top_dir, includes=includes, excludes=excludes)
    tar_it_up(dest, files)

if __name__ == '__main__':
    excludes = list(EXCLUDES)
    includes = list(INCLUDES)

    parser = optparse.OptionParser()
    parser.add_option('', '--exclude', action='append', default=excludes)
    parser.add_option('', '--include', action='append', default=includes)

    options, args = parser.parse_args()

    if not len(args) == 2:
        parser.print_help()
        parser.exit(status=1)

    main(options, args)
