##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################

import Acquisition
from OFS.SimpleItem import Item
from OFS.ObjectManager import ObjectManager
from Globals import Persistent, HTMLFile, HTML
from Products.ZCatalog.ZCatalog import ZCatalog
from Products.ZCatalog.Lazy import LazyCat
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
          'index_html', 'menu', 'search', 'results', 'main', )),
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
    
    index_html=HTMLFile('frame', globals())
    menu=HTMLFile('menu', globals())
    search=HTMLFile('search', globals())
    results=HTMLFile('results', globals())
    main=HTML("""<html></html>""")
    standard_html_header=HTMLFile('menu_header', globals())
    standard_html_footer=HTMLFile('menu_footer', globals())

    button=HTMLFile('button', globals())

    def HelpButton(self, topic, product):
        """
        Insert a help button linked to a help topic.
        """
        return self.button(self, self.REQUEST, product=product, topic=topic)

    helpURL=HTMLFile('helpURL',globals())


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
        self.catalog=ZCatalog('catalog')
        c=self.catalog._catalog
        # clear catalog
        for index in c.indexes.keys():
            c.delIndex(index)
        for col in c.schema.keys():
            c.delColumn(col)
        c.addIndex('SearchableText', 'TextIndex')
        c.addIndex('categories', 'KeywordIndex')
        c.addIndex('permissions', 'KeywordIndex')
        c.addColumn('categories')
        c.addColumn('permissions')
        c.addColumn('title_or_id')
        c.addColumn('url')
        c.addColumn('id')

    addTopicForm=HTMLFile('addTopic', globals())

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
        for topic in self.objectValues('Help Topic'):
            if hasattr(topic,'isAPIHelpTopic') and topic.isAPIHelpTopic:
                apitopics.append(topic)
            else:
                if callable(topic.id):
                    id=topic.id()
                else:
                    id=topic.id
                if id[:5]=='dtml-':
                    dtmltopics.append(topic)
                else:
                    topics.append(topic)
        if dtmltopics:
            topics = topics + [TreeCollection(' DTML Reference', dtmltopics)]
        if apitopics:
            topics = topics + [TreeCollection(' API Reference', apitopics)]
        return topics
        
    def all_meta_types(self):
        f=lambda x: x['name'] in ('Image', 'File')
        return filter(f, Products.meta_types) + self.meta_types

    def __call__(self, *args, **kw):
        """
        Searchable interface
        """
        return apply(self.catalog.__call__, args, kw)

    standard_html_header=HTMLFile('topic_header', globals())
    standard_html_footer=HTMLFile('topic_footer', globals())


Globals.default__class_init__(ProductHelp)
