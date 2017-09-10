#######
Outline
#######

Covers audience, topic, and scope.  Gives brief description of the
developers guide and what goals the guide tries to acomplish.  Gives
simple chapter by chapter overview of entire guide.


Interfaces
==========

Zope is moving toward a more "self-documenting" model, where Zope
component describe themselves with interfaces.  Many of the prose
descriptions and examples in this guide will be working with these
kinds of components.  This chapter gives a brief overview of Zope
interfaces, how they describe Zope components, and how developers can
create their own interfaces.

This section is meant to enable the reader to discover the Zope "API"
for themselves.  One of the goals of this guide is *not* to be an
exhaustive descrption of the Zope API, that can be found in the
online help system and from Zope objects through their interfaces.

The majority of the content of this chapter will come from the
`Interface documentation
<http://www.zope.org/Wikis/Interfaces/InterfaceUserDocumentation>`_

1. What are interfaces, why are they useful?

2. Reading interfaces

3. Using and testing interfaces

4. Defining interfaces


Publishing
==========

One key facility that Zope provides for a component developer is
access to a component through various network protocols, like HTTP.
While a component can be designed to work exclusivly with other
components through Python only interfaces, most components are
designed to be used and managed through a network interface, most
commonly HTTP.

Zope provides network access to components by "publishing" them
through various network interfaces like HTTP, FTP, WebDAV and
XML-RPC.  This chapter describes how a component developer can
publish their components "through the web" and other network
protocols.

1. Object publishing overview

2. Traversal

3. Network Protocols

4. Publishable Interfaces

5. Object marshalling

6. Creating user interfaces

   - with DTMLFile

   - with presentation templates


Products
========

Zope defines a system that allows component developers to distribute
their components to other Zope users.  Components can be placed into
a package called a "Product".  Products can be created either through
the web, or in Python.  Through the web products are covered in *The
Zope Book*, and this chapter describes the more advanced Python
product interfaces that developers can use to distribute their
Python-based components.

The majority of the content of this chapter will come from
Amos/Shane's `Product Tutorial
<http://www.zope.org/Members/hathawsh/PythonProductTutorial>`_

1. Introduction

2. Development Process

3. Product Architecture

4. Building Product Classes

5. Building Management Interfaces

6. Packaging Products

7. Evolving Products


Persistence
===========

Most Zope components live in the Zope Object DataBase (ZODB).
Components that are stored in ZODB are called *persistent*.  Creating
persistent components is, for the most part, a trivial exercise, but
ZODB does impose a few rules that persistent components must obey in
oder to work properly.  This chapter describes the persistent model
and the interfaces that persistent objects can use to live inside the
ZODB.

1. Persistence Architecture

2. Using Persistent components

3. Creating Persistent Objects

4. Transactions


Security
========

Zope has a very fine-grained, uniquely powerful security model.  This
model allows Zope developers to create components that work safely in
an environment used by many different users, all with varying levels
of security privledge.

This section describes Zope's security model and how component
developers can work with it and manipulate it to define security
policies specific to their needs or the needs of their components.

The majority of the content of this chapter will come from Chris'
first cut at `Security documentation
<http://www.zope.org/Members/mcdonc/PDG/6-1-Security.stx>`_

1. Security architecture

2. Using protected components

3. Implementing Security in your Component

4. Security Policies


Debugging and Testing
=====================

Covers debugging Zope and unit testing.

- pdb debugging

- Control Panel debug view

- -D z2.py switch

- unit testing

  - zope fixtures for unit testing
