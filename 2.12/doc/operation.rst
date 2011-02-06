Configuring and Running Zope
============================

.. highlight:: bash


Whichever method you used to install Zope and create a server instance (see
:doc:`INSTALL` and :doc:`INSTALL-buildout`), the end result is configured
and operated the same way.


Configuring Zope
----------------

Your instance's configuration is defined in its ``etc/zope.conf`` file.
Unless you created the file manually, that file should contain fully-
annotated examples of each directive.

You can also pass an explicit configuration file on the commandline::

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

After making any changes to the configuration file, you need to restart any
running Zope server for the affected instance before changes are in effect.


Running Zope in the Foreground
------------------------------

To run Zope without detaching from the console, use the ``fg``
command (short for ``foreground``)::

  $ /path/to/zope/instance/bin/zopectl fg

In this mode, Zope emits its log messages to the console, and does not
detach from the terminal.


Running Zope as a Daemon
------------------------

Once an instance home has been created, the Zope server can now be
started using this command::

  $ /path/to/zope/instance/bin/zopectl start

During startup, Zope emits log messages into
`/path/to/zope/instance/log/event.log`.  You can examine it with the usual
tools (``cat``, ``more``, ``tail``, etc) and see if there are any errors
preventing Zope from starting.

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
a good place to start. You can access it at http://docs.zope.org/

Troubleshooting
---------------

- This version of Zope requires Python 2.6.4 or better.
  It will *not* run with Python 3.x.

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



Adding extra commands to Zope
-----------------------------

It is possible to add extra commands to ``zopectl`` by defining *entry points*
in ``setup.py``. Commands have to be put in the ``zopectl.command`` group:

.. code-block:: python

   setup(name="MyPackage",
         ....
         entry_points="""
         [zopectl.command]
         init_app = mypackage.commands:init_application
         """)

.. note::

   Due to an implementation detail of ``zopectl`` you can not use a minus
   character (``-``) in the command name.

This adds a ``init_app`` command that can be used directly from the command
line::

    bin\zopectl init_app

The command must be implemented as a Python callable. It will be called with
two parameters: the Zope2 application and a list with all command line
arguments. Here is a basic example:

.. code-block:: python

   def init_application(app, args):
       print 'Initializing the application'

Make sure the callable can be imported without side-effects, such as setting
up the database connection used by Zope 2.
