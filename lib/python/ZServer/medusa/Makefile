# -*- Mode: Makefile; tab-width: 4 -*-

all: dist

dist: clean
	python util/name_dist.py

clean:
	find ./ -name '*.pyc' -exec rm {} \;
	find ./ -name '*~' -exec rm {} \;
