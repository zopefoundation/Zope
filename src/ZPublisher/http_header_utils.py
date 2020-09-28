"""This module offers helpers to handle HTTP headers."""

# The function `make_content_disposition` was vendored from our
# friends from `CherryPy` - thank you!
#
# Copyright © 2004-2019, CherryPy Team (team@cherrypy.org)
#
# All rights reserved.
#
# * * *
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of CherryPy nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE  # noqa: E501
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import unicodedata
import urllib


def make_content_disposition(disposition, file_name):
    """Create HTTP header for downloading a file with a UTF-8 filename.
    This function implements the recommendations of :rfc:`6266#appendix-D`.
    See this and related answers: https://stackoverflow.com/a/8996249/2173868.
    """
    # As normalization algorithm for `unicodedata` is used composed form (NFC
    # and NFKC) with compatibility equivalence criteria (NFK), so "NFKC" is the
    # one. It first applies the compatibility decomposition, followed by the
    # canonical composition. Should be displayed in the same manner, should be
    # treated in the same way by applications such as alphabetizing names or
    # searching, and may be substituted for each other.
    # See: https://en.wikipedia.org/wiki/Unicode_equivalence.
    ascii_name = (
        unicodedata.normalize('NFKC', file_name).
        encode('ascii', errors='ignore').decode()
    )
    header = '{}; filename="{}"'.format(disposition, ascii_name)
    if ascii_name != file_name:
        quoted_name = urllib.parse.quote(file_name)
        header += '; filename*=UTF-8\'\'{}'.format(quoted_name)
    return header
