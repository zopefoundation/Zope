Running Zope2 as a WSGI Application
===================================

This document assumes you have installed Zope and created a Zope
instance home via `mkzopeinstance`.

The default configuration includes a WSGI configuration using
a PasteDeploy configuration file.


Start the WSGI Server
---------------------

.. code-block:: sh

   $ bin/runwsgi -v etc/zope.ini
   Starting server in PID 24934.
   serving on http://127.0.0.1:8080
