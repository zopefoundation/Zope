Maintenance information
========================

.. note::

   This is internal documentation for Zope 2 developer having
   to create official Zope 2 releases

Zope 2.12+ release process
--------------------------

- update version information:

  - setup.py
  - inst/versions.py
  - inst/WinBuilders/mk/zope.mk

- update docs/CHANGES.rst

- tag the release

- upload the tagged release to PyPI 

- create the release specfic download index on download.zope.org
  (requires login credentials on download.zope.org. In case of
  problems contact Jens Vagelpohl)
  
  - login to download.zope.org

  - change to user ``zope``::
    
     sudo su - zope

  - create the download index::
     
    /var/zope/zope2index/bin/z2_kgs tags/2.12.2 /var/www/download.zope.org/Zope2/index/2.12.2

- update version information on zope2.zope.org

  - login on https://zope2.zope.org into the Plone site  



