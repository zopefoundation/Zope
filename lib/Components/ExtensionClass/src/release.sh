#!/bin/sh

R=$1
M=ExtensionClass

StructuredText < $M.stx > $M.html
StructuredText < Installation > Installation.html
StructuredText < Acquisition.stx > Acquisition.html
StructuredText < MultiMapping.stx > MultiMapping.html
StructuredText < release.notes > release.html

rm -rf "$M-$R"
mkdir  "$M-$R"
for f in `cat release.fl`; do
  cp $f "$M-$R/"
done

tar cvf - "$M-$R" | gzip > "$M-$R.tar.gz"
