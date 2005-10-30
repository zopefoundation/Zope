======
Zope 3
======

Welcome to the Zope 3 distribution!

Zope 3 is the next major Zope release and has been written from
scratch based on the latest software design patterns and the
experiences of Zope 2.


Requirements
------------

Zope 3 requires that Python 2.4.1 or newer be installed.

Building the Zope 3 software requires a C compiler supported by the distutils.


Building and installing the software
------------------------------------

Unix
~~~~

Zope 3 is built using the conventional `configure`/`make` pattern on Unix and
Linux.  There are only a couple of options to the configure script, but you
shouldn't need either of them in the common case.  The `configure` script will
attempt to locate the available Python installations and pick the best one for
use with Zope::

  $ ./configure

  Configuring Zope 3 installation

  Testing for an acceptable Python interpreter...

  Python version 2.3.5 found at /usr/local/bin/python
  Python version 2.4.1 found at /usr/local/bin/python2.4

  The optimum Python version (2.4.1) was found at /usr/local/bin/python2.4.

If you want to specify which Python should be used with Zope, use the
`--with-python` option to indicate the specific Python interpreter to use::

  $ ./configure --with-python /opt/Python-2.4.1/bin/python

  Using Python interpreter at /opt/Python-2.4.1/bin/python

  Configuring Zope 3 installation

The default installation directory for Zope is ``/usr/local/Zope-<version>``,
where ``<version>`` is replaced with the version of Zope 3 you're installing;
it will match the version number from the compressed tarball you unpacked.  To
change the installation directory, use the ``--prefix`` option to specify an
alternate location:

  $ ./configure --prefix /opt/Zope-3.2.0

  Configuring Zope 3 installation

  Testing for an acceptable Python interpreter...

  Python version 2.3.5 found at /usr/local/bin/python
  Python version 2.4.1 found at /usr/local/bin/python2.4

  The optimum Python version (2.4.1) was found at /usr/local/bin/python2.4.

If you want to use the same prefix as a previous installation, you need to
remove the original installation first.  Instances created using one
installation may need to be modified to use a new installation.

Once you've configured Zope, you can build the software using ``make``.  No
options are needed.

  $ make
  python2.4 install.py -q build

Now that the software has been built, you can run the unit tests for the
software to make sure that everything is working on your platform.  This is an
optional step, and can take a while to complete.  The tests can be run using
``make`` as well::

  $ make check
  python2.4 install.py -q build
  python2.4 test.py -v
  Running UNIT tests at level 1
  Running UNIT tests from /home/user/Zope-3.2.0/build/lib.linux-i686-2.3
  [...lots of dots, one per test...]
  ----------------------------------------------------------------------
  Ran 8007 tests in 252.406s

  OK

  Running FUNCTIONAL tests at level 1
  Running FUNCTIONAL tests from /home/user/Zope-3.2.0/build/lib.linux-i686-2.3
  [...lots of dots, one per test...]
  ----------------------------------------------------------------------
  Ran 385 tests in 106.901s

  OK

The line before the final "OK" tells how many individual tests were run, and
long it took to run them.  These numbers will vary based on release, operating
system, and host platform.

To install the software, run ``make`` again::

  $ make install
  python2.4 install.py -q build
  python2.4 install.py -q install --home "/opt/Zope-3.2.0"

You now have a complete Zope 3 installation.


Windows (installer)
~~~~~~~~~~~~~~~~~~~

On Windows it's easiest to use the Windows installer.  The instructions here
assume you installed Python in its default location, ``\Python24``.

If you have a previous version of Zope 3 installed, use the Windows Control
Panel's Add/Remove Programs applet to uninstall the old version first. The
name of the appropriate entry starts with "Python 2.4 Zope 3-".

Run the installer.  Note that the installer creates an uninstallation program,
and an entry to run it under Control Panel's Add/Remove Programs applet.  This
will remove the files installed under ``\Python24``, but will not remove
anything in the instance directory (which you create next).

Change to the ``\Python24\Scripts`` directory and create an instance::

  ..\python mkzopeinstance -d <instance dir> -u <username>:<password>

Change to the instance directory (this is the new directory you specified as
the ``-d`` argument to ``mkzopeinstance``) and start Zope::

  \Python24\python bin/runzope


Windows (source)
~~~~~~~~~~~~~~~~

Using the source distribution on Windows is possible, but is somewhat
different from using the distribution on Unix.  You may want to use the
Windows installer instead of the source distribution.  If you don't have a
supported C compiler, you need to use the installer.

If you have previously installed Zope 3, either from source or using the
installer, you will need to remove the previous installation.

In using the distribution on Windows, you will need to run Python directly
several times with various command lines; you should be careful to use the
same Python installation for each of these.  The default installation for
Python 2.3.x on Windows places the Python interpreter at ``\Python24\python``;
this will be used in the examples, but you may need to use a different path to
the interpreter if you installed Python in a non-default location.  On
NT/2000/XP using cmd.exe, and if Python 2.4.x is associated with the .py
extension (the Python Windows installer does so by default), you can leave off
the ``\Python24\python `` at the start of each command line.

Build the Zope software by switching to the directory created by unpacking the
source distribution, then running the command::

  C:\Zope-3.2.0> \Python24\python install.py -q build

The unit tests for the Zope software can be run once this is complete.  This
is an optional step, and can take a while to complete.  The tests can be run
using the command::

  C:\Zope-3.2.0> \Python24\python test.py -v
  Running UNIT tests at level 1
  Running UNIT tests from C:\Zope-3.2.0\build\lib.win32-2.3
  [...lots of dots, one per test...]
  ----------------------------------------------------------------------
  Ran 4500 tests in 501.389s

  OK

The line before the final "OK" tells how many individual tests were run, and
how long it took to run them.  These numbers will vary based on release,
operating system, and host platform.

At this point, you can install the software using the command:

  C:\Zope-3.2.0> \Python24\python install.py -q install

You now have a complete Zope 3 installation.  Note that this method of
installing Zope does not allow for easy uninstallation later: you will need to
delete Zope files manually from your Python's ``Lib\site-packages\`` and
``Scripts\`` directories, and remove the directory zopeskel\ from your Python
installation entirely.  If you use the Windows installer instead, it creates
an uninstallation program, and an entry to run it in Control Panel's
Add/Remove Programs applet.


Creating a Zope instance home
-----------------------------

The Zope installation includes a script called ``mkzopeinstance``; this is
used to create a new "instance home."  On Unix, this will be in
``$prefix/bin/``, and on Windows this will be in ``Scripts\`` in the Python
installation.

Run this script to create the instance home::

  $ .../bin/mkzopeinstance -u username:password -d directory

or::

  C:\Python24\Scripts> ..\python mkzopeinstance -u username:password -d directory

This will create the directory named on the command line and provide a default
configuration. The configuration files for the Zope application server are in
the ``etc/`` sub-directory in the instance home. You should review those files
to make sure they meet your needs before starting the application server for
the first time. Of particular interest are the files ``zope.conf`` and
``principals.zcml``.


Starting Zope
-------------

XXX to be written


Where to get more information
-----------------------------

For more information about Zope 3, consult the Zope 3 project pages on
the Zope community website:

  http://dev.zope.org/Zope3/

The information there includes links to relevant mailing lists and IRC
forums.
