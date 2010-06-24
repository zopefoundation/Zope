Running Zope in Debug Mode
==========================

A utility known as 'zopectl' is installed into generated instance homes.

If you wish to run Zope in debug mode, run zopectl in foreground mode::

  $ bin/zopectl fg

You can also use it to inspect a Zope instance's running state via an
interactive Python interpreter by passing zopectl the 'debug' parameter on the
command line.
The 'top-level' Zope object (the root folder) will be bound to the name 'app'
within the interpreter. You can then use normal Python method calls against app
and use the Python interpreter normally to inspect results::

  $ bin/zopectl debug
  Starting debugger (the name "app" is bound to the top-level Zope object)
  >>> app.keys()
  ['acl_users', 'Control_Panel', 'temp_folder', 'browser_id_manager', 'session_data_manager', 'error_log', 'index_html', 'standard_error_message']
  >>>
