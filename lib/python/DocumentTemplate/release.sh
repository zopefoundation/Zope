#!/bin/sh

R=$1
M=DocumentTemplate

# StructuredText < $M.stx > $M.html
StructuredText -t < release_notes > DocumentTemplate-rn.html
cp DocumentTemplate-rn.html ..
rm -rf "$M-$R"
mkdir  "$M-$R" "$M-$R/$M"
echo
for f in `cat pyfiles`; do
  python1.5 -c "import sys; sys.path.append('..'); from tabnanny import *; f='$f'; check(f)"
done 
echo
tar -c -T release.fl -f - | (cd "$M-$R/$M"; tar xvf -)
cp INSTALL "$M-$R"/
tar cvf "$M-$R.tar" "$M-$R"
rm -f "$M-$R.tar.gz"
gzip "$M-$R.tar"
