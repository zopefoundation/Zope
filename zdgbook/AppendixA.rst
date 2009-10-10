#################################
Appendix A: Zope Core Permissions
#################################

This is a list of standard permissions included with Zope.  It is a
good idea to use these permissions when applicable with your Zope
products, rather than creating new ones.  A list of built-in Zope
permissions are available in Zope source code:
``src/AccessControl/Permissions.py``.

Core Permissions
================

- Access contents information -- get "directory listing" info

- Add Accelerated HTTP Cache Managers -- add HTTP Cache Manager objects

- Add Database Methods -- add ZSQL Method objects

- Add Documents, Images, and Files -- add DTML Method/Document objects,
  Image objects, and File objects

- Add External Methods  -- add External Method objects

- Add Folders -- add Folder objects

- Add MailHost objects  -- add MailHost objects

- Add Python Scripts  -- Add Python Script objects

- Add RAM Cache Managers  -- Add RAM Cache manager objects

- Add Site Roots -- add Site Root objects

- Add User Folders  -- add User Folder objects

- Add Versions  -- add Version objects

- Add Virtual Host Monsters  -- add Virtual Host Monster objects

- Add Vocabularies  -- add Vocabulary objects (ZCatalog-related)

- Add ZCatalogs  -- add ZCatalog objects

- Add Zope Tutorials  -- add Zope Tutorial objects

- Change DTML Documents -- modify DTML Documents

- Change DTML Methods  -- modify DTML Methods

- Change Database Connections  -- change database connection objects

- Change Database Methods  -- change ZSQL method objects

- Change External Methods -- change External Method objects

- Change Images and Files  -- change Image and File objects

- Change Python Scripts  -- change Python Script objects

- Change Versions  -- change Version objects

- Change bindings  -- change bindings (for Python Scripts)

- Change cache managers  -- change cache manager objects

- Change cache settings  -- change cache settings (cache mgr parameters)

- Change configuration  -- generic

- Change permissions  -- change permissions

- Change proxy roles  -- change proxy roles

- Create class instances  -- used for ZClass permission mappings

- Delete objects  -- delete objects

- Edit Factories  -- edit Factory objects (ZClass)

- FTP access  -- allow FTP access to this object

- Import/Export objects  -- export and import objects

- Join/leave Versions  -- join and leave Zope versions

- Manage Access Rules -- manage access rule objects

- Manage Vocabulary  -- manage Vocabulary objects

- Manage Z Classes  -- Manage ZClass objects (in the control panel)

- Manage ZCatalog Entries  -- catalog and uncatalog objects

- Manage properties -- manage properties of an object

- Manage users  -- manage Zope users

- Open/Close Database Connections  -- open and close database connections    

- Query Vocabulary -- query Vocabulary objects (ZCatalog-related)

- Save/discard Version changes -- save or discard Zope version changes

- Search ZCatalog -- search a ZCatalog instance

- Take ownership  -- take ownership of an object

- Test Database Connections  -- test database connection objects

- Undo changes  -- undo changes to the ZODB (e.g. use the Undo tab)

- Use Database Methods  -- use ZSQL methods

- Use Factories  -- use Factory objects (ZClass-related)

- Use mailhost services -- use MailHost object services

- View -- view or execute an object

- View History -- view ZODB history of an object

- View management screens -- view management screens related to an object
