#!/bin/bash
# Update the index for all release tags

printf "# Zope Releases\n\n" > README.md
rm -rf releases

# 4.x: 'versions.cfg', 'versions-prod.cfg', and 'requirements-full.txt'
for tag in "master" $(git tag -l "4*" | sort -r); do
    echo $tag
    mkdir -p releases/$tag
    git show $tag:versions.cfg > releases/$tag/versions.cfg
    git show $tag:versions-prod.cfg > releases/$tag/versions-prod.cfg
    printf "## $tag\n\n* [versions.cfg](releases/$tag/versions.cfg)\n* [versions-prod.cfg](releases/$tag/versions-prod.cfg)\n" >> README.md
    git show $tag:requirements-full.txt > releases/$tag/requirements-full.txt 2>/dev/null && printf "* [requirements-full.txt](releases/$tag/requirements-full.txt)\n" >> README.md || rm releases/$tag/requirements-full.txt
    git show $tag:requirements.txt > releases/$tag/requirements.txt 2>/dev/null && printf "* [requirements.txt](releases/$tag/requirements.txt)\n" >> README.md || rm releases/$tag/requirements.txt
    printf "\n" >> README.md
done

# Select 2.13 versions
for tag in "2.13.28" "2.13.27" "2.13.26"; do
    echo $tag
    mkdir -p releases/$tag
    echo "[versions]" >releases/$tag/versions-prod.cfg
    git show $tag:requirements.txt | sed -e 's/\=\=/ = /g' >>releases/$tag/versions-prod.cfg && printf "## $tag\n\n* [versions-prod.cfg](releases/$tag/versions-prod.cfg)\n" >> README.md
    git show $tag:requirements.txt > releases/$tag/requirements.txt && printf "* [requirements.txt](releases/$tag/requirements.txt)\n" >> README.md || rm releases/$tag/requirements.txt
    printf "\n" >> README.md
done

# Select 2.12 versions
for tag in "2.12.28"; do
    echo $tag
    mkdir -p releases/$tag
    git show $tag:versions.cfg > releases/$tag/versions.cfg && printf "## $tag\n\n* [versions.cfg](releases/$tag/versions.cfg)\n" >> README.md
    printf "\n" >> README.md
done

# Select pre egg releases
printf "## Pre egg releases\n\n" >> README.md
for release in $(ls -1 pre-egg-releases); do
    echo $release
    printf "* [$release](pre-egg-releases/$release)\n" >> README.md
done

# Add a footer
printf "\n_____\n\n" >> README.md
printf "[How to maintain this page](HOWTO.md)\n" >> README.md
