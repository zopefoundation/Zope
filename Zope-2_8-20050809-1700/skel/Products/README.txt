Zope Content Management Framework (CMF) README

  What is the CMF?

    The Zope Content Management Framework provides a set of
    services and content objects useful for building highly
    dynamic, content-oriented portal sites.  As packaged, the
    CMF generates a site much like the Zope.org site.  The CMF is
    intended to be easily customizable, in terms of both the
    types of content used and the policies and services it
    provides.

  Resources

    General

      - The mailing list, "zope-cmf@zope.org",
        mailto:zope-cmf@zope.org.
      
        o List information and online signup are available at the
          list's "Mailman information page",
	      http://lists.zope.org/mailman/listinfo/zope-cmf.
        
        o Archives of the list are at the "Pipermail archive",
          http://lists.zope.org/pipermail/zope-cmf.

      - The 'docs/' directory contains user-oriented documentation

    Developer

      - The CMFDefault package is an example application, built using
        the API and services defined in CMFCore.  You will probably want to
        alter it.  In the first instance, refer to the source of CMFDefault
        for usage examples, standard idioms, etc.

      - The API is documented in the 'interfaces/' directory of each
	    package.

      - Refer to the unit tests in the 'tests/' directory of each package
	    for usage examples.

    Known Issues

      - Please search the "CMF Collector", http://zope.org/Collectors/CMF
        for issues which are open against the CMF. You can also report
        issues there (please look for similar ones first!).

    Installation

      - Please see "Installing CMF":INSTALL.txt
