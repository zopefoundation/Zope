PYTHON=python2.2
WHOA_PIGGY=wo_pcgi.py
TESTOPTS=-a -v1

all:
	$(PYTHON) $(WHOA_PIGGY)

test:
	$(PYTHON) utilities/testrunner.py $(TESTOPTS)

clean:
	find . \( -name '*.o' -o -name '*.so' -o -name '*.py[co]' \
	          -o -name 'core*' \) \
	       -exec rm {} \;
