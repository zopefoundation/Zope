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
"""HTTP Range support utilities.

The RFC 2616 specification defines the 'Range' and 'If-Range' headers for
enabeling partial download of published resources. This module provides a
flag-interface and some support functions for implementing this functionality.

For an implementation example, see the File class in OFS/Image.py.
"""

__version__='$Revision'[11:-2]

import re, string, sys
import Interface

WHITESPACE = re.compile('\s*', re.MULTILINE)

def parseRange(header):
    """RFC 2616 (HTTP 1.1) Range header parsing.

    Convert a range header to a list of slice indexes, returned as (start, end)
    tuples. If no end was given, end is None. Note that the RFC specifies the
    end offset to be inclusive, we return python convention indexes, where the
    end is exclusive. Syntactically incorrect headers are to be ignored, so if
    we encounter one we return None.

    """

    ranges = []
    add = ranges.append

    # First, clean out *all* whitespace. This is slightly more tolerant
    # than the spec asks for, but hey, it makes this function much easier.
    header = WHITESPACE.sub('', header)

    # A range header only can specify a byte range
    try: spec, sets = string.split(header, '=')
    except ValueError: return None
    if spec != 'bytes':
        return None

    # The sets are delimited by commas.
    sets = string.split(sets, ',')
    # Filter out empty values, things like ',,' are allowed in the spec
    sets = filter(None, sets)
    # We need at least one set
    if not sets:
        return None

    for set in sets:
        try: start, end = string.split(set, '-')
        except ValueError: return None

        # Catch empty sets
        if not start and not end:
            return None

        # Convert to integers or None (which will raise errors if
        # non-integers were used (which is what we want)).
        try:
            if start == '': start = None
            else: start = int(start)
            if end == '': end = None
            else: end = int(end)
        except ValueError:
            return None

        # Special case: No start means the suffix format was used, which
        # means the end value is actually a negative start value.
        # Convert this by making it absolute.
        # A -0 range is converted to sys.maxint, which will result in a
        # Unsatisfiable response if no other ranges can by satisfied either.
        if start is None:
            start, end = -end, None
            if not start:
                start = sys.maxint
        elif end is not None:
            end = end + 1 # Make the end of the range exclusive

        if end is not None and end <= start:
            return None

        # And store
        add((start, end))

    return ranges

def optimizeRanges(ranges, size):
    """Optimize Range sets, given those sets and the length of the resource.

    Optimisation is done by first expanding relative start values and open
    ends, then sorting and combining overlapping or adjacent ranges. We also
    remove unsatisfiable ranges (where the start lies beyond the size of the
    resource).

    """

    expanded = []
    add = expanded.append
    for start, end in ranges:
        if start < 0:
            start = size + start
        end = end or size
        if end > size: end = size
        # Only use satisfiable ranges
        if start < size:
            add((start, end))

    ranges = expanded
    ranges.sort()
    ranges.reverse()
    optimized = []
    add = optimized.append
    start, end = ranges.pop()
    
    while ranges:
        nextstart, nextend = ranges.pop()
        # If the next range overlaps or is adjacent
        if nextstart <= end:
            # If it falls within the current range, discard
            if nextend <= end:
                continue
            
            # Overlap, adjust end
            end = nextend
        else:
            add((start, end))
            start, end = nextstart, nextend

    # Add the remaining optimized range
    add((start, end))
    
    return optimized

class HTTPRangeInterface(Interface.Base):
    """Objects implementing this Interface support the HTTP Range header.

    Objects implementing support for the HTTP Range header will return partial
    content as specified in RFC 2616. Note that the'If-Range' header must
    either be implemented correctly or result in a normal '200 OK' response at
    all times.

    This interface specifies no methods, as this functionality can either be
    implemented in the index_html or __call__ methods of a published object.

    """
