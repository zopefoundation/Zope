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

from App.special_dtml import HTML

MessageDialog = HTML("""
<HTML>
<HEAD>
<TITLE>&dtml-title;</TITLE>
</HEAD>
<BODY BGCOLOR="#FFFFFF">
<FORM ACTION="&dtml-action;" METHOD="GET" <dtml-if
 target>TARGET="&dtml-target;"</dtml-if>>
<TABLE BORDER="0" WIDTH="100%" CELLPADDING="10">
<TR>
  <TD VALIGN="TOP">
  <BR>
  <CENTER><B><FONT SIZE="+6" COLOR="#77003B">!</FONT></B></CENTER>
  </TD>
  <TD VALIGN="TOP">
  <BR><BR>
  <CENTER>
  <dtml-var message>
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
