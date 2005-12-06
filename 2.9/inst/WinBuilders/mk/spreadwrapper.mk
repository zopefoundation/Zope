# Builds the Python Spread wrapper module.
# Puts:
#     spread.pyd into build/lib/python/
#     testspread.py into build/lib/python/SpreadTest/
#     various text files (Windowsized and renamed) into build/doc

# Download the wrapper module tarball, from
# http://www.python.org/other/spread/.
# Store it in tmp/.  NOTE:  May need to rename it to .tgz (depends on how
# it's downloaded).  The name is of the form SpreadModule-n.n.tgz

# XXX There's no natural way to clean up SPREADWRAPPER_TMPDIR here.

SPREADWRAPPER_VERSION=1.4
SPREADWRAPPER_DIR=SpreadModule-$(SPREADWRAPPER_VERSION)
SPREADWRAPPER_ARCHIVE=$(SPREADWRAPPER_DIR).tgz
SPREADWRAPPER_REQUIRED_FILES=tmp/$(SPREADWRAPPER_ARCHIVE)

REQUIRED_FILES=$(SPREADWRAPPER_REQUIRED_FILES)

SPREADWRAPPER_TMPDIR=src/tmp/spreadwrapper-install

# Unpack the tarball into src/.
build_spreadwrapper: $(SRC_DIR)/$(SPREADWRAPPER_DIR)/spreadmodule.c

# Copy the Windows stuff into the build tree.
install_spreadwrapper: $(BUILD_DIR)/lib/python/spread.pyd \
		       $(BUILD_DIR)/lib/python/SpreadTest/testspread.py \
		       $(BUILD_DIR)/doc/spreadwrapper_doc.txt \
		       $(BUILD_DIR)/doc/SPREADWRAPPER_LICENSE.txt \
		       $(BUILD_DIR)/doc/SPREADWRAPPER_README.txt


$(SRC_DIR)/$(SPREADWRAPPER_DIR)/spreadmodule.c: tmp/$(SPREADWRAPPER_ARCHIVE)
	$(MKDIR) "$(SRC_DIR)"
	$(TAR) -C "$(SRC_DIR)" -xvzf $<
	$(TOUCH) $@

# A dumb trick so we don't unpack the tarball multiple times.
$(SRC_DIR)/$(SPREADWRAPPER_DIR)/doc.txt \
$(SRC_DIR)/$(SPREADWRAPPER_DIR)/LICENSE \
$(SRC_DIR)/$(SPREADWRAPPER_DIR)/README \
$(SRC_DIR)/$(SPREADWRAPPER_DIR)/testspread.py \
		: $(SRC_DIR)/$(SPREADWRAPPER_DIR)/spreadmodule.c
	$(TOUCH) $@


$(SPREADWRAPPER_TMPDIR)/Lib/site-packages/spread.pyd: $(SRC_DIR)/$(SPREADWRAPPER_DIR)/spreadmodule.c
	$(CD) $(SRC_DIR)/$(SPREADWRAPPER_DIR); \
		$(BUILD_DIR)/bin/python.exe setup.py install \
			--prefix=../../$(SPREADWRAPPER_TMPDIR)

$(BUILD_DIR)/lib/python/spread.pyd: $(SPREADWRAPPER_TMPDIR)/Lib/site-packages/spread.pyd
	$(MKDIR) $(@D)
	$(CP) $< $@
	$(TOUCH) $@

$(BUILD_DIR)/doc/spreadwrapper_doc.txt: $(SRC_DIR)/$(SPREADWRAPPER_DIR)/doc.txt
	$(COPY_AND_WINDOWIZE_LINEENDS)

$(BUILD_DIR)/doc/SPREADWRAPPER_LICENSE.txt: $(SRC_DIR)/$(SPREADWRAPPER_DIR)/LICENSE
	$(COPY_AND_WINDOWIZE_LINEENDS)

$(BUILD_DIR)/doc/SPREADWRAPPER_README.txt: $(SRC_DIR)/$(SPREADWRAPPER_DIR)/README
	$(COPY_AND_WINDOWIZE_LINEENDS)

$(BUILD_DIR)/lib/python/SpreadTest/testspread.py: $(SRC_DIR)/$(SPREADWRAPPER_DIR)/testspread.py
	$(COPY_AND_WINDOWIZE_LINEENDS)
