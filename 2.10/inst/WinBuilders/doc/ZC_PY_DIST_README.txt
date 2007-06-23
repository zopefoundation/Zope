The version of Python shipped in this package has been compiled for
win32 using Microsoft's Visual C++ 6.0.  There are differences between
the Win32 Python version shipped with Zope and ZEO (the "ZC" version)
and the version available from the Python.org website:

- The ZC version does not write the same registry entries as the
  Python.org distribution.

- The ZC version includes Mark Hammond's win32all package, although the
  package structure is lost, and whenever there's more than one file
  with the same name in win32all only one of them gets included here.
  This ought to be fixed, but the uses Zope makes of win32all appear
  not to care about the ways in which the win32all installation is
  flawed.

- The Doc, Tools and Script directories aren't installed.

- Tcl/Tk is not included.

- Python's Lib/test directory doesn't contain enough to run the Python
  tests successfully (the expected-output subdirectory isn't installed,
  and various test-input data files aren't installed -- only .py files
  are installed).
