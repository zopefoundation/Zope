ZOPEVERSION = 2.9.10
ZOPEDIRNAME := Zope-$(ZOPEVERSION)

ZOPE_REQUIRED_FILES=tmp/$(ZOPEDIRNAME).tgz

REQUIRED_FILES=$(PYTHON_REQUIRED_FILES) \
               $(ZOPE_REQUIRED_FILES)

clean_zope:
	$(RMRF) src/$(ZOPEDIRNAME)

install_zope: src/$(ZOPEDIRNAME)/inst/configure.py \
	install_python \
	$(BUILD_DIR)/lib/python/Zope2/version.txt \
	$(BUILD_DIR)/Zope-$(ZOPEVERSION)-win32.exe

ESCAPED=$(shell sh $(MAKEFILEDIR)/bin/escape.sh '$(WIN_MAKEFILEDIR)')
SEDSCRIPT="s@<<VERSION>>@$(ZOPEVERSION)@g;s@<<MAKEFILEDIR>>@$(ESCAPED)@g"

$(BUILD_DIR)/Zope-$(ZOPEVERSION)-win32.exe: $(BUILD_DIR)/lib/python/Zope2/version.txt
	$(SED) $(SEDSCRIPT) < "$(MAKEFILEDIR)/etc/zope.iss.in" | unix2dos > "$(BUILD_DIR)/zope.iss"

	# Remove CVS directories and compiled Python files from the build tree.
	find $(BUILD_DIR) -name CVS -type d -exec $(RMRF) {} \; -prune
	find $(BUILD_DIR) -name "*.pyc" -o -name "*.pyo" | xargs $(RM)

	# Convert text files to Windows line ends.  unix2dos has the nice
	# property that it leaves lines with \r\n alone, so it doesn't hurt
	# to do this on files already converted to Windows convention.
	find $(BUILD_DIR) -name "*.bat"  | xargs unix2dos
	find $(BUILD_DIR) -name "*.conf" | xargs unix2dos
	find $(BUILD_DIR) -name "*.html" | xargs unix2dos
	find $(BUILD_DIR) -name "*.in"   | xargs unix2dos
	find $(BUILD_DIR) -name "*.py"   | xargs unix2dos
	find $(BUILD_DIR) -name "*.stx"  | xargs unix2dos
	find $(BUILD_DIR) -name "*.txt"  | xargs unix2dos
	find $(BUILD_DIR) -name "*.xml"  | xargs unix2dos
	find $(BUILD_DIR) -name "*.zcml" | xargs unix2dos

	# Build the Inno installer.
	$(CD) "$(BUILD_DIR)";"$(ISS_COMPILER)" /cc "$(WIN_BUILD_DIR)\zope.iss"

MAKEZOPE="$(MAKEFILEDIR)/bin/makezope.bat" "$(WIN_SRC_DIR)\\$(ZOPEDIRNAME)"

# This builds Zope, then installs it into the build directory, then
# creates lib/python/Zope2/version.txt in the build directory.
$(BUILD_DIR)/lib/python/Zope2/version.txt: $(BUILD_DIR)/bin/python.exe
	cd "$(SRC_DIR)/$(ZOPEDIRNAME)" && \
		"$<" inst/configure.py  \
                        --prefix="$(WIN_BUILD_DIR)" \
                        --no-compile
	$(MAKEZOPE)
	echo Zope $(ZOPEVERSION) > $@
	$(TOUCH) $@

tmp/$(ZOPEDIRNAME).tgz:
	$(TOUCH) tmp/$(ZOPEDIRNAME).tgz

# This merely unpacks the Zope tarball.
src/$(ZOPEDIRNAME)/inst/configure.py: tmp/$(ZOPEDIRNAME).tgz
	$(MKDIR) "$(SRC_DIR)"
	$(CD) "$(SRC_DIR)" && $(TAR) xzf ../tmp/$(ZOPEDIRNAME).tgz
	$(TOUCH) $@
