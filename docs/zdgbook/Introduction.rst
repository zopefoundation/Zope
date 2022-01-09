############
Introduction
############

Overview
========

Zope is a free and open-source, object-oriented web application
server written in the Python programming language.  The term ZOPE is
an acronym for "Z Object Publishing Environment" (the Z doesn't
really mean anything in particular).  However, nowadays ZOPE is
simply written as Zope.  It has three distinct audiences.

*Site Managers*
  Individuals who use of Zope's "out of the box" features to build
  websites.  This audience is interested in making use of Zope's
  existing array of features to create content management solutions.
  They are generally less concerned about code
  reuse than the speed with which they can create a custom
  application or website.

*Developers*
  Individuals who wish to extend Zope to create highly customized
  solutions.  This audience is likely interested in creating highly
  reusable custom code that makes Zope do something new and
  interesting.

*Administrators*
  Individuals responsible for keeping a Zope site running and
  performing installations and upgrades.

This guide is intended to document Zope for the second audience,
Developers, as defined above.  If you fit more into the "user"
audience defined above, you'll probably want to start by reading `The
Zope Book <https://zope.readthedocs.io/en/latest/zopebook/>`_ .

Throughout this guide, it is assumed that you know how to program in
the Python programming language.  Most of the examples in this guide
will be in Python.  There are a number of great resources and books
for learning Python; the best online resource is the `python.org web
site <https://www.python.org/>`_ and many books can be found on the
shelves of your local bookstore.

Organization of the book
========================

This book describes Zope's services to the developer from a hands on,
example-oriented standpoint.  This book is not a complete reference
to the Zope API, but rather a practical guide to applying Zope's
services to develop and deploy your own web applications.  This book
covers the following topics:

*Getting Started*
  This chapter provides a brief overview of installation and getting
  started with application development.

*Components and Interfaces*
  Zope uses a component-centric development model.  This chapter
  describes the component model in Zope and how Zope components are
  described through interfaces.

*Object Publishing*
  Developing applications for Zope involves more than just creating a
  component, that component must be *publishable* on the web.  This
  chapter describes publication, and how your components need to be
  designed to be published.

*Zope Products*
  New Zope components are distributed and installed in packages
  called "Products".  This chapter explains Products in detail.

*Persistent Components*
  Zope provides a built-in, transparent Python object database called
  ZODB.  This chapter describes how to create persistent components,
  and how they work in conjunction with the ZODB.

*Acquisition*
  Zope relies heavily on a dynamic technique called acquisition. This
  chapter explores acquisition thoroughly.

*Security*
  When your component is used by many different people through the
  web, security becomes a big concern.  This chapter describes Zope's
  security API and how you can use it to make security assertions
  about your object.

*Debugging and Testing*
  Zope has built in debugging and testing support.  This chapter
  describes these facilities and how you can debug and test your
  components.
