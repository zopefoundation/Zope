#
# XML-RPC CLIENT LIBRARY
# $Id: xmlrpclib.py,v 1.1.1.1 1999/06/11 15:04:49 emk Exp $
#
# an XML-RPC client interface for Python
#
# the marshalling and response parser code can also be used to
# implement XML-RPC servers
#
# History:
# 1999-01-14 fl  Created
# 1999-01-15 fl  Changed dateTime to use localtime
# 1999-01-16 fl  Added Binary/base64 element, default to RPC2 service
# 1999-01-19 fl  Fixed array data element (from Skip Montanaro)
# 1999-01-21 fl  Fixed dateTime constructor, etc.
# 1999-02-02 fl  Added fault handling, handle empty sequences, etc.
#
# written by Fredrik Lundh, January 1999.
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
# Permission to use, copy, modify, and distribute this software and its
# associated documentation for any purpose and without fee is hereby
# granted, provided that the above copyright notice appears in all
# copies, and that both that copyright notice and this permission notice
# appear in supporting documentation, and that the name of Secret Labs
# AB or the author not be used in advertising or publicity pertaining to
# distribution of the software without specific, written prior
# permission.
# 
# SECRET LABS AB AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO
# THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS.  IN NO EVENT SHALL SECRET LABS AB OR THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
# OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
# --------------------------------------------------------------------

import operator, string, time
import httplib, urllib
import xmllib
from types import *
from cgi import escape

__version__ = "0.9.5"

USER_AGENT = "xmlrpclib.py/%s (by www.pythonware.com)" % __version__


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
    # indicates a broken response chunk
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
# (wrap your iso8601 string or localtime tuple or time value in this
# class to generate a "dateTime.iso8601" XML-RPC value)

class DateTime:

    def __init__(self, value):
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
# XML-RPC response parser

class ResponseParser(xmllib.XMLParser):
    """Parse an XML-RPC response into a Python data structure"""

    # USAGE: create a parser instance, and call "feed" to add data to
    # it (in chunks or as a single string).  call "close" to flush the
    # internal buffers and return the resulting data structure.

    # note that this reader is fairly tolerant, and gladly accepts
    # bogus XML-RPC data without complaining (but not bogus XML).

    # this could of course be simplified by using an XML tree builder
    # (DOM, coreXML, or whatever), but this version works with any
    # standard installation of 1.5 or later (except 1.5.2b1, but
    # we're working on that)

    # by the way, if you don't understand what's going on in here,
    # that's perfectly ok.

    def __init__(self):
	self.__type = None
	self.__stack = []
        self.__marks = []
	self.__data = []
	self.__methodname = None
	xmllib.XMLParser.__init__(self)

    def close(self):
	xmllib.XMLParser.close(self)
	# return response code and the actual response
	if self.__type is None or self.__marks:
	    raise ResponseError()
	if self.__type == "fault":
	    raise apply(Fault, (), self.__stack[0])
	return tuple(self.__stack)

    def getmethodname(self):
	return self.__methodname

    #
    # container types (containers can be nested, so we use a separate
    # mark stack to keep track of the beginning of each container).

    def start_array(self, attrs):
	self.__marks.append(len(self.__stack))

    start_struct = start_array

    def unknown_starttag(self, tag, attrs):
	self.__data = []
	self.__value = (tag == "value")

    def handle_data(self, text):
	self.__data.append(text)

    def unknown_endtag(self, tag, join=string.join):
	# the standard dispatcher cannot handle tags with uncommon
	# characters in them, so we have to do this ourselves.
	if tag == "dateTime.iso8601":
	    value = DateTime()
	    value.decode(join(self.__data, ""))
	    self.__stack.append(value)

    #
    # add values to the stack on end tags

    def end_boolean(self, join=string.join):
	value = join(self.__data, "")
	if value == "0":
	    self.__stack.append(False)
	elif value == "1":
	    self.__stack.append(True)
	else:
	    raise TypeError, "bad boolean value"

    def end_int(self, join=string.join):
	self.__stack.append(int(join(self.__data, "")))

    def end_double(self, join=string.join):
	self.__stack.append(float(join(self.__data, "")))

    def end_string(self, join=string.join):
	self.__stack.append(join(self.__data, ""))

    # aliases
    end_i4 = end_int
    end_name = end_string # struct keys are always strings

    def end_array(self):
        mark = self.__marks[-1]
	del self.__marks[-1]
	# map arrays to Python lists
        self.__stack[mark:] = [self.__stack[mark:]]

    def end_struct(self):
        mark = self.__marks[-1]
	del self.__marks[-1]
	# map structs to Python dictionaries
        dict = {}
        items = self.__stack[mark:]
        for i in range(0, len(items), 2):
            dict[items[i]] = items[i+1]
        self.__stack[mark:] = [dict]

    def end_base64(self, join=string.join):
	value = Binary()
	value.decode(join(self.__data, ""))
	self.__stack.append(value)

    def end_value(self):
	# if we stumble upon an value element with no
	# no internal elements, treat it as a string
	# element
	if self.__value:
	    self.end_string()

    def end_params(self):
	self.__type = "params"

    def end_fault(self):
	self.__type = "fault"

    def end_methodName(self, join=string.join):
	self.__methodname = join(self.__data, "")


# --------------------------------------------------------------------
# XML-RPC marshaller

class Marshaller:
    """Generate an XML-RPC params chunk from a Python data structure"""

    # USAGE: create a marshaller instance for each set of parameters,
    # and use "dumps" to convert your data (represented as a tuple) to
    # a XML-RPC params chunk.  to write a fault response, pass a Fault
    # instance instead.

    # again, this could of course be simplified by using an XML writer
    # (coreXML or whatever), but this version works with any standard
    # installation of 1.5 or later (except 1.5.2b1, but we're working
    # on that)

    # and again, if you don't understand what's going on in here,
    # that's perfectly ok.

    def __init__(self):
	self.memo = {}
	self.data = None

    dispatch = {}

    def dumps(self, values):
	if isinstance(values, Fault):
	    # fault instance
	    self.__out = ["<fault>\n"]
	    self.__dump(vars(values))
	    self.write("</fault>\n")
	else:
	    # parameter block
	    self.__out = ["<params>\n"]
	    for v in values:
		self.write("<param>\n")
		self.__dump(v)
		self.write("</param>\n")
	    self.write("</params>\n")
	return string.join(self.__out, "")

    def write(self, string):
	self.__out.append(string)

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
	self.write("<value><array><data>\n")
	for v in value:
	    self.__dump(v)
	self.write("</data></array></value>\n")
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
	write = self.write
	if value.__class__ in WRAPPERS:
	    value.encode(self)
	else:
	    # store instance attributes as a struct (?)
	    self.dump_struct(value.__dict__)
    dispatch[InstanceType] = dump_instance


# --------------------------------------------------------------------
# convenience functions

def dumps(params, methodname=None, methodresponse=None):

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
    # returns data plus methodname (None if not present)
    p = ResponseParser()
    p.feed(data)
    return p.close(), p.getmethodname()

# --------------------------------------------------------------------
# request dispatcher

class Method:
    # some magic to bind an XML-RPC method to an RPC server.
    # supports "nested" methods (e.g. examples.getStateName)
    def __init__(self, send, name):
	self.__send = send
	self.__name = name
    def __getattr__(self, name):
	return Method(self.__send, self.__name + "." + name)
    def __call__(self, *args):
	return self.__send(self.__name, args)


class Server:
    """Represents a connection XML-RPC server"""

    def __init__(self, uri):
	# establish a "logical" server connection

	type, uri = urllib.splittype(uri)
	if type != "http":
	    raise IOError, "unsupported XML-RPC protocol"
	self.__host, self.__handler = urllib.splithost(uri)
	if not self.__handler:
	    self.__handler = "/RPC2"

    def __request(self, methodname, params):
	# call a method on the remote server

	request = dumps(params, methodname)

	# send the request
	h = httplib.HTTP(self.__host)
	h.putrequest("POST", self.__handler)
	h.putheader("User-Agent", USER_AGENT)
	h.putheader("Host", self.__host)
	h.putheader("Content-Type", "text/xml")
	h.putheader("Content-Length", str(len(request)))
	h.endheaders()

	if request:
	    h.send(request)

	errcode, errmsg, headers = h.getreply()

	if errcode != 200:
	    raise ProtocolError(
		self.__host + self.__handler,
		errcode, errmsg,
		headers
		)

	# parse the response
	fp = h.getfile()

	p = ResponseParser()

	while 1:
	    response = fp.read(1024)
	    if not response:
		break
	    p.feed(response)

	response = p.close()

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
	# method dispatcher
	return Method(self.__request, name)


if __name__ == "__main__":

    # simple test program (from the specification)
    # server = Server("http://localhost:8000") # local server

    server = Server("http://nirvana.userland.com")

    print server

    try:
	print server.examples.getStateName(41)
    except Error, v:
	print "ERROR", v
