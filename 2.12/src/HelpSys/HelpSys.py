##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
from cgi import escape

from AccessControl.Permissions import access_contents_information
from AccessControl.Permissions import add_documents_images_and_files
from AccessControl.Permissions import view as View
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import Implicit
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from App.special_dtml import HTML
from OFS.ObjectManager import ObjectManager
from OFS.SimpleItem import Item
from Persistence import Persistent
from Products.PluginIndexes.KeywordIndex.KeywordIndex import KeywordIndex
from Products.ZCatalog.ZCatalog import ZCatalog
from Products.ZCatalog.Lazy import LazyCat
from Products.ZCTextIndex.OkapiIndex import OkapiIndex
from Products.ZCTextIndex.Lexicon import CaseNormalizer
from Products.ZCTextIndex.HTMLSplitter import HTMLWordSplitter
from Products.ZCTextIndex.Lexicon import StopWordRemover
from Products.ZCTextIndex.ZCTextIndex import PLexicon
from Products.ZCTextIndex.ZCTextIndex import ZCTextIndex


class HelpSys(Implicit, ObjectManager, Item, Persistent):
    """
    Zope Help System

    Provides browsing and searching of Zope Product Help.
    """
    meta_type='Help System'

    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    manage_options=(
        {'label' : 'Contents', 'action' : 'menu'},
        {'label' : 'Search', 'action' : 'search'},
    )

    def __init__(self, id='HelpSys'):
        self.id=id

    security.declareProtected(access_contents_information, 'helpValues')
    def helpValues(self, spec=None):
        "ProductHelp objects of all Products that have help"
        import Products
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

    security.declareProtected(View, '__call__')
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

    security.declareProtected(View, 'searchResults')
    searchResults=__call__

    security.declareProtected(View, 'index_html')
    index_html=DTMLFile('dtml/frame', globals())

    security.declareProtected(View, 'menu')
    menu=DTMLFile('dtml/menu', globals())

    security.declareProtected(View, 'search')
    search=DTMLFile('dtml/search', globals())

    security.declareProtected(View, 'results')
    results=DTMLFile('dtml/results', globals())

    security.declareProtected(View, 'main')
    main=HTML("""<html></html>""")
    standard_html_header=DTMLFile('dtml/menu_header', globals())
    standard_html_footer=DTMLFile('dtml/menu_footer', globals())

    button=DTMLFile('dtml/button', globals())

    security.declareProtected(View, 'HelpButton')
    def HelpButton(self, topic, product):
        """
        Insert a help button linked to a help topic.
        """
        return self.button(self, self.REQUEST, product=product, topic=topic)

    helpURL=DTMLFile('dtml/helpURL',globals())

    security.declareProtected(View, 'helpLink')
    def helpLink(self, product='OFSP', topic='ObjectManager_Contents.stx'):
        # Generate an <a href...> tag linking to a help topic. This
        # is a little lighter weight than the help button approach.
        basepath=self.REQUEST['BASEPATH1']
        products = self.Control_Panel.Products.objectIds()
        if product not in products:
            return None
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

InitializeClass(HelpSys)


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


class ProductHelp(Implicit, ObjectManager, Item, Persistent):
    """
    Manages a collection of Help Topics for a given Product.

    Provides searching services to HelpSystem.
    """

    meta_type='Product Help'
    icon='p_/ProductHelp_icon'

    security = ClassSecurityInfo()

    lastRegistered=None

    meta_types=({'name':'Help Topic',
                 'action':'addTopicForm',
                 'permission':'Add Documents, Images, and Files'},
                )

    manage_options=(
        ObjectManager.manage_options +
        Item.manage_options
        )

    def __init__(self, id='Help', title=''):
        self.id = id
        self.title = title
        c = self.catalog = ZCatalog('catalog')

        l = PLexicon('lexicon', '', HTMLWordSplitter(), CaseNormalizer(),
                     StopWordRemover())
        c._setObject('lexicon', l)
        i = ZCTextIndex('SearchableText', caller=c, index_factory=OkapiIndex,
                        lexicon_id=l.id)
        # not using c.addIndex because it depends on Product initialization
        c._catalog.addIndex('SearchableText', i)
        c._catalog.addIndex('categories', KeywordIndex('categories'))
        c._catalog.addIndex('permissions', KeywordIndex('permissions'))
        c.addColumn('categories')
        c.addColumn('permissions')
        c.addColumn('title_or_id')
        c.addColumn('url')
        c.addColumn('id')

    security.declareProtected(add_documents_images_and_files, 'addTopicForm')
    addTopicForm=DTMLFile('dtml/addTopic', globals())

    security.declareProtected(add_documents_images_and_files, 'addTopic')
    def addTopic(self, id, title, REQUEST=None):
        "Add a Help Topic"
        from HelpSys.HelpTopic import DTMLDocumentTopic
        from HelpSys.HelpTopic import default_topic_content
        topic = DTMLDocumentTopic(default_topic_content, __name__=id)
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
        import Products
        f=lambda x: x['name'] in ('Image', 'File')
        return filter(f, Products.meta_types) + self.meta_types

    def __call__(self, *args, **kw):
        """
        Searchable interface
        """
        return apply(self.catalog.__call__, args, kw)

    standard_html_header=DTMLFile('dtml/topic_header', globals())
    standard_html_footer=DTMLFile('dtml/topic_footer', globals())

InitializeClass(ProductHelp)
