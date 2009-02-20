Running Zope in Debug Mode
==========================

If you wish to run Zope in debug mode, set the 'debug-mode'
configuration file parameter to 'on' (this is the default).  This
will have the following effects:

- On UNIX, Zope will not detach from the controlling terminal.

- The Z_DEBUG_MODE environment variable gets set, which causes
  behavioral changes to Zope appropriate for software development.
  See the configuration file description of 'debug-mode' for more
  information.

Using 'zopectl debug'
---------------------

A utility known as 'zopectl' is installed into generated instance homes.
You can use it to inspect a Zope instance's running state via an
interactive Python interpreter by passing zopectl the 'debug' parameter
on the command line.  The 'top-level' Zope object (the root folder) will
be bound to the name 'app' within the interpreter.  You can then use
normal Python method calls against app and use the Python interpreter
normally to inspect results::

    [chrism@james Trunk]$ bin/zopectl debug
    Starting debugger (the name "app" is bound to the top-level Zope object)
    >>> app.objectIds()
    ['acl_users', 'Control_Panel', 'temp_folder', 'browser_id_manager', 'session_data_manager', 'error_log', 'index_html', 'standard_error_message']
    >>> 
