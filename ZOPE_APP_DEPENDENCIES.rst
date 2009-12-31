Zope2 Dependencies on ``zope.app`` Packages
===========================================

Zope2 depends on the following zope.app packages directly:

- [X] zope.app.appsetup
      * Zope2.Startup
      * Zope.App.Startup

- [X] zope.app.component
      * Products.Five (meta.zcml)

- [X] zope.app.container
      * Products.Five.browser.adding (only indirect now)
      * Products.Five.browser.metaconfigure
      * Products/Five/browser/doc/products/ViewsTutorial/configure.zcml

- [X] zope.app.form
      x Products.Five.form.* (should be factored out into a separate
        package, maybe ``five.formlib``)

- [X] zope.app.pagetemplate 
      * Products.PageTemplates.Expressions
      * Products.Five.browser.pagetemplatefile
      * Products.Five.browser.metaconfigure

- [X] zope.app.publication
      * ZPublisher.BaseRequest (imports ``EndRequestEvent``)
      * Products.Five.component (imports ``BeforeTraverseEvent``;
        ZCML registers subscribers for ``IBeforeTraverseEvent``
        and ``IEndRequestEvent``)

- [X] zope.app.publisher 
      * ZPublisher.BaseRequest
      * Products.Five.browser.adding (for ``getMenu``)
      * Products/Five/browser/configure.zcml (for ``IMenuItemType``,
        ``MenuAccessView``, and ``IMenuAccessView``)
      * Products.Five.viewlet.metaconfigure (for ``viewmeta``)
      * Products.Five.form.metaconfigure (for ``menuItemDirective``)
      * Products.Five.fivedirectives (for ``IBasicResourceInformation``)

- [X] zope.app.schema 
      * Products.Five (imports ``zope.app.schema.vocabulary`` for
        side-effects ?!).

- [X] zope.app.twisted
      * Zope2.Startup.datatypes (conditionally imports ``ServerFactory``)
      * Zope2.Startup.handlers (conditionally imports ``ServerType``,
      ``SSLServerType``, ``IServerType``;  worse, conditionally imports
      ``zope.app.twisted.main`` for side effects, which includes pulling
      back ``zope.app.appsetup`` as well as adding ``zope.app.wsgi``?!)

This shell script can be used to verify the direct dependencies::

  #! /bin/bash
  python=$(find src/ -name "*.py" | xargs grep -l "zope\.app")
  zcml=$(find src/ -name "*.zcml" | xargs grep -l "zope\.app")
  doctest=$(find src/ -name "*.txt" | grep -v "egg-info" |
            xargs grep -l "zope\.app")
  for f in $python $zcml $doctest; do
      echo ====================================================
      echo $f
      echo ====================================================
      grep "zope\.app" $f
   done

Zope2 has transitive dependencies on these packages:

- [X] zope.app.applicationcontrol 
      * zope.traversing
      * zope.app.publication
      * zope.app.twisted

- [X] zope.app.basicskin 
      * zope.app.form

- [X] zope.app.dependable 
      * zope.container
      * zope.app.testing

- [X] zope.app.exception 
      * zope.app.publication

- [X] zope.app.http 
      * zope.app.publication

- [X] zope.app.interface 
      * zope.app.component

- [X] zope.app.pagetemplate
      x zope.viewlet
      x zope.formlib

- [X] zope.app.security 
      * zope.viewlet
      * zope.traversing
      * zope.testbrowser
      * zope.app.*

- [X] zope.app.testing 
      * zope.viewlet
      * zope.copypastemve
      * zope.error
      * zope.dublincore
      * zope.formlib
      * zope.traversing
      * zope.testbrowser
      * zope.site
      * zope.app.*

Zope2 Dependencies on ``zope`` Packages
=======================================

Zope2 depends on some packages only via transitive test dependencies.

- [X] zope.copy
      * zope.location
      * zope.site
      * zope.copypastemove

- [X] zope.copypastemove
      * zope.container

- [ ] zope.datetime
      o zope.app.form
      * zope.dublincore

- [X] zope.dublincore
      * zope.lifecycleevent


Questionable dependencies
=========================

- [X] zope.authentication (seems to be used for some ILogin related stuff)
      x zope.publisher

- [ ] zope.broken (this is really just one interface, merge into ZODB3?)
      o zope.container

- [ ] zope.cachedescriptors (this is only used for the Lazy implementation)
      o zope.container
      o zope.formlib

- [ ] zope.deferredimport (we should stop using it)
      o Zope2

- [ ] zope.filerepresentation (only used for the IDirectoryFactory interface)
      o zope.container
      o zope.site

Further merge tasks
===================

- [ ] zope.exceptions
      Our own zExceptions should be merged with it in some way. There's a good
      deal of similar code.

Security
========

The relationship between AccessControl and zope.security is unclear. Right now
Five plugs in AccessControl into the zope.security machinery. But large parts
of it aren't applicable like the entire zope.proxy machinery. The specific way
of how "interactions" work with the zope.publisher are also pretty muddy.

- [ ] zope.proxy
      o zope.annotation
      o zope.app.form
      o zope.browserresource
      o zope.component
      o zope.deferredimport
      o zope.location
      o zope.pagetemplate
      o zope.publisher
      o zope.security
      o zope.traversing

- [ ] zope.security
      o zope.app.form
      o zope.authentication
      o zope.browsermenu
      o zope.browserpage
      o zope.browserresource
      o zope.component
      o zope.container
      o zope.formlib
      o zope.pagetemplate
      o zope.ptresource
      o zope.publisher
      o zope.sendmail
      o zope.traversing
      o zope.viewlet
