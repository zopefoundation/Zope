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

"""Common HTML dialog boxes

    MessageDialog(title, message, action, [target])

    A very simple dialog used to display an HTML page titled title, 
    displaying message message and an OK button. Clicking the OK 
    button will take the browser to the URL specified in action. 
    The *optional* target argument can be used to force a (frames 
    capable) browser to load the URL specified in action into a specific 
    frame. (Specifying '_new' will cause the browser to load the
    specified URL into a new window, for example).

    example usage:
    <PRE>
    return MessageDialog(title='Just thought you should know...',
                         message='You have wiped out your data.',
                         action='/paid_tech_support/prices.html',
                         target='_top')
    </PRE>"""

__version__='$Revision: 1.5 $'[11:-2]

 
from Globals import HTML

MessageDialog = HTML("""
<HTML>
<HEAD>
<TITLE><!--#var title--></TITLE>
</HEAD>
<BODY BGCOLOR="#FFFFFF">
<FORM ACTION="<!--#var action-->" METHOD="GET" 
      <!--#if target-->
      TARGET="<!--#var target-->"
      <!--#/if target-->>
<TABLE BORDER="0" WIDTH="100%" CELLPADDING="10">
<TR>
  <TD VALIGN="TOP">
  <BR>
  <CENTER><B><FONT SIZE="+6" COLOR="#77003B">!</FONT></B></CENTER>
  </TD>
  <TD VALIGN="TOP">
  <BR><BR>
  <CENTER>
  <!--#var message-->
  </CENTER>
  </TD>
</TR>
<TR>
  <TD VALIGN="TOP">
  </TD>
  <TD VALIGN="TOP">
  <CENTER>
  <INPUT TYPE="SUBMIT" VALUE="   Ok   ">
  </CENTER>
  </TD>
</TR>
</TABLE>
</FORM>
</BODY></HTML>""", target='', action='manage_main', title='Changed')
