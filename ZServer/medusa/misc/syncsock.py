# -*- Mode: Python; tab-width: 4 -*-

# set the global SO_OPENTYPE parameter

import struct
import windll
import winerror

wsock32 = windll.module ('wsock32')

option = windll.membuf (4)
option_len = windll.membuf (4)

option_len.write (struct.pack ('l', 4))

INVALID_SOCKET		= -1
SOCKET_SOL			= 0xffff

#
# Option for opening sockets for synchronous access.
#

SO_OPENTYPE     		= 0x7008

SO_SYNCHRONOUS_ALERT   	= 0x10
SO_SYNCHRONOUS_NONALERT	= 0x20

def set_sync_option (on=1):
	result = wsock32.getsockopt (
		INVALID_SOCKET,
		SOCKET_SOL,
		SO_OPENTYPE,
		option,
		option_len
		)
	if result:
		raise SystemError, "getsockopt: (%d)" % (
			wsock32.WSAGetLastError()
			)
	else:
		old = struct.unpack ('l', option.read())[0]
	if on:
		new = old | SO_SYNCHRONOUS_ALERT
	else:
		new = old & (~SO_SYNCHRONOUS_ALERT)
	option.write (struct.pack ('l', new))
	result = wsock32.setsockopt (
		INVALID_SOCKET,
		SOCKET_SOL,
		SO_OPENTYPE,
		option,
		option_len
		)
	if result:
		raise SystemError, "getsockopt: (%d)" % (
			wsock32.WSAGetLastError()
			)
	return old

def sync_on():
	return set_sync_option (1)

def sync_off():
	return set_sync_option (0)
