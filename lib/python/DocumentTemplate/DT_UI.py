
__doc__='''Machinery to support through-the-web editing

$Id: DT_UI.py,v 1.2 1997/09/02 19:04:52 jim Exp $''' 

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
__version__='$Revision: 1.2 $'[11:-2]

from DT_HTML import HTML

FactoryDefaultString="Factory Default"

HTML.document_template_edit_header='<h2>Document Template Editor</h2>'
HTML.document_template_form_header=''
HTML.document_template_edit_footer=(
    """<FONT SIZE="-1">
    <I><A HREF="http://www.digicool.com/products/copyright.html">
    &copy; 1997 Digital Creations, L.L.C.</A></I></FONT>""")
HTML.document_template_edit_width=58

HTML._manage_editForm = HTML(
    """<HTML>
    <HEAD>
    <TITLE>HTML Template Editor</TITLE>
    </HEAD>
    <BODY bgcolor="#FFFFFF">
    <!--#var document_template_edit_header-->
    
    <em><!--#var PATH_INFO--></em><br>

    <FORM name="editform" ACTION="<!--#var PARENT_URL-->/manage_edit" METHOD="POST">
    <!--#var document_template_form_header-->
    Document template source:
    <center>
    <br>
    <TEXTAREA NAME="data:text" cols="<!--#var document_template_edit_width-->" 
                    rows="20"><!--#var __str__--></TEXTAREA>

    <br>
      <INPUT NAME=SUBMIT TYPE="SUBMIT" VALUE="Change">
      <INPUT NAME=SUBMIT TYPE="RESET"  VALUE="Reset">
      <INPUT NAME="dt_edit_name" TYPE="HIDDEN"
             VALUE="<!--#var PATH_INFO-->">
      <!--#if FactoryDefaultString-->
        <INPUT NAME=SUBMIT TYPE="SUBMIT" 
         VALUE="<!--#var FactoryDefaultString-->">
      <!--#/if FactoryDefaultString-->
      <INPUT NAME=SUBMIT TYPE="SUBMIT" VALUE="Cancel">
      <!--#if HTTP_REFERER-->
    	 <INPUT NAME="CANCEL_ACTION" TYPE="HIDDEN" 
    		VALUE="<!--#var HTTP_REFERER-->">
      <!--#else HTTP_REFERER-->
         <!--#if PARENT_URL-->
    	   <INPUT NAME="CANCEL_ACTION" TYPE="HIDDEN"
    		  VALUE="<!--#var PARENT_URL-->">
         <!--#/if PARENT_URL-->
      <!--#/if HTTP_REFERER-->
    </center>
    </FORM>
    
    <!--#if vars-->
      <p>The following variables may be used in this template:</p>
      <table border>
      <tr>
      <th>Variables
      <th>Description
      <!--#in vars-->
        <tr>
           <td><!--#var sequence-key--></td>
           <td><!--#var __str__--></td>
        </tr>
      <!--#/in vars-->
      </table>
    <!--#/if vars-->

    <BR CLEAR="ALL">
    <!--#var document_template_edit_footer-->
    
    </BODY>
    </HTML>""", #"
    __names__={
    'HTTP_REFERER':'Referring URL',
    'PARENT_URL':"This page's parent",
    'document_template_edit_header':"(internal)",
    'document_template_edit_footer':"(internal)",
    '__str__':"(internal)",
    'vars':'list of DTML variables you can manipulate',
    'descrip':'desciption of DTML variables you can manipulate',
    })

HTML.editConfirmation=HTML(
    """<html><head><title>Change Successful</title></head><body>
    <!--#if CANCEL_ACTION-->
      <form action="<!--#var CANCEL_ACTION-->" method="POST">
    	<center>
    	   <em><!--#var dt_edit_name--></em><br>has been changed.<br><br>
    	   <input type=submit name="SUBMIT" value="OK">
    	</center>
      </form></body></html>
    <!--#else CANCEL_ACTION-->
      <center>
    	 <em><!--#var dt_edit_name--></em><br>has been changed.
      </center>
    <!--#/if CANCEL_ACTION-->""",#"
    __names__={
    'CANCEL_ACTION':'???',
    'PARENT_URL':"This page's parent",
    })

############################################################################
# $Log: DT_UI.py,v $
# Revision 1.2  1997/09/02 19:04:52  jim
# Got rid of ^Ms
#
# Revision 1.1  1997/08/27 18:55:43  jim
# initial
#
