Installing Zope in a ``virtualenv``
===================================

.. highlight:: bash

This document describes how to install Zope into a ``virtualenv``
using ``pip``.


Create a Virtual Environment
----------------------------

Python 3
++++++++

.. code-block:: sh

   $ python3.6 -m venv zope
   $ cd zope

.. note::
  You might need to install ``virtualenv``.
  
  For example, on Ubuntu 18.04 you have to type the following::
  
    $ sudo apt-get install python3-venv

Python 2.7
++++++++++

If you are still using Python 2.7, install `virtualenv` onto your
system, then call:

.. code-block:: sh

   $ virtualenv --python=python2.7 zope
   New python executable in zope/bin/python2.7
   Installing setuptools, pip, wheel...done.
   $ cd zope
   
Make sure you use at least version ``12.0.1`` of `virtualenv`
(Calling ``virtualenv --version`` tells you the used version
number.).
Older versions install a `pip` version which is not compatible with
the file format of ``requirements-full.txt`` used in `Zope`.

.. note::
  It is recommended to update pip to the lastest version. ::
  
    $ path/to/your/pip install --upgrade pip


Install the Zope Software Packages
----------------------------------

Look for the release you want to install on
https://zopefoundation.github.io/Zope/. Than use the specific
version of ``requirements-full.txt`` in the URL, replacing 4.0b6 in the example below:

.. code-block:: sh

   $ bin/pip install Zope==4.0b6\
   -c https://zopefoundation.github.io/Zope/releases/4.0b6/constraints.txt
   ...
   Obtaining Zope
   ...
   Successfully installed ...
   
.. note::
  In order to compile C code, you might need to install the Python development package.
  
  For Ubuntu 18.04, you have to type the following::
  
    $ sudo apt-get install python3-dev

You can also install Zope using a single requirements file. Note that this
installation method might install packages that are not actually needed (i.e.
are not listed in the ``install_requires`` section of ``setup.py``

 .. code-block:: sh

-   $ bin/pip install \
-   -r https://zopefoundation.github.io/Zope/releases/4.0b6/requirements-full.txt


If you are on Python 2 and want to use ZServer instead of WSGI , you'll have to
install that package seperately using the version spec in constraints.txt

.. code-block:: sh

    $ bin/pip install \
    -c https://zopefoundation.github.io/Zope/releases/4.0b6/constraints.txt \
    ZServer


Creating a Zope instance
------------------------

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
