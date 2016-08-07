What's new in Zope 4.0
======================

The article explains the new high-level features and changes found in this
version of Zope.

You can have a look at the `detailed change log <CHANGES.html>`_ to learn
about all minor new features and bugs being solved in this release.

Note: This is currently work-in-progress!


Version numbering increase
--------------------------

Version numbers for Zope have been confusing in the past. The original Zope
project iterated through version one to two up to version 2.13. In parallel
a separate project was launched using the name Zope 3. Zope 3 wasn't a new
version of the original Zope project and in hindsight should have used a
different project name. These days this effort is known as BlueBream.

In order to avoid confusion between the separate Zope 3 project and a new
version of this project, it was decided to skip ahead and use Zope 4.0 as the
next version number. The increase in the major part of the version also
indicates the clear intention to allow backwards incompatible changes.


Recommended WSGI setup
----------------------

Zope 2.13 first gained support for running Zope as a WSGI application,
using any WSGI capable web server instead of the built-in ZServer.

Zope 4.0 takes this one step further and recommends using WSGI as the
default setup. In fact ZServer got moved into its own optional project.

If you rely on ZServer features, like Webdav, FTP, zdaemon or zopectl
support, please make sure to install ZServer and use its ``mkzopeinstance``
script to create a Zope instance.

By default Zope only ships with a new ``mkwsgiinstance`` script which
creates a Zope instance configured to run as a WSGI application. The
example configuration uses the ``waitress`` web server, but Zope can
be run using any WSGI capable web server.

To make running Zope easier, a new ``runwsgi`` command line script got
added, which can read a PasteDeploy configuration and create and run
the WSGI pipeline specified in it. By default such a configuration is
created in the ``etc/zope.ini`` file.


Memory use
----------

Zope 4 depends on the new DateTime version 3. DateTime 3 has been optimized
for better memory use. Applications using a lot of DateTime values like the
Plone CMS have seen total memory usage to decrease by 10% to 20% for medium
to large deployments.
