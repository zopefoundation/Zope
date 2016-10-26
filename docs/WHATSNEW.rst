What's new in Zope 4.0
======================

The article explains the new high-level features and changes found in this
version of Zope.

You can have a look at the `detailed change log <CHANGES.html>`_ to learn
about all minor new features and bugs being solved in this release.


Version numbering increase
--------------------------

Version numbers for Zope have been confusing in the past. The original Zope
project iterated through version one to two up to version 2.13. In parallel
a separate project was launched using the name Zope 3. Zope 3 wasn't a new
version of the original Zope project and in hindsight should have used a
different project name. These days this effort is known as BlueBream.

In order to avoid confusion between the separate Zope 3 project and a
new version of this project, it was decided to skip ahead and use
Zope 4.0 as the next version number. The increase in the major part of
the version also indicates the number of backwards incompatible changes
found in this release.


Python versions
---------------

Zope 4 exclusively supports Python 2.7. A large number of its dependencies
have been ported to Python 3, so there is reasonable hope that Python 3
support can be added to Zope in the future. It is most likely that this
support will not extend to optional dependencies like the ZServer project
or projects supporting TTW development.


Recommended WSGI setup
----------------------

Zope 2.13 first gained support for running Zope as a WSGI application,
using any WSGI capable web server instead of the built-in ZServer.

Zope 4.0 takes this one step further and recommends using WSGI as the
default setup and functional testing (testbrowser) support uses the new
WSGI publisher.

The ZServer based publisher got moved into its own optional project.
So if you rely on ZServer features, like Webdav, FTP, zdaemon or zopectl
support, please make sure to install ZServer and use its ``mkzopeinstance``
script to create a Zope instance.

The ZServer project also includes limited functional testing support
in the `ZServer.Testing` sub-package. testbrowser support is exclusively
available based on the WSGI publisher, as a result of a switch from
the unmaintained mechanize project to WebTest.

By default Zope only ships with a new ``mkwsgiinstance`` script which
creates a Zope instance configured to run as a WSGI application. The
example configuration uses the ``waitress`` web server, but Zope can
be run using any WSGI capable web server.

To make running Zope easier, a new ``runwsgi`` command line script got
added, which can read a PasteDeploy configuration and create and run
the WSGI pipeline specified in it. By default such a configuration is
created in the ``etc/zope.ini`` file. The WSGI support has no built-in
support for running as a daemon. Your chosen WSGI server might support
this or you can use external projects like supervisord.

The WSGI support in Zope 4 has changed in a number of ways to make it
more similar to its ZServer equivalent. In Zope 2.13 the WSGI support
required using repoze WSGI middlewares to add transaction and retry
handling. The WSGI support in Zope 4 no longer supports those middlewares
but integrates transaction and retry handling back into the publisher
code. This allows it to also add back full support for publication events
and exception views. It does mean that the transaction is begun and
committed or aborted inside the publisher code and you can no longer
write WSGI middlewares that take part in the transaction cycle, but
instead have to use Zope specific hooks like you do in the ZServer based
publisher.


Reduced ZMI functionality
-------------------------

Zope traditionally came with a full-featured through-the-web development
and administration environment called the Zope Management Interface (ZMI).

Over time the ZMI has not been maintained or developed further and today
is a large source of vulnerabilities like cross site scripting (XSS)
or cross site request forgery (CSRF) attacks. Generally it is therefor
recommended to restrict access to the ZMI via network level protections,
for example firewalls and VPN access to not expose it to the public.

In Zope 4 the functionality of the ZMI is starting to be reduced and
development support and general content editing are being removed.
If you relied on those features before, you will need to write your own
content editing UI or move development to the file system.


View components without Acquisition
-----------------------------------

In Zope 2.12 Zope Toolkit view components changed and stopped inheriting
from Acquisition base classes, as Acquisition got aware of `__parent__`
pointers, which meant that ``aq_parent(view)`` worked, without the view
having to mix-in an Acquisition base class. For backwards compatibility
a new `AcqusitionBBB` class was mixed in, to continue to support calling
``view.aq_parent``. This backwards compatibility class has been removed
in Zope 4, so ``view.aq_parent`` no longer works and you have to use
``aq_parent(view)``. The same applies for other view components like
view page template files or viewlets.


Chameleon based page templates
------------------------------

Chameleon is an alternative implementation of the page template language
supporting additional features and impressive template rendering speed.

So far it was available via the `five.pt` project. In Zope 4 the code
from `five.pt` has been merged into Zope core and the Chameleon based
engine is now the default, removing the need to install `five.pt`
manually.


Memory use
----------

Zope 4 depends on the new DateTime version 3. DateTime 3 has been optimized
for better memory use. Applications using a lot of DateTime values like the
Plone CMS have seen total memory usage to decrease by 10% to 20% for medium
to large deployments.
