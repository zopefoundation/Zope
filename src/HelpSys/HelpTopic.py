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
import os

from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import access_contents_information
from AccessControl.Permissions import view as View
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import Implicit
from App.ImageFile import ImageFile
from App.special_dtml import DTMLFile
from App.special_dtml import HTML
from ComputedAttribute import ComputedAttribute
from OFS.DTMLDocument import DTMLDocument
from OFS.PropertyManager import PropertyManager
from OFS.SimpleItem import Item
from Persistence import Persistent

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

    def authorized(self, sm):
        "Is a given user authorized to view this Help Topic?"
        if not self.permissions:
            return True
        return any( sm.checkPermission(p, self) for p in self.permissions )

    # Indexable methods
    # -----------------

    def SearchableText(self):
        "The full text of the Help Topic, for indexing purposes"
        raise NotImplementedError

    def url(self):
        "URL for indexing purposes"
        return '/'.join(self.getPhysicalPath())

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


class HelpTopic(Implicit, HelpTopicBase, Item, PropertyManager, Persistent):
    """
    Abstract base class for Help Topics
    """

    meta_type='Help Topic'
    icon='p_/HelpTopic_icon'
    _v_last_read = 0

    security = ClassSecurityInfo()

    manage_options=(
        {'label':'Properties', 'action':'manage_propertiesForm'},
        {'label':'View', 'action':'index_html'},
        )

    security.declareProtected(View, 'SearchableText')

    security.declareProtected(View, 'url')

    security.declareProtected(access_contents_information, 'helpValues')

    def _set_last_read(self, filepath):
        try:    mtime = os.stat(filepath)[8]
        except: mtime = 0
        self._v_last_read = mtime

    def _check_for_update(self):
        import Globals
        if Globals.DevelopmentMode:
            try:    mtime=os.stat(self.file)[8]
            except: mtime=0
            if mtime != self._v_last_read:
                fileob = open(self.file)
                self.obj = fileob.read()
                fileob.close()
                self._v_last_read=mtime
                self.reindex_object()

    security.declareProtected(View, 'index_html')
    def index_html(self, REQUEST, RESPONSE):
        "View the Help Topic"
        raise NotImplementedError

InitializeClass(HelpTopic)


class DTMLDocumentTopic(HelpTopicBase, DTMLDocument):
    """
    A user addable Help Topic based on DTML Document.
    """
    meta_type='Help Topic'
    icon='p_/HelpTopic_icon'

    def munge(self,*args, **kw):
        apply(DTMLDocument.munge, (self,) + args, kw)
        self.reindex_object()

    def SearchableText(self):
        return '%s %s' % (self.title, self.read())


default_topic_content="""\
<html>
  <head><title><dtml-var title_or_id></title>
  </head>
  <body bgcolor="#FFFFFF">
<h2><dtml-var title></h2>
<p>This is the <dtml-var id> Help Topic.</p>
</body>
</html>
"""

class DTMLTopic(HelpTopic):
    """
    A basic Help Topic. Holds a HTMLFile object.
    """
    def __init__(self, id, title, file, permissions=None, categories=None):
        self.id=id
        self.title=title
        file,ext=os.path.splitext(file)
        prefix,file=os.path.split(file)
        self.index_html=DTMLFile(file,prefix)
        if permissions is not None:
            self.permissions=permissions
        if categories is not None:
            self.categories=categories

    def SearchableText(self):
        "The full text of the Help Topic, for indexing purposes"
        return '%s %s' % (self.title, self.index_html.read())


class TextTopic(HelpTopic):
    """
    A basic Help Topic. Holds a text file.
    """
    index_html = None
    def __init__(self, id, title, file, permissions=None, categories=None):
        self.id=id
        self.title=title
        self.file = file
        self.obj=open(file).read()
        self._set_last_read(file)
        if permissions is not None:
            self.permissions=permissions
        if categories is not None:
            self.categories=categories

    def __call__(self, REQUEST=None):
        "View the Help Topic"
        self._check_for_update()
        return self.obj

    def SearchableText(self):
        "The full text of the Help Topic, for indexing purposes"
        return '%s %s' % (self.title, self.obj)


class STXTopic(TextTopic):
    """
    A structured-text topic. Holds a HTMLFile object.
    """
    index_html = None

    def __call__(self, REQUEST=None):
        """ View the STX Help Topic """
        self._check_for_update()
        return self.htmlfile(self, REQUEST)

    htmlfile = HTML("""\
    <html>
      <head><title><dtml-var title_or_id></title>
      </head>
      <body bgcolor="#FFFFFF">
        <dtml-var obj fmt="structured-text">
      </body>
    </html>""")


class ReSTTopic(TextTopic):
    """
    A reStructuredText [1]_ topic.  Similar to STXTopic, it uses a
    simle DTML construct to render its contents - this time using the
    *reStructuredText* language.

    .. [1] reStructuredText
       (http://docutils.sourceforge.net/rst.html)
    """
    index_html = None

    def __call__(self, REQUEST=None):
        """ Renders the ReST Help Topic """
        self._check_for_update()
        return self.htmlfile(self, REQUEST)

    htmlfile = HTML("""\
    <html>
      <head><title><dtml-var title_or_id></title>
      </head>
      <body bgcolor="#FFFFFF">
        <dtml-var obj fmt="restructured-text">
      </body>
    </html>""")
    

class ImageTopic(HelpTopic):
    """
    A image Help Topic. Holds an ImageFile object.
    """

    meta_type='Help Image'

    def __init__(self, id, title, file, categories=None, permissions=None):
        self.id=id
        self.title=title
        self.file = file
        self.obj=open(file).read()
        self._set_last_read(file)
        dir, file=os.path.split(file)
        self.image=ImageFile(file, dir)
        if permissions is not None:
            self.permissions=permissions
        if categories is not None:
            self.categories=categories

    def index_html(self, REQUEST, RESPONSE):
        "View the Help Topic"
        self._check_for_update()
        return self.image.index_html(REQUEST, RESPONSE)

    def SearchableText(self):
        "The full text of the Help Topic, for indexing purposes"
        return ''
