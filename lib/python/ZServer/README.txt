ZServer README
--------------

What is ZServer?
  
  ZServer is an integration of the Zope application server and the
  Medusa information server. See the ZServer architecture document for
  more information::
  
    http://www.zope.org/Documentation/Reference/ZServer
    
  ZServer gives you HTTP, FTP, WebDAV, PCGI, and remote interactive
  Python access. In later releases it will probably offer more
  protocols such as FastCGI, etc.

What is Medusa?

  Medusa is a Python server framework with uses a single threaded
  asynchronous sockets approach. For more information see::
  
    http://www.nightmare.com/medusa
  
  There's also an interesting Medusa tutorial at::
  
    http://www.nightmare.com:8080/nm/apps/medusa/docs/programming.html

ZServer HTTP support

  ZServer offers HTTP 1.1 publishing for Zope. It does not support
  publishing files from the file system. You can specify the HTTP port
  using the -w command line argument for the z2.py start script. You
  can also specify CGI environment variables on the command line using
  z2.py

ZServer FTP support

  What you can do with FTP

    FTP access to Zope allows you to FTP to the Zope object hierarchy
    in order to perform managerial tasks. You can:

      * Navigate the object hierarchy with 'cd'
    
      * Replace the content of Documents, Images, and Files
    
      * Create Documents, Images, Files, Folders
    
      * Delete objects and Folders.

    So basically you can do more than is possible with HTTP PUT. Also,
    unlike PUT, FTP gives you access to Document content. So when you
    download a Document you are getting its content, not what it looks
    like when it is rendered.

  Using FTP
  
    To FTP into Zope, ZServer must be configured to serve FTP. By
    default ZServer serves FTP on port 9221. So to connect to Zope you
    would issue a command like so::
    
      $ ftp localhost 9221
      
    When logging in to FTP, you have some choices. You can connect
    anonymously by using a username of 'anonymous' and any password.
    Or you can login as a Zope user. Since Zope users are defined at
    different locations in the object hierarchy, authentication can be
    problematic. There are two solutions:
    
      * login and then cd to the directory where you are defined.
      
      * login with a special name that indicates where you are
      defined.
      
    The format of the special name is '<username>@<path>'. For
    example::
    
      joe@Marketing/Projects

  FTP permissions

    FTP support is provided for Folders, Documents, Images, and Files.
    You can control access to FTP via the new 'FTP access' permission.
    This permission controls the ability to 'cd' to a Folder and to
    download objects. Uploading and deleting and creating objects are
    controlled by existing permissions.

  FTP limits
  
    You can set limits for the number of simultaneous FTP connections.
    You can separately configure the number of anonymous and
    authenticated connections. Right now this setting is set in
    'ZServerFTP.py'. In the future, it may be more easy to configure.

  Properties and FTP: The next step

    The next phase of FTP support will allow you to edit properties of
    all Zope objects. Probably properties will be exposed via special
    files which will contain an XML representation of the object's
    properties. You could then download the file, edit the XML and
    upload it to change the object's properties.

    We do not currently have a target date for FTP property support.

  How does FTP work?

    The ZServer's FTP channel object translates FTP requests into
    ZPublisher requests. The FTP channel then analyses the response
    and formulates an appropriate FTP response. The FTP channel
    stores some state such as the current working directory and the
    username and password.

    On the Zope side of things, the 'lib/python/OFS/FTPInterface.py'
    module defines the Zope FTP interface, for listing sub-items,
    stating, and getting content. The interface is implemented in
    'SimpleItem', and in other Zope classes. Programmers will not
    need to implement the entire interface if they inherit from
    'SimpleItem'. All the other FTP functions are handled by
    existing methods like 'manage_delObjects', and 'PUT', etc.

ZServer PCGI support

  ZServer will service PCGI requests with both inet and unix domain
  sockets. This means you can use ZServer instead of
  'pcgi_publisher.py' as your long running PCGI server process. In the
  future, PCGI may be able to activate ZServer.
  
  Using PCGI instead of HTTP allows you to forward requests from
  another web server to ZServer. The CGI environment and HTTP headers
  are controlled by the web server, so you don't need to worry about
  managing the ZServer environment. However, this configuration will
  impose a larger overhead than simply using the web server as an HTTP
  proxy for ZServer.
  
  To use PCGI, configure your PCGI info files to communicate with
  ZServer by setting the PCGI_PORT, PCGI_SOCKET_FILE, and PCGI_NAME.
  The other PCGI settings are currently ignored by ZServer.

  ZServer's PCGI support will work with mod_pcgi.

ZServer monitor server

  ZServer now includes the Medusa monitor server. This basically gives
  you a remote, secure Python prompt. You can interactively access Zope.
  This is a very powerful, but dangerous tool. Be careful.
  
  To use the monitor server specify a monitor port number using the -m
  option with the z2.py start script. The default port is 9999.
  
  To connect to the monitor server use the 'ZServer/medusa/monitor_client.py'
  or 'ZServer/medusa/monitor_client_win32.py' script. For example::
  
    $ python2.1 ZServer/medusa/monitor_client.py localhost 9999
	
  You will then be asked to enter a password. This is the Zope super manager
  password which is stored in the 'access' file.
  
  Then you will be greeted with a Python prompt. To access Zope import
  the Zope module::
  
    >>> import Zope

  The Zope top level Zope object is available via the 'Zope.app' function::
  
    >>> a=Zope.app()

  From this object you can reach all other Zope objects as subobjects.
  
  Remember if you make changes to Zope objects and want those changes to be
  saved you need to commmit the transaction::

    >>> import transaction
    >>> transaction.commit()
	
ZServer WebDAV support

  WebDAV is a new protocol for managing web resources. WebDAV operates
  over HTTP. Since WebDAV uses HTTP, ZServer doesn't really have to do
  anything special, except stay out of Zope's way when handling WebDAV
  requests.
  
  The only major WebDAV client at this time is Internet Explorer 5. It
  works with Zope.

Differences between ZopeHTTPServer and ZServer

  ZopeHTTPServer is old and no longer being actively maintained.
  
  Both ZopeHTTPServer and ZServer are Python HTTP servers.
  ZopeHTTPServer is built on the standard Python SimpleHTTPServer
  framework. ZServer is built on Medusa.

  ZopeHTTPServer is very limited. It can only publish one module at a
  time. It can only publish via HTTP. It has no support for thread
  pools.
  
  ZServer on the other hand is more complex and supports publishing
  multiple modules, thread pools, and it uses a new threaded
  architecture for accessing ZPublisher.
  
Running ZServer as nobody

  Normally ZServer will run with the userid of the user who starts
  it. However, if ZServer is started by root, it will attempt to
  become nobody or any userid you specify with the -u argument to the
  z2.py start script.
 
  ZServer is similar to ZopeHTTPServer in these respects.

  If you run Zope with different userids you must be aware of
  permission issues. Zope must be able to read and write to the 'var'
  directory. If you change the userid Zope is running under you will
  probably need to change the permissions on the 'var' directory
  and the files in it in order for Zope to run under a different
  userid.

Support

  Questions and comments should go to 'support@digicool.com'.

  You can report bugs and check on the status of bugs using the Zope
  bug collector::
    
    http://www.zope.org/Resources/Collector/

License

  ZServer is covered by the ZPL despite the fact that it comes with
  much of the Medusa source code. The portions of Medusa that come
  with ZServer are licensed under the ZPL.

Outstanding issues

  The FTP interface for Zope objects may be changed.
  
  HTTP 1.1 support is ZServer is incomplete, though it should work for
  most HTTP 1.1 clients.
  
