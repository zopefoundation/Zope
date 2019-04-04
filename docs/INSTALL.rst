Installing Zope
===============
This document describes three ways to install Zope.

.. contents::

.. highlight:: bash


Prerequisites
-------------
In order to install Zope, you must have the following prerequisites
available:

- A supported version of Python, including the development support if
  installed from system-level packages.  Supported versions include:

  * 2.7
  * 3.5
  * 3.6
  * 3.7
  * 3.8

- Zope needs the Python ``zlib`` module to be importable.  If you are
  building your own Python from source, please be sure that you have the
  headers installed which correspond to your system's ``zlib``.

- A C compiler capable of building extension modules for your Python
  (gcc recommended).

- If you are using a Python interpreter shipping with your Linux distribution,
  you need to install the matching Python development package. As example, for
  Python 3 on Ubuntu 18.04, you have to type the following::

    $ sudo apt-get install python3-dev


Installing Zope with ``zc.buildout``
------------------------------------
In this configuration, we use ``zc.buildout`` to install the Zope software,
and then generate a server "instance" inside the buildout environment.

About ``zc.buildout``
~~~~~~~~~~~~~~~~~~~~~
`zc.buildout <https://pypi.python.org/pypi/zc.buildout>`_ is a powerful
tool for creating repeatable builds of a given software configuration
and environment.  The Zope developers use ``zc.buildout`` to develop
Zope itself, as well as the underlying packages it uses.

Installing the Zope software
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Installing the Zope software using ``zc.buildout`` involves the following
steps:

- Download the Zope source distribution from `PyPI`__

  __ https://pypi.org/project/Zope/

- Bootstrap the buildout

- Run the buildout

You may need to replace the used Zope version used in the examples (4.0b6) with
 he one you actually want to install.

On Linux, this can be done as follows::

  $ wget https://pypi.python.org/packages/source/Z/Zope/Zope-4.0b6.tar.gz
  $ tar xfvz Zope-<Zope version>.tar.gz
  $ cd Zope-<Zope version>
  $ python3.7 -m venv .
  $ bin/pip install -U pip zc.buildout
  $ bin/buildout

.. note::

  When using Python 2.7 instead of calling ``python3.7 -m venv .`` you have to
  install `virtualenv` and then call ``virtualenv-2.7 .``.

Instead of using the buildout configuration shipping with Zope itself, you
can also start with a minimum configuration like this::

    [buildout]
    extends =
        https://zopefoundation.github.io/Zope/releases/4.0b6/versions-prod.cfg
    parts =
        zopescripts
    
    [zopescripts]
    recipe = zc.recipe.egg
    interpreter = zopepy
    eggs =
        Zope

Creating a Zope instance
~~~~~~~~~~~~~~~~~~~~~~~~

.. attention::

  The following steps describe how to install a WSGI based Zope instance.
  If you want/have to use ZServer instead of WSGI (Python 2 only!) follow
  the documentation `Creating a Zope instance for Zope 2.13`_, as it has not
  changed since that version.

.. _`Creating a Zope instance for Zope 2.13` : http://zope.readthedocs.io/en/2.13/INSTALL-buildout.html#creating-a-zope-instance

Once you've installed Zope, you will need to create an "instance
home". This is a directory that contains configuration and data for a
Zope server process.  The instance home is created using the
``mkwsgiinstance`` script::

  $ bin/mkwsgiinstance -d .

You will be asked to provide a user name and password for an
administrator's account during ``mkwsgiinstance``.  To see the available
command-line options, run the script with the ``--help`` option::

  $ bin/mkwsgiinstance --help

After installation, refer to :doc:`operation` for documentation on
configuring and running Zope.


Building the documentation with ``Sphinx``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To build the HTML documentation, run the :command:`make-docs` script (installed
by the buildout)::

   $ bin/make-docs


Installing Zope via ``pip``
---------------------------
This document describes how to install Zope into a ``virtualenv``
using ``pip``.

Create a Virtual Environment (Python 3)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: sh

   $ python3.6 -m venv zope
   $ cd zope

.. note::
  You might need to install ``virtualenv``.

  For example, on Ubuntu 18.04 you have to type the following::

    $ sudo apt-get install python3-venv

Create a Virtual Environment (Python 2.7)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you are still using Python 2.7, install `virtualenv` onto your
system, then call:

.. code-block:: sh

   $ virtualenv --python=python2.7 zope
   New python executable in zope/bin/python2.7
   Installing setuptools, pip, wheel...done.
   $ cd zope

Make sure you use at least version ``12.0.1`` of `virtualenv` (Calling
``virtualenv --version`` tells you the used version number.).
Older versions install a `pip` version which is not compatible with
the file format of ``requirements-full.txt`` used in `Zope`.

.. note::
  It is recommended to update pip to the lastest version. ::

    $ path/to/your/pip install --upgrade pip


Installing the Zope software
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Look for the release you want to install on
https://zopefoundation.github.io/Zope/. Than use the specific version of
``requirements-full.txt`` in the URL, replacing 4.0b7 in the example below:

.. code-block:: sh

   $ bin/pip install Zope==4.0b7 -c https://zopefoundation.github.io/Zope/releases/4.0b7/constraints.txt
   ...
   Obtaining Zope
   ...
   Successfully installed ...

You can also install Zope using a single requirements file. Note that this
installation method might install packages that are not actually needed (i. e.
are not listed in the ``install_requires`` section of ``setup.py``):

.. code-block:: sh

    $ bin/pip install \
    -r https://zopefoundation.github.io/Zope/releases/4.0b7/requirements-full.txt


If you are on Python 2 and want to use ZServer instead of WSGI , you'll have to
install that package seperately using the version spec in constraints.txt

.. code-block:: sh

    $ bin/pip install \
    -c https://zopefoundation.github.io/Zope/releases/4.0b7/constraints.txt \
    ZServer


Creating a Zope instance
~~~~~~~~~~~~~~~~~~~~~~~~

.. attention::

  The following steps describe how to install a WSGI based Zope
  instance.   If you want/have to use ZServer instead of WSGI (Python
  2 only!) follow  the documentation
  `Creating a Zope instance for Zope 2.13`_, .

.. _`Creating a Zope instance for Zope 2.13` : http://zope.readthedocs.io/en/2.13/INSTALL-virtualenv.html#creating-a-zope-instance


Once you've installed Zope, you will need to create an "instance
home". This is a directory that contains configuration and data for a
Zope server process.  The instance home is created using the
``mkwsgiinstance`` script:

.. code-block:: sh

  $ bin/mkwsgiinstance -d .

You will be asked to provide a user name and password for an
administrator's account during ``mkwsgiinstance``.  To see the
available command-line options, run the script with the ``--help``
option:

.. code-block:: sh

   $ bin/mkwsgiinstance --help

The `-d .` argument specifies the directory to create the instance
home in.
If you follow the example and choose the current directory, you'll
find the instances files in the subdirectories of the ``virtualenv``:

- ``etc/`` will hold the configuration files.
- ``var/`` will hold the database files.


Installing Zope via ``pipenv``
------------------------------
This document describes how to install Zope via ``pipenv`` (Python 3 only).
Please note, that the support for Pipenv is considered experimental.
Also, currently there is no support to update the Zope installation via
``pipenv``.

Create a Virtual Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: sh

   $ python3.6 -m venv zope
   $ cd zope


Install pipenv
~~~~~~~~~~~~~~

.. code-block:: sh
    
    $ bin/pip install pipenv


Install the Zope software
~~~~~~~~~~~~~~~~~~~~~~~~~~
Look for the release you want to install on
https://zopefoundation.github.io/Zope/. Then use the specific version of
``requirements-full.txt`` in the URL, replacing 4.0b4 in the example below.
(Remove the --pre option for final releases.)

.. code-block:: sh

   $ bin/pipenv install -r https://zopefoundation.github.io/Zope/releases/4.0b4/requirements-full.txt --pre
   ...
   Successfully installed ...


Creating a Zope instance
~~~~~~~~~~~~~~~~~~~~~~~~
Once you've installed Zope, you will need to create an "instance
home". This is a directory that contains configuration and data for a
Zope server process.  The instance home is created using the
``mkwsgiinstance`` script:

.. code-block:: sh

  $ bin/pipenv run mkwsgiinstance -d .

You will be asked to provide a user name and password for an
administrator's account during ``mkwsgiinstance``.  To see the available
command-line options, run the script with the ``--help`` option:

.. code-block:: sh

   $ bin/pipenv run mkwsgiinstance --help

The `-d .` specifies the directory to create the instance home in.
If you follow the example and choose the current directory, you'll
find the instances files in the subdirectories of the ``virtualenv``:

- ``etc/`` will hold the configuration files.
- ``var/`` will hold the database files.


Starting your created instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To start your newly created instance, run the provided runwsgi script 
with the generated configuration:

.. code-block:: sh

    $ bin/pipenv run runwsgi etc/zope.ini
