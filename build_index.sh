#!/bin/bash
# Update the index for all release tags

printf "# Zope Releases\n\n" > README.md
rm -rf releases

# 4.x: 'versions.cfg', 'versions-prod.cfg', and 'requirements-full.txt'
for tag in $(git tag -l "4*" | sort -r); do
    echo $tag
    mkdir -p releases/$tag
    git show $tag:versions.cfg > releases/$tag/versions.cfg
    git show $tag:versions-prod.cfg > releases/$tag/versions-prod.cfg
    git show $tag:requirements-full.txt > releases/$tag/requirements-full.txt || rm releases/$tag/requirements-full.txt
    git show $tag:requirements.txt > releases/$tag/requirements.txt || rm releases/$tag/requirements.txt
    printf "## $tag\n\n- [versions.cfg](releases/$tag/versions.cfg)\n- [versions-prod.cfg](releases/$tag/versions-prod.cfg)\n- [requirements-full.txt](releases/$tag/requirements-full.txt)\n" >> README.md
done
