#! /bin/sh

# Run the regression test suite

: ${TMPDIR=/tmp}

flags=""

while :
do
    case $1 in
    -*) flags="$flags $1"; shift;;
    *)  break;;
    esac
done

for test in ${*-test/test*.xml}
do
    out=` echo $test | sed 's,/[^/0-9]*\([0-9]*\).xml,/out\1.xml,' `
    tmp=$TMPDIR/taltest$$`basename $test`
    ./driver.py $flags $test >$tmp
    if cmp -s $tmp $out
    then
        echo $test OK
    else
        echo "$test failed -- diff (expected vs. actual) follows"
        diff $out $tmp
    fi
    rm $tmp
done
