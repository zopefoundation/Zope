#!/usr/local/bin/python 
# $What$

from DT_Util import *
import DT_Doc, DT_Var, DT_In, DT_If
__doc__=DT_Doc.__doc__ % {
    'In': DT_In.__doc__,
    'If': DT_If.__doc__,
    'Var': DT_Var.__doc__,
    'id': '$Id: DocumentTemplate.py,v 1.1 1997/08/27 18:55:45 jim Exp $'
    }

############################################################################
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.  Copyright in this software is owned by DCLC,
#       unless otherwise indicated. Permission to use, copy and
#       distribute this software is hereby granted, provided that the
#       above copyright notice appear in all copies and that both that
#       copyright notice and this permission notice appear. Note that
#       any product, process or technology described in this software
#       may be the subject of other Intellectual Property rights
#       reserved by Digital Creations, L.C. and are not licensed
#       hereunder.
#
#     Trademarks 
#
#       Digital Creations & DCLC, are trademarks of Digital Creations, L.C..
#       All other trademarks are owned by their respective companies. 
#
#     No Warranty 
#
#       The software is provided "as is" without warranty of any kind,
#       either express or implied, including, but not limited to, the
#       implied warranties of merchantability, fitness for a particular
#       purpose, or non-infringement. This software could include
#       technical inaccuracies or typographical errors. Changes are
#       periodically made to the software; these changes will be
#       incorporated in new editions of the software. DCLC may make
#       improvements and/or changes in this software at any time
#       without notice.
#
#     Limitation Of Liability 
#
#       In no event will DCLC be liable for direct, indirect, special,
#       incidental, economic, cover, or consequential damages arising
#       out of the use of or inability to use this software even if
#       advised of the possibility of such damages. Some states do not
#       allow the exclusion or limitation of implied warranties or
#       limitation of liability for incidental or consequential
#       damages, so the above limitation or exclusion may not apply to
#       you.
#  
#
# If you have questions regarding this software,
# contact:
#
#   Jim Fulton, jim@digicool.com
#
#   (540) 371-6909
#
############################################################################ 
__version__='$Revision: 1.1 $'[11:-2]

ParseError='Document Template Parse Error'

from DT_String import String, File
from DT_HTML import HTML, HTMLFile
import DT_UI # Install HTML editing

############################################################################
# $Log: DocumentTemplate.py,v $
# Revision 1.1  1997/08/27 18:55:45  jim
# initial
#
# Revision 1.13  1997/08/19 19:15:51  jim
# Escaped some quotes in strings to make python-mode happy.
# Moved Python implementation of things implemented in cDocumentTemplate
# to pDocumentTemplate.
#
# Revision 1.12  1997/08/06 14:06:16  jim
# Added id method.
#
# Revision 1.11  1997/08/05 21:44:59  jim
# Changed the way InstanceDicts call template attributes to avoid
# problem with instance attributes overriding kw arguments.
#
# Revision 1.10  1997/07/07 18:50:08  jim
# Many new features including:
#
#   - Better tracebacks from In, Var, etc.,
#   - shared globals so that you can have DT class-specific globals.
#   - Now can say /if or endif, and in or endin.
#
# Revision 1.9  1997/04/30 15:20:28  jim
# Made editing window skinnier for now.
# Added a variable, document_template_edit_width to control editing
# width.
#
# Revision 1.8  1997/04/21 20:34:57  jim
# Removed code to quote %es, since we don't use Python's rendering
# machinery any more.
#
# Revision 1.7  1997/04/14 12:07:34  jim
# Changed user interface to get edit display name from
# PATH_INFO and to give precedence to HTTP_REFERER over PARENT_URL as a
# post-editing destination.
#
# Revision 1.6  1997/04/12 17:28:42  jim
# Prettified editing.
#
# Revision 1.5  1997/04/11 19:30:47  jim
# Took out Skip's print statements.
#
# Revision 1.4  1997/04/09 22:23:43  jim
# Major changes to use new rendering machinery.
#
# Validation is mainly disabled.  It will be reenabled in a future
# revision.
#
# TemplateDict, InstanceDict and core rendering loop written in C.
#
# Revision 1.3  1997/04/08 02:07:36  jim
# Changed to use MultiMapping module, rather than cMultiMapping.
#
# Revision 1.2  1997/03/14 17:25:08  jim
# Fixed bug that prevented exception propigation from #if blocks.
#
# Added code to prevent uneeded saving of persistent DTs when the state
# changes during rendering.
#
# Revision 1.1  1997/03/08 14:50:14  jim
# I screwed up on hacking CVS and lost older revisions.
#
# Revision 1.19  1997/01/30 22:13:16  jim
# Fixed bug in __setstate__.
#
# Revision 1.18  1997/01/29 23:40:32  jim
# Integrated and debugged Skip's validation updates.
#
# Changed if and else to treat undefined objects as false.
#
# Changed editing logic for File classes so that edited objects are
# still file objects.  This means you can subclass File (HTMLFile)
# classes without having to subclass String (HTML).
#
# Moved log section of comments to bottom of file.
#
# Revision 1.17  1996/12/02 14:41:23  jim
# Fixed bug in parsing if constructs.
#
# Revision 1.16  1996/10/24 17:17:43  jim
# Renamed edit and editForm to manage_edit and manage_editForm.
# (The name editForm is retained temporarily, until we make sure we
# don't use it anywhere, which we shouldn't be anyway.
#
# Added allow groups definitions for manage_edit and manage_editForm.
#
# Revision 1.15  1996/10/15 20:43:33  jim
# Fixed bug in edit confirmation that caused server to hang due to
# getting a post with no input fields.
#
# Revision 1.14  1996/10/02 18:43:42  jim
# Added several special formats.
#
# Revision 1.13  1996/09/18 21:37:03  jim
# Took out !@@$# print statement!
#
# Revision 1.12  1996/09/18 14:49:38  jim
# Added null option for var and allowed custom C format strings, such as
# $ %.2f.
#
# Revision 1.11  1996/09/17 21:45:25  jim
# Added user-defined formats.
# Fixed orphans to match definition.
# Made handling of batch parameters more robust so pages that specify
# parameters don't have to cast to int.
# Updated docs.
#
# Revision 1.10  1996/08/30 22:39:02  jfulton
# *** empty log message ***
#
# Revision 1.9  1996/08/30 17:12:13  jfulton
# *** empty log message ***
#
# Revision 1.8  1996/08/28 21:12:04  jfulton
# Many fixes
# and roman numerals.
#
# Revision 1.7  1996/08/20 23:24:50  jfulton
# Added default method.
# Made mapping arg in __call__ check for None.
# Updated tests.
#
# Revision 1.6  1996/08/16 19:10:59  jfulton
# Added batch sequence processing.
# Improved error propigation.
# Other things I've already forgotten.
#
# Revision 1.5  1996/08/07 20:04:18  jfulton
# Fixed bug in do_vars
#
# Revision 1.4  1996/08/06 19:31:57  jfulton
# Added new HTML syntax and updated docs.
#
# Revision 1.3  1996/08/05 11:31:00  jfulton
# Added HTML class that does HTML quoting.
# Added conditional insertion (if and else) and explicit iteration (in).
# Added testing and mutating methods.
# Fixed bug in __setstate__.
# Updated doc string.
#
# Revision 1.2  1996/07/30 21:01:08  jfulton
# Added logic to prevent instance dicts from divuldging names that start
# with _.
#
# Revision 1.1  1996/07/30 20:56:39  jfulton
# *** empty log message ***
#
#
