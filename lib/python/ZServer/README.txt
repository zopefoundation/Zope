ZServer Release 1.0a1
---------------------

Welcome to the first Zope ZServer alpha release. This release provides
a first look at Zope/Medusa integration, and introduces FTP support in
Zope.

What is ZServer?
  
  ZServer is an integration of the Zope application server and the
  Medusa information server. See the ZServer architecture document for
  more information.::
  
  http://www.zope.org/Documentation/Reference/ZServer
    
  ZServer gives you HTTP and FTP access. In later releases it will
  probably offer more protocols such as PCGI, WebDAV, etc.

What is Medusa?

  Medusa is a Python server framework with uses a single threaded
  asynchronous sockets approach. For more information see::
  
    http://www.nightmare.com/medusa
  
  There's also an interesting Medusa tutorial at::
  
    http://www.nightmare.com:8080/nm/apps/medusa/docs/programming.html

ZServer FTP support

  FTP access to Zope allows you to FTP to the Zope object hierarchy in
  order to perform managerial tasks. You can:
  
    * Navigate the object hierarchy with 'cd'
    * Replace the content of Documents, Images, and Files
    * Create Documents, Images, Files, Folders
    * Delete any sort of object

  So basically you can do more than is possible with PUT. Also, unlike
  PUT, FTP gives you access to Document content. So when you download
  a Document you are getting its content, not what it looks like when
  it rendered.

  FTP permissions

    FTP support is provided for Folders, Documents, Images, and Files.
    You can control access to FTP via the new 'FTP access' permission.
    This permission controls the ability to 'cd' to a Folder and to
    download objects. Uploading and deleting and creating objects are
    controlled by existing permissions.

  Properties and FTP: The next step

    The next phase of FTP support will allow you to edit properties of
    all Zope objects. Probably properties will be exposed via special
    files which will contain an XML representation of the object's
    properties. You could then download the file, edit the XML and
    upload it to change the object's properties.

    We do not currently have a target date for FTP property support.
    It will probably need to wait until Zope has property sheets.

Differences between ZopeHTTPServer and ZServer

  Both ZopeHTTPServer and ZServer are Python HTTP servers.
  ZopeHTTPServer is built on the standard Python SimpleHTTPServer
  framework. ZServer is built on Medusa.

  ZopeHTTPServer is very limited. It can only publish one module at a
  time. It can only publish via HTTP. It has no support for thread
  pools. And more importantly, it is no longer being actively
  developed, since its author has moved on the ZServer.
  
  ZServer on the other hand is more complex and supports publishing
  multiple modules, thread pools, and it uses a new threaded
  architecture for accessing ZPublisher. Right now the thread pool is
  limited to one thread, since the object database cannot yet support
  concurrent access. This should change within the next few months.

How does FTP work?

  The ZServer's FTP channel object translates FTP requests into
  ZPublisher requests. The FTP channel then analyses the response and
  formulates an appropriate FTP response. The FTP channel stores some
  state such as the current working directory and the username and
  password.
  
  On the Zope side of things, the 'FTPSupport.py' module provides a
  few mix-in classes for Document, Folder, and File (which Image
  inherits from). These mix in classes provide directory listing and
  stat-like methods. All the other FTP functions are handled by
  existing methods like 'manage_delObjects', and 'PUT', etc.

Who should use ZServer?

  This release is *alpha* quality. It should be used by Zope hackers.
  If you are not inquisitive and self-reliant, this release will
  frustrate you.

Installation

  To install ZServer you need to do two things: edit the start script
  and update some Zope files to introduce FTP support.
  
  To edit the start up script, open 'start.py' in your favorite editor
  and change the configuration variables. If you understand Medusa,
  you can also change the rest of the script.
  
  To enable FTP support in Zope you need to update some files in
  'lib/python/OFS'. You should probably first back up your 'OFS'
  directory, or at least make copies of the files that will be
  replaced ('Document.py', 'Image.py', 'Folder.py'). Then copy the
  contents of ZServer's 'OFS' directory to your Zope 'lib/python/OFS'
  directory.
  
  Finally make sure the shebang line is right on the start script. You
  can use your own copy of Python, or the copy that came with Zope (if
  you are using a binary distribution).
  
  Now your ready to go.  

Usage

  To start ZServer run the start script::
  
    ./start.py
    
  To stop the server type 'control-c'.

  You should see some logging information come up on the screen.  

  Once you start ZServer is will publish Zope (or any Python module)
  on HTTP and/or FTP. To access Zope via HTTP point your browser at
  the server like so::
  
    http://www.example.com:9673/Main
    
  This assumes that you have chosen to put HTTP on port 9673 and that
  you are publishing a module named 'Main'. Note: to publish Zope
  normally you publish the 'lib/python/Main.py' module.

  To access Zope via FTP you need to FTP to it at the port you set FTP
  to run on. For example::
  
    ftp www.example.com 8021

  This starts and FTP session to your machine on port 8021, ZServer's
  default FTP port. When you are prompted to log in you should supply
  a Zope username and password. (Probably you should use an account
  with the 'Manager' role, unless you have configured Zope to allow
  FTP access to the 'Anonymous' role.) You can also enter 'anonymous'
  and any password for anonymous FTP access. Once you have logged in
  you can start issuing normal FTP commands. Right now ZServer only
  supports basic FTP commands. Note: When you log in your working
  directory is set to '/'. If you do not have FTP permissions in this
  directory, you will need to 'cd' to a directory where you have
  permissions before you can do anything.

Support

  Questions and comments should go to 'support@digicool.com'.

  You can report bugs and check on the status of bugs using the Zope
  bug collector.::
    
    http://www.zope.org/Collector/

License

  ZServer is covered by the ZPL despite the fact that it comes with
  much of the Medusa source code. The portions of Medusa that come
  with ZServer are licensed under the ZPL.

Outstanding issues

  PCGI support is not done yet. The FTP interface for Zope objects may
  be changed, i.e. 'manage_FTPlist' and 'manage_FTPstat' maybe changed
  and/or renamed. When FTP support for properties is added, this may
  change a lot. WebDAV support will also probably cause a little
  reorganization.
  
  Currently ZServer's Medusa files are a bit modified from the
  originals. It would be good idea to try and keep deviations to a
  minimum. For this reason we have been feeding bug reports and change
  requests back to Sam Rushing for inclusion in the official Medusa
  souces. It is possible, however, that Medusa and ZServer will
  diverge in some small respects despite our best efforts to keep them
  unified. One area in particular where ZServer currently departs from
  Medusa is in the use of future producers. Change is likely in
  ZServer's use of future producers.
