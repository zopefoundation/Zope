#! /bin/bash

# Run the regression test suite

: ${TMPDIR=/tmp}

for test in test/test*.xml
do
    out=` echo $test | sed 's,test/test,test/out,' `
    tmp=$TMPDIR/taltest$$`basename $test`
    ./driver.py $test >$tmp
    if cmp -s $tmp $out
    then
        echo $test OK
    else
        echo $test failed -- diff follows
	diff $out $tmp
    fi
    rm $tmp
done
