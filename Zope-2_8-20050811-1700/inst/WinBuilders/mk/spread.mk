# Justs repackages the Spread binaries.
# Puts binaries into build/bin, and some docs into build/doc.

# See README.txt for system requirements.

# Download the binary distribution of Spread, from http://www.spread.org/.
# Store it in tmp/.  NOTE:  May need to rename it to .tgz (depends on how
# it's downloaded).  The name is of the form spread-bin-n.nn.n.tgz

SPREAD_VERSION=3.17.1
SPREAD_DIR=spread-bin-$(SPREAD_VERSION)
SPREAD_ARCHIVE=$(SPREAD_DIR).tgz
SPREAD_REQUIRED_FILES=tmp/$(SPREAD_ARCHIVE)

REQUIRED_FILES=$(SPREAD_REQUIRED_FILES)

# Unpack the tarball into src/.
build_spread: $(SRC_DIR)/$(SPREAD_DIR)/win/spread.exe

$(SRC_DIR)/$(SPREAD_DIR)/win/spread.exe : tmp/$(SPREAD_ARCHIVE)
	$(MKDIR) "$(SRC_DIR)"
	$(TAR) -C "$(SRC_DIR)" -xvzf tmp/$(SPREAD_ARCHIVE)
	$(TOUCH) $@

# A dumb trick so we don't unpack the tarball multiple times.
$(SRC_DIR)/$(SPREAD_DIR)/license.txt \
$(SRC_DIR)/$(SPREAD_DIR)/Readme.txt \
$(SRC_DIR)/$(SPREAD_DIR)/sample.spread.conf \
		: $(SRC_DIR)/$(SPREAD_DIR)/win/spread.exe
	$(TOUCH) $@

# Copy the Windows stuff from src/ into build/bin/ and build/doc
install_spread: $(BUILD_DIR)/bin/spread.exe \
		$(BUILD_DIR)/bin/sprecv.exe \
		$(BUILD_DIR)/bin/spsend.exe \
		$(BUILD_DIR)/bin/sptuser.exe \
		$(BUILD_DIR)/bin/spflooder.exe \
		$(BUILD_DIR)/doc/SPREAD_LICENSE.txt \
		$(BUILD_DIR)/doc/SPREAD_README.txt \
		$(BUILD_DIR)/doc/sample.spread.conf


$(BUILD_DIR)/bin/spread.exe \
$(BUILD_DIR)/bin/sprecv.exe \
$(BUILD_DIR)/bin/spsend.exe \
$(BUILD_DIR)/bin/sptuser.exe \
$(BUILD_DIR)/bin/spflooder.exe : $(BUILD_DIR)/bin/% : \
				 $(SRC_DIR)/$(SPREAD_DIR)/win/%
	$(MKDIR) $(@D)
	$(CP) $< $@
	$(TOUCH) $@

$(BUILD_DIR)/doc/SPREAD_LICENSE.txt: $(SRC_DIR)/$(SPREAD_DIR)/license.txt
	$(COPY_AND_WINDOWIZE_LINEENDS)

$(BUILD_DIR)/doc/SPREAD_README.txt: $(SRC_DIR)/$(SPREAD_DIR)/Readme.txt
	$(COPY_AND_WINDOWIZE_LINEENDS)

$(BUILD_DIR)/doc/sample.spread.conf: $(SRC_DIR)/$(SPREAD_DIR)/sample.spread.conf
	$(COPY_AND_WINDOWIZE_LINEENDS)
