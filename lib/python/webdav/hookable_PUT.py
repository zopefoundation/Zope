#   Implement the "hookable PUT" hook.
import re, OFS.DTMLMethod

TEXT_PATTERN = re.compile( '^text/.*$' )

def PUT_factory( self, name, typ, body ):
    """
    """
    if TEXT_PATTERN.match( typ ):
        return OFS.DTMLMethod.DTMLMethod( '', __name__=name )
    return None
