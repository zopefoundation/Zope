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

def manage_addPythonScript(self, id, REQUEST=None):
    """Add a Python script to a folder.
    """

class PythonScript:
    """

    Python Scripts contain python code that gets executed when you call the
    script by:

      o Calling the script through the web by going to its location with a
        web browser.

      o Calling the script from another script object.

      o Calling the script from a method object, such as a DTML Method.

    Python scripts can contain a "safe" subset of the python language.
    Python Scripts must be safe because they can be potentially edited by
    many different users through an insecure medium like the web.  The
    following safety issues drive the need for secure Python Scripts:

      o Because many users can use Zope, a Python Script must make sure it
        does not allow a user to do something they are not allowed to do,
        like delete an object they do not have permission to delete.
        Because of this requirement, Python Scripts do many security checks
        in the course of their execution.

      o Because Python Scripts can be edited through the insecure medium of
        the web, they are not allowed access to the Zope server's
        file-system.  Normal Python builtins like 'open' are, therefore,
        not allowed.

      o Because many standard Python modules break the above two security
        restrictions, only a small subset of Python modules may be imported
        into a Python Scripts with the "import" statement unless they have
        been validated by Zope's security policy.  Currently, the following
        standard python modules have been validated:

          o string

          o math

          o whrandom and random

          o Products.PythonScripts.standard

      o Because it allows you to execute arbitrary python code, the python
        "exec" statement is not allowed in Python methods.

      o Because they may represent or cause security violations, some
        Python builtin functions are not allowed or are restricted.  The
        following Python builtins are not allowed:

          o open, input, raw_input

          o eval, execfile, compile

          o type, coerce, intern

          o dir, globals, locals, vars

          o buffer, reduce

        Other builtins are restricted in nature.  The following builtins
        are restricted:

          range -- Due to possible memory denial of service attacks, the
          range builtin is restricted to creating ranges less than 10,000
          elements long.

          filter, map, tuple, list -- For the same reason, builtins
          that construct lists from sequences do not operate on strings.
          
          getattr, setattr, delattr -- Because these may enable Python
          code to circumvent Zope's security system, they are replaced with
          custom, security constrained versions.

      o In order to be consistent with the Python expressions
      available to DTML, the builtin functions are augmented with a
      small number of functions and a class:

          o test, namespace, render

          o same_type

          o DateTime

      o Because the "print" statement cannot operate normally in Zope,
        its effect has been changed.  Rather than sending text to
        stdout, "print" appends to an internal variable.  The special
        builtin name "printed" evaluates to the concatenation of all
        text printed so far during the current execution of the
        script.

    """

    __constructor__ = manage_addPythonScript

    __extends__=(
        'PythonScripts.Script.Script',
        )
    

    def ZPythonScriptHTML_editAction(REQUEST, title, params, body):
        """

        Change the script's main parameters.  This method accepts the
        following arguments:

          REQUEST -- The current request.

          title -- The new value of the Python Script's title.  This must
          be a string.

          params -- The new value of the Python Script's parameters.  Must
          be a comma seperated list of values in valid python function
          signature syntax.  If it does not contain a valid signature
          string, a SyntaxError is raised.

          body -- The new value of the Python Script's body.  Must contain
          valid Python syntax.  If it does not contain valid Python syntax,
          a SyntaxError is raised.

        """

    def ZPythonScript_setTitle(title):
        """

        Change the script's title.  This method accepts one argument,
        'title' which is the new value for the script's title and must be a
        string.

        """

    def ZPythonScript_edit(params, body):
        """

        Change the parameters and body of the script.  This method accepts
        two arguments:

          params -- The new value of the Python Script's parameters.  Must
          be a comma seperated list of values in valid python function
          signature syntax.  If it does not contain a valid signature
          string, a SyntaxError is raised.

          body -- The new value of the Python Script's body.  Must contain
          valid Python syntax.  If it does not contain valid Python syntax,
          a SyntaxError is raised.

        """

    def ZPythonScriptHTML_upload(REQUEST, file=''):
        """

        Pass the text in file to the 'write' method.

        """


    def ZScriptHTML_tryParams(self):
        """

        Return a list of the required parameters with which to
        test the script.

        """


    def read(self):
        """

        Return the body of the Python Script, with a special comment
        block prepended.  This block contains meta-data in the form of
        comment lines as expected by the 'write' method.

        """

    def write(self, text):
        """

        Change the script by parsing the text argument into parts.
        Leading lines that begin with '##' are stripped off, and if
        they are of the form '##name=value', they are used to set
        meta-data such as the title and parameters.  The remainder of
        the text is set as the body of the Python Script.

        """

    def document_src(REQUEST=None, RESPONSE=None):
        """

        Return the text of the 'read' method, with content type
        'text/plain' set on the RESPONSE.

        """





