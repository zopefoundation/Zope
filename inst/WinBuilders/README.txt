Quick instructions:

The buildout has been tested under Windows 2K and XP Pro SP2.


Setup Environment
------------------

Install Python 2.4.3 (or whatever is most current) by running its native
Windows installer from python.org.

    Note:  Python 2.4 switched from using a Wise installer to using a
    Microsoft .msi installer, and the latter is harder to work with.  The
    buildout used to extract Python source and binaries (.exe, .pyd, .dll)
    from the Wise installer (which could be treated much like a zip file).
    Now the Python installer isn't used at all.  Instead, the Python
    source is taken from the Python tarball release, and the binaries are
    copied from your installed Python.

Install Cygwin from cygwin.org (the default installation should give
you everything you need).

Install Microsoft Visual C++ 7.1 (aka Visual Studio .NET 2003).  This is
needed to compile Zope's Python C extensions compatible with Python 2.4
(and 2.5, when that's released).

Install InnoSetup 5.1.5 (or later) from www.jrsoftware.org, into its
default location.  Inno 4.x (or earlier) cannot work:  Inno 5 introduced a
vastly simpler way to create the custom dialog pages we want.

'svn switch' to, or check out, the Zope tag for which an installer is to be
built.

Within a Zope checkout, the parent directory of this package is inst.  Make
a "tmp" directory, inst/tmp.  Place the necessary pre-requisites in the tmp
directory.  At the time of this writing, these are:

  - Python-2.4.3.tgz
  - pywin32-208.win32-py2.4.exe
  - Zope-2.9.3.tgz

As time marches on, these version numbers will obviously change.  See/edit
mk/python.mk and mk/zope.mk for the exact versions required.

You also need to install the same Windows Python that Zope will repackage.
There doesn't appear to be a sane way to extract binaries (.exe, .pyd,
.dll, .lib) from an .msi installer, and building Python from source is a long
& messy process on Windows.  So python.mk just copies them from an installed
Python instead.  Cautions:

- If you didn't accept the Python installer's default directory, or if
  you did but it's on a different drive, you'll need to change
  WIN_PYINSTALLEDDIR in python.mk.

- The main Python DLL must live in WIN_PYINSTALLEDDIR too.  Depending on
  how you installed Python, that may be sitting in some Windows system
  directory instead; if so, make a copy in the root of your Python
  installation.

  Places you may want to hunt for python24.dll:

  C:\Program Files
  C:\Windows\System32

  Place you most likely want to copy it to:

  C:\Python24

Building
--------

Launch a Cygwin bash shell, and from the parent directory (inst/) type:

    WinBuilders/buildout <type>

where type is one of "zope", "python", or "zeo".  Alternatively, you can
avoid the bash shell completely, and from a Windows command prompt type:

    bash WinBuilders/buildout <type>

Everything should work!

  * For 'zope', the buildout populates the "build" directory with a Windows
    executable installer.

  * For python, the buildout populates the "build" directory with a Python
    laid out for Zope and/or ZEO.  [Tim isn't sure this target has ever
    been tested/used.]

  * For 'zeo', the buildout populates the "build" directory with a Windows
    executable installer.   [Tim isn't sure this target has ever been
    tested/used.]

An 'inst\src' directory is also created.  The makefiles don't even pretend to
do a good job of keeping track of dependencies; best practice is to blow away
the 'build' and 'src' directories between runs.  Note that the 'tmp'
directory should _not_ be deleted -- it's purely an input to this process.

If the build fails:

If the Windows drive you are working on is not C: (or Inno isn't installed
there!), try executing the following:

    WinBuilders/buildout <type> CYGROOT=/cygdrive/{your_drive_letter}

If you see errors relating to MSVC not being installed, or the build process
failing to find MSVC, it may be necessary to bring up the MSVC gui
at least once (MSDev doesn't finish writing all the registry keys it should
until the GUI is first launched).  If may also be necessary to run VCVARS.bat
to set up the VC++ environment (but generally is not.)  See below for Win98SE.

If you see any make errors with references to any of the files required
in tmp/ (see 'Setup Environment' above), it's because a later version is
now required, or the files you've downloaded are not in 'tmp'.


Testing Zope
------------

XXX This doesn't work right starting with Zope 2.9:  it's clumsier than it
XXX should be, and the functional tests don't even try to run (just the
XXX unit tests).
XXX Someone who understands how Zope3 testing from a zpkgtools-tarball build
XXX was made to work again may be able to help here.

The test suite can be run from inst\build\, after building the installer.

- Open a native (not Cygwin) DOS box.  We want to test with the Python the
  Zope installer includes, in an all-native environment, to match what
  the installer-installed code will do as closely as possible.

- cd inst\build

- Copy log.ini from the root of the Zope _checkout_ -- it's not included
  in the tarball::

      copy ..\..\log.ini .

  Copying log.ini isn't necessary for the tests to pass, but if you don't
  do it a great many spurious log messages will be displayed on the
  console, some of which "look like" errors (some of the tests deliberately
  provoke errors).

- Copy test.py from the unpacked tarball::

      copy ..\src\$(ZOPE_VERSION)\test.py .

- Enter::

      bin\python test.py -vv -m "!^zope[.]app[.]" --all

  or whatever variation you like best.  All tests should pass.

  Note that zope.app tests should be excluded because not all of them _can_
  pass (this isn't "a Windows thing", it's a temporary all-platform wart
  due to missing bits from Zope3).

Also run the Windows installer, and play with the Zope it installs.


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
