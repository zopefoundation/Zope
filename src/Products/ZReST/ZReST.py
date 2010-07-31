''' ReStructuredText Product for Zope

This Product stores two texts - a "source" text in ReStructureText format,
and a HTML "formatted" version of that text.

'''

import docutils.core
import docutils.io
from docutils.writers.html4css1 import HTMLTranslator
from docutils.writers.html4css1 import Writer
import sys

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityInfo import ModuleSecurityInfo
from Acquisition import Implicit
from App.config import getConfiguration 
from App.special_dtml import DTMLFile
from DateTime.DateTime import DateTime
from OFS.SimpleItem import Item
from OFS.PropertyManager import PropertyManager
from OFS.History import Historical
from OFS.History import html_diff
from Persistence import Persistent

modulesecurity = ModuleSecurityInfo()

modulesecurity.declareProtected('View management screens',
    'manage_addZReSTForm')
manage_addZReSTForm = DTMLFile('dtml/manage_addZReSTForm', globals())

modulesecurity.declareProtected('Add RestructuredText Document', 'manage_addZReST')
def manage_addZReST(self, id, file='', REQUEST=None):
    """Add a ZReST product """
    # validate the instance_home
    self._setObject(id, ZReST(id))
    self._getOb(id).manage_upload(file)
    if REQUEST is not None:
        return self.manage_main(self, REQUEST)

class Warnings:
    def __init__(self):
        self.messages = []
    def write(self, message):
        self.messages.append(message)

class ZReST(Item, PropertyManager, Historical, Implicit, Persistent):
    '''An instance of this class provides an interface between Zope and
       ReStructuredText for one text.
    '''
    meta_type =  'ReStructuredText Document'
    security = ClassSecurityInfo()
    _v_formatted = _v_warnings = None

    def __init__(self, id,output_encoding=None,
                 input_encoding=None):
        self.id = id
        self.title = id
        self.stylesheet = ''
        self.report_level = '2'
        self.source = ''

        from reStructuredText import default_output_encoding, \
                                     default_input_encoding
        self.input_encoding = input_encoding or \
                              default_input_encoding
        self.output_encoding = output_encoding  or \
                               default_output_encoding

    # define the properties that define this object
    _properties = (
        {'id':'stylesheet', 'type': 'string', 'mode': 'w',
            'default': ''},
        {'id':'report_level', 'type': 'string', 'mode': 'w', 'default': '2'},
        {'id':'input_encoding', 'type': 'string', 'mode': 'w', 'default': 'iso-8859-15'},
        {'id':'output_encoding', 'type': 'string', 'mode': 'w', 'default': 'iso-8859-15'},
    )
    property_extensible_schema__ = 0

    # define the tabs for the management interface
    manage_options= ( {'label': 'Edit', 'action':'manage_main'},
                      {'label': 'View', 'action':'index_html'},
                      {'label': 'Source', 'action':'source_txt'},
                    ) \
        + PropertyManager.manage_options \
        + Historical.manage_options \
        + Item.manage_options

    # access to the source text and formatted text
    security.declareProtected('View', 'index_html')
    def index_html(self, REQUEST=None):
        ''' Getting the formatted text
        '''
        if REQUEST is not None:
            REQUEST.RESPONSE.setHeader('content-type', 'text/html; charset=%s' % self.output_encoding)
        return self.render()

    security.declareProtected('View', 'source_txt')
    def source_txt(self, REQUEST=None):
        ''' Getting the source text
        '''
        if REQUEST is not None:
            REQUEST.RESPONSE.setHeader('content-type', 'text/plain; charset=%s' % self.input_encoding)
        return self.source

    # edit form, which is also the primary interface
    security.declareProtected('Edit ReStructuredText', 'manage_main')
    manage_main = DTMLFile('dtml/manage_editForm', globals())

    # edit action
    security.declareProtected('Edit ReStructuredText', 'manage_edit')
    def manage_edit(self, data, SUBMIT='Change',dtpref_cols='50',
                    dtpref_rows='20', REQUEST=None):
        '''Alias index_html to roundup's index
        '''
        if self._size_changes.has_key(SUBMIT):
            return self._er(data, SUBMIT, dtpref_cols, dtpref_rows, REQUEST)
        if data != self.source:
            self.source = data
            self._clear_cache()

        if REQUEST is not None:
            message="Saved changes."
            return self.manage_main(self, REQUEST, manage_tabs_message=message)

    # handle edit window size changes
    _size_changes = {
        'Bigger': (5,5),
        'Smaller': (-5,-5),
        'Narrower': (0,-5),
        'Wider': (0,5),
        'Taller': (5,0),
        'Shorter': (-5,0),
    }
    def _er(self, data, SUBMIT, dtpref_cols, dtpref_rows, REQUEST):
        dr,dc = self._size_changes[SUBMIT]
        rows = str(max(1, int(dtpref_rows) + dr))
        cols = str(dtpref_cols)
        if cols.endswith('%'):
           cols = str(min(100, max(25, int(cols[:-1]) + dc))) + '%'
        else:
           cols = str(max(35, int(cols) + dc))
        e = (DateTime("GMT") + 365).rfc822()
        setCookie = REQUEST["RESPONSE"].setCookie
        setCookie("dtpref_rows", rows, path='/', expires=e)
        setCookie("dtpref_cols", cols, path='/', expires=e)
        REQUEST.other.update({"dtpref_cols":cols, "dtpref_rows":rows})
        return self.manage_main(self, REQUEST, __str__=self.quotedHTML(data))

    security.declarePrivate('quotedHTML')
    def quotedHTML(self,
                   text=None,
                   character_entities=(
                       (('&'), '&amp;'),
                       (("<"), '&lt;' ),
                       ((">"), '&gt;' ),
                       (('"'), '&quot;'))): #"
        if text is None: text=self.read_raw()
        for re,name in character_entities:
            if text.find(re) >= 0: text=name.join(text.split(re))
        return text

    security.declarePrivate('_clear_cache')
    def _clear_cache(self):
        """ Forget results of rendering.
        """
        try:
            del self._v_formatted
        except AttributeError:
            pass
        try:
            del self._v_warnings
        except AttributeError:
            pass

    # handle uploads too
    security.declareProtected('Edit ReStructuredText', 'manage_upload')
    def manage_upload(self, file='', REQUEST=None):
        ''' Replaces the current source with the upload.
        '''
        if isinstance(file, type('')):
            self.source = file
        else:
            self.source = file.read()
        self._clear_cache()

        if REQUEST is not None:
            message="Saved changes."
            return self.manage_main(self, REQUEST, manage_tabs_message=message)

    security.declarePrivate('render')
    def render(self):
        ''' Render the source to HTML
        '''
        if self._v_formatted is None:
            warnings = self._v_warnings = Warnings()
            settings = {
                'halt_level': 6,
                'report_level' : int(self.report_level),
                'input_encoding': self.input_encoding,
                'output_encoding': self.output_encoding,
                'initial_header_level' : 1,
                'stylesheet' : self.stylesheet,
                'stylesheet_path' : None,
                'warning_stream' : warnings,
                'raw_enabled' : 0,
                'file_insertion_enabled' : 0,
                }

            self._v_formatted = docutils.core.publish_string(
                                        self.source,
                                        writer=Writer(),
                                        settings_overrides=settings,
                                )

        return self._v_formatted


    security.declareProtected('Edit ReStructuredText', 'PUT', 'manage_FTPput')
    def PUT(self, REQUEST, RESPONSE):
        ''' Handle HTTP PUT requests
        '''
        data = REQUEST.get('BODY', '')
        if data != self.source:
            if data.startswith('.. '):
                data = data.splitlines()
                new = []
                for i in range(len(data)):
                    line = data[i]
                    if not line.startswith('.. '):
                        break
                    if line.startswith('.. stylesheet='):
                        self.stylesheet = line.split('=')[1]
                    elif line.startswith('.. report_level='):
                        self.report_level = line.split('=')[1]
                    else:
                        pass # ignore
                data = '\n'.join(new) + '\n'.join(data[i:])
            self.source = data
        RESPONSE.setStatus(204)
        return RESPONSE        

    manage_FTPput = PUT

    def manage_FTPget(self):
        ''' Get source for FTP download
        '''
        self.REQUEST.RESPONSE.setHeader('Content-Type', 'text/plain')
        s = [
            '.. This is a ReStructuredText Document. Initial comment lines '
                '(".. ") will be stripped.',
            '.. stylesheet='+self.stylesheet,
            '.. report_level='+self.report_level
        ]
        if self._v_warnings:
            s.append('.. ')
            s.append('.. ' + '\n.. '.join(self._v_warnings.splitlines()))
        s.append('.. ')
        return '\n'.join(s) + '\n' + self.source

    def __str__(self):
        ''' Stringfy .. return the source
        '''
        return self.quotedHTML(self.source)

    __call__ = __str__

    def PrincipiaSearchSource(self):
        ''' Support for searching - the document's contents are searched.
        '''
        return self.source

    def manage_historyCompare(self, rev1, rev2, REQUEST,
                              historyComparisonResults=''):
        return ZReST.inheritedAttribute('manage_historyCompare')(
            self, rev1, rev2, REQUEST,
            historyComparisonResults=html_diff(rev1.source, rev2.source))

    def manage_editProperties(self, REQUEST):
        """ re-render the page after changing the properties (encodings!!!) """
        result = PropertyManager.manage_editProperties(self, REQUEST)        
        self._clear_cache()
        return result


InitializeClass(ZReST)
modulesecurity.apply(globals())


# vim: set filetype=python ts=4 sw=4 et si
