PYTHON=python
WHOA_PIGGY=wo_pcgi.py
TESTOPTS=-a

all:
	$(PYTHON) $(WHOA_PIGGY)

test:
	$(PYTHON) utilities/testrunner.py $(TESTOPTS)

clean:
	./stupid_clean
