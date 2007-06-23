# The Python and pywin32 versions.
#
# For Python, the source tarball must be in tmp/.  You must also install the
# appropriate Python on Windows, and set WIN_PYINSTALLEDDIR here to its root
# directory.  A copy of the main Python DLL must also be in the root (you
# may need to copy it from your Windows system directory).  Earlier versions
# of this extracted .dll, .exe, and .pyd files from Python's Wise installer,
# but Python 2.4 uses an .msi installer, and there doesn't appear to be a
# way to _just_ extract files from one of those.
#
# For pywin32 (previously known as win32all), the Windows installer must be
# in tmp/.
#
# Nothing beyond those is required to build Python, and you don't even need
# a compiler.
PYVERSION_MAJOR := 2
PYVERSION_MINOR := 4
PYVERSION_PATCH := 3
W32ALLVERSION := 208

PYVERSION := $(PYVERSION_MAJOR).$(PYVERSION_MINOR).$(PYVERSION_PATCH)

PYMAJORMINOR := python$(PYVERSION_MAJOR)$(PYVERSION_MINOR)

# This is the default directory into which a Python installs.
WIN_PYINSTALLEDDIR := \$(PYMAJORMINOR)

# pywin32 now uses a standard distutils 'bdist_wininst' installation .exe.
# These executables are valid .zip files with a "PLATLIB" directory being
# the complete directory structure as installed into "site-packages".  These
# recent pywin32 builds have no dependencies on registry settings etc so
# will work directly as copied out of the .exe.  The only concerns are the
# pywintypes/pythoncom dlls, which are handled by the Inno installer.

PYDIRNAME := Python-$(PYVERSION)
# Standard bdist_wininst name - eg: pywin32-203.win32-py2.3
W32ALLDIRNAME := pywin32-$(W32ALLVERSION).win32-py$(PYVERSION_MAJOR).$(PYVERSION_MINOR)
W32EXCLUDE := *.chm

# The Python tarball is extracted to PYSRCDIR.
# pywin32 is extracted to W32EXTRACTDIR.
PYSRCDIR := $(BASE_DIR)/src/$(PYDIRNAME)
W32EXTRACTDIR := $(BASE_DIR)/src/$(W32ALLDIRNAME)

WIN_PYSRCDIR := $(shell cygpath -w $(PYSRCDIR))
WIN_W32EXTRACTDIR := $(shell cygpath -w $(W32EXTRACTDIR))

PYTHON_REQUIRED_FILES := tmp/$(W32ALLDIRNAME).exe \
			 tmp/$(PYDIRNAME).tgz

# Arbitrary files from each of the installers and tarballs, to use as
# targets to force them to get unpacked.
ARB_PYSRCDIR := $(PYSRCDIR)/PCbuild/pcbuild.dsw
ARB_W32EXTRACTDIR := $(W32EXTRACTDIR)/PLATLIB

# Building Python just consists of extracting files.
build_python: $(ARB_PYSRCDIR) $(ARB_W32EXTRACTDIR)

# Installing Python consists of copying oodles of files into
# $(BUILD_DIR).
install_python: $(BUILD_DIR)/bin/python.exe

clean_python:
	$(RMRF) $(PYSRCDIR)

clean_libs:
	$(RMRF) $(W32EXTRACTDIR)

# Fetch dependencies
tmp:
	$(MKDIR) tmp

$(ARB_PYSRCDIR): tmp/$(PYDIRNAME).tgz
	$(MKDIR) "$(SRC_DIR)"
	$(CD) "$(SRC_DIR)" && $(TAR) xzf ../tmp/$(PYDIRNAME).tgz
	$(TOUCH) "$(ARB_PYSRCDIR)"

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
	$(CP) "$(SRC_DIR)/$(W32ALLDIRNAME)/PLATLIB/pythonwin/License.txt" \
	      "$(BUILD_DIR)/doc/PYWIN32_LICENSE.txt"

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

	$(MKDIR) "$(BUILD_DIR)/bin"
	$(MKDIR) "$(BUILD_DIR)/bin/libs"
	$(MKDIR) "$(BUILD_DIR)/bin/DLLs"
	$(XCOPY) "$(WIN_PYINSTALLEDDIR)\python.exe" "$(WIN_BUILD_DIR)\bin"
	$(XCOPY) "$(WIN_PYINSTALLEDDIR)\pythonw.exe" "$(WIN_BUILD_DIR)\bin"
	$(XCOPY) "$(WIN_PYINSTALLEDDIR)\w9xpopen.exe" "$(WIN_BUILD_DIR)\bin"
	$(XCOPY) "$(WIN_PYINSTALLEDDIR)\$(PYMAJORMINOR).dll" \
						"$(WIN_BUILD_DIR)\bin"
	$(XCOPY) "$(WIN_MAKEFILEDIR)\bin\msvcr71.dll" "$(WIN_BUILD_DIR)\bin"
	$(XCOPY) "$(WIN_PYINSTALLEDDIR)\libs" "$(WIN_BUILD_DIR)\bin\libs"
	$(XCOPY) "$(WIN_PYINSTALLEDDIR)\DLLs\*.pyd" \
						"$(WIN_BUILD_DIR)\bin\DLLs"

	$(TOUCH) "$(BUILD_DIR)/bin/python.exe"
