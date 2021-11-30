Installing Zope with ``zc.buildout``
====================================

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


Installing Zope using zc.buildout
---------------------------------

In this configuration, we use ``zc.buildout`` to install the Zope software.
We are using a buildout recipe which does most of the configuration work.

Installing the Zope software using ``zc.buildout`` involves the following
steps:

- Create a virtual environment where you install ``zc.buildout``::

  $ virtualenv --python 2.7 zope-2.13
  $ cd zope-2.13
  $ bin/pip install "zc.buildout<3"

- Write a minimal ``buildout.cfg`` and store it in the ``zope-2.13``
  directory::

    $ cat > buildout.cfg << EOF
    [buildout]
    extends = https://zopefoundation.github.io/Zope/releases/2.13.30/versions-prod.cfg
    show-picked-versions = true
    parts = zopectl

    [versions]
    plone.recipe.zope2instance = < 5
    mailinglogger = < 6

    [zopectl]
    recipe = plone.recipe.zope2instance
    http-address = 127.0.0.1:8080
    eggs =
    EOF

- Run ``zc.buildout`` to install Zope::

  $ bin/buildout

- The buildout recipe ``plone.recipe.zope2instance`` has many more
  configuration options which can be leveraged in ``buildout.cfg``,
  see https://pypi.org/project/plone.recipe.zope2instance/4.4.1/

After installation, refer to :doc:`operation` for documentation on
configuring and running Zope.


Manually creating a buildout-based Zope instance
------------------------------------------------

Rather than installing Zope using a recipe you can also do this by hand.
This procedure involves the following steps:

- Create the home directory for the buildout, including
  ``etc``, ``log`` and ``var`` subdirectories.

- Fetch the buildout bootstrap script into the environment.

- Fetch the version files into the environment, for example:
  https://raw.github.com/zopefoundation/Zope/2.13.30/versions.cfg
  https://raw.github.com/zopefoundation/Zope/2.13.30/ztk-versions.cfg

- Create a buildout configuration as follows:

.. topic:: buildout.cfg
 :class: file

 ::

   [buildout]
   parts = instance
   extends = versions.cfg

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
   $ wget https://svn.zope.org/zc.buildout/trunk/bootstrap/bootstrap.py
   $ vi buildout.cfg
   $ /path/to/your/python bootstrap.py  # assumes no setuptools installed
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

After installation, refer to :doc:`operation` for documentation on
configuring and running Zope.
