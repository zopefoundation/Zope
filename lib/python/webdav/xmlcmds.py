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

"""WebDAV xml request objects."""

__version__='$Revision: 1.15 $'[11:-2]

import sys, os, string
from common import absattr, aq_base, urlfix
from OFS.PropertySheets import DAVProperties
from xmltools import XmlParser
from cStringIO import StringIO


class DAVProps(DAVProperties):
    """Emulate required DAV properties for objects which do
       not themselves support properties."""
    def __init__(self, obj):
        self.__obj__=obj
    def v_self(self):
        return self.__obj__



class PropFind:
    """Model a PROPFIND request."""
    def __init__(self, request):
        self.request=request
        self.depth='infinity'
        self.allprop=0
        self.propname=0
        self.propnames=[]
        self.parse(request)
        
    def parse(self, request, dav='DAV:'):
        self.depth=request.get_header('Depth', 'infinity')
        if not (self.depth in ('0','1','infinity')):
            raise 'Bad Request', 'Invalid Depth header.'
        body=request.get('BODY', '')
        self.allprop=(not len(body))
        if not body: return
        try:    root=XmlParser().parse(body)
        except: raise 'Bad Request', sys.exc_value
        e=root.elements('propfind', ns=dav)
        if not e: raise 'Bad Request', 'Invalid xml request.'
        e=e[0]
        if e.elements('allprop', ns=dav):
            self.allprop=1
            return
        if e.elements('propname', ns=dav):
            self.propname=1
            return
        prop=e.elements('prop', ns=dav)
        if not prop: raise 'Bad Request', 'Invalid xml request.'
        prop=prop[0]
        for val in prop.elements():
            self.propnames.append((val.name(), val.namespace()))
        if (not self.allprop) and (not self.propname) and \
           (not self.propnames):
            raise 'Bad Request', 'Invalid xml request.'
        return

    def apply(self, obj, url=None, depth=0, result=None, top=1):
        if result is None:
            result=StringIO()
            depth=self.depth
            url=urlfix(self.request['URL'], 'PROPFIND')
            result.write('<?xml version="1.0" encoding="utf-8"?>\n' \
                         '<d:multistatus xmlns:d="DAV:">\n')
        iscol=hasattr(obj, '__dav_collection__')
        if iscol and url[-1] != '/': url=url+'/'
        result.write('<d:response>\n<d:href>%s</d:href>\n' % url)
        if hasattr(obj, '__propsets__'):
            propsets=obj.propertysheets.values()
            obsheets=obj.propertysheets
        else:
            davprops=DAVProps(obj)
            propsets=(davprops,)
            obsheets={'DAV:': davprops}
        if self.allprop:
            stats=[]
            for ps in propsets:
                if hasattr(aq_base(ps), 'dav__allprop'):
                    stats.append(ps.dav__allprop())
            stats=string.join(stats, '') or '<d:status>200 OK</d:status>\n'
            result.write(stats)            
        elif self.propname:
            stats=[]
            for ps in propsets:
                if hasattr(aq_base(ps), 'dav__propnames'):
                    stats.append(ps.dav__propnames())
            stats=string.join(stats, '') or '<d:status>200 OK</d:status>\n'
            result.write(stats)
        elif self.propnames:
            for name, ns in self.propnames:
                ps=obsheets.get(ns, None)
                if ps is not None and hasattr(aq_base(ps), 'dav__propstat'):
                    stat=ps.dav__propstat(name)
                else:
                    stat='<d:propstat xmlns:n="%s">\n' \
                    '  <d:prop>\n' \
                    '  <n:%s/>\n' \
                    '  </d:prop>\n' \
                    '  <d:status>HTTP/1.1 404 Not Found</d:status>\n' \
                    '  <d:responsedescription>\n' \
                    '  The property %s does not exist.\n' \
                    '  </d:responsedescription>\n' \
                    '</d:propstat>\n' % (ns, name, name)
                result.write(stat)
        else: raise 'Bad Request', 'Invalid request'
        result.write('</d:response>\n')        
        if depth in ('1', 'infinity') and iscol:
            for ob in obj.objectValues():
                dflag=hasattr(ob, '_p_changed') and (ob._p_changed == None)
                if hasattr(ob, '__dav_resource__'):
                    uri=os.path.join(url, absattr(ob.id))
                    depth=depth=='infinity' and depth or 0
                    self.apply(ob, uri, depth, result, top=0)
                    if dflag: ob._p_deactivate()
        if not top: return result
        result.write('</d:multistatus>')
        return result.getvalue()


class PropPatch:
    """Model a PROPPATCH request."""
    def __init__(self, request):
        self.request=request
        self.values=[]
        self.parse(request)

    def parse(self, request, dav='DAV:'):
        body=request.get('BODY', '')
        try:    root=XmlParser().parse(body)
        except: raise 'Bad Request', sys.exc_value
        vals=self.values
        e=root.elements('propertyupdate', ns=dav)
        if not e: raise 'Bad Request', 'Invalid xml request.'
        e=e[0]
        for ob in e.elements():
            if ob.name()=='set' and ob.namespace()==dav:
                proptag=ob.elements('prop', ns=dav)
                if not proptag: raise 'Bad Request', 'Invalid xml request.'
                proptag=proptag[0]
                for prop in proptag.elements():
                    # We have to ensure that all tag attrs (including
                    # an xmlns attr for all xml namespaces used by the
                    # element and its children) are saved, per rfc2518.
                    name, ns=prop.name(), prop.namespace()
                    e, attrs=prop.elements(), prop.attrs()
                    if (not e) and (not attrs):
                        # simple property
                        item=(name, ns, prop.strval(), {})
                        vals.append(item)
                    else:
                        # xml property
                        attrs={}
                        prop.remap({ns:'n'})
                        prop.del_attr('xmlns:n')
                        for attr in prop.attrs():
                            attrs[attr.qname()]=attr.value()
                        md={'__xml_attrs__':attrs}
                        item=(name, ns, prop.strval(), md)
                        vals.append(item)
            if ob.name()=='remove' and ob.namespace()==dav:
                proptag=ob.elements('prop', ns=dav)
                if not proptag: raise 'Bad Request', 'Invalid xml request.'
                proptag=proptag[0]
                for prop in proptag.elements():
                    item=(prop.name(), prop.namespace())
                    vals.append(item)

    def apply(self, obj):
        url=urlfix(self.request['URL'], 'PROPPATCH')
        if hasattr(obj, '__dav_collection__'):
            url=url+'/'
        result=StringIO()
        errors=[]
        result.write('<?xml version="1.0" encoding="utf-8"?>\n' \
                     '<d:multistatus xmlns:d="DAV:">\n' \
                     '<d:response>\n' \
                     '<d:href>%s</d:href>\n' % url)
        propsets=obj.propertysheets
        for value in self.values:
            status='200 OK'
            if len(value) > 2:
                name, ns, val, md=value
                propset=propsets.get(ns, None)
                if propset is None:
                    propsets.manage_addPropertySheet('', ns)
                    propset=propsets.get(ns)
                propdict=propset._propdict()
                if propset.hasProperty(name):
                    try: propset._updateProperty(name, val, meta=md)
                    except:
                        errors.append(str(sys.exc_value))
                        status='409 Conflict'
                else:
                    try: propset._setProperty(name, val, meta=md)
                    except:
                        errors.append(str(sys.exc_value))
                        status='409 Conflict'
            else:
                name, ns=value
                propset=propsets.get(ns, None)
                if propset is None or not propset.hasProperty(name):
                    errors.append('Property not found: %s' % name)
                    status='404 Not Found'
                else:
                    try: propset._delProperty(name)
                    except:
                        errors.append('%s cannot be deleted.' % name)
                        status='409 Conflict'
            if result != '200 OK': abort=1
            result.write('<d:propstat xmlns:n="%s">\n' \
                         '  <d:prop>\n' \
                         '  <n:%s/>\n' \
                         '  </d:prop>\n' \
                         '  <d:status>HTTP/1.1 %s</d:status>\n' \
                         '</d:propstat>\n' % (ns, name, status))
        errmsg=string.join(errors, '\n') or 'The operation succeded.'
        result.write('<d:responsedescription>\n' \
                     '%s\n' \
                     '</d:responsedescription>\n' \
                     '</d:response>\n' \
                     '</d:multistatus>' % errmsg)
        result=result.getvalue()
        if not errors: return result
        # This is lame, but I cant find a way to keep ZPublisher
        # from sticking a traceback into my xml response :(
        get_transaction().abort()
        result=string.replace(result, '200 OK', '424 Failed Dependency')
        return result





class Lock:
    """Model a LOCK request."""
    def __init__(self, request):
        self.request=request
        data=request.get('BODY', '')
        self.scope='exclusive'
        self.type='write'
        self.owner=''
        self.parse(data)

    def parse(self, data, dav='DAV:'):
        root=XmlParser().parse(data)
        info=root.elements('lockinfo', ns=dav)[0]
        ls=info.elements('lockscope', ns=dav)[0]
        self.scope=ls.elements()[0].name()
        lt=info.elements('locktype', ns=dav)[0]
        self.type=lt.elements()[0].name()
        lo=info.elements('owner', ns=dav)
        if lo: self.owner=lo[0].toxml()
