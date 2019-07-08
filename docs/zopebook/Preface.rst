Preface
=======

.. include:: includes/zope2_notice.rst

Welcome to *The Zope Book*.  This book is designed to introduce you
to ``Zope2``, an open-source web application server.

To make effective use of the book, you should know how to use a web
browser and have a basic understanding of the ``Hyper
Text Markup Language`` (HTML) and ``Uniform Resource Locators`` (URLs).

You don't need to be a highly-skilled programmer in order to use Zope2,
but you may find the understanding of some programming concepts (particularly
in object-oriented programming) to be extremely helpful.

Preface to the 2.12 edition
---------------------------

This book has originally been written for Zope 2.6 back in 2002. It has been
available in an almost unmodified form for the last seven years. During those
many years quite a bit has happened in Zope itself and the general web market.

The 2.12 edition of this book does not try to write a new book on how-to do
Zope development today. Instead it tries to update the original books content
to be true and helpful again. Many of the underlying principles of Zope2 have
not changed in the last years. The ZMI, security machinery, page templates and
how-to use the ZCatalog are still there in an almost unmodified fashion.
The general ideas behind object orientation, being Python based and the
general architecture are still the same.

If you want to understand Zope2 you still need to understand how Acquisition
works, even though it has been discouraged as a way to design your application
logic.

One of the most notable differences between the original Zope2 approach and
todays best-practices is in the way you develop applications with Zope2. The
original Zope2 approach has focussed on a Through-The-Web (TTW) development
model. You would create your entire application and manage your data through
the same browser interface and store everything transparently in the same
database. This model has worked very well in the beginning of "the web" as
many dynamic websites have been rather simple and specialized projects.

Over the years websites have grown their requirements and often turned into
development projects of a considerable size. Today websites are understood
as applications in themselves and need an approach which is no longer
compatible with the TTW approach of the early Zope2.

In this book you will still read about using the TTW approach for many of
the examples. Please understand this as a way to quickly and easily learn
about the underlying technologies. If you want to built an application based
on top of Zope2, you are almost always better of approaching the project from
the so called "file-system based approach" or using Python packages to extend
Zope in a predictable way.


How the Book Is Organized
-------------------------

This book is laid out in the following chapters:

- Introducing Zope

    This chapter explains what Zope is and what it can do for you. You'll also
    learn about the differences between Zope and other web application servers.

- Zope Concepts and Architecture

    This chapter explains fundamental Zope concepts and describes the basics
    about Zope's architecture.

- Installing and Starting Zope

    This chapter explains how to install and start Zope for the first time. By
    the end of this chapter, you will have Zope installed and working.

- Object Orientation

    This chapter explains the concept of *object orientation*, which is the
    development methodology most often used to create Zope applications.

- Using the Zope Management Interface

    This chapter explains how to use Zope's web-based management interface. By
    the end of this chapter, you will be able to navigate around the Zope
    object space, copy and move objects, and use other basic Zope features.

- Using Basic Zope Objects

    This chapter introduces *objects*, which are the most important elements of
    Zope. You'll learn the basic Zope objects: content objects, presentation
    objects, and logic objects, and you'll build a simple application using
    these objects.

- Acquisition

    This chapter introduces *Acquisition*, which is Zope's mechanism for
    sharing site behavior and content.

- Basic Zope Scripting

    This chapter will introduce you to the basics of scripting.

- Using Zope Page Templates

    This chapter introduces *Zope Page Templates*, another Zope tool used to
    create dynamic web pages. You will learn about basic template statements
    that let you insert dynamic content, and how to create and edit page
    templates.

- Creating Basic Zope Applications  

    This chapter presents several real-world examples of building a Zope
    application. You'll learn how to use basic Zope objects and how they can
    work together to form basic applications.

- Users and Security

    This chapter looks at how Zope handles users, authentication,
    authorization, and other security-related matters.

- Advanced Page Templates

    This chapter goes into more depth with Zope Page Templates. You will learn
    all about template statements, expression types, and macros, which let you
    reuse presentation elements.

- Advanced Zope Scripting

    This chapter covers scripting Zope with Python. You will learn how to write
    business logic in Zope using tools more powerful than TAL, about the idea
    of *scripts* in Zope, and about Scripts (Python).

- Zope Services

    This chapter covers Zope objects that are considered "services," which
    don't readily fit into any of the basic "content," "presentation," or
    "logic" object groups.

- Basic DTML

    This chapter introduces DTML, the second tag-based scripting language.
    You'll learn DTML syntax, its basic tags, and how to use DTML templates and
    scripting facilities. After reading this chapter, you'll be able to create
    dynamic web pages with DTML.

- Advanced DTML

    This chapter takes a closer look at DTML. You'll learn about DTML security,
    the tricky issue of how variables are looked up in DTML, advanced use of
    basic tags, and the myriad of special purpose tags.

- Searching and Categorizing Content

    This chapter shows you how to index and search objects with Zope's built-in
    search engine: the *Catalog*. You'll learn about indexing concepts,
    different patterns for indexing and searching, metadata, and search
    results.

- Relational Database Connectivity

    This chapter describes how Zope connects to external relational databases.
    You'll learn about features that allow you to treat relational data as
    though it were Zope objects, and security and performance considerations.

- Virtual Hosting Services

    This chapter explains how to set up Zope in a "virtual hosting"
    environment, in which Zope sub-folders can be served as "top-level" host
    names. It includes examples that allow virtual hosting to be performed
    either "natively" or using Apache's 'mod_rewrite' facility.

- Sessions

    This chapter describes Zope's "sessioning" services, which allow Zope
    developers to "keep state" between HTTP requests.

- Scalability and ZEO

    This chapter covers issues and solutions for building and maintaining large
    web applications, and focuses on issues of management and scalability. In
    particular, the Zope Enterprise Option (ZEO) is covered in detail. You'll
    learn about the tools and techniques needed to turn a small site into a
    large-scale site, servicing many simultaneous visitors.

- Managing Zope Objects Using External Tools

    This chapter explains how to use tools outside of your web browser to
    manipulate Zope objects.

- Maintaining Zope

    This chapter covers Zope maintenance and administration tasks, such as
    database "packing" and package installation.

- Appendix A: DTML Reference

    Reference of DTML syntax and commands.

- Appendix B: API Reference

    Reference of Zope object APIs.

- Appendix C: Page Template Reference

    Reference of Zope Page Template syntax and commands.

- Appendix D: Zope Resources

    Reference of "resources" which can be used to further enhance your Zope
    learning experience.

- Appendix E:

    DTML Name Lookup Rules Describes DTML's name lookup rules.

