"""
Products.PythonScripts.standard: Utility functions and classes

  The functions and classes in this module are available from
  Python-based scripts, DTML, and Page Templates.

"""

def whole_dollars(number):
    """
    Show a numeric value with a dollar symbol.
    """

def dollars_and_cents(number):
    """
    Show a numeric value with a dollar symbol and two decimal places.
    """

def structured_text(s):
    """
    Convert a string in structured-text format to HTML.

    See Also

      "Structured-Text Rules":http://dev.zope.org/Members/jim/StructuredTextWiki/StructuredTextNGRules

    """

def sql_quote(s):
    """
    Convert single quotes to pairs of single quotes. This is needed to
    safely include values in Standard Query Language (SQL) strings.
    """

def html_quote(s):
    """
    Convert characters that have special meaning in HTML to HTML
    character entities.

    See Also

      "Python 'cgi' module":http://www.python.org/doc/current/lib/Functions_in_cgi_module.html
      'escape' function.

    """

def url_quote(s):
    """
    Convert characters that have special meaning in URLS to HTML
    character entities using decimal values.

    See Also

       "Python 'urllib' module":http://www.python.org/doc/current/lib/module-urllib.html
       'quote' function.

    """
    
def url_quote_plus(s):
    """
    Like url_quote but also replace blank space characters with
    '+'. This is needed for building query strings in some cases.

    See Also

      "Python 'urllib' module":http://www.python.org/doc/current/lib/module-urllib.html
      'quote_plus' function.

    """

def url_unquote(s):
    """
    Convert HTML %xx character entities into the characters they
    represent.  (Undoes the affects of url_quote).

    See Also

       "Python 'urllib' module":http://www.python.org/doc/current/lib/module-urllib.html
       'unquote' function.

    """

def url_unquote_plus(s):
    """
    Like url_unquote but also replace '+' characters with blank spaces.

    See Also

      "Python 'urllib' module":http://www.python.org/doc/current/lib/module-urllib.html
      'unquote_plus' function.

    """
    
def urlencode(query, doseq=0):
    """
    Convert a mapping object (such as a dictionary) or a sequence of 
    two-element  tuples to a URL encoded query string. Useful for generating 
    query strings programmatically.

    See Also

      "Python 'urllib' module":http://www.python.org/doc/current/lib/module-urllib.html
      'urlencode' function.
    """

def newline_to_br(s):
    """
    Convert newlines and carriage-return and newline combinations to
    break tags.
    """

def thousand_commas(number):
    """
    Insert commas every three digits to the left of a decimal point in
    values containing numbers.  For example, the value, "12000
    widgets" becomes "12,000 widgets".
    """

class DTML:
    """
    DTML - temporary, security-restricted DTML objects
    """

    def __init__(source, **kw):
        """
        Create a DTML object with source text and keyword
        variables. The source text defines the DTML source
        content. The optinal keyword arguments define variables.
        """

    def call(client=None, REQUEST={}, **kw):
        """
        Render the DTML.

        To accomplish its task, DTML often needs to resolve various
        names into objects.  For example, when the code &lt;dtml-var
        spam&gt; is executed, the DTML engine tries to resolve the
        name 'spam'.

        In order to resolve names, you must be pass a namespace to the
        DTML.  This can be done several ways:

        * By passing a 'client' object - If the argument 'client' is
          passed, then names are looked up as attributes on the
          argument.

        * By passing a 'REQUEST' mapping - If the argument 'REQUEST'
          is passed, then names are looked up as items on the
          argument.  If the object is not a mapping, an TypeError
          will be raised when a name lookup is attempted.

        * By passing keyword arguments -- names and their values can
          be passed as keyword arguments to the Method.

        The namespace given to a DTML object is the composite of these
        three methods.  You can pass any number of them or none at
        all. Names will be looked up first in the keyword argument,
        next in the client and finally in the mapping.

        """
