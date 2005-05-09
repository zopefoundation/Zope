# The Python and win32all versions.  For Python, both the source tarball
# and the Windows installer must be in tmp/.  For win32all, the Windows
# installer must be in tmp/.  Nothing beyond those is required to
# build Python, and you don't even need a compiler for this part.
PYVERSION=2.3.5
W32ALLVERSION=163

# CAUTION:  Extracting files from Wise installers doesn't really do what
# you expect.  While a Wise installer is a zip file, the zip file
# structure is flat (Wise reconstructs the intended directory structure
# from metadata stored in proprietary FILEnnnn.DAT files also in the
# zip file).  Consequently, the package structure of Python packages is
# lost, and if there's more than one file with the same name, you only
# get "the last one" to be extracted (all files are extracted to the
# same directory).
#
# For Python, this doesn't matter, because we're only sucking out the
# precompiled .pyd and .exe files from the Python installer -- there
# are no name clashes in that set, and it's a pretty safe bet there never
# will be (else Python wouldn't be able to decide which to use!).  We
# use the Python source tarball to get all the non-executable parts we
# need.
#
# For win32all, I'm not sure what all the consequences are.  Zope has
# gotten away with it so far.  Favoring it, Zope makes little use of
# win32all.  Against it, there's (as of the time of this writing) little
# field experience with Windows Zope after Python 2.1.  Python and
# win32all have both gotten hairier since then, and win32all has
# significant package structure with many instances of files with the
# same name in different subtrees.  For now it's poke-and-hope.

PYDIRNAME=Python-$(PYVERSION)
W32ALLDIRNAME=win32all-$(W32ALLVERSION)

# The Python tarball is extracted to PYSRCDIR.
# The contents of the Python installer get extracted to PYEXTRACTDIR.
# The    "      "  "  win32all   "      "     "       " W32EXTRACTDIR.
PYSRCDIR=$(BASE_DIR)/src/$(PYDIRNAME)
PYEXTRACTDIR=$(BASE_DIR)/src/$(PYDIRNAME)-extract
W32EXTRACTDIR=$(BASE_DIR)/src/$(W32ALLDIRNAME)

WIN_PYSRCDIR=$(shell cygpath -w $(PYSRCDIR))
WIN_PYEXTRACTDIR=$(shell cygpath -w $(PYEXTRACTDIR))
WIN_W32EXTRACTDIR=$(shell cygpath -w $(W32EXTRACTDIR))

PYTHON_REQUIRED_FILES=tmp/$(W32ALLDIRNAME).exe \
                      tmp/$(PYDIRNAME).tgz \
                      tmp/$(PYDIRNAME).exe

# Arbitrary files from each of the installers and tarballs, to use as
# targets to force them to get unpacked.
ARB_PYSRCDIR=$(PYSRCDIR)/PCbuild/pcbuild.dsw
ARB_PYEXTRACTDIR=$(PYEXTRACTDIR)/zlib.pyd
ARB_W32EXTRACTDIR=$(W32EXTRACTDIR)/readme.txt

# Building Python just consists of extracting files.
build_python: $(ARB_PYSRCDIR) $(ARB_PYEXTRACTDIR) $(ARB_W32EXTRACTDIR)

# Installing Python consists of copying oodles of files into
# $(BUILD_DIR).
install_python: $(BUILD_DIR)/bin/python.exe

clean_python:
	$(RMRF) $(PYSRCDIR)
	$(RMRF) $(PYEXTRACTDIR)

clean_libs:
	$(RMRF) $(W32EXTRACTDIR)

$(ARB_PYSRCDIR): tmp/$(PYDIRNAME).tgz
	$(MKDIR) "$(SRC_DIR)"
	$(CD) "$(SRC_DIR)" && $(TAR) xvzf ../tmp/$(PYDIRNAME).tgz
	$(TOUCH) "$(ARB_PYSRCDIR)"

$(ARB_PYEXTRACTDIR): tmp/$(PYDIRNAME).exe
	$(MKDIR) "$(PYEXTRACTDIR)"
	"tmp/$(PYDIRNAME).exe" /S /X "$(WIN_PYEXTRACTDIR)"
	$(TOUCH) "$(ARB_PYEXTRACTDIR)"

$(ARB_W32EXTRACTDIR): tmp/$(W32ALLDIRNAME).exe
	$(MKDIR) "$(W32EXTRACTDIR)"
	"tmp/$(W32ALLDIRNAME).exe" /S /X "$(WIN_W32EXTRACTDIR)"
	$(TOUCH) "$(ARB_W32EXTRACTDIR)"

$(BUILD_DIR)/bin/python.exe:
	$(MKDIR) "$(BUILD_DIR)"

	$(MKDIR) "$(BUILD_DIR)/doc"
	$(CP) "$(MAKEFILEDIR)/doc/ZC_PY_DIST_README.txt" "$(BUILD_DIR)/doc"
	$(CP) "$(PYSRCDIR)/LICENSE" "$(BUILD_DIR)/doc/PYTHON_LICENSE.txt"
	unix2dos "$(BUILD_DIR)/doc/PYTHON_LICENSE.txt"
	$(CP) "$(SRC_DIR)/$(W32ALLDIRNAME)/License.txt" \
	      "$(BUILD_DIR)/doc/WIN32ALL_LICENSE.txt"

	$(MKDIR) "$(BUILD_DIR)/bin/DLLs"
	$(XCOPY) "$(WIN_PYEXTRACTDIR)\*.pyd" "$(WIN_BUILD_DIR)\bin\DLLs"

	$(MKDIR) "$(BUILD_DIR)/bin/Lib"
	$(XCOPY) "$(WIN_PYSRCDIR)\Lib\*.py" "$(WIN_BUILD_DIR)\bin\Lib"
	$(MKDIR) "$(BUILD_DIR)/bin/Lib/site-packages"
	$(CP) "$(PYSRCDIR)/Lib/site-packages/README" \
	      "$(BUILD_DIR)/bin/Lib/site-packages"
	$(XCOPY) "$(WIN_W32EXTRACTDIR)\*.pyd" \
	         "$(WIN_BUILD_DIR)\bin\Lib\site-packages"
	$(XCOPY) "$(WIN_W32EXTRACTDIR)\*.dll" \
		 "$(WIN_BUILD_DIR)\bin\Lib\site-packages"
	$(XCOPY) "$(WIN_W32EXTRACTDIR)\*.exe" \
		 "$(WIN_BUILD_DIR)\bin\Lib\site-packages"
	$(XCOPY) "$(WIN_W32EXTRACTDIR)\*.py" \
		 "$(WIN_BUILD_DIR)\bin\Lib\site-packages"

	$(CP) "$(MAKEFILEDIR)/etc/sitecustomize.py" \
	      "$(BUILD_DIR)/bin/Lib/site-packages"

	$(MKDIR) "$(BUILD_DIR)/bin/Include"
	$(XCOPY) "$(WIN_PYSRCDIR)\Include\*.h" "$(WIN_BUILD_DIR)\bin\Include"
	$(XCOPY) "$(WIN_PYSRCDIR)\PC\*.h" "$(WIN_BUILD_DIR)\bin\Include"

	$(MKDIR) "$(BUILD_DIR)/bin/libs"
	$(CP) "$(PYEXTRACTDIR)/python23.lib" "$(BUILD_DIR)/bin/libs"

	$(MKDIR) "$(BUILD_DIR)/bin"
	$(CP) "$(PYEXTRACTDIR)/pythonw.exe" "$(BUILD_DIR)/bin"
	$(CP) "$(PYEXTRACTDIR)/w9xpopen.exe" "$(BUILD_DIR)/bin"
	$(CP) "$(PYEXTRACTDIR)/python23.dll" "$(BUILD_DIR)/bin"
	$(CP) "$(PYEXTRACTDIR)/python.exe" "$(BUILD_DIR)/bin"
	$(TOUCH) "$(BUILD_DIR)/bin/python.exe"

