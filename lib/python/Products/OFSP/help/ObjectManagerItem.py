class ObjectManagerItem:
    """
    A Zope object that can be contained within an Object Manager.
    Almost all Zope objects that can be managed through the web are
    Object Manager Items.

    Attributes

      'id' -- The id of the object.

         This is the unique name of the object within its parent
         object manager. This should be a string, and can contain
         letters, digits, underscores, dashes, commas, and spaces.
         
         This attribute should not be changed directly.

      'title' -- The title of the object.
      
        This is an optional one-line string description of the object.

      'meta_type' --  A short name for the type of the object.
      
        This is the name that shows up in product add list for the
        object and is used when filtering objects by type.
        
        This attribute is provided by the object's class and should
        not be changed directly.

      'REQUEST' -- The current web request.
      
        This object is acquired and should not be set.
    """
    
    def title_or_id(self):
        """
        If the title is not blank, return it, otherwise
        return the id.
        
        Permission -- 'Allways accessable'
        """

    def title_and_id(self):
        """
        If the title is not blank, the return the title
        followed by the id in parentheses. Otherwise return the id.

        Permission -- 'Allways accessable'
        """

    def manage_workspace(self):
        """

        This is the web method that is called when a user selects an
        item in a object manager contents view or in the Zope
        Management navigation view.

        """
  
    def this(self):
        """
        Return the object.
        
        This turns out to be handy in two situations. First, it
        provides a way to refer to an object in DTML expressions.

        The second use for this is rather deep. It provides a way to
        acquire an object without getting the full context that it was
        acquired from.  This is useful, for example, in cases where
        you are in a method of a non-item subobject of an item and you
        need to get the item outside of the context of the subobject.

        Permission --
        """

    def absolute_url(self, relative=None):
        """
        Return the absolute url to the object.

        If the relative argument is provided with a true value, then
        the URL returned is relative to the site object. Note, if
        virtual hosts are being used, then the path returned is a
        logical, rather than a physical path.
        
        Permission --Allways available
        """

    def getPhysicalRoot(self):
        """
        Returns the top-level Zope Application object.
        
        Permission --Python only
        """

    def getPhysicalPath(self):
        """
        Get the path of an object from the root, ignoring virtual
        hosts.

        Permission -- Python only

        """

    def unrestrictedTraverse(self, path, default=None):
        """
        Return the object obtained by traversing the given path from
        the object on which the method was called. This method begins
        with "unrestricted" because (almost) no security checks are
        performed.

        """

    def restrictedTraverse(self, path, default=None):
        """
        Return the object obtained by traversing the given path from
        the object on which the method was called, performing security 
        checks along the way.

        """


    
