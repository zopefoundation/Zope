Quick instructions:

The installers have only been tested under Windows 2K, but should work
without incident on XP.  It "almost works" on Win98SE (see bottom of
file for discussion).

Setup Environment
------------------

Install Cygwin from cygwin.org (the default installation should give
you everything you need).

Install Microsoft Visual C++ 6.0 (or MSVC 7 once we get to Python 2.4)

Install InnoSetup 4.2 from www.jrsofware.org (into its default location).
Versions earlier than 4.0.11 are known to not work; any 4.2.x release
or later should be fine.  Inno 5.x versions do *not* work (it appears the
Inno "custom dialog" mechanism has changed in an incompatible way)

From the parent directory of the package, make a "tmp" directory.  Place
the necessary pre-requisites in this directory.  At the time of this writing,
this includes:

  - Python-2.3.5.tgz
  - Python-2.3.5.exe (used for binary modules)
  - pywin32-204.win32-py2.3.exe (extracts binaries and sources)
  - Zope.tgz

As time marches on, these version numbers will obviously change.  See
mk/python.mk for the exact versions required.

Building
--------
Launch a Cygwin bash shell, and from the parent directory, type:
  WinBuilders/buildout <type>
where type is one of "python", "zope", or "zeo".  Alternatively, you can
avoid the bash shell completely, and from a Windows command prompt type:
  bash WinBuilders/buildout <type>

Everything should work!
  * For python, the buildout populates the "build" directory with a Python
    laid out for Zope and/or ZEO.

  * For 'zope', the buildout populates the "build" directory with a Windows
    executable installer (read the Makefile.zope for special instructions).

  * For 'zeo', the buildout populates the "build" directory with a Windows
   executable installer (read the Makefile.zeo for special instructions).

If the build fails:

If the Windows drive you are working on is not C: (or Inno isn't installed
there!), try executing the following:
  WinBuilders/buildout <type> CYGROOT=/cygdrive/{your_drive_letter}

If you see errors relating to MSVC not being installed, or the build process
failing to find MSVC, it may be necessary to bring up the MSVC gui
at least once (MSDev doesn't finish writing
all the registry keys it should until the GUI is first launched).  If may
also be necessary to run VCVARS.bat to set up the VC++ environment (but
generally is not.)  See below for Win98SE.

If you see any make errors with references to any of the files required
in tmp/ (see 'Setup Environment' above), it's because a later version is
now required, or the files you've downloaded are not in 'tmp'.

All platform notes
------------------
- Depending on your MSVC installation options, you have to run vcvars32.bat
  to set up envars for MSVC.  Running that from a bash shell doesn't have any
  effect on the Cygwin PATH. This works:

+ Open a native DOS box.
+ Run vcvars32.bat.
+ Start a bash shell from the same box (== run cygwin.bat, found in the
  root of your Cygwin installation -- the same thing the Cygwin shell
  desktop shortcut resolves to, so you can get the exact path by looking
  at the icon's Properties).

Win98SE notes
-------------
- Every time a makefile runs xcopy, there's a segfault in kernel32.dll,
  which hangs the bash shell with an endless succession of error boxes.
  The only way I found to break out of this was to bring up the debugger,
  close it, then type Ctrl+C at the hung bash shell.  The bash shell
  appears to be fine at that point, but you can never close it (short of
  killing it via the task manager).
  Same thing if xcopy32 is used instead.
  xcopy works OK directly from a bash shell.  The segfaults occur if it's
  run via a makefile, or via a shell script.  Guessing a problem with I/O
  redirection, since some other apps can't see keyboard input before the
  hung stuff is killed.

  Workaround:  xxcopy works fine <http://www.xxcopy.com/>; free for
  personal use, but not for commercial use.  Rename it to xcopy.exe and
  get it into your path before the native xcopy, or fiddle the XCOPY
  defn in common.mk to use xxcopy instead of xcopy.
