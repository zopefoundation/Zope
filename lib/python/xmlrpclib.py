#
# XML-RPC CLIENT LIBRARY
# $Id$
#
# an XML-RPC client interface for Python.
#
# the marshalling and response parser code can also be used to
# implement XML-RPC servers.
#
# Notes:
# this version uses the sgmlop XML parser, if installed.  this is
# typically 10-15x faster than using Python's standard XML parser.
#
# you can get the sgmlop distribution from:
#
#    http://www.pythonware.com/madscientist
#
# also note that this version is designed to work with Python 1.5.1
# or newer.  it doesn't use any 1.5.2-specific features.
#
# History:
# 1999-01-14 fl  Created
# 1999-01-15 fl  Changed dateTime to use localtime
# 1999-01-16 fl  Added Binary/base64 element, default to RPC2 service
# 1999-01-19 fl  Fixed array data element (from Skip Montanaro)
# 1999-01-21 fl  Fixed dateTime constructor, etc.
# 1999-02-02 fl  Added fault handling, handle empty sequences, etc.
# 1999-02-10 fl  Fixed problem with empty responses (from Skip Montanaro)
# 1999-06-20 fl  Speed improvements, pluggable XML parsers and HTTP transports
#
# Copyright (c) 1999 by Secret Labs AB.
# Copyright (c) 1999 by Fredrik Lundh.
#
# fredrik@pythonware.com
# http://www.pythonware.com
#
# --------------------------------------------------------------------
# The XML-RPC client interface is
# 
# Copyright (c) 1999 by Secret Labs AB
# Copyright (c) 1999 by Fredrik Lundh
# 
# By obtaining, using, and/or copying this software and/or its
# associated documentation, you agree that you have read, understood,
# and will comply with the following terms and conditions:
#
# Permission to use, copy, modify, and distribute this software and
# its associated documentation for any purpose and without fee is
# hereby granted, provided that the above copyright notice appears in
# all copies, and that both that copyright notice and this permission
# notice appear in supporting documentation, and that the name of
# Secret Labs AB or the author not be used in advertising or publicity
# pertaining to distribution of the software without specific, written
# prior permission.
#
# SECRET LABS AB AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD
# TO THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANT-
# ABILITY AND FITNESS.  IN NO EVENT SHALL SECRET LABS AB OR THE AUTHOR
# BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY
# DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
# WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE
# OF THIS SOFTWARE.
# --------------------------------------------------------------------

import string, time
import urllib, xmllib
from types import *
from cgi import escape

try:
    import sgmlop
except ImportError:
    sgmlop = None # accelerator not available

__version__ = "0.9.8"


# --------------------------------------------------------------------
# Exceptions

class Error:
    # base class for client errors
    pass

class ProtocolError(Error):
    # indicates an HTTP protocol error
    def __init__(self, url, errcode, errmsg, headers):
	self.url = url
	self.errcode = errcode
	self.errmsg = errmsg
	self.headers = headers
    def __repr__(self):
	return (
	    "<ProtocolError for %s: %s %s>" %
	    (self.url, self.errcode, self.errmsg)
	    )

class ResponseError(Error):
    # indicates a broken response package
    pass

class Fault(Error):
    # indicates a XML-RPC fault package
    def __init__(self, faultCode, faultString, **extra):
	self.faultCode = faultCode
	self.faultString = faultString
    def __repr__(self):
	return (
	    "<Fault %s: %s>" %
	    (self.faultCode, repr(self.faultString))
	    )


# --------------------------------------------------------------------
# Special values

# boolean wrapper
# (you must use True or False to generate a "boolean" XML-RPC value)

class Boolean:

    def __init__(self, value = 0):
	self.value = (value != 0)

    def encode(self, out):
	out.write("<value><boolean>%d</boolean></value>\n" % self.value)

    def __repr__(self):
	if self.value:
	    return "<Boolean True at %x>" % id(self)
	else:
	    return "<Boolean False at %x>" % id(self)

    def __int__(self):
	return self.value

    def __nonzero__(self):
	return self.value

True, False = Boolean(1), Boolean(0)

#
# dateTime wrapper
# (wrap your iso8601 string or time tuple or localtime time value in
# this class to generate a "dateTime.iso8601" XML-RPC value)

class DateTime:

    def __init__(self, value = 0):
	t = type(value)
	if t is not StringType:
	    if t is not TupleType:
		value = time.localtime(value)
	    value = time.strftime("%Y%m%dT%H:%M:%S", value)
	self.value = value

    def __repr__(self):
	return "<DateTime %s at %x>" % (self.value, id(self))

    def decode(self, data):
	self.value = string.strip(data)

    def encode(self, out):
	out.write("<value><dateTime.iso8601>")
	out.write(self.value)
	out.write("</dateTime.iso8601></value>\n")

#
# binary data wrapper (NOTE: this is an extension to Userland's
# XML-RPC protocol! only for use with compatible servers!)

class Binary:

    def __init__(self, data=None):
	self.data = data

    def decode(self, data):
	import base64
	self.data = base64.decodestring(data)

    def encode(self, out):
	import base64, StringIO
	out.write("<value><base64>\n")
	base64.encode(StringIO.StringIO(self.data), out)
	out.write("</base64></value>\n")

WRAPPERS = DateTime, Binary, Boolean


# --------------------------------------------------------------------
# XML parsers

if sgmlop:

    class FastParser:
	# sgmlop based XML parser.  this is typically 15x faster
	# than SlowParser...

	def __init__(self, target):

	    # setup callbacks
	    self.finish_starttag = target.start
	    self.finish_endtag = target.end
	    self.handle_data = target.data

	    # activate parser
	    self.parser = sgmlop.XMLParser()
	    self.parser.register(self)
	    self.feed = self.parser.feed
	    self.entity = {
		"amp": "&", "gt": ">", "lt": "<",
		"apos": "'", "quot": '"'
		}

	def close(self):
	    try:
		self.parser.close()
	    finally:
		self.parser = None # nuke circular reference

	def handle_entityref(self, entity):
	    # <string> entity
	    try:
		self.handle_data(self.entity[entity])
	    except KeyError:
		self.handle_data("&%s;" % entity)

else:

    FastParser = None

class SlowParser(xmllib.XMLParser):
    # slow but safe standard parser, based on the XML parser in
    # Python's standard library

    def __init__(self, target):
	self.unknown_starttag = target.start
	self.handle_data = target.data
	self.unknown_endtag = target.end
	xmllib.XMLParser.__init__(self)


# --------------------------------------------------------------------
# XML-RPC marshalling and unmarshalling code

class Marshaller:
    """Generate an XML-RPC params chunk from a Python data structure"""

    # USAGE: create a marshaller instance for each set of parameters,
    # and use "dumps" to convert your data (represented as a tuple) to
    # a XML-RPC params chunk.  to write a fault response, pass a Fault
    # instance instead.  you may prefer to use the "dumps" convenience
    # function for this purpose (see below).

    # by the way, if you don't understand what's going on in here,
    # that's perfectly ok.

    def __init__(self):
	self.memo = {}
	self.data = None

    dispatch = {}

    def dumps(self, values):
	self.__out = []
	self.write = write = self.__out.append
	if isinstance(values, Fault):
	    # fault instance
	    write("<fault>\n")
	    self.__dump(vars(values))
	    write("</fault>\n")
	else:
	    # parameter block
	    write("<params>\n")
	    for v in values:
		write("<param>\n")
		self.__dump(v)
		write("</param>\n")
	    write("</params>\n")
	result = string.join(self.__out, "")
	del self.__out, self.write # don't need this any more
	return result

    def __dump(self, value):
	try:
	    f = self.dispatch[type(value)]
	except KeyError:
	    raise TypeError, "cannot marshal %s objects" % type(value)
	else:
	    f(self, value)

    def dump_int(self, value):
	self.write("<value><int>%s</int></value>\n" % value)
    dispatch[IntType] = dump_int

    def dump_double(self, value):
	self.write("<value><double>%s</double></value>\n" % value)
    dispatch[FloatType] = dump_double

    def dump_string(self, value):
	self.write("<value><string>%s</string></value>\n" % escape(value))
    dispatch[StringType] = dump_string

    def container(self, value):
	if value:
	    i = id(value)
	    if self.memo.has_key(i):
		raise TypeError, "cannot marshal recursive data structures"
	    self.memo[i] = None

    def dump_array(self, value):
	self.container(value)
	write = self.write
	write("<value><array><data>\n")
	for v in value:
	    self.__dump(v)
	write("</data></array></value>\n")
    dispatch[TupleType] = dump_array
    dispatch[ListType] = dump_array

    def dump_struct(self, value):
	self.container(value)
	write = self.write
	write("<value><struct>\n")
	for k, v in value.items():
	    write("<member>\n")
	    if type(k) is not StringType:
		raise TypeError, "dictionary key must be string"
	    write("<name>%s</name>\n" % escape(k))
	    self.__dump(v)
	    write("</member>\n")
	write("</struct></value>\n")
    dispatch[DictType] = dump_struct

    def dump_instance(self, value):
	# check for special wrappers
	if value.__class__ in WRAPPERS:
	    value.encode(self)
	else:
	    # store instance attributes as a struct (really?)
	    self.dump_struct(value.__dict__)
    dispatch[InstanceType] = dump_instance


class Unmarshaller:

    # unmarshal an XML-RPC response, based on incoming XML event
    # messages (start, data, end).  call close to get the resulting
    # data structure

    # note that this reader is fairly tolerant, and gladly accepts
    # bogus XML-RPC data without complaining (but not bogus XML).

    # and again, if you don't understand what's going on in here,
    # that's perfectly ok.

    def __init__(self):
	self._type = None
	self._stack = []
        self._marks = []
	self._data = []
	self._methodname = None
	self.append = self._stack.append

    def close(self):
	# return response code and the actual response
	if self._type is None or self._marks:
	    raise ResponseError()
	if self._type == "fault":
	    raise apply(Fault, (), self._stack[0])
	return tuple(self._stack)

    def getmethodname(self):
	return self._methodname

    #
    # event handlers

    def start(self, tag, attrs):
	# prepare to handle this element
	if tag in ("array", "struct"):
	    self._marks.append(len(self._stack))
	self._data = []
	self._value = (tag == "value")

    def data(self, text):
	self._data.append(text)

    dispatch = {}

    def end(self, tag):
	# call the appropriate end tag handler
	try:
	    f = self.dispatch[tag]
	except KeyError:
	    pass # unknown tag ?
	else:
	    return f(self)

    #
    # element decoders

    def end_boolean(self, join=string.join):
	value = join(self._data, "")
	if value == "0":
	    self.append(False)
	elif value == "1":
	    self.append(True)
	else:
	    raise TypeError, "bad boolean value"
	self._value = 0
    dispatch["boolean"] = end_boolean

    def end_int(self, join=string.join):
	self.append(int(join(self._data, "")))
	self._value = 0
    dispatch["i4"] = end_int
    dispatch["int"] = end_int

    def end_double(self, join=string.join):
	self.append(float(join(self._data, "")))
	self._value = 0
    dispatch["double"] = end_double

    def end_string(self, join=string.join):
	self.append(join(self._data, ""))
	self._value = 0
    dispatch["string"] = end_string
    dispatch["name"] = end_string # struct keys are always strings

    def end_array(self):
        mark = self._marks[-1]
	del self._marks[-1]
	# map arrays to Python lists
        self._stack[mark:] = [self._stack[mark:]]
	self._value = 0
    dispatch["array"] = end_array

    def end_struct(self):
        mark = self._marks[-1]
	del self._marks[-1]
	# map structs to Python dictionaries
        dict = {}
        items = self._stack[mark:]
        for i in range(0, len(items), 2):
            dict[items[i]] = items[i+1]
        self._stack[mark:] = [dict]
	self._value = 0
    dispatch["struct"] = end_struct

    def end_base64(self, join=string.join):
	value = Binary()
	value.decode(join(self._data, ""))
	self.append(value)
	self._value = 0
    dispatch["base64"] = end_base64

    def end_dateTime(self, join=string.join):
	value = DateTime()
	value.decode(join(self._data, ""))
	self.append(value)
    dispatch["dateTime.iso8601"] = end_dateTime

    def end_value(self):
	# if we stumble upon an value element with no internal
	# elements, treat it as a string element
	if self._value:
	    self.end_string()
    dispatch["value"] = end_value

    def end_params(self):
	self._type = "params"
    dispatch["params"] = end_params

    def end_fault(self):
	self._type = "fault"
    dispatch["fault"] = end_fault

    def end_methodName(self, join=string.join):
	self._methodname = join(self._data, "")
    dispatch["methodName"] = end_methodName


# --------------------------------------------------------------------
# convenience functions

def getparser():
    # get the fastest available parser, and attach it to an
    # unmarshalling object.  return both objects.
    target = Unmarshaller()
    if FastParser:
	return FastParser(target), target
    return SlowParser(target), target

def dumps(params, methodname=None, methodresponse=None):
    # convert a tuple or a fault object to an XML-RPC packet

    assert type(params) == TupleType or isinstance(params, Fault),\
	   "argument must be tuple or Fault instance"

    m = Marshaller()
    data = m.dumps(params)

    # standard XML-RPC wrappings
    if methodname:
	# a method call
	data = (
	    "<?xml version='1.0'?>\n"
	    "<methodCall>\n"
	    "<methodName>%s</methodName>\n"
	    "%s\n"
	    "</methodCall>\n" % (methodname, data)
	    )
    elif methodresponse or isinstance(params, Fault):
	# a method response
	data = (
	    "<?xml version='1.0'?>\n"
	    "<methodResponse>\n"
	    "%s\n"
	    "</methodResponse>\n" % data
	    )
    return data

def loads(data):
    # convert an XML-RPC packet to data plus a method name (None
    # if not present).  if the XML-RPC packet represents a fault
    # condition, this function raises a Fault exception.
    p, u = getparser()
    p.feed(data)
    p.close()
    return u.close(), u.getmethodname()


# --------------------------------------------------------------------
# request dispatcher

class _Method:
    # some magic to bind an XML-RPC method to an RPC server.
    # supports "nested" methods (e.g. examples.getStateName)
    def __init__(self, send, name):
	self.__send = send
	self.__name = name
    def __getattr__(self, name):
	return _Method(self.__send, "%s.%s" % (self.__name, name))
    def __call__(self, *args):
	return self.__send(self.__name, args)


class Transport:
    """Handles an HTTP transaction to an XML-RPC server"""

    # client identifier (may be overridden)
    user_agent = "xmlrpclib.py/%s (by www.pythonware.com)" % __version__

    def request(self, host, handler, request_body):
	# issue XML-RPC request

	import httplib
	h = httplib.HTTP(host)
	h.putrequest("POST", handler)

	# required by HTTP/1.1
	h.putheader("Host", host)

	# required by XML-RPC
	h.putheader("User-Agent", self.user_agent)
	h.putheader("Content-Type", "text/xml")
	h.putheader("Content-Length", str(len(request_body)))

	h.endheaders()

	if request_body:
	    h.send(request_body)

	errcode, errmsg, headers = h.getreply()

	if errcode != 200:
	    raise ProtocolError(
		host + handler,
		errcode, errmsg,
		headers
		)

	return self.parse_response(h.getfile())

    def parse_response(self, f):
	# read response from input file, and parse it

	p, u = getparser()

	while 1:
	    response = f.read(1024)
	    if not response:
		break
	    p.feed(response)

	f.close()
	p.close()

	return u.close()


class Server:
    """Represents a connection to an XML-RPC server"""

    def __init__(self, uri, transport=None):
	# establish a "logical" server connection

	# get the url
	type, uri = urllib.splittype(uri)
	if type != "http":
	    raise IOError, "unsupported XML-RPC protocol"
	self.__host, self.__handler = urllib.splithost(uri)
	if not self.__handler:
	    self.__handler = "/RPC2"

	if transport is None:
	    transport = Transport()
	self.__transport = transport

    def __request(self, methodname, params):
	# call a method on the remote server

	request = dumps(params, methodname)

	response = self.__transport.request(
	    self.__host,
	    self.__handler,
	    request
	    )

	if len(response) == 1:
	    return response[0]

	return response

    def __repr__(self):
	return (
	    "<Server proxy for %s%s>" %
	    (self.__host, self.__handler)
	    )

    __str__ = __repr__

    def __getattr__(self, name):
	# magic method dispatcher
	return _Method(self.__request, name)


if __name__ == "__main__":

    # simple test program (from the XML-RPC specification)
    # server = Server("http://localhost:8000") # local server

    server = Server("http://betty.userland.com")

    print server

    try:
	print server.examples.getStateName(41)
    except Error, v:
	print "ERROR", v
