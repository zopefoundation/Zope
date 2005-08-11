ZODBVERSION=3.2
ZODBDIRNAME=ZODB3-$(ZODBVERSION)
ZEO_REQUIRED_FILES=tmp/$(ZODBDIRNAME).tar.gz

REQUIRED_FILES=$(ZEO_REQUIRED_FILES)\
               $(PYTHON_REQUIRED_FILES)

# run the Zope tests

clean_zope:
	$(RMRF) src/$(ZODBDIRNAME)

install_zeo: src/$(ZODBDIRNAME)/setup.py install_python \
             $(BUILD_DIR)/lib/python/version.txt \
             $(BUILD_DIR)/ZEO-$(ZODBDIRNAME)-win32.exe

ESCAPED=$(shell sh $(MAKEFILEDIR)/bin/escape.sh '$(WIN_MAKEFILEDIR)')
SEDSCRIPT="s@<<VERSION>>@$(ZODBVERSION)@g;s@<<MAKEFILEDIR>>@$(ESCAPED)@g"

$(BUILD_DIR)/ZEO-$(ZODBDIRNAME)-win32.exe: $(BUILD_DIR)/lib/python/version.txt
	$(SED) $(SEDSCRIPT) < "$(MAKEFILEDIR)/etc/zeo.iss.in" | unix2dos > "$(BUILD_DIR)/zeo.iss"

	# Remove CVS directories from the build tree.
	find $(BUILD_DIR) -name CVS -type d -exec $(RMRF) {} \; -prune

	# Convert text files to Windows line ends.  unix2dos has the nice
	# property that it leaves lines with \r\n alone, so it doesn't hurt
	# to do this on files already converted to Windows convention.
	find $(BUILD_DIR) -name "*.py" -o -name "*.txt" -o -name "*.bat" | \
		xargs unix2dos

	# Build the Inno installer.
	$(CD) "$(BUILD_DIR)";"$(ISS_COMPILER)" /cc "$(WIN_BUILD_DIR)\zeo.iss"

$(BUILD_DIR)/lib/python/ExtensionClass.pyd: WIN_TMPDIR=tmp\zeotmp
$(BUILD_DIR)/lib/python/ExtensionClass.pyd: install_python
	$(MKDIR) $(WIN_TMPDIR)
	$(CD) $(SRC_DIR)/$(ZODBDIRNAME); \
            $(BUILD_DIR)/bin/python.exe setup.py install \
            --prefix="$(WIN_BASE_DIR)\$(WIN_TMPDIR)" --no-compile
	$(MKDIR) $(@D)
	$(XCOPY) "$(WIN_TMPDIR)\Lib\site-packages\*.py" "$(shell cygpath -w $(@D))"
	$(XCOPY) "$(WIN_TMPDIR)\Lib\site-packages\*.pyd" "$(shell cygpath -w $(@D))"
	$(XCOPY) "$(WIN_TMPDIR)\Lib\site-packages\*.txt" "$(shell cygpath -w $(@D))"
	$(XCOPY) "$(WIN_TMPDIR)\Lib\site-packages\*.xml" "$(shell cygpath -w $(@D))"
	$(XCOPY) "$(WIN_TMPDIR)\Lib\site-packages\*.conf" "$(shell cygpath -w $(@D))"
	$(XCOPY) "$(WIN_TMPDIR)\Include\*.h" "$(WIN_BUILD_DIR)\bin\Include"
	$(XCOPY) "$(WIN_TMPDIR)\Scripts\*.py" "$(WIN_BUILD_DIR)\bin"
	$(RMRF) $(shell cygpath -u $(WIN_TMPDIR))

$(BUILD_DIR)/lib/python/nt_svcutils/__init__.py: CVS_REPOSITORY=$(ZOPE_CVS_REPOSITORY)
$(BUILD_DIR)/lib/python/nt_svcutils/__init__.py: CVS_MODULE=Zope/lib/python/nt_svcutils
$(BUILD_DIR)/lib/python/nt_svcutils/__init__.py: CVS_TAG=-r HEAD

$(BUILD_DIR)/lib/python/nt_svcutils/__init__.py:
	${CD} ${BUILD_DIR}/lib/python && \
	${CVS} -d ${CVS_REPOSITORY} export ${CVS_TAG} -d \
        $(shell basename $(@D)) ${CVS_MODULE}

$(BUILD_DIR)/skel/README.txt:
	$(MKDIR) "$(@D)"
	$(CPR) $(MAKEFILEDIR)/zeo_addons/skel/* $(@D)
	$(TOUCH) "$@"

$(BUILD_DIR)/bin/mkzeoinstance.py:
	$(MKDIR) "$(@D)"
	$(CPR) $(MAKEFILEDIR)/zeo_addons/utilities/* $(@D)
	$(TOUCH) "$(@)"

$(BUILD_DIR)/lib/python/version.txt: $(BUILD_DIR)/lib/python/ExtensionClass.pyd $(BUILD_DIR)/lib/python/nt_svcutils/__init__.py $(BUILD_DIR)/skel/README.txt $(BUILD_DIR)/bin/mkzeoinstance.py
	@echo ZEO $(ZODBVERSION) > "$(BUILD_DIR)/lib/python/version.txt"
	$(TOUCH) $@

src/$(ZODBDIRNAME)/setup.py:
	$(MKDIR) "$(SRC_DIR)"
	$(CD) "$(SRC_DIR)" && $(TAR) xvzf ../tmp/$(ZODBDIRNAME).tar.gz
	$(TOUCH) $@
