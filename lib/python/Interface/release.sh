
R=$1
M=Interface

for f in test.py `cat pyfiles`; do
  python1.5.1 /projects/sbin/tabnanny.py $f
done

mkdir "$M-$R" "$M-$R/Interface"

for f in `cat pyfiles`; do
  cp $f  "$M-$R/Interface/"
done

for f in README.txt CHANGES.txt test.py; do
  cp $f  "$M-$R/"
done

tar cvf "$M-$R.tar" "$M-$R"
rm -f "$M-$R.tar.gz"
gzip "$M-$R.tar"
