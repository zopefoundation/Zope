#!/bin/sh

R=$1
M=ExtensionClass

StructuredText < $M.stx > $M.html
rm -rf "$M-$R"
mkdir  "$M-$R"
for f in `cat release.fl`; do
  cp $f "$M-$R/"
done

tar cvf - "$M-$R" | gzip > "$M-$R.tar.gz"
