SUBDIRS=tests code_gen doc

clean: clean-local clean-recursive
release: version src-release doc-release

clean-local:
	$(RM) *.pyc *~ *.pyo

clean-recursive:
	for i in $(SUBDIRS); do \
	 (cd $$i && make clean); \
        done

src-release: clean
	cd .. && ./mkdist.sh

doc-release: clean
	cd doc && make release
