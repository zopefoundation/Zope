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
from ComputedAttribute import ComputedAttribute
from OFS.SimpleItem import Item
from Globals import Persistent, HTML, HTMLFile, ImageFile
from OFS.DTMLDocument import DTMLDocument
from OFS.PropertyManager import PropertyManager
import os.path
import string

class HelpTopicBase:
    "Mix-in Help Topic support class"

    _properties=(
        {'id':'title', 'type':'string', 'mode':'w'},
        {'id':'categories', 'type':'multiple selection',
         'select_variable':'categories_values', 'mode':'w'},
        {'id':'permissions', 'type':'multiple selection',
         'select_variable':'permissions_values', 'mode':'w'},
        )

    # default values
    categories=('Content Manager Information',)
    permissions=('View',)

    def _permissions_values(self):
        perms=[]
        for m in self.permission_settings():
            perms.append(m['name'])
        return perms
    
    permissions_values=ComputedAttribute(_permissions_values, 1)

    categories_values=(
        'Content Manager Information',
        'DTML Programmer Information',
        'Python Programmer Information',
        )

    def helpValues(self, REQUEST=None):
        return ()

    def authorized(self, user):
        "Is a given user authorized to view this Help Topic?"
        if not self.permissions:
            return 1
        for perm in self.permissions:
            if user.has_permission(perm, self):
                return 1
        return 0
    
    # Indexable methods
    # -----------------

    def SearchableText(self):
        "The full text of the Help Topic, for indexing purposes"
        raise "Unimplemented"

    def url(self):
        "URL for indexing purposes"
        return self.absolute_url(1)

    # Private indexing methods
    # ------------------------
    
    def manage_afterAdd(self, item, container):
        self.index_object()

    def manage_afterClone(self, item):
        self.index_object()

    def manage_beforeDelete(self, item, container):
        self.unindex_object()

    def _setPropValue(self, id, value):
        setattr(self,id,value)
        self.reindex_object()

    def index_object(self, prefix=''):
        self.get_catalog().catalog_object(self, prefix + self.url())

    def unindex_object(self, prefix=''):
        self.get_catalog().uncatalog_object(prefix + self.url())

    def reindex_object(self):
        self.unindex_object()
        self.index_object()

    def get_catalog(self):
        return self.catalog


class HelpTopic(Acquisition.Implicit, HelpTopicBase, Item, PropertyManager, Persistent):
    """
    Abstract base class for Help Topics
    """
    
    meta_type='Help Topic'

    manage_options=(
        {'label':'Properties', 'action':'manage_propertiesForm'},
        {'label':'View', 'action':'index_html'},
        )

    __ac_permissions__=()

    def index_html(self, REQUEST, RESPONSE):
        "View the Help Topic"
        raise "Unimplemented"


class DTMLDocumentTopic(HelpTopicBase, DTMLDocument):
    """
    A user addable Help Topic based on DTML Document.
    """
    meta_type='Help Topic'

    def munge(self,*args, **kw):
        apply(DTMLDocument.munge, (self,) + args, kw)
        self.reindex_object()

    def SearchableText(self):
        return '%s %s' % (self.title, self.read())
   

default_topic_content="""\
<dtml-var standard_html_header>
<h2><dtml-var title></h2>
<p>This is the <dtml-var id> Help Topic.</p>
<dtml-var standard_html_footer>
"""

class DTMLTopic(HelpTopic):
    """
    A basic Help Topic. Holds a HTMLFile object.
    """
    def __init__(self, id, title, file, permissions=None, categories=None):
        self.id=id
        self.title=title
        if string.rfind(file, '.dtml') == len(file) -5:
            file=file[:-5]
        self.index_html=HTMLFile(file,'')
        if permissions is not None:
            self.permissions=permissions
        if categories is not None:
            self.categories=categories
        
    def SearchableText(self):
        "The full text of the Help Topic, for indexing purposes"
        return '%s %s' % (self.title, self.obj.read())

        
class TextTopic(HelpTopic):
    """
    A basic Help Topic. Holds a text file.
    """
    def __init__(self, id, title, file, permissions=None, categories=None):
        self.id=id
        self.title=title
        self.obj=open(file).read()
        if permissions is not None:
            self.permissions=permissions
        if categories is not None:
            self.categories=categories
        
    def index_html(self, REQUEST=None):
        "View the Help Topic"
        return self.obj

    def SearchableText(self):
        "The full text of the Help Topic, for indexing purposes"
        return '%s %s' % (self.title, self.obj)

    
class STXTopic(TextTopic):
    """
    A structured-text topic. Holds a HTMLFile object.
    """
    
    index_html=HTML("""\
<dtml-var standard_html_header>
<dtml-var obj fmt="structured-text">
<dtml-var standard_html_footer>""")


class ImageTopic(HelpTopic):
    """
    A image Help Topic. Holds an ImageFile object.
    """

    meta_type='Help Image'

    def __init__(self, id, title, file, categories=None, permissions=None):
        self.id=id
        self.title=title
        dir, file=os.path.split(file)
        self.image=ImageFile(file, dir)
        if permissions is not None:
            self.permissions=permissions
        if categories is not None:
            self.categories=categories  
    
    def index_html(self, REQUEST, RESPONSE):
        "View the Help Topic"
        return self.image.index_html(REQUEST, RESPONSE)
        
    def SearchableText(self):
        "The full text of the Help Topic, for indexing purposes"
        return ''
        
