# split off into its own module for aliasing without circrefs

from cgi import escape
from ustr import ustr

def html_quote(v, name='(Unknown name)', md={}):
    return escape(ustr(v), 1)

