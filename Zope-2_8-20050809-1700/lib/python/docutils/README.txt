==================
 README: Docutils
==================

:Author: David Goodger
:Contact: goodger@users.sourceforge.net
:Date: $Date: 2005/01/07 15:11:43 $
:Web site: http://docutils.sourceforge.net/
:Copyright: This document has been placed in the public domain.

.. contents::


Thank you for downloading the Python Docutils project archive.  As
this is a work in progress, please check the project website for
updated working files (snapshots).  This project should be considered
highly experimental; APIs are subject to change at any time.


Quick-Start
===========

This is for those who want to get up & running quickly.  Read on for
complete details.

1. Get and install the latest release of Python, available from

       http://www.python.org/

   Python 2.2 or later [1]_ is required; Python 2.2.2 or later is
   recommended.

2. Use the latest Docutils code.  Get the code from CVS or from the
   snapshot:

       http://docutils.sf.net/docutils-snapshot.tgz

   See `Releases & Snapshots`_ below for details.

3. Unpack the tarball in a temporary directory (**not** directly in
   Python's ``site-packages``) and install with the standard ::

       python setup.py install

   See Installation_ below for details.

4. Use a front-end tool from the "tools" subdirectory of the same
   directory as in step 3.  For example::

       cd tools
       ./rst2html.py ../FAQ.txt ../FAQ.html        (Unix)
       python rst2html.py ..\FAQ.txt ..\FAQ.html   (Windows)

   See Usage_ below for details.


Purpose
=======

The purpose of the Docutils project is to create a set of tools for
processing plaintext documentation into useful formats, such as HTML,
XML, and TeX.  Support for the following sources has been implemented:

* Standalone files.

* `PEPs (Python Enhancement Proposals)`_.

Support for the following sources is planned:

* Inline documentation from Python modules and packages, extracted
  with namespace context.  **This is the focus of the current
  development effort.**

* Email (RFC-822 headers, quoted excerpts, signatures, MIME parts).

* Wikis, with global reference lookups of "wiki links".

* Compound documents, such as multiple chapter files merged into a
  book.

* And others as discovered.

.. _PEPs (Python Enhancement Proposals):
   http://www.python.org/peps/pep-0012.html


Releases & Snapshots
====================

Putting together an official "Release" of Docutils is a significant
effort, so it isn't done that often.  In the meantime, the CVS
snapshots always contain the latest code and documentation, usually
updated within an hour of changes being committed to the repository,
and usually bug-free:

* Snapshot of Docutils code, documentation, front-end tools, and
  tests: http://docutils.sf.net/docutils-snapshot.tgz

* Snapshot of the Sandbox (experimental, contributed code):
  http://docutils.sf.net/docutils-sandbox-snapshot.tgz

* Snapshot of web files (the files that generate the web site):
  http://docutils.sf.net/docutils-web-snapshot.tgz

To keep up to date on the latest developments, download fresh copies
of the snapshots regularly.  New functionality is being added weekly,
sometimes daily.  (There's also the CVS repository, and a mailing list
for CVS messages.  See the web site [address above] or
docs/dev/policies.txt for details.)


Requirements
============

To run the code, Python 2.2 or later [1]_ must already be installed.
The latest release is recommended.  Python is available from
http://www.python.org/.

The `Python Imaging Library`, or PIL, is used for some image
manipulation operations if it is installed.

Docutils uses Greg Ward's Optik_/optparse option processing package.
It is included in the Docutils distribution.  Python 2.3 and later
come with optparse in the standard library; in this case, the Docutils
copy is not installed.

.. [1] Python 2.1 may be used providing the compiler package is
   installed.  The compiler package can be found in the Tools/
   directory of Python 2.1's source distribution.

.. _Python Imaging Library: http://www.pythonware.com/products/pil/
.. _Optik: http://optik.sourceforge.net/


Project Files & Directories
===========================

* README.txt: You're reading it.

* COPYING.txt: Public Domain Dedication and copyright details for
  non-public-domain files (most are PD).

* FAQ.txt: Docutils Frequently Asked Questions.

* HISTORY.txt: Release notes for the current and previous project
  releases.

* setup.py: Installation script.  See "Installation" below.

* install.py: Quick & dirty installation script.  Just run it.  For
  any kind of customization or help though, setup.py must be used.

* docutils: The project source directory, installed as a Python
  package.

* extras: Directory for third-party modules that Docutils depends on.
  These are only installed if they're not already present.

* docs: The project documentation directory.  Read ``docs/index.txt``
  for an overview, which is especially interesting for developers.

* docs/user: The project user documentation directory.  Contains the
  following documents, among others:

  - docs/user/tools.txt: Docutils Front-End Tools
  - docs/user/latex.txt: Docutils LaTeX Writer
  - docs/user/rst/quickstart.txt: A ReStructuredText Primer
  - docs/user/rst/quickref.html: Quick reStructuredText (HTML only)

* docs/ref: The project reference directory.
  ``docs/ref/rst/restructuredtext.txt`` is the reStructuredText
  reference.

* licenses: Directory containing copies of license files for
  non-public-domain files.

* tools: Directory for Docutils front-end tools.  See
  ``docs/user/tools.txt`` for documentation.

* test: Unit tests.  Not required to use the software, but very useful
  if you're planning to modify it.  See `Running the Test Suite`_
  below.


Installation
============

The first step is to expand the ``.tar.gz`` or ``.tgz`` archive in a
temporary directory (**not** directly in Python's ``site-packages``).
It contains a distutils setup file "setup.py".  OS-specific
installation instructions follow.


GNU/Linux, BSDs, Unix, Mac OS X, etc.
-------------------------------------

1. Open a shell.

2. Go to the directory created by expanding the archive::

       cd <archive_directory_path>

3. Install the package::

       python setup.py install

   If the python executable isn't on your path, you'll have to specify
   the complete path, such as /usr/local/bin/python.  You may need
   root permissions to complete this step.

You can also just run install.py; it does the same thing.


Windows
-------

1. Open a DOS box (Command Shell, MSDOS Prompt, or whatever they're
   calling it these days).

2. Go to the directory created by expanding the archive::

       cd <archive_directory_path>

3. Install the package::

       <path_to_python.exe>\python setup.py install

If your system is set up to run Python when you double-click on .py
files, you can run install.py to do the same as the above.


Mac OS 8/9
----------

1. Open the folder containing the expanded archive.

2. Double-click on the file "setup.py", which should be a "Python
   module" file.

   If the file isn't a "Python module", the line endings are probably
   also wrong, and you will need to set up your system to recognize
   ".py" file extensions as Python files.  See
   http://gotools.sourceforge.net/mac/python.html for detailed
   instructions.  Once set up, it's easiest to start over by expanding
   the archive again.

3. The distutils options window will appear.  From the "Command" popup
   list choose "install", click "Add", then click "OK".

If install.py is a "Python module" (see step 2 above if it isn't), you
can run it (double-click) instead of the above.  The distutils options
window will not appear.


Usage
=====

After unpacking and installing the Docutils package, the following
shell commands will generate HTML for all included documentation::

    cd <archive_directory_path>/tools
    ./buildhtml.py ../

On Windows systems, type::

    cd <archive_directory_path>\tools
    python buildhtml.py ..

The final directory name of the ``<archive_directory_path>`` is
"docutils" for snapshots.  For official releases, the directory may be
called "docutils-X.Y.Z", where "X.Y.Z" is the release version.
Alternatively::

    cd <archive_directory_path>
    tools/buildhtml.py --config=tools/docutils.conf          (Unix)
    python tools\buildhtml.py --config=tools\docutils.conf   (Windows)

Some files may generate system messages (warnings and errors).  The
``docs/user/rst/demo.txt`` file (under the archive directory) contains
5 intentional errors.  (They test the error reporting mechanism!)

There are many front-end tools in the unpacked "tools" subdirectory.
You may want to begin with the "rst2html.py" front-end tool.  Most
tools take up to two arguments, the source path and destination path,
with STDIN and STDOUT being the defaults.  Use the "--help" option to
the front-end tools for details on options and arguments.  See
Docutils Front-End Tools (``docs/user/tools.txt``) for full documentation.

The package modules are continually growing and evolving.  The
``docutils.statemachine`` module is usable independently.  It contains
extensive inline documentation (in reStructuredText format of course).

Contributions are welcome!


Running the Test Suite
======================

To run the entire test suite, after installation_ open a shell and use
the following commands::

    cd <archive_directory_path>/test
    ./alltests.py

Under Windows, type::

    cd <archive_directory_path>\test
    python alltests.py

You should see a long line of periods, one for each test, and then a
summary like this::

    Ran 518 tests in 24.653s

    OK
    Elapsed time: 26.189 seconds

The number of tests will grow over time, and the times reported will
depend on the computer running the tests.  The difference between the
two times represents the time required to set up the tests (import
modules, create data structures, etc.).

If any of the tests fail, please `open a bug report`_ or `send email`_
[2]_.  Please include all relevant output, information about your
operating system, Python version, and Docutils version.  To see the
Docutils version, use these commands in the shell::

    cd ../tools
    ./quicktest.py --version

Windows users type these commands::

    cd ..\tools
    python quicktest.py --version

.. _open a bug report:
   http://sourceforge.net/tracker/?group_id=38414&atid=422030
.. _send email: mailto:docutils-users@lists.sourceforge.net
   ?subject=Docutils%20test%20suite%20failure


Getting Help
============

If you have questions or need assistance with Docutils or
reStructuredText, please `post a message`_ to the `Docutils-Users
mailing list`_ [2]_.

.. [2] Due to overwhelming amounts of spam, the
   docutils-users@lists.sourceforge.net mailing list has been set up
   for subscriber posting only.  Non-subscribers who post to
   docutils-users will receive a message with "Subject: Your message
   to Docutils-users awaits moderator approval".  Legitimate messages
   are accepted and posted as soon as possible (a list administrator
   must verify the message manually).  If you'd like to subscribe to
   docutils-users, please visit
   <http://lists.sourceforge.net/lists/listinfo/docutils-users>.

.. _post a message: mailto:docutils-users@lists.sourceforge.net
.. _Docutils-Users mailing list:
   http://lists.sourceforge.net/lists/listinfo/docutils-users


..
   Local Variables:
   mode: indented-text
   indent-tabs-mode: nil
   sentence-end-double-space: t
   fill-column: 70
   End:
