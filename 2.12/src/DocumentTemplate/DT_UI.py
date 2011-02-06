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
__doc__='''Machinery to support through-the-web editing

$Id$'''
__version__='$Revision: 1.15 $'[11:-2]

from DocumentTemplate.DT_HTML import HTML

FactoryDefaultString="Factory Default"

HTML.document_template_edit_header='<h2>Edit Document</h2>'
HTML.document_template_form_header=''
HTML.document_template_edit_footer=(
    """<FONT SIZE="-1">
    <I><A HREF="http://www.zope.com">
    &copy; 2002 Zope Corporation</A></I></FONT>""")
HTML._manage_editForm = HTML(
    """<HTML>
    <HEAD>
    <TITLE>HTML Template Editor</TITLE>
    </HEAD>
    <BODY bgcolor="#FFFFFF">
    <!--#var document_template_edit_header-->

    <FORM name="editform" ACTION="&dtml-URL1;/manage_edit" METHOD="POST">
    <!--#var document_template_form_header-->
    Document template source:
    <center>
    <br>
    <dtml-let cols="REQUEST.get('dtpref_cols', '100%')"
              rows="REQUEST.get('dtpref_rows', '20')">
    <dtml-if expr="cols[-1]=='%'">
    <textarea name="data:text" style="width: &dtml-cols;;"
    <dtml-else>
    <textarea name="data:text" cols="&dtml-cols;"
    </dtml-if>
              rows="&dtml-rows;"><dtml-var __str__></textarea>
    </dtml-let>
    <br>
      <INPUT NAME=SUBMIT TYPE="SUBMIT" VALUE="Change">
      <INPUT NAME=SUBMIT TYPE="RESET"  VALUE="Reset">
      <INPUT NAME="dt_edit_name" TYPE="HIDDEN"
             VALUE="&dtml-URL1;">
      <!--#if FactoryDefaultString-->
        <INPUT NAME=SUBMIT TYPE="SUBMIT"
         VALUE="&dtml-FactoryDefaultString;">
      <!--#/if FactoryDefaultString-->
      <INPUT NAME=SUBMIT TYPE="SUBMIT" VALUE="Cancel">
      <!--#if HTTP_REFERER-->
         <INPUT NAME="CANCEL_ACTION" TYPE="HIDDEN"
                VALUE="&dtml-HTTP_REFERER;">
      <!--#else HTTP_REFERER-->
         <!--#if URL1-->
           <INPUT NAME="CANCEL_ACTION" TYPE="HIDDEN"
                  VALUE="&dtml-URL1;">
         <!--#/if URL1-->
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
      <form action="&dtml-CANCEL_ACTION;" method="POST">
        <center>
           <em>&dtml-dt_edit_name;</em><br>has been changed.<br><br>
           <input type=submit name="SUBMIT" value="OK">
        </center>
      </form></body></html>
    <!--#else CANCEL_ACTION-->
      <center>
         <em>&dtml-dt_edit_name;</em><br>has been changed.
      </center>
    <!--#/if CANCEL_ACTION-->""")
