class ObjectManager:
    """
    An ObjectManager contains other Zope objects. The contained
    objects are Object Manager Items.
    """

    def objectIds(self, type=None):
        """
        This method returns a list of the ids of the contained
        objects.
        
        Optionally, you can pass an argument specifying what object
        meta_type(es) to restrict the results to. This argument can be
        a string specifying one meta_type, or it can be a list of
        strings to specify many.

        Example::

          <dtml-in objectIds>
            <dtml-var sequence-item>
          <dtml-else>
            There are no sub-objects.
          </dtml-in>

        This DTML code will display all the ids of the objects
        contained in the current Object Manager.

        Permission -- 'Access contents information'
        """

    def objectValues(self, type=None):
        """
        This method returns a sequence of contained objects.
        
        Like objectValues and objectIds, it accepts one argument,
        either a string or a list to restrict the results to objects
        of a given meta_type or set of meta_types.

        Example::

          <dtml-in "objectValues('Folder')">
            <dtml-var icon>
            This is the icon for the: <dtml-var id> Folder<br>.
          <dtml-else>
            There are no Folders.
          </dtml-in>

        The results were restricted to Folders by passing a 
        meta_type to 'objectItems' method.
        
        Permission -- 'Access contents information'
        """

    def objectItems(self, type=None):
        """
        This method returns a sequence of (id, object) tuples.
        
        Each tuple's first element is the id of an object contained in
        the Object Manager, and the second element is the object
        itself.
        
        Example::

          <dtml-in objectItems>
           id: <dtml-var sequence-key>,
           type: <dtml-var meta_type>
          <dtml-else>
            There are no sub-objects.
          </dtml-in>
          
        Permission -- 'Access contents information'
        """

    def superValues(self, t):
        """
        This method returns a list of objects of a given meta_type(es)
        contained in the Object Manager and all its parent Object
        Managers.
        
        The t argument specifies the meta_type(es). It can be a string
        specifying one meta_type, or it can be a list of strings to
        specify many.
        
        Permission -- Python only
        """
