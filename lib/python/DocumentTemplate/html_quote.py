# split off into its own module for aliasing without circrefs

from cgi import escape

def html_quote(v, name='(Unknown name)', md={}):
    return escape(str(v), 1)

