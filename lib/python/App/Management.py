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

$Id: Management.py,v 1.27 1999/08/11 18:19:25 jim Exp $"""

__version__='$Revision: 1.27 $'[11:-2]

import sys, Globals, ExtensionClass
from Dialogs import MessageDialog
from Globals import HTMLFile
from string import split, join, find

class Tabs(ExtensionClass.Base):
    """Mix-in provides management folder tab support."""

    manage_tabs__roles__=('Anonymous',)
    manage_tabs     =HTMLFile('manage_tabs', globals())
    
    __ac_permissions__=(
        ('View management screens', ('manage_help', )),
        )

    def manage_help(self, RESPONSE, SCRIPT_NAME):
        "Help!"
        RESPONSE.redirect(SCRIPT_NAME+'/HelpSys/hs_index')
        return ''

    manage_options  =()

    filtered_manage_options__roles__=None

    def filtered_manage_options(
        self, REQUEST=None,
        help_option_=({'label': 'Help', 'action': 'manage_help',
                       'target':"z_help_wnd"},),
        ):
        if REQUEST is None and hasattr(self, 'aq_acquire'):
            try: REQUEST=self.aq_acquire('REQUEST')
            except: pass
        try: user=REQUEST['AUTHENTICATED_USER']
        except: user=None
        
        result=[]
        seen_roles={}

        try: options=tuple(self.manage_options)+help_option_
        except: options=tuple(self.manage_options())+help_option_

        for d in options:

            label=d.get('label', None)
            if (label=='Security'
                and hasattr(self, '_isBeingUsedAsAMethod')
                and self._isBeingUsedAsAMethod()):
                d['label']='Define Permissions'

            path=d.get('path', None)
            if path is None: path=d['action']

            try:
                # Traverse to get the action:
                o=self
                for a in split(path,'/'):
                    if not a: continue
                    if a=='..':
                        o=o.aq_parent
                        continue
                    if hasattr(o, '__bobo_traverse__'):
                        o=o.__bobo_traverse__(o, a)
                    elif hasattr(o,a):
                        o=getattr(o,a)
                    else:
                        o=o[a]
            except:
                o=None

            if o is None:
                continue
                result.append(d) # Waaaa

            # Get the roles and check for public methods
            try: roles=o.__roles__
            except: roles=None
            if roles is None or 'Anonymous' in roles:
                result.append(d)
                continue

            # Do the validation check, trying to
            # optimize things for the common case of
            # many actions with the same roles.
            for r in roles:
                ok=seen_roles.get(r,None)
                if ok is None:
                    if user is None: break
                    else:
                        try: ok=user.allowed(o, (r,))
                        except: ok=0
                    seen_roles[r]=ok

                if ok:
                    result.append(d)
                    break


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
    
    
    def tabs_path_info(self, script, path):
        url=script
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
            script="%s/%s" % (script, p)
            out.append('<a href="%s/manage_workspace">%s</a>' % (script, p))
        out.append(last)
        return join(out,'&nbsp;/&nbsp;')

Globals.default__class_init__(Tabs)

class Navigation(ExtensionClass.Base):
    """Basic (very) navigation UI support"""

    manage          =HTMLFile('manage', globals())
    manage_menu     =HTMLFile('menu', globals())
    manage_copyright=HTMLFile('copyright', globals())
    manage_copyright__roles__=None

    __ac_permissions__=(
        ('View management screens', ('manage', 'manage_menu',)),
        )

Globals.default__class_init__(Navigation)
