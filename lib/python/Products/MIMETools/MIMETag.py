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
__rcs_id__='$Id: MIMETag.py,v 1.6 2001/04/27 20:27:41 shane Exp $'
__version__='$Revision: 1.6 $'[11:-2]

from DocumentTemplate.DT_Util import *
from DocumentTemplate.DT_String import String
from MimeWriter import MimeWriter
from cStringIO import StringIO
import string, mimetools

MIMEError = "MIME Tag Error"

class MIMETag:
    '''
    '''

    name='mime'
    blockContinuations=('boundary',)
    encode=None

    def __init__(self, blocks):
        self.sections = []

        for tname, args, section in blocks:
            if tname == 'mime':
                args = parse_params( args
                                   , type=None, type_expr=None
                                   , disposition=None, disposition_expr=None
                                   , encode=None, encode_expr=None
                                   , name=None, name_expr=None
                                   , filename=None, filename_expr=None
                                   , skip_expr=None
                                   , multipart=None
                                   )
                self.multipart = args.get('multipart', 'mixed')
            else:
                args = parse_params( args
                                   , type=None, type_expr=None
                                   , disposition=None, disposition_expr=None
                                   , encode=None, encode_expr=None
                                   , name=None, name_expr=None
                                   , filename=None, filename_expr=None
                                   , skip_expr=None
                                   )

            has_key=args.has_key

            if has_key('type'): 
                type = args['type']
            else:
                type = 'application/octet-stream'

            if has_key('type_expr'):
                if has_key('type'):
                    raise ParseError, _tm('type and type_expr given', 'mime')
                args['type_expr']=Eval(args['type_expr'])
            elif not has_key('type'):
                args['type']='application/octet-stream'

            if has_key('disposition_expr'):
                if has_key('disposition'):
                    raise ParseError, _tm('disposition and disposition_expr given', 'mime')
                args['disposition_expr']=Eval(args['disposition_expr'])
            elif not has_key('disposition'):
                args['disposition']=''

            if has_key('encode_expr'):
                if has_key('encode'):
                    raise ParseError, _tm('encode and encode_expr given', 'mime')
                args['encode_expr']=Eval(args['encode_expr'])
            elif not has_key('encode'):
                args['encode']='base64'

            if has_key('name_expr'):
                if has_key('name'):
                    raise ParseError, _tm('name and name_expr given', 'mime')
                args['name_expr']=Eval(args['name_expr'])
            elif not has_key('name'):
                args['name']=''

            if has_key('filename_expr'):
                if has_key('filename'):
                    raise ParseError, _tm('filename and filename_expr given', 'mime')
                args['filename_expr']=Eval(args['filename_expr'])
            elif not has_key('filename'):
                args['filename']=''

            if has_key('skip_expr'):
                args['skip_expr']=Eval(args['skip_expr'])

            if args['encode'] not in \
            ('base64', 'quoted-printable', 'uuencode', 'x-uuencode',
             'uue', 'x-uue', '7bit'):
                raise MIMEError, (
                    'An unsupported encoding was specified in tag')

            self.sections.append((args, section.blocks))


    def render(self, md):
        contents=[]
        mw = MimeWriter(StringIO())
        outer = mw.startmultipartbody(self.multipart)
        for x in self.sections:
            a, b = x
            has_key=a.has_key

            if has_key('skip_expr') and a['skip_expr'].eval(md):
                continue
                
            inner = mw.nextpart()

            if has_key('type_expr'): t=a['type_expr'].eval(md)
            else: t=a['type']

            if has_key('disposition_expr'): d=a['disposition_expr'].eval(md)
            else: d=a['disposition']

            if has_key('encode_expr'): e=a['encode_expr'].eval(md)
            else: e=a['encode']

            if has_key('name_expr'): n=a['name_expr'].eval(md)
            else: n=a['name']
            
            if has_key('filename_expr'): f=a['filename_expr'].eval(md)
            else: f=a['filename']

            if d:
                if f:
                    inner.addheader('Content-Disposition', '%s;\n filename="%s"' % (d, f))
                else:
                    inner.addheader('Content-Disposition', d)

            inner.addheader('Content-Transfer-Encoding', e)
            if n:
                plist = [('name', n)]
            else:
                plist = []

            innerfile = inner.startbody(t, plist, 1)

            output = StringIO()
            if e == '7bit':
                innerfile.write(render_blocks(b, md))
            else:
                mimetools.encode(StringIO(render_blocks(b, md)),
                                 output, e)
                output.seek(0)
                innerfile.write(output.read())

        # XXX what if self.sections is empty ??? does it matter that mw.lastpart() is called
        # right after mw.startmultipartbody() ?
        if x is self.sections[-1]:
            mw.lastpart()

        outer.seek(0)
        return outer.read()


    __call__=render



String.commands['mime'] = MIMETag





