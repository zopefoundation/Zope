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

__version__='$Revision: 1.1 $'[11:-2]

 
from STPDocumentTemplate import HTML

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
</BODY></HTML>""", target='')
