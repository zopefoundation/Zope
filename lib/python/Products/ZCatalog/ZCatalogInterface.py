from Zope.Interfaces.Interface import Interface
from OFS.FolderInterface import FolderInterface


class ZCatalog:
    """

    ZCatalog's support indexing and searching for Zope objects.  A
    ZCatalog is basically a collection of indexes.  The ZCatalog
    object is a web managble interface to add and delete indexes and
    to find objects to catalog.

    """

    __extends__ = (FolderInterface,)

    def catalog_object(self, obj, uid):
        """

        This method will catalog the object 'obj' with the unique id
        'uid'.  By convention, the 'uid' is the object's path in Zope, 
        but this is not set in stone.  This method returns nothing.

        """

    def uncatalog_object(self, uid):
        """

        This method will uncatalog any reference to 'uid'.  If the
        catalog has no reference to 'uid', an error will NOT be
        raised.  This method returns nothing.

        """

    def uniqueValuesFor(self, name):
        """

        Return a sequece of all uniquely indexed values in the index
        'name'.  'name' is a string that identifies the index you want 
        unique values for.  Note that some indexes do not support this 
        notion, and will raise an error if you call this method on
        them.  Currently, only FieldIndexes and KeywordIndexes support 
        the notion of uniqueValuesFor.

        """

    def getpath(self, rid):
        """

        Record objects returned by catalog queries have a special
        integer id called a 'record id' (rid).  It is often useful to
        ask the catalog what unique id (uid) this rid maps to.  Since
        the convention is for uids to be paths, this method is called
        getpath, although it is probably better named getuid.  This
        method returns the uid that maps to rid.

        """

    def getobject(self, rid, REQUEST=None):
        """

        This method works like getpath, except that it goes one step
        further and tries to resolve the path into the actual object
        that uid uniquely defines.  This method depends on uid being a
        path to the object, so don't use this if you use your own
        uids.  This method returns an object or raises an
        NotFoundError if the object is not found.

        """

    def schema(self):
        """

        This method returns a sequence of meta-data table names.  This 
        sequence of names is often refered to as the 'schema' for
        record objects.

        """

    def indexes(self):
        """

        This method returns a sequece of index names.

        """

    def index_objects(self):
        """

        This method returns a sequence of actual index objects.

        """

    def searchResults(self, REQUEST=None, **kw):
        """

        This is the main query method for a ZCatalog.  It is named
        'searchResults' for historical reasons.  This is usually
        because this method is used from DTML with the in tag, and it
        reads well::

          <dtml-in searchResults>
            <dtml-var id>
          </dtml-in>

        This is one way to call this method.  In this case, you are
        passing no argument explicitly, and the DTML engine will pass
        the 'REQUEST' object in as the first argument to this method.

        The REQUEST argument must be a mapping from index name to
        search term.  Like this:

          Catalog.searchResults({'id' : 'Foo'})

        This will search the 'id' index for objects that have the id
        'Foo'.  More than one index query can be passed at one time.
        The various queries are implicitly intersected, also know as
        'ANDed'.  So:

          Catalog.searchResults({'id' : 'Foo',
                                 'title' : 'Bar'})

        will search for objects that have the id 'Foo' AND the title
        'Bar'.  Currently unions ('ORing') is not supported, but is
        planned.

        searchResults returns a sequence of 'Record Objects'.  Record
        objects are descriptions of cataloged objects that match the
        query terms.  Record objects are NOT the objects themselves,
        but the objects themselvles can be found with the 'getobject'
        method.

        Record Objects have attributes that corespond to entries in
        the meta-data table.  When an object is cataloged, the value
        of any attributes it has that have the same name as a
        meta-data table entry will get recorded by the meta-data
        table.   This information is then stuffed into the record
        that is returned by the ZCatalog.

        """

    def getVocabulary(self):
        """

        This method returns the Vocabulary object being used by this
        ZCatalog.

        """

ZCatalogInterface=Interface(ZCatalog) # create the interface object

