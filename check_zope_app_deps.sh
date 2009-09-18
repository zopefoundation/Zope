#! /bin/bash
python=$(find src/ -name "*.py" | xargs grep -l "zope\.app")
zcml=$(find src/ -name "*.zcml" | xargs grep -l "zope\.app")
doctest=$(find src/ -name "*.txt" | grep -v "egg-info" |
           xargs grep -l "zope\.app")
for f in $python $zcml $doctest; do
    echo ====================================================
    echo $f
    echo ====================================================
    grep "zope\.app" $f
done

