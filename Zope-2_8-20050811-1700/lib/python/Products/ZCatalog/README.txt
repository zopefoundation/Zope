ZCatalog

  Notes for Zope 2.0

    Catalog now comes with the Zope core, there is no need to install it.

  This is the ZCatalog product for the Z Object Publishing 
  Environment.

  ****** IMPORTANT ******

  This product contains no binaries, and should install
  identically on all platforms.

  Installation

    o Extract the distribution file into the top-level 
      directory of your Zope installation.

    o Restart your Zope installation.


 Notes for Zope 2.5
  
   Zope 2.5 now fully supports unicode. The unicode supports
   keyword indexes and text indexes.

     - Properties to be indexed using a KeywordIndex may 
       now contain strings and/or unicode strings. Queries
       on KeywordIndexes now support also unicode strings.


     - Properties to be indexed with a TextIndex can be either
       strings or unicode strings. The corresponding TextIndex
       *must* use a vocabulary that uses the new UnicodeSplitter.
       The UnicodeSplitter will not be the default splitter so 
       the standard vocabulary of the ZCatalog will not support
       unicode except it is replaced with a new vocabulary using
       the unicode splitter. When using an unicode-enabled TextIndex
       it is not neccessary that the corresponding attribute/method
       of the indexed object must be a unicode string. If it is
       a standard normal string then this string is converted
       to unicode using ISO-8859-1 encoding. A different encoding
       can be defined by an attribute '<attribute>_encoding' providing
       the encoding.


     - Using a KeywordIndex with unicode strings is slightly different.
       In general you can mix columns containing unicode strings and
       standard Python string to be indexed using a KeywordIndex. For
       internal reasons it is neccessary to change Pythons default
       encoding (set in site.py of the Python installation) if any
       to the keyword uses a non-ascii encoding (e.g. using accented
       characters). 

  Notes for Zope 2.8:

       reindexIndex() and refreshCatalog() accept a new optional parameter 
       'pghandler' which must be a handler instance implementing the 
       IProgressHandler interface (see ProgressHandler.py). This can be useful
       to provide logging during long running operations.

       Example to reindex a catalog using zopectl:

           > zopectl debug    
           
           From the zopectl shell: 

           > from Products.ZCatalog.ProgressHandler import StdoutHandler
           > from Products.ZCatalog.ProgressHandler import ZLogHandler
           >
           > # Reference to the portal catalog of some CMF site unter
           > # /cmfsite/portal_catalog
           > cat = app.cmfsite.portal_catalog
           >
           > # Refreshing a single index
           > cat.reindexIndex('SearchableText', None, pghandler=StdoutHandler())
           >
           > # Let's refresh the whole catalog
           > cat.refreshCatalog(pghandler=ZLogHandler())
           > 
           > # Don't forget to commit
           > import transaction
           > transaction.commit()
           

        The constructor of the handler can be given an optional parameter 
        'steps' (default is 100) that specifies after how much iterations 
        the progress should be reported.

        You might also checkout utilities/reindex_catalog.py (a script to perform
        ZCatalog maintenance operations from the command line).
         
