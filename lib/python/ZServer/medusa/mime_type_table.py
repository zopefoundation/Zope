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
#
#	Author: Sam Rushing <rushing@nightmare.com>
#

# Converted by ./convert_mime_type_table.py from:
# /usr/src2/apache_1.2b6/conf/mime.types

content_type_map = \
  {
        'ai':  'application/postscript',
       'aif':  'audio/x-aiff',
      'aifc':  'audio/x-aiff',
      'aiff':  'audio/x-aiff',
        'au':  'audio/basic',
       'avi':  'video/x-msvideo',
     'bcpio':  'application/x-bcpio',
       'bin':  'application/octet-stream',
       'cdf':  'application/x-netcdf',
     'class':  'application/octet-stream',
      'cpio':  'application/x-cpio',
       'cpt':  'application/mac-compactpro',
       'csh':  'application/x-csh',
       'dcr':  'application/x-director',
       'dir':  'application/x-director',
       'dms':  'application/octet-stream',
       'doc':  'application/msword',
       'dvi':  'application/x-dvi',
       'dxr':  'application/x-director',
       'eps':  'application/postscript',
       'etx':  'text/x-setext',
       'exe':  'application/octet-stream',
       'gif':  'image/gif',
      'gtar':  'application/x-gtar',
        'gz':  'application/x-gzip',
       'hdf':  'application/x-hdf',
       'hqx':  'application/mac-binhex40',
       'htm':  'text/html',
      'html':  'text/html',
       'ice':  'x-conference/x-cooltalk',
       'ief':  'image/ief',
       'jpe':  'image/jpeg',
      'jpeg':  'image/jpeg',
       'jpg':  'image/jpeg',
       'kar':  'audio/midi',
     'latex':  'application/x-latex',
       'lha':  'application/octet-stream',
       'lzh':  'application/octet-stream',
       'man':  'application/x-troff-man',
        'me':  'application/x-troff-me',
       'mid':  'audio/midi',
      'midi':  'audio/midi',
       'mif':  'application/x-mif',
       'mov':  'video/quicktime',
     'movie':  'video/x-sgi-movie',
       'mp2':  'audio/mpeg',
       'mpe':  'video/mpeg',
      'mpeg':  'video/mpeg',
       'mpg':  'video/mpeg',
      'mpga':  'audio/mpeg',
       'mp3':  'audio/mpeg',
        'ms':  'application/x-troff-ms',
        'nc':  'application/x-netcdf',
       'oda':  'application/oda',
       'pbm':  'image/x-portable-bitmap',
       'pdb':  'chemical/x-pdb',
       'pdf':  'application/pdf',
       'pgm':  'image/x-portable-graymap',
       'png':  'image/png',
       'pnm':  'image/x-portable-anymap',
       'ppm':  'image/x-portable-pixmap',
       'ppt':  'application/powerpoint',
        'ps':  'application/postscript',
        'qt':  'video/quicktime',
        'ra':  'audio/x-realaudio',
       'ram':  'audio/x-pn-realaudio',
       'ras':  'image/x-cmu-raster',
       'rgb':  'image/x-rgb',
      'roff':  'application/x-troff',
       'rpm':  'audio/x-pn-realaudio-plugin',
       'rtf':  'application/rtf',
       'rtx':  'text/richtext',
       'sgm':  'text/x-sgml',
      'sgml':  'text/x-sgml',
        'sh':  'application/x-sh',
      'shar':  'application/x-shar',
       'sit':  'application/x-stuffit',
       'skd':  'application/x-koan',
       'skm':  'application/x-koan',
       'skp':  'application/x-koan',
       'skt':  'application/x-koan',
       'snd':  'audio/basic',
       'src':  'application/x-wais-source',
   'sv4cpio':  'application/x-sv4cpio',
    'sv4crc':  'application/x-sv4crc',
         't':  'application/x-troff',
       'tar':  'application/x-tar',
       'tcl':  'application/x-tcl',
       'tex':  'application/x-tex',
      'texi':  'application/x-texinfo',
   'texinfo':  'application/x-texinfo',
       'tif':  'image/tiff',
      'tiff':  'image/tiff',
        'tr':  'application/x-troff',
       'tsv':  'text/tab-separated-values',
       'txt':  'text/plain',
     'ustar':  'application/x-ustar',
       'vcd':  'application/x-cdlink',
      'vrml':  'x-world/x-vrml',
       'wav':  'audio/x-wav',
       'wrl':  'x-world/x-vrml',
       'xbm':  'image/x-xbitmap',
       'xpm':  'image/x-xpixmap',
       'xwd':  'image/x-xwindowdump',
       'xyz':  'chemical/x-pdb',
       'zip':  'application/zip',
  }
