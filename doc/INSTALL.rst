============================
Building and Installing Zope
============================

.. highlight:: bash

This document descibes how to get going with Zope.

Prerequisites
=============

In order to use Zope, you must have the following pre-requisites
available: 

- A supported version of Python, including the development support if
  installed from system-level packages.  Supported versions include:

  * 2.5.x, (x >= 4)

  * 2.6.x

- Zope needs the Python ``zlib`` module to be importable.  If you are
  building your own Python from source, please be sure that you have the
  headers installed which correspond to your system's ``zlib``.

- A C compiler capable of building extension modules for your Python
  (gcc recommended). This is not necessary for Windows as binary
  releases of the parts that would need compiling are always made
  available.

- If you wish to install Zope as a Service on Windows, you will need
  to have the `pywin32`__ package installed.

  __ https://sourceforge.net/projects/pywin32/

Installing Zope
===============

Unless using buildout to build a zope instance as described
:ref:`below <buildout-instances>`, you will need to install Zope
separately. If you want to create a buildout-based Zope instance,
please skip directly to that section.

Installing Zope using virtualenv
--------------------------------

Zope can be installed within a virtualized Python environment using 
``virtualenv`` as follows::

  $ virtualenv --no-site-packages my_zope
  $ cd my_zope
  $ source bin/activate
  $ bin/easy_install -i http://download.zope.org/Zope2/index/<Zope version> Zope2

Using ``virtualenv`` is **highly recommended**. Otherwise, you may encounter
unexpected conflicts with packages that have already been installed.

Once you've installed Zope, you'll need to :ref:`create an instance <classic-instances>`.

Installing Zope using zc.buildout
---------------------------------

Unless you are `developing zope`__, you most likely
want to be creating a :ref:`buildout-based Zope instance <buildout-instances>` rather
that installing using buildout as described in this section.

__ http://docs.zope.org/developer/

However, if you really just want to create Zope instances using the
classic ``mkzopeinstance`` but with the software installed by buildout,
then you need to do the following:

- Download the Zope 2 source distribution from `PyPI`__

  __ http://pypi.python.org/pypi/Zope2

- Bootstrap the buildout

- Run the buildout

On Linux, this can be done as follows::

  $ wget http://pypi.python.org/packages/source/Z/Zope2/Zope2-<Zope version>.tar.gz
  $ tar xfvz Zope2-2.12.0.tar.gz
  $ cd Zope2-2.12.0
  $ /path/to/your/python bootstrap/bootstrap.py
  $ bin/buildout

Once you've installed Zope, you'll need to :ref:`create an instance <classic-instances>`.

Installing Zope using easy_install
----------------------------------

Zope can be installed using ``easy_install``, but it is recommended to
use ``virtualenv`` as described above to avoid unexpected conflicts
with other packages installed directly in your python installation.

However, if you want to use easy_install globally, all you need to do
is::

  $ easy_install -i http://download.zope.org/Zope2/index/<Zope version> Zope2

This will create the related scripts such as ``mkzopeinstance`` within the
scripts folder of your python installation. You can then use them to
create instances as described below.

.. _classic-instances:

Creating a classic Zope Instance
================================

Once you've installed Zope, you will need to create an "instance
home". This is a directory that contains configuration and data for a
Zope server process.  The instance home is created using the
``mkzopeinstance`` script::

  $ bin/mkzopeinstance

You can specify the Python interpreter to use for the instance
explicitly:: 

  $ bin/mkzopeinstance --python=$PWD/bin/zopepy

You will be asked to provide a user name and password for an
administrator's account during ``mkzopeinstance``.  To see the available
command-line options, run the script with the ``--help`` option::

  $ bin/mkzopeinstance --help

.. note::
  The traditional "inplace" build is no longer supported. If using
  ``mkzopeinstance``, always do so outside the buildout/virtualenv
  environment. If you wish to manage your Zope instance using
  buildout, please see the section below.

.. _buildout-instances:

Creating a buildout-based Zope Instance
=======================================

If you wish to use buildout to manage your Zope instance, then the
instance is created as follows:

* Create a directory for your instance. In this directory, create a
  ``etc``, ``logs`` and ``var`` subdirectories.

* Download the following file into your instance directory:

  `http://svn.zope.org/*checkout*/zc.buildout/trunk/bootstrap/bootstrap.py`__
    
  __ http://svn.zope.org/*checkout*/zc.buildout/trunk/bootstrap/bootstrap.py

.. highlight:: none

* Create a buildout configuration as follows:

.. topic:: buildout.cfg
 :class: file

 ::

   [buildout]
   parts = instance 
   extends = http://svn.zope.org/*checkout*/Zope/tags/<Zope version>/versions.cfg

   [instance]
   recipe = zc.recipe.egg
   eggs = Zope2
   interpreter = py
   scripts = runzope zopectl
   initialization =
     import sys
     sys.argv[1:1] = ['-C',r'${buildout:directory}/etc/zope.conf']

This is the minimum but all the usual buildout techniques can be
used.

* Create a Zope configuration file starting as follows:

.. topic:: etc/zope.cfg
 :class: file

 ::

   %define INSTANCE <path to your instance directory>

   python $INSTANCE/bin/py[.exe on Windows]
 
   instancehome $INSTANCE

.. highlight:: bash

* Now, run the following commands::

    $ /path/to/your/python bootstrap.py
    $ bin/buildout

  In the ``bin`` subdirectory of your instance directory, you will
  find ``runzope`` and ``zopectl`` scripts that can be used as
  normal.

Using your Zope instance
========================

There are various ways to run Zope from your newly created
instance. They are all described below.

Running Zope in the Foreground
------------------------------

To run Zope without detaching from the console, use the ``fg``
command (short for ``foreground``)::

  $ /path/to/zope/instance/bin/zopectl fg

In this mode, Zope emits its log messages to the console, and does not
detach from terminal.


Running Zope as a Daemon
-------------------------

Once an instance home has been created, the Zope server can now be
started using this command::

  $ /path/to/zope/instance/bin/zopectl start

During start, zope emits log messages into ./log/event.log
You can examine it with the usual tools (cat, more, tail)
and see if there are any errors preventing zope from starting.

.. highlight:: none
.. note::

  For this to work on Windows, the Zope instance must be installed as
  a Service. This is done with::

    bin\zopectl install

  If you later want to remove this Service, do the following::

    bin\zopectl remove

  For the full list of options available for setting up Zope as a
  Windows Service, do::

    bin\zopectl install --help

.. highlight:: bash

Integrating with System Startup
-------------------------------

zopectl can be linked as rc-script in the usual start directories
on linux or other System V unix variants.

You can use ``zopectl`` interactively as a command shell by just
calling it without any arguments. Try ``help`` there and ``help <command>``
to find out about additionally commands of zopectl. These commands
also work at the command line.

.. note::

  On Windows, a Service can be installed and set to start
  automatically with the following:

  .. code-block:: none

    bin\zopectl install --startup=auto

Configuring Zope
================

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
use, then you may have to change the ports Zope uses for HTTP or FTP. 
The default HTTP and FTP ports used by Zope are
8080 and 8021 respectively. You can change the ports used by
editing ./etc/zope.conf appropriately.

The section in the configuration file looks like this::

  <http-server>
    # valid keys are "address" and "force-connection-close"
    address 8080
    # force-connection-close on
  </http-server>

The address can just be a port number as shown, or a  host:port
pair to bind only to a specific interface.

Logging In To Zope
==================

Once you've started Zope, you can then connect to the Zope webserver
by directing your browser to::

  http://yourhost:8080/manage

where 'yourhost' is the DNS name or IP address of the machine
running Zope.  If you changed the HTTP port as described, use the port
you configured.

You will be prompted for a user name and password. Use the user name
and password you provided in response to the prompts issued during
the "make instance" process.

If you are using a buildout-based Zope instance, you will need to
create a user as follows::

  $ bin/zopectl adduser username password

Now you're off and running! You should be looking at the Zope
management screen which is divided into two frames. On the left you
can navigate between Zope objects and on the right you can edit them
by selecting different management functions with the tabs at the top
of the frame.

If you haven't used Zope before, you should head to the Zope web
site and read some documentation. The Zope Documentation section is
a good place to start. You can access it at http://docs.zope.org/

Troubleshooting
===============

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

- See the :doc:`CHANGES` for important notes on this version of Zope.
