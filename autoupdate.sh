#!/bin/sh
#
#	autoupdate: Automatically update the zope2book HTML
#
ROOT="/home/zope/zope2docs"

export PATH="${PATH}:${ROOT}/bin"

before=$(svn info $ROOT | grep "^Last Changed Rev:" | cut -d " " -f 4)
svn up -q $ROOT
after=$(svn info $ROOT | grep "^Last Changed Rev:" | cut -d " " -f 4)

if [ "$before" != "$after" ]; then
    echo "Updated from revision $before to $after;  rebuilding HTML docs."
    cd $ROOT
    python bootstrap.py
    ${ROOT}/bin/buildout -q -q
    make -s html >/dev/null
fi
