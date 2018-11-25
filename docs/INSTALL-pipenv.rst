Installing Zope via ``pipenv``
==============================

.. highlight:: bash

This document describes how to install Zope via ``pipenv``. Python 3 only.

Please note, that the support for Pipenv is considered experimental.

Also, currently there is no support to update the Zope installation via ``pipenv``.

Prerequisites
-------------

In order to install Zope, you must have the following prerequisites
available:

- A supported version of Python, including the development support if
  installed from system-level packages. Supported versions include:

  * 2.7
  * 3.5
  * 3.6
  * 3.7

- Zope needs the Python ``zlib`` module to be importable.  If you are
  building your own Python from source, please be sure that you have the
  headers installed which correspond to your system's ``zlib``.

- A C compiler capable of building extension modules for your Python
  (gcc recommended).

- If you are using a Python interpreter shipping with your Linux distribution,
  you need to install the matching Python development package. As example, for
  Python 3 on Ubuntu 18.04, you have to type the following::

    $ sudo apt-get install python3-dev


Create a Virtual Environment
----------------------------

.. code-block:: sh

   $ python3.6 -m venv zope
   $ cd zope


Install pipenv
--------------

.. code-block:: sh
    
    $ bin/pip install pipenv


Install the Zope Software Packages
----------------------------------

Look for the release you want to install on
https://zopefoundation.github.io/Zope/. Than use the specific
version of ``requirements-full.txt`` in the URL, replacing 4.0b4 in the example below.
(Remove the --pre option for final releases.)

.. code-block:: sh

   $ bin/pipenv install -r https://zopefoundation.github.io/Zope/releases/4.0b4/requirements-full.txt --pre
   ...
   Successfully installed ...


Creating a Zope instance
------------------------

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
------------------------------

To start your newly created instance, run the provided runwsgi script 
with the generated configuration:

.. code-block:: sh

    $ bin/pipenv run runwsgi etc/zope.ini
