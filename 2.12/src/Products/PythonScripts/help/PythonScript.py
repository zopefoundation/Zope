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

def manage_addPythonScript(id, REQUEST=None):
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

    Python Scripts can contain a "safe" subset of the python language.
    Python Scripts must be safe because they can be potentially edited by
    many different users through an insecure medium like the web.  The
    following safety issues drive the need for secure Python Scripts:

      o Because many users can use Zope, a Python Script must make sure it
        does not allow a user to do something they are not allowed to do,
        like deleting an object they do not have permission to delete.
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

          o random

          o Products.PythonScripts.standard

      o Because it allows you to execute arbitrary python code, the python
        "exec" statement is not allowed in Python methods.

      o Because they may represent or cause security violations, some
        Python builtin functions are not allowed.  The following
        Python builtins are not allowed:

          o open

          o input

          o raw_input

          o eval

          o execfile

          o compile

          o type

          o coerce

          o intern

          o dir

          o globals

          o locals

          o vars

          o buffer

          o reduce

      o Other builtins are restricted in nature.  The following builtins
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

          o test

          o namespace

          o render

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


    def ZScriptHTML_tryParams():
        """

        Return a list of the required parameters with which to
        test the script.

        """


    def read():
        """

        Return the body of the Python Script, with a special comment
        block prepended.  This block contains meta-data in the form of
        comment lines as expected by the 'write' method.

        """

    def write(text):
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
