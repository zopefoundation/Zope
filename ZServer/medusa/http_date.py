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
#
#	Author: Sam Rushing <rushing@nightmare.com>
#

import regex
import string
import time

def concat (*args):
	return string.joinfields (args, '')

def join (seq, field=' '):
	return string.joinfields (seq, field)

def group (s):
	return '\\(' + s + '\\)'

short_days = ['sun','mon','tue','wed','thu','fri','sat']
long_days = ['sunday','monday','tuesday','wednesday','thursday','friday','saturday']

short_day_reg = group (join (short_days, '\\|'))
long_day_reg = group (join (long_days, '\\|'))

daymap = {}
for i in range(7):
	daymap[short_days[i]] = i
	daymap[long_days[i]] = i

hms_reg = join (3 * [group('[0-9][0-9]')], ':')

months = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']

monmap = {}
for i in range(12):
	monmap[months[i]] = i+1

months_reg = group (join (months, '\\|'))

# From draft-ietf-http-v11-spec-07.txt/3.3.1
#       Sun, 06 Nov 1994 08:49:37 GMT  ; RFC 822, updated by RFC 1123
#       Sunday, 06-Nov-94 08:49:37 GMT ; RFC 850, obsoleted by RFC 1036
#       Sun Nov  6 08:49:37 1994       ; ANSI C's asctime() format

# rfc822 format
rfc822_date = join (
	[concat (short_day_reg,','),	# day
	 group('[0-9][0-9]?'),			# date
	 months_reg,					# month
	 group('[0-9]+'),				# year
	 hms_reg,						# hour minute second
	 'gmt'
	 ],
	' '
	)

rfc822_reg = regex.compile (rfc822_date)

def unpack_rfc822 ():
	g = rfc822_reg.group
	a = string.atoi
	return (
		a(g(4)),	   	# year
		monmap[g(3)],	# month
		a(g(2)),		# day
		a(g(5)),		# hour
		a(g(6)),		# minute
		a(g(7)),		# second
		0,
		0,
		0
		)

# rfc850 format
rfc850_date = join (
	[concat (long_day_reg,','),
	 join (
		 [group ('[0-9][0-9]?'),
		  months_reg,
		  group ('[0-9]+')
		  ],
		 '-'
		 ),
	 hms_reg,
	 'gmt'
	 ],
	' '
	)

rfc850_reg = regex.compile (rfc850_date)
# they actually unpack the same way
def unpack_rfc850 ():
	g = rfc850_reg.group
	a = string.atoi
	return (
		a(g(4)),	   	# year
		monmap[g(3)],	# month
		a(g(2)),		# day
		a(g(5)),		# hour
		a(g(6)),		# minute
		a(g(7)),		# second
		0,
		0,
		0
		)

# parsdate.parsedate	- ~700/sec.
# parse_http_date    	- ~1333/sec.

def build_http_date (when):
	return time.strftime ('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(when))

def parse_http_date (d):
	d = string.lower (d)
	tz = time.timezone
	if rfc850_reg.match (d) == len(d):
		retval = int (time.mktime (unpack_rfc850()) - tz)
	elif rfc822_reg.match (d) == len(d):
		retval = int (time.mktime (unpack_rfc822()) - tz)
	else:
		return 0
	# Thanks to Craig Silverstein <csilvers@google.com> for pointing
	# out the DST discrepancy
	if time.daylight and time.localtime(retval)[-1] == 1: # DST correction
		retval = retval + (tz - time.altzone)
	return retval
