========================================
Building and installing Zope from source
========================================

Welcome to Zope!  This document describes building and installing
Zope on UNIX and Linux.

See ``doc/WINDOWS.rst`` for information about Windows.

Prerequisites
-------------

System requirements when building from source

- A supported version of Python, including the development support if
  installed from system-level packages.  Supported versions include:

  * 2.5.x, (x >= 4)

  * 2.6.x

- Zope needs the Python ``zlib`` module to be importable.  If you are
  building your own Python from source, please be sure that you have the
  headers installed which correspond to your system's ``zlib``.

- A C compiler capable of building extension modules for your Python
  (gcc recommended).


Building Zope using zc.buildout
-------------------------------

Zope is built using the ``zc.buildout`` library, which needs to be
"boostrapped" with your Python version.  E.g.::

  $ cd /path/to/zope
  $ /path/to/your/python bootstrap/bootstrap.py

The boostrap script creates a ``buildout`` script in ``bin``;  run this
script to finish building Zope::

  $ bin/buildout

Installing Zope using easy_install
----------------------------------

.. note:: Installation using ``easy_install`` is not fully supported
      right now

Zope can be installed using ``easy_install`` either using a global
easy_install installation or within a virtualized Python environment
(using ``virtualenv``)::

  $ /path/to/easy_install Zope2

This will create the related scripts like ``mkzopeinstance`` within the
``bin`` folder of you global or virtualized Python environment.


Creating a Zope Instance
------------------------

Once you've performed the install step, to begin actually using
Zope, you will need to create an "instance home", which is a
directory that contains configuration and data for a Zope server
process.  The instance home is created using the ``mkzopeinstance``
script::

  $ bin/mkzopeinstance

If you use Zope from SVN, you will need to specify the Python interpreter
to use for the instance explicitly::

  $ bin/mkzopeinstance --python=bin/zopepy

You will be asked to provide a user name and password for an
administrator's account during ``mkzopeinstance``.  To see the available
command-line options, run the script with the ``--help`` option::

  $ bin/mkzopeinstance --help


Starting Zope as a Daemon
-------------------------

Once an instance home has been created, the Zope server can now be
started using this command::

  $ /path/to/zope/instance/bin/zopectl start

During start, zope emits log messages into ./log/event.log
You can examine it with the usual tools (cat, more, tail)
and see if there are any errors preventing zope from starting.


Running Zope in the Foreground
------------------------------

By default, ``zopectl start`` will start a background process (a
"daemon) that manages Zope.  ``zopectl stop`` will stop the background
process.  To run Zope without detaching from the console, use the ``fg``
command (short for ``foreground``)::

  $ /path/to/zope/instance/bin/zopectl fg

In this mode, Zope emits its log messages to the console, and does not
detach from terminal.


Configuring Zope
----------------

Your Zope instance is configured through a file, either found by
default::

  $ /path/to/zope/instance/bin/zopectl show
  ...
  Config file:  /path/to/zope/instance/etc/zope.conf

or passed explicitly on the commandline::

  $ /path/to/zope/instance/bin/zopectl -c /tmp/other.conf show
  ...
  Config file:  /tmp/other.conf

When starting Zope, if you see errors indicating that an address is in
use, then you will have to supply arguments to runzope to change the ports
used for HTTP or FTP. The default HTTP and FTP ports used by Zope are
8080 and 8021 respectively. You can change the ports used by
editing ./etc/zope.conf apropriately.

The section in the configuration file looks like this::

  <http-server>
    # valid keys are "address" and "force-connection-close"
    address 8080
    # force-connection-close on
  </http-server>

The address can just be a port number as shown, or a  host:port
pair to bind only to a specific interface.


Integrating with System Startup
-------------------------------

zopectl can be linked as rc-script in the usual start directories
on linux or other System V unix variants.

You can use ``zopectl`` interactively as a command shell by just
calling it without any arguments. Try ``help`` there and ``help <command>``
to find out about additionally commands of zopectl. These commands
also work at the command line.


Logging In To Zope
------------------

Once you've started Zope, you can then connect to the Zope webserver
by directing your browser to::

  http://yourhost:8080/manage

where 'yourhost' is the DNS name or IP address of the machine
running Zope.  If you changed the HTTP port as described, use the port
you configured.

You will be prompted for a user name and password. Use the user name
and password you provided in response to the prompts issued during
the "make instance" process.

Now you're off and running! You should be looking at the Zope
management screen which is divided into two frames. On the left you
can navigate between Zope objects and on the right you can edit them
by selecting different management functions with the tabs at the top
of the frame.

If you haven't used Zope before, you should head to the Zope web
site and read some documentation. The Zope Documentation section is
a good place to start. You can access it at:

http://docs.zope.org/

Troubleshooting
---------------

- This version of Zope requires Python 2.5.4 or better, including
  2.6.x.  It will *not* run with Python 3.x.

- The Python you run Zope with *must* have threads compiled in,
  which is the case for a vanilla build.  Warning: Zope will not run
  with a Python version that uses ``libpth``.  You *must* use
  ``libpthread``.

- To build Python extensions you need to have Python configuration
  information available. If your Python comes from an RPM you may
  need the python-devel (or python-dev) package installed too. If
  you built Python from source all the configuration information
  should already be available.

- See ``doc/CHANGES.rst`` for important notes on this version of Zope.
