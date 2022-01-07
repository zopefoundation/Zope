Introducing Zope
================

.. include:: includes/zope2_notice.rst

Zope is family of related Python packages focussed on web technologies. The
first version of Zope has originated from a company called
Digital Creations, which later morphed into Zope Corporation.

Today the `Zope Foundation <https://www.zope.dev/community.html>`_ and its
successor, the `Plone Foundation <https://plone.org/foundation>`_, hold the
copyright of the Zope source code and supervises a diverse community of
open-source contributers working on a variety of related projects.

This book is about the original Zope project as opposed to the discontinued
`Zope 3`. When we refer to Zope in this book without a narrower specification
we speak of Zope 2 and its successors (Zope 4, Zope 5 and higher).

Other projects include the
`Zope Toolkit <https://zopetoolkit.readthedocs.io/en/latest/>`_ libraries
and many individual packages located in the
`zopefoundation GitHub organization <https://github.com/zopefoundation>`_ as
well as projects being based on or related to these packages. One of the more
widely known applications based on top of Zope is the content management system 
`Plone <https://plone.org/>`_.

Zope itself is a web framework that allows developers of varying skill
levels to build *web applications*. This chapter explains Zope's purpose,
what problems it solves and what audience it targets in greater detail.
It also describes what makes Zope different and more powerful than
similar applications.

*NOTE*: The moniker "Zope" stands for the *Z Object Publishing
Environment* (the "Z" doesn't really mean anything in particular).

The Static Web Site Dilemma
---------------------------

When a company or organization goes through the process of developing and
eventually deploying a website, one of its most important goals is to
present timely and up-to-date information to its website visitors.

Let us consider two examples of such time-dependent sites:

- a stock market information site that needs to be updated with
  new information continually, maybe as often as every five or 10
  minutes. It will also present information tailored to each
  visitor's preferred settings (portfolios, stocks to follow, etc.)

- a commercial website that helps its visitors sell and buy used
  automobiles. It is usually required that such a site run
  advertisements only for cars that have not yet been sold.  It is
  also important that new ads be posted immediately after
  they've been placed by a seller.

These two examples describe two very different sites that
nevertheless have one basic requirement in common: automated and
periodic updates of the information presented. If this single
requirement is not met, these sites will likely be
unsuccessful.

So, how does Zope work to fulfill such a requirement? To understand
this, we need to consider how websites are perceived by their
visitors and the basic ways in which websites can be constructed.

In general, many website visitors think about navigation in terms
of moving "from page-to-page" within a website.  When they click
a hyperlink, their browser transports them to a new page.  When they
hit their browser's *back* button, they are returned to the last page
they visited, and so on.

Some websites are *static*. A static website stores its
information in files on a web server. Each file then represents a
complete page on the website. This may seem like a simple and
efficient way of creating a website; however, *updating the
information* within those pages becomes a problem when the site consists of
more than a few pages, and the pages, or parts of the pages, need to be updated 
frequently.

The layout of text and images that are displayed in a user's web browser
when the user visits a website are commonly composed in a simple
language known as Hyper Text Markup Language (HTML). When a user
visits a typical website, a chunk of text that is "marked-up"
with formatting in HTML is transferred between the website and the user's
browser. The browser interprets the chunk of text and displays text
and images to the user.  The chunk of text which is transferred is
typically referred to as a *page*.

To achieve this, the static website requires a person with a
privileged level of access (sometimes termed the *webmaster*) to
manually create and update the site's content.

Typically, this is done by editing a set of text-based files on the *web
server* (the machine that runs the website), where each file
represents a single page. In some cases, a site-wide change to the "look-and-feel"
of a static website requires that the webmaster visit and update
each and every file that comprises the website.

The webmaster responsible for our automobile advertising website
has the additional responsibility of keeping the ads themselves
fresh.  If each page in the website represents an ad for a
particular automobile, he needs to delete the pages representing
ads that have expired and create new pages for ads that have been
recently sold.  He then needs to make sure that no hyperlinks on
other pages point to any of these deleted pages.

Obviously, this quickly becomes a lot of work.  With any more than a 
few pages to update each day, this type of repetitive work 
can become pretty dull.  In addition, being a human being, the webmaster 
may also make mistakes, such as forgetting to update or remove
critical pages.  While updating a static website with only 10 to 20
pages might be dull, it's perfectly manageable.  However, websites
can typically grow to encompass thousands of files, making the
process of "timely updates" a non-trivial (and sometimes
impossible) task.

Somewhere down the line, smart webmasters begin to think to
themselves, "Wow, this is a lot of work.  It's tedious and
complicated, and I seem to be making a lot of mistakes.  Computers
are really good at doing tedious and complicated tasks, and they
don't make very many mistakes.  I bet my web server computer could
automatically do a lot of the work I now do manually."  And he would 
be right.

At this point, the webmaster is ready to be introduced to *web
applications*. It is in this area where Zope's strength and power
becomes clear.


What Is A Web Application?
--------------------------

A *web application* is a computer program that users invoke by
using a web browser to contact a web server via the Internet. Users
and browsers are typically unaware of the difference between
a web server that fronts a statically-built website
and one that fronts a web application.  But unlike a
static website, a web application creates its "pages"
*dynamically*, or on-the-fly, upon request.  A website that is dynamically-
constructed uses an a computer program to provide its content.
These kinds of dynamic applications can be written in any number of
computer languages.

Web applications are everywhere.  Common examples of web
applications are those that let you search the web, like *Google*;
collaborate on projects, like *SourceForge*; buy
items at an auction, like *eBay*; communicate with other people over
e-mail, like *Gmail*; or view the latest news ala *CNN.com*.

In a dynamically-constructed website, the webmaster is not
required to visit the site "page-by-page" in order to update its
content or style.  Instead, he is able to instruct the web server
to *generate the site's HTML pages dynamically*, where each page is
made up of different bits of content. While each bit of content is
unique, each can nevertheless appear in several pages if so 
instructed by the web server. In this way, the webmaster is able to create
a common "look and feel" for the set of pages that make up his
site. The software on the web server that generates these
pages is the web application.

If our auto-classifieds webmaster chose to construct a web
application to maintain his classifieds system, he could maintain a
list of "current" ads separate from the HTML pages, perhaps stored
in a database of some kind.  He could then instruct his web
application to query this database and generate a particular chunk
of HTML that represented an ad, or an index of ads, when a user
visited a page in his website.

A framework that allows people to construct a web application is often called a
*web application server*, or sometimes just an *application server*. Zope is a
web application server, as are competing products like `WebSphere
<https://www.ibm.com/cloud/websphere-application-server>`_,
`JBoss <https://www.jboss.org/>`_,
and (to some extent)
`SAP NetWeaver <https://www.sap.com/products/netweaver-platform.html>`_.

Zope is a web application server, which is not
a web application in itself; rather it is *framework that allows
people to construct web applications*. Sometimes this framework is
called an *application server*.

Using some common computer programming language, an application
server typically allows a developer to create a web application,
but it also provides services *beyond* the basic capabilities of
the programming language used. Examples of such services are web
page template creation facilities, a common security model, data
persistence, sessions, and other features that people find useful
when constructing a typical web application.


How You Can Benefit From Using An Application Server
----------------------------------------------------

If you are considering writing even a moderately-sized web
application, it is typically a good idea to start your project
using an application server framework, unless your application
requirements are extremely specialized.  By starting a web
application project with an application server framework (as
opposed to a "raw" computer language, such as Java, Perl, Python, or
C), you are able to utilize the services of the framework that have
already been written and proven to work, and you avoid the need to
write the functionality yourself "from scratch" in a "raw"
language.

Many application servers allow you to perform some of the following tasks:

Present Dynamic Content -- You may tailor your web site's
presentation to its users and provide users with search features.
Application servers allow you to serve dynamic content and typically
come with facilities for personalization, database integration,
content indexing, and searching.

Manage Your Web Site -- A small web site is easy to manage, but a
web site that serves thousands of documents, images, and files
requires heavy-duty management tools. It is useful to be able to
manage your site's data, business logic, and presentation from a
single place.  An application server can typically help manage
your content and presentation in this way.

Build a Content Management System -- A *content management system* allows
non-technical editors to create and manage content for your website.
Application servers provide the tools with which you can build a
content management system.

Build an E-Commerce Application -- Application servers provide a
framework in which sophisticated e-commerce applications can be
created.

Securely Manage Contributor Responsibility -- When you deal with
more than a handful of web users, security becomes very important.
You must be able to safely delegate tasks to different
classes of system users. For example, folks in your engineering
department may need to be able to manage their web pages and
business logic, designers may need to update site templates, and
database administrators need to manage database queries.
Application servers typically provide a mechanism for access
control and delegation.

Provide Network Services -- You may want to produce or consume
*network services*.  A network service-enabled web site must
to be able to accept requests from other computer programs.  For
example, if you're building a news site, you may wish to share
your news stories with another site; you can do this by making
the news feed a network service.  Or perhaps you want to make
products for sale on your site automatically searchable from a
product comparison site.  Application servers 
offer methods for enabling these kinds of network services.

Integrate Diverse Systems -- Your existing content may be
contained in many places: relational databases, files, separate
web sites, and so on.  Application servers typically allow you
to present a unified view of your existing data by integrating
diverse, third-party systems.

Provide Scalability -- Application servers allow your web
applications to scale across as many systems as necessary to
handle the load demands of your sites.

The Zope application server allows you to perform all of these
tasks.


Why Use Zope Instead of Another Application Server
--------------------------------------------------

If you're in the business of creating web applications, Zope can
potentially help you create them at less cost and at a faster rate
than you could by using another competing web application server.
This claim is backed by a number of Zope features:

- Zope is free of cost and distributed under an open-source
  license.  There are many non-free commercial application servers
  that are relatively expensive.

- Zope itself is an inclusive platform.  It ships with all the
  necessary components to begin developing an application.  You
  don't need to license extra software to support Zope (e.g., a
  relational database) in order to develop your application.  This
  also makes Zope very easy to install.  Many other application
  servers have "hidden" costs by requiring that you license
  expensive software or configure complex, third-party
  infrastructure software before you can begin to develop your
  application.

- Zope allows and encourages third-party developers to package and
  distribute ready-made applications.  Due to this, Zope has a
  wide variety of integrated services and add-on packages
  available for immediate use.  Most of these components, like
  Zope itself, are free and open-source.  Zope's popularity has
  bred a large community of application developers.

- Applications created in Zope can scale almost linearly using
  Zope's built-in "Zope Enterprise Objects" (ZEO) clustering
  solution.  Using ZEO, you can deploy a Zope application across
  many physical computers without needing to change much (if any)
  of your application code.  Many application servers don't scale
  quite as transparently or as predictably.

- Zope provides a granular and extensible security framework.  You
  can easily integrate Zope with diverse authentication and
  authorization systems, such as LDAP, Kerberos, and RADIUS,
  simultaneously and using pre-built modules.  Many other application
  servers lack support for important authentication and
  authorization systems.

- Zope runs on most popular microcomputer operating system
  platforms: Linux, Windows, Solaris, FreeBSD, NetBSD,
  OpenBSD, and Mac OS X.  Many
  other application server platforms require that you run an
  operating system of their licensor's choosing.

- Zope can be extended using the interpreted `Python <https://www.python.org/>`_
  scripting language. Python is popular and easy to learn, and it promotes
  rapid development. Many libraries are available for Python that can be used
  when creating your own application. Many other application servers must be
  extended using compiled languages, such as Java, which cuts down on
  development speed. Many other application servers use less popular languages
  for which there are not as many ready-to-use library features.


Zope Audiences and What Zope Isn't
----------------------------------

Managing the development process of a large-scale site can be a
difficult task. It often takes many people working together to
create, deploy, and manage a web application.

*Information Architects*
  make platform decisions and keep track of the "big picture".

*Component Developers*
  create software intended for reuse and distribution.

*Integrators*
  integrate the software written by component developers and native
  application server services, building an application in the process.

*Web Designers*
  create the site's look and feel.

*Content Managers*
  create and manage the site's content.

*Administrators*
  keep the software and environment running.

*Consumers*
  use the site to locate and work with useful content.

Of the parties listed above, Zope is most useful for *component
developers*, *integrators*, and *web designers*.  These three
groups can collaborate to produce an application using
Zope's native services and third-party Zope *Plugins*.  They 
typically produce applications useful to *content managers* and
*consumers* under the guide of the *information architect*.
*Administrators* deploy the application and tend to the
application after it is has been created.

Note that Zope is a web application construction framework that
programmers of varying skill levels may use to create web-based
applications.  It *is not* itself an application that is ready to
use "out of the box" for any given application.  For example, Zope
itself is not a blog, a content management system, or a
"e-shop-in-a-box" application.

However, freely available *Plugins* built on top of Zope offer these kinds of
services. At the time of this writing, the `Python Package Index
<https://pypi.org/>`_ lists roughly 1700 `Plugins that you can browse
<https://pypi.org/search/?q=&o=&c=Framework+%3A%3A+Zope>`_
and even reuse in your own
applications. These include Plugins for blogging, content management,
internationalization, and e-commerce.

Zope is not a visual design tool.  Tools like Macromedia
Dreamweaver and Adobe GoLive allow designers to create "look and
feel".  You may use these tools to successfully manage Zope-based
web sites, but Zope itself does not replace them.  You can edit
content "through the web" using Zope, but it does not try to replace the
features offered by these kind of tools.


Introduction to Zope Maintenance and The Zope Community
-------------------------------------------------------

A community of developers is responsible for maintaining and
extending the Zope application server.  Many community members are
professional consultants, developers, and webmasters who develop
applications using Zope for their own gain.  Others are students
and curious amateur site developers.  Zope Corporation is a member
of this community.

The Zope Foundation controls the distribution of the defacto,
"canonical", official Zope version, and permits its developers, as
well as other selected developers, to modify the distribution's
source code.

The Zope community gets together occasionally at conferences, but it
commonly discusses all things Zope on the many Zope mailing
lists and web sites. You can find out more about Zope-related
mailing lists at https://mail.zope.dev/mailman/listinfo.

Zope Corporation makes its revenue by using Zope to create web
applications for its paying customers, by training prospective
Zope developers, by selling support contracts to companies who use
Zope, and by hosting Zope-powered websites; it does not make any
direct revenues from the distribution of the Zope application
server itself.


Zope's Terms of Use and License
-------------------------------

Zope is free of cost. You are permitted to use Zope to create and run your web
applications without paying licensing or usage fees. You may also include Zope
in your own products and applications without paying royalty fees to Zope's
licensor, *Zope Foundation*.

Zope is distributed under an open source license, the `Zope Public License or
'ZPL' <https://opensource.org/licenses/ZPL-2.1>`_. The terms of the ZPL license
stipulate that you will be able to obtain and modify the source code for Zope.

The ZPL is different than another popular open source license, the `GNU Public
License <https://www.gnu.org/licenses/licenses.html>`_. The licensing terms of
the GPL require that if
you intend to redistribute a GPL-licensed application, and you modify or extend
the application in a meaningful way, when you `redistribute
<https://www.gnu.org/licenses/gpl-faq.html>`_ a
GPL-licensed application, you must distribute it under the terms of the GPL,
including licensing any modifications or extensions you make under the GPL. You
must also provide the full source code, including source for your
modifications.

However, this is *not* required for ZPL-licensed applications. You may modify
and redistribute Zope without contributing your modifications back to Zope
Corporation, as long as you follow the other terms of the license faithfully.

Note that the ZPL has been `certified`_ as `OSD`_ compliant by the
`Open Source Initiative`_ and is listed as `GPL compliant`_ by the
`Free Software Foundation`_.

.. _certified: https://opensource.org/licenses/ZPL-2.1
.. _OSD: https://opensource.org/osd
.. _Open Source Initiative: https://opensource.org/
.. _GPL compliant: https://www.gnu.org/licenses/license-list.html#GPLCompatibleLicenses
.. _Free Software Foundation: https://www.fsf.org/


Zope History
------------

In 1996, Jim Fulton (the current CTO of Zope Corporation, the orginators of
Zope) was drafted to teach a class on CGI programming, despite not knowing very
much about the subject. CGI, or *common gateway interface*, programming is a
commonly-used web development model that allows developers to construct dynamic
websites. Jim studied all of the existing documentation on CGI on his way to
the class. On the way back from the class, Jim considered what he didn't like
about traditional, CGI-based programming environments. From these initial
musings, the core of Zope was written on the plane flight back from the class.

Zope Corporation (then known as Digital Creations) went on to release three
open-source software packages to support web publishing: *Bobo*, *Document
Template*, and *BoboPOS*. These packages were written in a language called
Python, and respectively provided a web publishing facility, text templating,
and an object database. Digital Creations developed a commercial application
server based on their three open-source components. This product was called
*Principia*. In November of 1998, investor Hadar Pedhazur convinced Digital
Creations to open source Principia. These packages have evolved into what today
are the core components of Zope.

Most of Zope is written in the `Python <https://www.python.org/>`_ scripting
language, with performance-critical pieces written in C.
