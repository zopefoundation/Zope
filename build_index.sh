#!/bin/bash
# Update the index for all release tags

printf "# Zope Releases\n\n" > README.md
rm -rf releases

# master
echo "master"
mkdir -p releases/master
git show master:versions.cfg > releases/master/versions.cfg
git show master:versions-prod.cfg > releases/master/versions-prod.cfg
printf "## latest\n\n(files created from master but not necessarily in sync with it)" >> README.md
printf "\n\n* [versions.cfg](releases/master/versions.cfg)\n* [versions-prod.cfg](releases/master/versions-prod.cfg)\n" >> README.md
git show master:requirements-full.txt > releases/master/requirements-full.txt 2>/dev/null && printf "* [requirements-full.txt](releases/master/requirements-full.txt)\n" >> README.md || rm releases/master/requirements-full.txt
git show master:requirements.txt > releases/master/requirements.txt 2>/dev/null && printf "* [requirements.txt](releases/master/requirements.txt)\n" >> README.md || rm releases/master/requirements.txt
git show master:constraints.txt > releases/master/constraints.txt 2>/dev/null && printf "* [constraints.txt](releases/master/constraints.txt)\n" >> README.md || rm releases/master/constraints.txt
printf "\n" >> README.md


# 4.0
for tag in "4.0"; do
    echo $tag
    mkdir -p releases/$tag
    git show $tag:versions.cfg > releases/$tag/versions.cfg
    git show $tag:versions-prod.cfg > releases/$tag/versions-prod.cfg
    printf "## $tag" >> README.md
    printf "\n\n* [versions.cfg](releases/$tag/versions.cfg)\n* [versions-prod.cfg](releases/$tag/versions-prod.cfg)\n" >> README.md
    git show $tag:requirements-full.txt > releases/$tag/requirements-full.txt 2>/dev/null && printf "* [requirements-full.txt](releases/$tag/requirements-full.txt)\n" >> README.md || rm releases/$tag/requirements-full.txt
    git show $tag:requirements.txt > releases/$tag/requirements.txt 2>/dev/null && printf "* [requirements.txt](releases/$tag/requirements.txt)\n" >> README.md || rm releases/$tag/requirements.txt
    git show $tag:constraints.txt > releases/$tag/constraints.txt 2>/dev/null && printf "* [constraints.txt](releases/$tag/constraints.txt)\n" >> README.md || rm releases/$tag/constraints.txt
    printf "\n" >> README.md
done

# 4.x: 'versions.cfg', 'versions-prod.cfg', and 'requirements-full.txt'
# 4.0b6+: additionally 'constraints.txt'
for tag in $(git tag -l "4*" | sort -Vr); do
    if [ "$tag" == "4.0" ] ; then
        continue
    fi
    echo $tag
    mkdir -p releases/$tag
    git show $tag:versions.cfg > releases/$tag/versions.cfg
    git show $tag:versions-prod.cfg > releases/$tag/versions-prod.cfg
    printf "## $tag" >> README.md
    printf "\n\n* [versions.cfg](releases/$tag/versions.cfg)\n* [versions-prod.cfg](releases/$tag/versions-prod.cfg)\n" >> README.md
    git show $tag:requirements-full.txt > releases/$tag/requirements-full.txt 2>/dev/null && printf "* [requirements-full.txt](releases/$tag/requirements-full.txt)\n" >> README.md || rm releases/$tag/requirements-full.txt
    git show $tag:requirements.txt > releases/$tag/requirements.txt 2>/dev/null && printf "* [requirements.txt](releases/$tag/requirements.txt)\n" >> README.md || rm releases/$tag/requirements.txt
    if [ $tag == "master" -o $tag == "4.0b6" -o $tag == "4.0b7" -o $tag == "4.0b8" -o $tag == "4.0b9" -o $tag == "4.0b10" ] ; then
        git show $tag:constraints.txt > releases/$tag/constraints.txt 2>/dev/null && printf "* [constraints.txt](releases/$tag/constraints.txt)\n" >> README.md || rm releases/$tag/constraints.txt
    fi
    printf "\n" >> README.md
done

# Select 2.13 versions
for tag in "2.13.29" "2.13.28" "2.13.27" "2.13.26"; do
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

# Select pre egg releases >= 2.10
printf "## Pre egg releases\n\n" >> README.md
for release in $(find pre-egg-releases -name Zope-2.1* -print); do
    rel=${release/pre-egg-releases\//}
    echo $rel
    printf "* [$rel]($release)\n" >> README.md
done
# Select pre egg releases < 2.10 (This is a separate block to ensure the sort order newest --> oldest.)
for release in $(find pre-egg-releases -name Zope* -a -not -name Zope-2.1* -print); do
    rel=${release/pre-egg-releases\//}
    echo $rel
    printf "* [$rel]($release)\n" >> README.md
done

# Add a footer
printf "\n_____\n\n" >> README.md
printf "[How to maintain this page](HOWTO.md)\n" >> README.md
