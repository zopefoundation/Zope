FILES = ZReST.py __init__.py refresh.txt version.txt TODO.txt README.txt
DTML = dtml/manage_addZReSTForm.dtml dtml/manage_editForm.dtml
VERSION := $(shell cat version.txt)

all: ${FILES} ${DTML}
	rm -rf dist
	mkdir dist
	mkdir dist/ZReST
	mkdir dist/ZReST/dtml
	cp ${FILES} dist/ZReST
	cp ${DTML}  dist/ZReST/dtml
	(cd dist; tar zcf ZReST-${VERSION}.tgz ZReST)
	mv dist/ZReST-${VERSION}.tgz .
	rm -rf dist

