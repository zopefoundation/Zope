#!/bin/sh

R=$1
M=ExtensionClass

StructuredText -t < $M.stx > $M.html
StructuredText -t < Installation > Installation.html
StructuredText -t < Acquisition.stx > Acquisition.html
StructuredText -t < MultiMapping.stx > MultiMapping.html
StructuredText -t < COPYRIGHT.txt > COPYRIGHT.html
StructuredText -t < release.notes > release.html
StructuredText -t < index.stx > index.html

rm -rf "$M-$R"
mkdir  "$M-$R"
for f in `cat release.fl`; do
  cp $f "$M-$R/"
done

tar cvf - "$M-$R" | gzip > "$M-$R.tar.gz"
