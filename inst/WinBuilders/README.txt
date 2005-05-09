Quick instructions:

The installers have only been tested under Windows 2K, but should work
without incident on XP.  It "almost works" on Win98SE (see bottom of
file for discussion).

Install Cygwin from cygwin.org (the default installation should give
you everything you need).

Install Microsoft Visual C++ 6.0.

Install InnoSetup 4.0 from www.jrsofware.org (into its default location).
4.0.4-beta seems to work, while 4.0.7 does not.  Symptom: type error
on compilation.  4.0.11 appears to work.

Unpack this package into a directory.

Launch a Cygwin bash shell.  If necessary, run the VCVARS.bat to set up
the VC++ environment.  This shouldn't be necessary on Win2K, provided
you've brought up the GUI at least once (MSDev doesn't finish writing
all the registry keys it should until the GUI is first launched).  See
below for Win98SE.

If you're building Zope against Python 2.3.X, you may need to add some
registry entries due to a bug in the distutils msvccompiler.py:

[HKEY_CURRENT_USER\Software\Microsoft\DevStudio\6.0\Build System\Components\Platforms\Win32 (x86)\Directories]
"path dirs"="c:\\windows\\system32;c:\\Program Files\\Microsoft Visual Studio\\Common\\Tools\\WinNT; c:\\Program Files\\Microsoft Visual Studio\\Common\\MSDev98\\Bin;c:\\Program Files\\Microsoft Visual Studio\\Common\\Tools;c:\\Program Files\\Microsoft Visual Studio\\VC98\\bin"
"library dirs"="C:\\Program Files\\Microsoft Visual Studio\\VC98\\mfc\\lib;C:\\Program Files\\Microsoft Visual Studio\\VC98\\lib"
"include dirs"="C:\\Program Files\\Microsoft Visual Studio\\VC98\\atl\\include;C:\\Program Files\\Microsoft Visual Studio\\VC98\\mfc\\include;C:\\Program Files\\Microsoft Visual Studio\\VC98\\include"

This is unecessary if building against Python 2.2.X.  [Tim didn't find
this necessary building against Python 2.3.3 and Christian against 2.3.4 either.]

From the parent directory of the package, make a "tmp" directory.

Get necessary source packages and place them in the tmp directory.  At the time
of this writing, this includes:

  - Python-2.3.4.tgz
  - Python-2.3.4.exe (used for binary modules)
  - win32all-163.exe
  - Zope.tgz

As time marches on, these version numbers will obviously change.

If you see any make errors with references to one of these files, it's because
you've not downloaded them or you've not placed them in 'tmp'.

From the parent directory of the package, type WinBuilders/buildout <type>
where type is one of "python", "zope", or "zeo".

For python, the buildout populates the "build" directory with a Python
laid out for Zope and/or ZEO.

For 'zope', the buildout populates the "build" directory with a Windows
executable installer (read the Makfile.zope for special instructions).

For 'zeo', the buildout populates the "build" directory with a Windows
executable installer (read the Makefile.zeo for special instructions).



Win98SE notes
-------------
- You have to run vcvars32.bat to set up envars for MSVC 6.  Running that
  from a bash shell doesn't have any effect on the Cygwin PATH.
  This works:

+ Open a native DOS box.
+ Run vcvars32.bat.
+ Start a bash shell from the same box (== run cygwin.bat, found in the
  root of your Cygwin installation -- the same thing the Cygwin shell
  desktop shortcut resolves to, so you can get the exact path by looking
  at the icon's Properties).

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
