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

"""Standard management interface support

$Id: Management.py,v 1.42 2001/01/13 15:01:55 shane Exp $"""

__version__='$Revision: 1.42 $'[11:-2]

import sys, Globals, ExtensionClass, urllib
from Dialogs import MessageDialog
from Globals import DTMLFile, HTMLFile
from string import split, join, find
from AccessControl import getSecurityManager

class Tabs(ExtensionClass.Base):
    """Mix-in provides management folder tab support."""

    manage_tabs__roles__=('Anonymous',)
    manage_tabs=DTMLFile('dtml/manage_tabs', globals())
    

    manage_options  =()

    filtered_manage_options__roles__=None
    def filtered_manage_options(self, REQUEST=None):

        validate=getSecurityManager().validate
        
        result=[]

        try: options=tuple(self.manage_options)
        except: options=tuple(self.manage_options())

        for d in options:

            filter=d.get('filter', None)
            if filter is not None and not filter(self):
                continue

            path=d.get('path', None)
            if path is None: path=d['action']

            o=self.unrestrictedTraverse(path, None)
            if o is None: continue

            try:
                if validate(container=self, value=o):
                    result.append(d)
            except:
                if not hasattr(o, '__roles__'):
                    result.append(d)

        return result
                    
            
    manage_workspace__roles__=('Anonymous',)
    def manage_workspace(self, REQUEST):
        """Dispatch to first interface in manage_options
        """
        options=self.filtered_manage_options(REQUEST)
        try:
            m=options[0]['action']
            if m=='manage_workspace': raise TypeError
        except:
            raise 'Unauthorized', (
                'You are not authorized to view this object.<p>')

        if find(m,'/'):
            raise 'Redirect', (
                "%s/%s" % (REQUEST['URL1'], m))
        
        return getattr(self, m)(self, REQUEST)
    
    def tabs_path_default(self, REQUEST,
                          # Static var
                          unquote=urllib.unquote,
                          ):
        steps = REQUEST._steps[:-1]
        script = REQUEST['BASEPATH1']
        linkpat = '<a href="%s/manage_workspace">%s</a>'
        out = []
        url = linkpat % (script, '&nbsp;/')
        if not steps:
            return url
        last = steps.pop()
        for step in steps:
            script = '%s/%s' % (script, step)
            out.append(linkpat % (script, unquote(step)))
        out.append(unquote(last))
        return '%s%s' % (url, join(out,'/'))

    def tabs_path_info(self, script, path,
                       # Static vars
                       quote=urllib.quote,
                       ):
        out=[]
        while path[:1]=='/': path=path[1:]
        while path[-1:]=='/': path=path[:-1]
        while script[:1]=='/': script=script[1:]
        while script[-1:]=='/': script=script[:-1]
        path=split(path,'/')[:-1]
        if script: path=[script]+path
        if not path: return ''
        script=''
        last=path[-1]
        del path[-1]
        for p in path:
            script="%s/%s" % (script, quote(p))
            out.append('<a href="%s/manage_workspace">%s</a>' % (script, p))
        out.append(last)
        return join(out, '/')

Globals.default__class_init__(Tabs)


class Navigation(ExtensionClass.Base):
    """Basic navigation UI support"""

    __ac_permissions__=(
        ('View management screens',
         ('manage', 'manage_menu', 'manage_top_frame',
          'manage_page_header',
          'manage_page_footer',
          )),
        )

    manage            =DTMLFile('dtml/manage', globals())
    manage_menu       =HTMLFile('dtml/menu', globals())

    manage_top_frame  =DTMLFile('dtml/manage_top_frame', globals())
    manage_page_header=DTMLFile('dtml/manage_page_header', globals())
    manage_page_footer=DTMLFile('dtml/manage_page_footer', globals())

    manage_form_title =DTMLFile('dtml/manage_form_title', globals(),
                                form_title='Add Form',
                                help_product=None,
                                help_topic=None)
    manage_form_title._setFuncSignature(
        varnames=('form_title', 'help_product', 'help_topic') )
    manage_form_title.__roles__ = None

    manage_copyright=DTMLFile('dtml/copyright', globals())
    manage_copyright.__roles__ = None

    manage_logout__roles__ = None
    def manage_logout(self, REQUEST=None):
        """Logout current user"""
        p = getattr(REQUEST, '_logout_path', None)
        if p is not None:
            return apply(self.restrictedTraverse(p))
        return """<html>
<head><title>Not implmented</title></head>
<body>
Sorry, this is not yet implemented.
</body>
</html>"""

file = DTMLFile('dtml/manage_page_style.css', globals())
setattr(Navigation, 'manage_page_style.css', file)
file.__roles__ = None

Globals.default__class_init__(Navigation)
