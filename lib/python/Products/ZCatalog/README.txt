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
       the unicode splitter.

