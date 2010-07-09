Installing and Zope with ``zc.buildout``
========================================

.. highlight:: bash

This document describes how to get going with Zope using ``zc.buildout``.


About ``zc.buildout``
---------------------

`zc.buildout <http://www.buildout.org/>`_ is a powerful tool for creating
repeatable builds of a given software configuration and environment.  The
Zope developers use ``zc.buildout`` to develop Zope itself, as well as
the underlying packages it uses.

Prerequisites
-------------

In order to use Zope, you must have the following pre-requisites
available:

- A supported version of Python, including the development support if
  installed from system-level packages.  Supported versions include:

  * 2.6.x
  * 2.7.x

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


Installing standalone Zope using zc.buildout
--------------------------------------------

In this configuration, we use ``zc.buildout`` to install the Zope software,
but then generate server "instances" outside the buildout environment.

Installing the Zope software
::::::::::::::::::::::::::::

Installing the Zope software using ``zc.buildout`` involves the following
steps:

- Download the Zope 2 source distribution from `PyPI`__

  __ http://pypi.python.org/pypi/Zope2

- Bootstrap the buildout

- Run the buildout

On Linux, this can be done as follows::

  $ wget http://pypi.python.org/packages/source/Z/Zope2/Zope2-<Zope version>.tar.gz
  $ tar xfvz Zope2-<Zope version>.tar.gz
  $ cd Zope2-<Zope version>
  $ /path/to/your/python bootstrap/bootstrap.py
  $ bin/buildout


Creating a Zope instance
::::::::::::::::::::::::

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
  ``mkzopeinstance``, always do so outside the buildout environment.


Creating a buildout-based Zope instance
---------------------------------------

Rather than installing Zope separately from your instance, you may wish
to use ``zc.buildout`` to create a self-contained environment, containing
both the Zope software and the configuration and data for your server.
This procedure involves the following steps:

- Create the home directory for the buildout, including
  ``etc``, ``log`` and ``var`` subdirectories.

- Fetch the buildout bootstrap script into the environment.

- Create a buildout configuration as follows:

.. topic:: buildout.cfg
 :class: file

 ::

   [buildout]
   parts = instance
   extends = http://download.zope.org/Zope2/index/<Zope version>/versions.cfg

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

- Bootstrap the buildout

- Run the buildout

- Create a Zope configuration file.  A minimal version would be:

.. topic:: etc/zope.cfg
 :class: file

 ::

   %define INSTANCE <path to your instance directory>

   python $INSTANCE/bin/py[.exe on Windows]

   instancehome $INSTANCE

A fully-annotated sample can be found in the Zope2 egg::

   $ cat eggs/Zope2--*/Zope2/utilities/skel/etc/zope.conf.in

   <rest of the stuff that goes into a zope.conf, e.g. databases and log files.>

.. highlight:: bash

An example session::

   $ mkdir /path/to/instance
   $ cd /path/to/instance
   $ mkdir etc logs var
   $ wget http://svn.zope.org/zc.buildout/trunk/bootstrap/bootstrap.py
   $ vi buildout.cfg
   $ /path/to/your/python bootstrap.py
   $ bin/buildout
   $ cat eggs/Zope2--*/Zope2/utilities/skel/etc/zope.conf.in > etc/zope.conf
   $ vi etc/zope.conf  # replace <<INSTANCE_HOME>> with buildout directory
   $ bin/zopectl start

In the ``bin`` subdirectory of your instance directory, you will
find ``runzope`` and ``zopectl`` scripts that can be used as
normal.

You can use ``zopectl`` interactively as a command shell by just
calling it without any arguments. Try ``help`` there and ``help <command>``
to find out about additionally commands of zopectl. These commands
also work at the command line.

Note that there are there are recipes such as `plone.recipe.zope2instance
<http://pypi.python.org/pypi/plone.recipe.zope2instance>`_ which can be
used to automate this whole process.

After installation, refer to :doc:`operation` for documentation on
configuring and running Zope.
