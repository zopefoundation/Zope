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
__doc__='''Machinery to support through-the-web editing

$Id: DT_UI.py,v 1.9 1999/03/10 00:15:07 klm Exp $''' 
__version__='$Revision: 1.9 $'[11:-2]

from DT_HTML import HTML

FactoryDefaultString="Factory Default"

HTML.document_template_edit_header='<h2>Edit Document</h2>'
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
             VALUE="<!--#var URL1-->">
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
    
    <BR CLEAR="ALL">
    <!--#var document_template_edit_footer-->
    
    </BODY>
    </HTML>""",)

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
    <!--#/if CANCEL_ACTION-->""")
