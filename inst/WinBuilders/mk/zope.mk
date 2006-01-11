ZOPEVERSION := 2.9.0
ZOPEDIRNAME := Zope-$(ZOPEVERSION)

ZOPE_REQUIRED_FILES=tmp/$(ZOPEDIRNAME).tgz

REQUIRED_FILES=$(PYTHON_REQUIRED_FILES)\
               $(ZOPE_REQUIRED_FILES)

MAKEZOPE="$(MAKEFILEDIR)/bin/makezope.bat" "$(WIN_BUILD_DIR)"
# run the Zope tests
test_zope:
	$(CD) "$(BASE_DIR)/src/Zope"
	"$(PYPCBUILDDIR)/python.exe" utilities/testrunner.py -a
	$(CD) "$(BASE_DIR)"

clean_zope:
	$(RMRF) src/$(ZOPEDIRNAME)

install_zope: src/$(ZOPEDIRNAME)/inst/configure.py \
	$(BUILD_DIR)/lib/python/version.txt install_python \
	$(BUILD_DIR)/Zope-$(ZOPEVERSION)-win32.exe

ESCAPED=$(shell sh $(MAKEFILEDIR)/bin/escape.sh '$(WIN_MAKEFILEDIR)')
SEDSCRIPT="s@<<VERSION>>@$(ZOPEVERSION)@g;s@<<MAKEFILEDIR>>@$(ESCAPED)@g"

$(BUILD_DIR)/Zope-$(ZOPEVERSION)-win32.exe: $(BUILD_DIR)/lib/python/version.txt
	$(SED) $(SEDSCRIPT) < "$(MAKEFILEDIR)/etc/zope.iss.in" | unix2dos > "$(BUILD_DIR)/zope.iss"

	# Remove CVS directories and compiled Python files from the build tree.
	find $(BUILD_DIR) -name CVS -type d -exec $(RMRF) {} \; -prune
	find $(BUILD_DIR) -name "*.pyc" -o -name "*.pyo" | xargs $(RM)

	# Convert text files to Windows line ends.  unix2dos has the nice
	# property that it leaves lines with \r\n alone, so it doesn't hurt
	# to do this on files already converted to Windows convention.
	find $(BUILD_DIR) -name "*.py"   | xargs unix2dos
	find $(BUILD_DIR) -name "*.txt"  | xargs unix2dos
	find $(BUILD_DIR) -name "*.bat"  | xargs unix2dos
	find $(BUILD_DIR) -name "*.conf" | xargs unix2dos
	find $(BUILD_DIR) -name "*.xml"  | xargs unix2dos
	find $(BUILD_DIR) -name "*.in"   | xargs unix2dos

	# Build the Inno installer.
	$(CD) "$(BUILD_DIR)";"$(ISS_COMPILER)" /cc "$(WIN_BUILD_DIR)\zope.iss"

$(BUILD_DIR)/lib/python/Zope2/Startup/run.py:
	$(CD) "$(BUILD_DIR)"; \
	bin/python.exe \
            "$(WIN_SRC_DIR)\$(ZOPEDIRNAME)\inst\configure.py" \
            --prefix="$(WIN_BUILD_DIR)" --no-compile
	$(MAKEZOPE)
	$(TOUCH) "$(BUILD_DIR)/lib/python/Zope2/Startup/run.py"

$(BUILD_DIR)/lib/python/version.txt: $(BUILD_DIR)/lib/python/Zope2/Startup/run.py
	@echo Zope $(ZOPEVERSION) > "$(BUILD_DIR)/lib/python/version.txt"
	$(TOUCH) "$(BUILD_DIR)/lib/python/version.txt"

src/$(ZOPEDIRNAME)/inst/configure.py:
	$(MKDIR) "$(SRC_DIR)"
	$(CD) "$(SRC_DIR)" && $(TAR) xvzf ../tmp/$(ZOPEDIRNAME).tgz \
           && $(TOUCH) $(ZOPEDIRNAME)/inst/configure.py
