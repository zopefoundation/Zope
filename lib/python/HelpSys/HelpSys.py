##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import Acquisition
from OFS.SimpleItem import Item
from OFS.ObjectManager import ObjectManager
from Globals import Persistent, DTMLFile, HTML
from Products.ZCatalog.ZCatalog import ZCatalog
from Products.ZCatalog.Lazy import LazyCat
from cgi import escape
import Products
import HelpTopic
import Globals

class HelpSys(Acquisition.Implicit, ObjectManager, Item, Persistent):
    """
    Zope Help System

    Provides browsing and searching of Zope Product Help.
    """
    meta_type='Help System'

    manage_options=(
        {'label' : 'Contents', 'action' : 'menu'},
        {'label' : 'Search', 'action' : 'search'},
    )

    __ac_permissions__=(
        ('View',
         ('__call__', 'searchResults', 'HelpButton', '',
          'index_html', 'menu', 'search', 'results', 'main',
          'helpLink')),
        ('Access contents information', ('helpValues',)),
        )

    def __init__(self, id='HelpSys'):
        self.id=id

    def helpValues(self, spec=None):
        "ProductHelp objects of all Products that have help"
        hv=[]
        for product in self.Control_Panel.Products.objectValues():
            productHelp=product.getProductHelp()
            # only list products that actually have help
            if productHelp.helpValues():
                hv.append(productHelp)
        return hv

    # Seaching does an aggregated search of all ProductHelp
    # objects. Only Help Topics for which the user has permissions
    # are returned.
    def __call__(self, REQUEST=None, **kw):
        "Searchable interface"
        if REQUEST is not None:
            perms=[]
            user=REQUEST.AUTHENTICATED_USER
            for p in self.ac_inherited_permissions():
                if user.has_permission(p[0], self):
                    perms.append(p[0])
            REQUEST.set('permissions',perms)
        results=[]
        for ph in self.helpValues():
            results.append(apply(getattr(ph, '__call__'), (REQUEST,) , kw))
        return LazyCat(results)

    searchResults=__call__

    index_html=DTMLFile('dtml/frame', globals())
    menu=DTMLFile('dtml/menu', globals())
    search=DTMLFile('dtml/search', globals())
    results=DTMLFile('dtml/results', globals())
    main=HTML("""<html></html>""")
    standard_html_header=DTMLFile('dtml/menu_header', globals())
    standard_html_footer=DTMLFile('dtml/menu_footer', globals())

    button=DTMLFile('dtml/button', globals())

    def HelpButton(self, topic, product):
        """
        Insert a help button linked to a help topic.
        """
        return self.button(self, self.REQUEST, product=product, topic=topic)

    helpURL=DTMLFile('dtml/helpURL',globals())

    def helpLink(self, product='OFSP', topic='ObjectManager_Contents.stx'):
        # Generate an <a href...> tag linking to a help topic. This
        # is a little lighter weight than the help button approach.
        basepath=self.REQUEST['BASEPATH1']
        help_url='%s/Control_Panel/Products/%s/Help/%s' % (
            basepath,
            product,
            topic
            )
        help_url='%s?help_url=%s' % (self.absolute_url(), help_url)

        script="window.open('%s','zope_help','width=600,height=500," \
               "menubar=yes,toolbar=yes,scrollbars=yes,resizable=yes');" \
               "return false;" % escape(help_url, 1).replace("'", "\\'")

        h_link='<a href="%s" onClick="%s" onMouseOver="window.status=' \
               '\'Open online help\'; return true;" onMouseOut="' \
               'window.status=\'\'; return true;">Help!</a>' % (
               escape(help_url, 1), script
               )

        return h_link

    def tpValues(self):
        """
        Tree protocol - returns child nodes

        Aggregates Product Helps with the same title.
        """
        helps={}
        for help in self.helpValues():
            if helps.has_key(help.title):
                helps[help.title].append(help)
            else:
                helps[help.title]=[help]
        cols=[]
        for k,v in helps.items():
            cols.append(TreeCollection(k,v,0))
        return cols

Globals.default__class_init__(HelpSys)


class TreeCollection:
    """
    A temporary wrapper for a collection of objects
    objects, used for help topic browsing to make a collection
    of objects appear as a single object.
    """

    def __init__(self, id, objs, simple=1):
        self.id=self.title=id
        self.objs=objs
        self.simple=simple

    def tpValues(self):
        values=[]
        if self.simple:
            values=self.objs
        else:
            for obj in self.objs:
                values=values + list(obj.tpValues())
        # resolve overlap
        ids={}
        for value in values:
            if ids.has_key(value.id):
                ids[value.id].append(value)
            else:
                ids[value.id]=[value]
        results=[]
        for k,v in ids.items():
            if len(v)==1:
                results.append(v[0])
            else:
                values=[]
                for topic in v:
                    values=values + list(topic.tpValues())
                results.append(TreeCollection(k, values))
        results.sort(lambda x, y: cmp(x.id, y.id))
        return results

    def tpId(self):
        return self.id


class ProductHelp(Acquisition.Implicit, ObjectManager, Item, Persistent):
    """
    Manages a collection of Help Topics for a given Product.

    Provides searching services to HelpSystem.
    """

    meta_type='Product Help'
    icon='p_/ProductHelp_icon'

    lastRegistered=None

    meta_types=({'name':'Help Topic',
                 'action':'addTopicForm',
                 'permission':'Add Documents, Images, and Files'},
                )

    manage_options=(
        ObjectManager.manage_options +
        Item.manage_options
        )

    __ac_permissions__=(
        ('Add Documents, Images, and Files', ('addTopicForm', 'addTopic')),
        )

    def __init__(self, id='Help', title=''):
        self.id=id
        self.title=title
        c=self.catalog=ZCatalog('catalog')
        # clear catalog
        for index in c.indexes():
            c.delIndex(index)
        for col in c.schema():
            c.delColumn(col)
        c.addIndex('SearchableText', 'TextIndex')
        c.addIndex('categories', 'KeywordIndex')
        c.addIndex('permissions', 'KeywordIndex')
        c.addColumn('categories')
        c.addColumn('permissions')
        c.addColumn('title_or_id')
        c.addColumn('url')
        c.addColumn('id')

    addTopicForm=DTMLFile('dtml/addTopic', globals())

    def addTopic(self, id, title, REQUEST=None):
        "Add a Help Topic"
        topic=HelpTopic.DTMLDocumentTopic(
            HelpTopic.default_topic_content, __name__=id)
        topic.title=title
        self._setObject(id, topic)
        if REQUEST is not None:
            return self.manage_main(self, REQUEST,
                                    manage_tabs_message='Help Topic added.')

    def helpValues(self, REQUEST=None):
        """
        Lists contained Help Topics.
        Help Topics for which the user is not authorized
        are not listed.
        """
        topics=self.objectValues('Help Topic')
        if REQUEST is None:
            return topics
        return filter(
            lambda ht, u=REQUEST.AUTHENTICATED_USER: ht.authorized(u), topics)

    def tpValues(self):
        """
        Tree protocol - child nodes
        """
        topics=[]
        apitopics=[]
        dtmltopics=[]
        zpttopics=[]
        for topic in self.objectValues('Help Topic'):
            if hasattr(topic,'isAPIHelpTopic') and topic.isAPIHelpTopic:
                apitopics.append(topic)
            else:
                try:
                    if callable(topic.id):
                        id=topic.id()
                    else:
                        id=topic.id
                    if id[:5]=='dtml-':
                        dtmltopics.append(topic)
                    if (id[:5] in ('metal', 'tales') and id[5] in ('.', '-')) or \
                    (id[:3]=='tal' and id[3] in ('.', '-')):
                        zpttopics.append(topic)
                    else:
                        topics.append(topic)
                except ImportError:
                    # Don't blow up if we have references to non-existant
                    # products laying around
                    pass
        if dtmltopics:
            topics = topics + [TreeCollection(' DTML Reference', dtmltopics)]
        if apitopics:
            topics = topics + [TreeCollection(' API Reference', apitopics)]
        if zpttopics:
            topics = topics + [TreeCollection(' ZPT Reference', zpttopics)]
        return topics

    def all_meta_types(self):
        f=lambda x: x['name'] in ('Image', 'File')
        return filter(f, Products.meta_types) + self.meta_types

    def __call__(self, *args, **kw):
        """
        Searchable interface
        """
        return apply(self.catalog.__call__, args, kw)

    standard_html_header=DTMLFile('dtml/topic_header', globals())
    standard_html_footer=DTMLFile('dtml/topic_footer', globals())


Globals.default__class_init__(ProductHelp)
