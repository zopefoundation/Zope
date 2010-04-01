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
__rcs_id__='$Id$'
__version__='$Revision: 1.12 $'[11:-2]

from DocumentTemplate.DT_Util import *
from DocumentTemplate.DT_String import String
from cStringIO import StringIO
import mimetools

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
                                   , cid=None, cid_expr=None
                                   , charset=None, charset_expr=None
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
                                   , cid=None, cid_expr=None
                                   , charset=None, charset_expr=None
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

            if has_key('cid_expr'):
                if has_key('cid'):
                    raise ParseError, _tm('cid and cid_expr given', 'mime')
                args['cid_expr']=Eval(args['cid_expr'])
            elif not has_key('cid'):
                args['cid']=''

            if has_key('charset_expr'):
                if has_key('charset'):
                    raise ParseError, _tm('charset and charset_expr given', 'mime')
                args['charset_expr']=Eval(args['charset_expr'])
            elif not has_key('charset'):
                args['charset']=''

            if has_key('skip_expr'):
                args['skip_expr']=Eval(args['skip_expr'])

            if args['encode'] not in \
            ('base64', 'quoted-printable', 'uuencode', 'x-uuencode',
             'uue', 'x-uue', '7bit'):
                raise MIMEError, (
                    'An unsupported encoding was specified in tag')

            self.sections.append((args, section.blocks))


    def render(self, md):
        from MimeWriter import MimeWriter # deprecated since Python 2.3!
        contents=[]
        IO = StringIO()
        IO.write("Mime-Version: 1.0\n")
        mw = MimeWriter(IO)
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

            if has_key('cid_expr'): cid=a['cid_expr'].eval(md)
            else: cid=a['cid']

            if has_key('charset_expr'): charset=a['charset_expr'].eval(md)
            else: charset=a['charset']

            if d:
                if f:
                    inner.addheader('Content-Disposition', '%s;\n filename="%s"' % (d, f))
                else:
                    inner.addheader('Content-Disposition', d)

            inner.addheader('Content-Transfer-Encoding', e)

            if cid:
                inner.addheader('Content-ID', '<%s>' % cid)

            if n:
                plist = [('name', n)]
            else:
                plist = []

            if t.startswith('text/'):
                plist.append(('charset', charset or 'us-ascii'))

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
