// -*- Mode: C; tab-width: 8 -*-

#include "Python.h"
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/uio.h>

//
// sendfile(), meant for use with a non-blocking socket
//

#if defined (__linux__)

// these are taken from linux/socket.h, for some reason including that file doesn't work here.
#define SOL_TCP 6
#define TCP_CORK 3

// non-blocking TCP_CORK sucks mugwump jism.

static PyObject *
py_sendfile (PyObject * self, PyObject * args)
{
  int fd;
  int sock;
  long o,n;
  char * head = NULL;
  size_t head_len = 0;
  char * tail = NULL;
  size_t tail_len = 0;
  
  if (!PyArg_ParseTuple (
          args, "iill|s#s#",
	  &fd, &sock, &o, &n,
	  &head, &head_len,
	  &tail, &tail_len
	  )) {
    return NULL;
  } else {
    off_t offset = o;
    size_t nbytes = n;
    int orig_cork = 1;
    int orig_cork_len = sizeof(int);
    PyObject * py_result = NULL;
    ssize_t sent_h = 0;
    ssize_t sent_f = 0;
    ssize_t sent_t = 0;

    if (head || tail) {
      int cork = 1;
      // first, fetch the original setting
      getsockopt (sock, SOL_TCP, TCP_CORK, (void*)&orig_cork, &orig_cork_len);
      setsockopt (sock, SOL_TCP, TCP_CORK, (void*)&cork, sizeof(cork));
    }											

    // send header
    if (head) {
      sent_h = send (sock, head, head_len, 0);
      if (sent_h < 0) {
	PyErr_SetFromErrno (PyExc_OSError);
	py_result = NULL;
	goto done;
      } else if (sent_h < head_len) {
	py_result = PyInt_FromLong (sent_h);
	goto done;
      }
    }
	
    // send file
    sent_f = sendfile (sock, fd, &offset, nbytes);
    if (sent_f < 0) {
      PyErr_SetFromErrno (PyExc_OSError);
      py_result = NULL;
      goto done;
    } else if (sent_f < nbytes) {
      py_result = PyInt_FromLong (sent_h + sent_f);
      goto done;
    }

    // send trailer
    if (tail) {
      sent_t = send (sock, tail, tail_len, 0);
      if (sent_t < 0) {
	PyErr_SetFromErrno (PyExc_OSError);
	py_result = NULL;
	goto done;
      }
    }
      
    py_result = PyInt_FromLong (sent_h + sent_f + sent_t);
    
  done:
    if (head || tail) {
      setsockopt (sock, SOL_TCP, TCP_CORK, (void*)&orig_cork, sizeof(orig_cork));
    }											
    return py_result;
  }
}

#elif defined (__FreeBSD__)
// XXX support the header/trailer stuff.
static PyObject *
py_sendfile (PyObject * self, PyObject * args)
{
  int fd;
  int sock;
  long o,n;
  char * head = NULL;
  size_t head_len = 0;
  char * tail = NULL;
  size_t tail_len = 0;
  
  if (!PyArg_ParseTuple (
          args, "iill|s#s#",
	  &fd, &sock, &o, &n,
	  &head, &head_len,
	  &tail, &tail_len
	  )
      ) {
    return NULL;
  } else {
    off_t offset = o;
    size_t nbytes = n;
    off_t sbytes;
    int result;

    if (head || tail) {
      struct iovec ivh = {head, head_len};
      struct iovec ivt = {tail, tail_len};
      struct sf_hdtr hdtr = {&ivh, 1, &ivt, 1};
      result = sendfile (fd, sock, offset, nbytes, &hdtr, &sbytes, 0);
    } else {
      result = sendfile (fd, sock, offset, nbytes, NULL, &sbytes, 0);
    }
    if (result == -1) {
      if (errno == EAGAIN) {
	return PyInt_FromLong (sbytes);
      } else {
	PyErr_SetFromErrno (PyExc_OSError);
      }
    } else {
      return PyInt_FromLong (sbytes);
    }
  }
}

#else
#error ("unknown platform")
#endif


// <off_t> and <size_t> are 64 bits on FreeBSD.
// If you need this feature, then look at PyLong_FromUnsignedLongLong.
// You'll have to specifically check for the PyLong type, etc...
// Also, LONG_LONG is a configure variable (i.e., the conversion function
// might not be available).

static PyMethodDef sendfile_methods[] = {
  {"sendfile",		py_sendfile,		1},
  {NULL,		NULL}		/* sentinel */
};

DL_EXPORT(void)
initsendfile()
{
  PyObject *m, *d;
  m = Py_InitModule("sendfile", sendfile_methods);
}
