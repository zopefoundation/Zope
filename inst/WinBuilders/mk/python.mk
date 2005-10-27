# The Python and pywin32 versions.  For Python, both the source tarball
# and the Windows installer must be in tmp/.  For pywin32 (previously known 
# as win32all), the Windows installer must be in tmp/.  Nothing beyond those
# is required to build Python, and you don't even need a compiler.
PYVERSION_MAJOR=2
PYVERSION_MINOR=3
PYVERSION_PATCH=5
PYVERSION=$(PYVERSION_MAJOR).$(PYVERSION_MINOR).$(PYVERSION_PATCH)
W32ALLVERSION=205

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
# pywin32 doesn't have this problem as it now uses
# a standard distutils 'bdist_wininst' installation .exe. These executables are
# valid .zip files with a "PLATLIB" directory being the complete directory
# structure as installed into "site-packages". These recent pywin32 builds have
# no dependencies on registry settings etc so will work directly as copied out of
# the .exe. The only concerns are the pywintypes/pythoncom dlls, which is
# handled by the Inno installer

PYDIRNAME=Python-$(PYVERSION)
# Standard bdist_wininst name - eg: pywin32-203.win32-py2.3[.exe]
W32ALLDIRNAME=pywin32-$(W32ALLVERSION).win32-py$(PYVERSION_MAJOR).$(PYVERSION_MINOR)
W32EXCLUDE=*.chm

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
ARB_W32EXTRACTDIR=$(W32EXTRACTDIR)/PLATLIB

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

# unzip warns about .exe not being exactly a .zip, then succeeds in
# extracting the files, then returns with exit != 0 - ignore exit code
$(ARB_W32EXTRACTDIR): tmp/$(W32ALLDIRNAME).exe
	-$(UNZIP) -o "-d$(W32EXTRACTDIR)" "tmp/$(W32ALLDIRNAME).exe"
	cd "$(WIN_W32EXTRACTDIR)\PLATLIB" ; $(RMRF) $(W32EXCLUDE)
	$(TOUCH) "$(ARB_W32EXTRACTDIR)"

$(BUILD_DIR)/bin/python.exe:
	$(MKDIR) "$(BUILD_DIR)"

	$(MKDIR) "$(BUILD_DIR)/doc"
	$(CP) "$(MAKEFILEDIR)/doc/ZC_PY_DIST_README.txt" "$(BUILD_DIR)/doc"
	$(CP) "$(PYSRCDIR)/LICENSE" "$(BUILD_DIR)/doc/PYTHON_LICENSE.txt"
	unix2dos "$(BUILD_DIR)/doc/PYTHON_LICENSE.txt"

	$(MKDIR) "$(BUILD_DIR)/bin/DLLs"
	$(XCOPY) "$(WIN_PYEXTRACTDIR)\*.pyd" "$(WIN_BUILD_DIR)\bin\DLLs"

	$(MKDIR) "$(BUILD_DIR)/bin/Lib"
	$(XCOPY) "$(WIN_PYSRCDIR)\Lib\*.py" "$(WIN_BUILD_DIR)\bin\Lib"
	$(MKDIR) "$(BUILD_DIR)/bin/Lib/site-packages"
	$(CP) "$(PYSRCDIR)/Lib/site-packages/README" \
	      "$(BUILD_DIR)/bin/Lib/site-packages"
	$(XCOPY) "$(WIN_W32EXTRACTDIR)\PLATLIB" \
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

