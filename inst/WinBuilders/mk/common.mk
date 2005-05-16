BASE_DIR=$(shell pwd)
WIN_BASE_DIR=$(shell cygpath -w $(BASE_DIR))
BUILD_DIR=$(BASE_DIR)/build
WIN_BUILD_DIR=$(shell cygpath -w $(BUILD_DIR))
SRC_DIR=$(BASE_DIR)/src
WIN_SRC_DIR=$(shell cygpath -w $(SRC_DIR))
TMP_DIR=$(BASE_DIR)/tmp
WIN_TMP_DIR=$(shell cygpath -w $(TMP_DIR))
WIN_MAKEFILEDIR=$(shell cygpath -w $(MAKEFILEDIR))

# Root of the Windows drive you're working on.  The setting here is for
# the C: drive and using a default out-of-the-box Cygwin.
CYGROOT=/cygdrive/c

RM=rm -f
RMRF=rm -rf
CD=cd

XCOPY=xcopy /i /s /e /y

CPR=cp -r
CP=cp
MKDIR=mkdir -p
CVS="$(MAKEFILEDIR)/bin/cvs.exe"
TAR=tar
SED=sed
TOUCH=touch
NMAKE=nmake
CSCRIPT=cscript
ECHO=echo
ISS_DIR=$(CYGROOT)/Progra~1/Inno Setup 4
ISS_COMPILER=$(ISS_DIR)/Compil32.exe
# We need a version that understands cygwin paths, so /bin/
UNZIP=/bin/unzip

$(REQUIRED_FILES):
	if [ -z "$(BASE_DIR)/$@" ]; then echo. &echo. & echo \
                   You must download $(@F) and place it in "$(BASE_DIR)/tmp" &\
                   error 1; fi

PRODUCTS_DIR=build/instance/Products

PYLIBDIR=build/instance/lib/python

ZOPE_CVS_REPOSITORY=:pserver:anonymous@cvs.zope.org:/cvs-repository

CVS=/usr/bin/cvs -z7 -q
CVS_UPDATE=${CVS} update -dP

CVSROOT=:ext:korak.zope.com:/cvs-turbointranet

# Use COPY_AND_WINDOWIZE_LINEENDS like so:
#
#     destination_path: source_path
#               $(COPY_AND_WINDOWIZE_LINEENDS)
#
# Any directories needed to hold destination_path are created.  The file
# is copied from source_path to there, and unix2dos is run on it in its
# new home.  The paths must give file names, not directories; this reflects
# that renaming of files is often needed in these makefiles.
define COPY_AND_WINDOWIZE_LINEENDS
	$(MKDIR) $(@D)
	$(CP) $< $@
	unix2dos $@
	$(TOUCH) $@
endef