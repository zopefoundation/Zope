#!/bin/sh

R=$1
M=ExtensionClass

StructuredText < $M.stx > $M.html
rm -rf "$M-$R"
mkdir  "$M-$R"
tar -c -R release.fl -f - | (cd "$M-$R"; tar xvf -)
tar cvf - "$M-$R" | gzip > "$M-$R.tar.gz"
