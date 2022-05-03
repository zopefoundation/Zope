Virtual Hosting Services
========================

.. include:: includes/zope2_notice.rst

Zope comes with one object that help you do virtual hosting:
*Virtual Host Monster*. Virtual hosting is a way to
serve many websites with one Zope server.

Virtual Host Monster
--------------------

Zope objects need to generate their own URLs from time to time.
For instance, when a Zope object has its "absolute_url" method
called, it needs to return a URL which is appropriate for
itself.  This URL typically contains a hostname, a port, and a
path.  In a "default" Zope installation, this hostname, port,
and path is typically what you want.  But when it comes time to
serve multiple websites out of a single Zope instance, each with
their own "top-level" domain name, or when it comes time to
integrate a Zope Folder within an existing website using Apache
or another webserver, the URLs that Zope objects generate need
to change to suit your configuration.

A Virtual Host Monster's only job is to change the URLs which
your Zope objects generate.  This allows you to customize the
URLs that are displayed within your Zope application, allowing
an object to have a different URL when accessed in a different
way.  This is most typically useful, for example, when you wish
to "publish" the contents of a single Zope Folder
(e.g. '/FooFolder') as a URL that does not actually contain this
Folder's name (e.g as the hostname 'www.foofolder.com').

The Virtual Host Monster performs this job by intercepting and
deciphering information passed to Zope within special path
elements encoded in the URLs of requests which come in to Zope.
If these special path elements are absent in the URLs of
requests to the Zope server, the Virtual Host Monster does
nothing.  If they are present, however, the Virtual Host Monster
deciphers the information passed in via these path elements and
causes your Zope objects to generate a URL that is different
from their "default" URL.

The Zope values which are effected by the presence of a Virtual
Host Monster include REQUEST variables starting with URL or BASE
(such as URL1, BASE2, URLPATH0), and the absolute_url() methods
of objects.

Virtual Host Monster configuration can be complicated, because
it requires that you *rewrite* URLs "on the way in" to Zope.  In
order for the special path elements to be introduced into the
URL of the request sent to Zope, a front-end URL "rewriting"
tool needs to be employed.  Virtual Host Monster comes with a
simple rewriting tool in the form of its *Mappings* view, or
alternately you can use Apache or another webserver to rewrite
URLs of requests destined to Zope for you.

Adding a Virtual Host Monster to your Zope
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

VirtualHostMonster is one of the add menu items supplied by the
stock Zope Product, 'SiteAccess'.  You can add one to any folder
by selecting its entry from the add menu and supplying an ID for
it (the ID you choose doesn't matter, except that it must not
duplicate the ID of another object in that folder).

Where to Put a Virtual Host Monster And What To Name It
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A single Virtual Host Monster in your Zope root can handle all
of your virtual hosting needs. It doesn't matter what 'id' you
give it, as long as nothing else in your site has the same
'id'.

Configuring the VirtualHostMonster
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The default mode for configuring the VirtualHostMonster is not
to do any configuration at all!  Rather, the external webserver
modifies the request URL to signal what the *real* public URL for
the request is (see "Apache Rewrite Rules" below).

If you *do* choose to change the settings of your VHM, the easiest
method to do so is to use the VHM's ZMI interface (as explained in
the "Virtual Host Monster *Mappings* Tab" and "Inside-Out Virtual
Hosting" sections below.

It is possible to modify the VHM settings from the command line
via Zope debugger;  no documentation for the low-level API
exists, however, except "the source",
'Products.SiteAccess.VirtualHostMonster.py,
which makes it an inadvisable choice for anyone but an experienced
Zope developer.

Special VHM Path Elements 'VirtualHostBase' and 'VirtualHostRoot'
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A Virtual Host Monster doesn't do anything unless it sees one
of the following special path elements in a URL:

'VirtualHostBase'
  if a VirtualHostMonster "sees" this name in the incoming URL, it causes
   Zope objects to generate URLs with a potentially different protocol, a
   potentially different hostname, and a potentially different port number.

'VirtualHostRoot'
  if a VirtualHostMonster "sees" this name in the incoming URL, it causes
   Zope objects to generate URLs which have a potentially different "path
   root"

'VirtualHostBase'
%%%%%%%%%%%%%%%%%

The 'VirtualHostBase' declaration is typically found at the
beginning of an incoming URL.  A Virtual Host Monster will
intercept two path elements following this name and will use
them to compose a new protocol, hostname, and port number.

The two path elements which must follow a 'VirtualHostBase'
declaration are 'protocol' and 'hostname:portnumber'.  They
must be separated by a single slash.  The colon and
portnumber parts of the second element are optional, and if
they don't exist, the Virtual Host Monster will not change
the port number of Zope-generated URLs.

Examples:

- If a VHM is installed in the root folder, and a request comes in to
  your Zope with the URL:

   'http://zopeserver:8080/VirtualHostBase/http/www.buystuff.com'

  URLs generated by Zope objects will start with
  'http://buystuff.com:8080'.

- If a VHM is installed in the root folder, and a request comes in to
  your Zope with the URL:

   'http://zopeserver:8080/VirtualHostBase/http/www.buystuff.com:80'

  URLs generated by Zope objects will start with 'http://buystuff.com'
  (port 80 is the default port number so it is left out).

- If a VHM is installed in the root folder, and a request comes in to
  your Zope with the URL:

   'http://zopeserver:8080/VirtualHostBase/https/www.buystuff.com:443'

  URLs generated by Zope objects will start with 'https://buystuff.com/'.
  (port 443 is the default https port number, so it is left off.

One thing to note when reading the examples above is that if
your Zope is running on a port number like 8080, and you
want generated URLs to not include this port number and
instead be served on the standard HTTP port (80), you must
specifically include the default port 80 within the
VirtualHostBase declaration, e.g.
'/VirtualHostBase/http/www.buystuff.com:80'.  If you don't
specify the ':80', your Zope's HTTP port number will be used
(which is likely not what you want).

'VirtualHostRoot'
%%%%%%%%%%%%%%%%%

The 'VirtualHostRoot' declaration is typically found near
the end of an incoming URL.  A Virtual Host Monster will
gather up all path elements which *precede* and *follow* the
'VirtualHostRoot' name, traverse the Zope object hierarchy
with these elements, and publish the object it finds with
the path rewritten to the path element(s) which *follow*
the 'VirtualHostRoot' name.

This is easier to understand by example.  For a URL
'/a/b/c/VirtualHostRoot/d', the Virtual Host Monster will
traverse "a/b/c/d" and then generate a URL with path /d.

Examples:

- If a VHM is installed in the root folder, and a request comes in to
  your Zope with the URL:

   'http://zopeserver:8080/Folder/VirtualHostRoot/

  The object 'Folder' will be traversed to and published,
  URLs generated by Zope will start with
  'http://zopeserver:8080/', and when they are visited, they
  will be considered relative to 'Folder'.

- If a VHM is installed in the root folder, and a request comes in to
  your Zope with the URL:

   'http://zopeserver:8080/HomeFolder/VirtualHostRoot/Chris

  The object '/Folder/Chris' will be traversed to and
  published, URLs generated by Zope will start with
  'http://zopeserver:8080/Chris', and when they are visited,
  they will be considered relative to '/HomeFolder/Chris'.

Using 'VirtualHostRoot' and 'VirtualHostBase' Together
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The most common sort of virtual hosting setup is one in which
you create a Folder in your Zope root for each domain that you
want to serve. For instance the site http://www.buystuff.com
is served from a Folder in the Zope root named /buystuff while
the site http://www.mycause.org is served from a Folder in the
Zope root named /mycause.  In order to do this, you need to
generate URLs that have both 'VirtualHostBase' and
'VirtualHostRoot' in them.

To access /mycause as http://www.mycause.org/, you would cause
Zope to be visited via the following URL::

  /VirtualHostBase/http/www.mycause.org:80/mycause/VirtualHostRoot/

In the same Zope instance, to access /buystuff as
http://www.buystuff.com/, you would cause Zope to be visited
via the following URL::

  /VirtualHostBase/http/www.buystuff.com:80/buystuff/VirtualHostRoot/

Testing a Virtual Host Monster
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Set up a Zope on your local machine that listens on HTTP port
8080 for incoming requests.

Visit the root folder, and select *Virtual Host Monster* from
the Add list.  Fill in the 'id' on the add form as 'VHM' and
click 'Add.'

Create a Folder in your Zope root named 'vhm_test'.  Within the
newly-created 'vhm_test' folder, create a DTML Method named
'index_html' and enter the following into its body::

   <html>
   <body>
   <table border="1">
     <tr>
       <td>Absolute URL</td>
       <td><dtml-var absolute_url></td>
     </tr>
     <tr>
       <td>URL0</td>
       <td><dtml-var URL0></td>
     </tr>
     <tr>
       <td>URL1</td>
       <td><dtml-var URL1></td>
     </tr>
   </table>
   </body>
   </html>

View the DTML Method by clicking on its View tab, and you will
see something like the following::

  Absolute URL   http://localhost:8080/vhm_test 
  URL0           http://localhost:8080/vhm_test/index_html
  URL1           http://localhost:8080/vhm_test 

Now visit the URL 'http://localhost:8080/vhm_test'.  You will be
presented with something that looks almost exactly the same.

Now visit the URL
'http://localhost:8080/VirtualHostBase/http/zope.com:80/vhm_test'.
You will be presented with something that looks much like this::

  Absolute URL   http://zope.com/vhm_test 
  URL0           http://zope.com/vhm_test/index_html
  URL1           http://zope.com/vhm_test

Note that the URLs that Zope is generating have changed.
Instead of using 'localhost:8080' for the hostname and path,
we've instructed Zope, through the use of a VirtualHostBase
directive to use 'zope.com' as the hostname.  No port is shown
because we've told Zope that we want to generate URLs with a
port number of 80, which is the default http port.

Now visit the URL
'http://localhost:8080/VirtualHostBase/http/zope.com:80/vhm_test/VirtualHostRoot/'.
You will be presented with something that looks much like this::

  Absolute URL   http://zope.com
  URL0           http://zope.com/index_html
  URL1           http://zope.com

Note that we're now publishing the 'vhm_test' folder as if it
were the root folder of a domain named 'zope.com'.  We did this
by appending a VirtualHostRoot directive to the incoming URL,
which essentially says "traverse to the vhm_root folder as if it
were the root of the site."

Arranging for Incoming URLs to be Rewritten
-------------------------------------------

At this point, you're probably wondering just how in the world
any of this helps you.  You're certainly not going to ask
people to use their browser to visit a URL like
'http://yourserver.com//VirtualHostBase/http/zope.com/vhm_test/VirtualHostRoot/'
just so your Zope-generated URLs will be "right".  That would
defeat the purpose of virtual hosting entirely.  The answer is:
don't ask humans to do it, ask your computer to do it.  There
are two common (but mutually exclusive) ways to accomplish
this: via the VirtualHostMonster *Mappings* tab and via Apache
"rewrite rules" (or your webserver's facility to do the same
thing if you don't use Apache).  Be warned: use either one of
these facilities or the other but not both or very strange
things may start to happen.  We give examples of using both
facilities below.

Virtual Host Monster *Mappings* Tab
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the Virtual Host Monster's *Mappings* tab to cause your
URLs to be rewritten if:

- You run a "bare" Zope without a front-end webserver like
  Apache.

- You have one or more folders in your Zope that you'd like
  to publish as "http://some.hostname.com/" instead of
  "http://hostname.com/a/folder".

The lines entered into the *Mappings* tab are in the form::

  www.example.com /path/to/be/rewritten/to

You can also match multiple subdomains by putting "\*." in front
of the host name in the mapping rule.  For example::

  *.example.com /folder 
  
This example  will match "my.example.com",
"zoom.example.com", etc. If an exact match exists, it is
used instead of a wildcard match.

The best way to explain how to use the *Mappings* tab is by
more specific example.  Assuming you've added a Virtual Host 
Monster object in your root folder on a Zope running on 'localhost'
on port 8080, create an alias in your local system's 'hosts'
file (in /etc/hosts on UNIX and in
c:\WINNT\system32\drivers\etc\hosts on Windows) that looks
like this::

  127.0.0.1 www.example.com

This causes your local machine to contact itself when a
hostname of 'wwww.example.com' is encountered.  For the sake
of this example, we're going to want to contact Zope via the
hostname 'www.example.com' through a browser (also on your
local host) and this makes it possible.

Then visit the VHM in the root folder and click on its
*Mappings* tab.  On a line by itself enter the following::

  www.example.com:8080/vhm_test

This will cause the 'vhm_test' folder to be published when
we visit 'http://www.example.com:8080'.  Visit
'http://www.example.com:8080'.  You will see::

  Absolute URL   http://www.example.com:8080
  URL0           http://www.example.com:8080/index_html
  URL1           http://www.example.com:8080

In the "real world" this means that you are "publishing" the
'vhm_test' folder as http://'www.example.com:8080'.

Note that it is not possible to rewrite the port part
(by default, '8080') of the URL this way. To change the
port Zope is listening on, you will have to configure
Zope's start parameter or use Apache rewriting.

Apache Rewrite Rules
~~~~~~~~~~~~~~~~~~~~

If you use Apache in front of Zope, instead of using the
*Mappings* tab, you should use Apache's rewrite rule
functionality to rewrite URLs in to Zope.  The way this
works is straightforward: Apache listens on its "normal"
port, typically port 80.  At the same time, Zope's web
server (on the same host or on another host) listens on a
different port (typically 8080).  Apache accepts requests on
its listening port.  A virtual host declaration in Apache's 
configuration tells Apache to apply the contained
directives to the specified virtual host.

Using Apache's rewrite rule functionality requires that the
'mod_rewrite' and 'mod_proxy' Apache modules be enabled.
This can for instance be done by configuring Apache with the
'--enable-modules="rewrite proxy"' flag during compile time or
by loading the corresponding shared modules.

If you are using the new Apache 2 series, you will also have
to include the 'mod_proxy_http' module. See the "Apache
mod_rewrite documentation",
https://httpd.apache.org/docs/current/mod/mod_rewrite.html
for details.

You can check whether you have the required modules installed
in Apache by examinint 'LoadModule' section of httpd.conf

After you've got Apache configured with mod_rewrite
and mod_proxy (and, depending on your Apache version,
mod_proxy_http), you can start configuring Apache's
config file and Zope for the following example.
Assuming you've added a Virtual Host Monster object in
your root folder on a Zope running on 'localhost' on
port 8080, create an alias in your local system's
'hosts' file (in /etc/hosts on UNIX and in
c:\WINNT\system32\drivers\etc\hosts on Windows) that
looks like this::

  127.0.0.1 www.example.com

This causes your local machine to contact itself when a
hostname of 'wwww.example.com' is encountered.  For the sake
of this example, we're going to want to contact Zope via the
hostname 'www.example.com' through a browser (also on your
local host) and this makes it possible.

Note:  On MacOS X Server, the 'Server Admin.app' program
simplifies adding virtual host definitions to your Apache.
This application can make and maintain virtual host , access
log, etc. 

Now, assuming you've got Apache running on port 80 and Zope
running on port 8080 on your local machine, and assuming
that you want to serve the folder named 'vhm_test' in Zope
as 'www.example.com' and, add the following to your Apache's
'httpd.conf' file and restart your Apache process::

  NameVirtualHost *:80
  <VirtualHost *:80>
  ServerName www.example.com
  RewriteEngine On
  RewriteRule ^/(.*) http://127.0.0.1:8080/VirtualHostBase/http/www.example.com:80/vhm_test/VirtualHostRoot/$1 [L,P]
  </VirtualHost>

If you want to proxy SSL to Zope, you need a similar directive
for port 443::

   NameVirtualHost *:443
   <VirtualHost *:443>
   ServerName www.example.com
   SSLProxyEngine on
   RewriteEngine On
   RewriteRule ^/(.*) http://127.0.0.1:8080/VirtualHostBase/https/www.example.com:443/vhm_test/VirtualHostRoot/$1 [L,P]
   </VirtualHost>

Note: the long lines in the RewriteRule directive above
*must* remain on a single line, in order for Apache's
configuration parser to accept it.


When you visit 'http://www.example.com' in your browser, you
will see::

  Absolute URL   http://www.example.com
  URL0           http://www.example.com/index_html
  URL1           http://www.example.com

This page is being served by Apache, but the results are
coming from Zope.  Requests come in to Apache with "normal"
URLs (e.g. 'http://www.example.com').  The VirtualHost
stanza in Apache's httpd.conf causes the request URL to be
rewritten (e.g. to
'http://127.0.0.1:8080/VirtualHostBase/http/www.example.com:80/vhm_test/VirtualHostRoot/').
Apache then calls the rewritten URL, and returns the result.

See the "Apache Documentation",
https://httpd.apache.org/docs/current/mod/mod_rewrite.html
for more information on the subject of rewrite rules.

Virtual Hosting Considerations for Content classes
--------------------------------------------------

Be sure that content objects catalog themselves using as their
unique ID a "site-relative" path, rather than their full physical
path;  otherwise, the object will be findable when using the site
without virtual hosting, but not with, or vice versa.

"Inside-Out" Virtual Hosting
----------------------------

Another use for virtual hosting is to make Zope appear to be
part of a site controlled by another server. For example, Zope
might only serve the contents of
'http://www.mycause.org/dynamic_stuff', while Apache or
another webserver serves files via
'http://www.mycause.org/'. To accomplish this, you want to add
"dynamic_stuff" to the start of all Zope-generated URLs.

If you insert VirtualHostRoot, followed by one or more path
elements that start with '_vh_', then these elements will be
ignored during traversal and then added (without the '_vh_')
to the start of generated URLs. For instance, a request for
"/a/VirtualHostRoot/_vh_z/" will traverse "a" and then
generate URLs that start with /z.

In our example, you would have the main server send requests
for http://www.mycause.org/dynamic_stuff/anything to Zope,
rewritten as /VirtualHostRoot/_vh_dynamic_stuff/anything.

