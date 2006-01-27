ZOPEVERSION := 2.9.0
ZOPEDIRNAME := Zope-$(ZOPEVERSION)

ZOPE_REQUIRED_FILES=tmp/$(ZOPEDIRNAME).tgz

REQUIRED_FILES=$(PYTHON_REQUIRED_FILES)\
               $(ZOPE_REQUIRED_FILES)

clean_zope:
	$(RMRF) src/$(ZOPEDIRNAME)

install_zope: src/$(ZOPEDIRNAME)/install.py \
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

# This builds Zope, then installs it into the build directory, then
# creates lib/python/Zope2/version.txt in the build directory.
#
# Yuck:  for whatever reason, distutils refuses to allow an absolute
# path for the --home option, so this hardcodes "build" as the name of
# the build directory, and assumes "build" is a sibling of SRC_DIR.
#
# Yuck:  the --no-compile option here has no effect:  the install step
# creates oodles of unwanted .pyc files.  They're removed by the
# $(BUILD_DIR)/Zope-$(ZOPEVERSION)-win32.exe target, though, before
# building the installer.
#
# Yuck:  no matter what I pass to --install-headers, it throws away the
# last path component.  We actually want to copy the Zope/ZODB headers
# into bin/Include.  The "nonsense" at the end gets thrown away, and that
# smells like a bug.  When it gets fixed, I suppose this will copy the
# headers to bin/Include/nonsense/.
$(BUILD_DIR)/lib/python/Zope2/version.txt: $(BUILD_DIR)/bin/python.exe
	cd "$(SRC_DIR)/$(ZOPEDIRNAME)" && \
		"$<" install.py install --no-compile --home=../../build \
			--install-headers=../../build/bin/Include/nonsense
	echo Zope $(ZOPEVERSION) > $@
	$(TOUCH) $@

tmp/$(ZOPEDIRNAME).tgz:
	$(CURL) -o tmp/$(ZOPEDIRNAME).tgz http://www.zope.org/Products/Zope/$(ZOPEVERSION)/$(ZOPEDIRNAME).tgz
	$(TOUCH) tmp/$(ZOPEDIRNAME).tgz

# This merely unpacks the Zope tarball.
src/$(ZOPEDIRNAME)/install.py: tmp/$(ZOPEDIRNAME).tgz
	$(MKDIR) "$(SRC_DIR)"
	$(CD) "$(SRC_DIR)" && $(TAR) xvzf ../tmp/$(ZOPEDIRNAME).tgz
