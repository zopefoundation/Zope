Using Zope Components in Zope 2 Applications
============================================

Background
----------

Zope 3 is a separate project from the Zope community aimed at web
development. It is designed to be more 'programmer-centric' and easier
to learn, use and extend for programmers. Zope 3 introduces an
interface-centric component architecture that makes it easier to develop
and deploy components without requiring developers to learn and
understand the entire Zope framework.

As of Zope 2.8, the "Five" project has been integrated into the 
Zope 2 core. The "Five" project implements a compatibility layer 
that allows many Zope 3 components and patterns to be used in 
new and existing Zope 2 applications.

Features
--------

The Five integration layer provides support for Zope 3 interfaces, 
Zope Configuration Markup Language (ZCML), adapters, views, 
utilities and schema-driven content.

Note that the Five layer does *not* attempt to provide a ZMI user 
interface for Zope 3 components.

Zope 2 includes the essential Zope 3 packages, so it is not 
necessary to install Zope 3.
