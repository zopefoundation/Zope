/***********************************************************
Copyright 1991-1995 by Stichting Mathematisch Centrum, Amsterdam,
The Netherlands.

                        All Rights Reserved

Permission to use, copy, modify, and distribute this software and its
documentation for any purpose and without fee is hereby granted,
provided that the above copyright notice appear in all copies and that
both that copyright notice and this permission notice appear in
supporting documentation, and that the names of Stichting Mathematisch
Centrum or CWI or Corporation for National Research Initiatives or
CNRI not be used in advertising or publicity pertaining to
distribution of the software without specific, written prior
permission.

While CWI is the initial source for this software, a modified version
is made available by the Corporation for National Research Initiatives
(CNRI) at the Internet address ftp://ftp.python.org.

STICHTING MATHEMATISCH CENTRUM AND CNRI DISCLAIM ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS, IN NO EVENT SHALL STICHTING MATHEMATISCH
CENTRUM OR CNRI BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL
DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR
PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.

******************************************************************/

#include "Python.h"

PyObject *
#ifdef HAVE_STDARG_PROTOTYPES
/* VARARGS 2 */
PyErr_Format(PyObject *ErrType, char *stringformat, char *format, ...)
#else
/* VARARGS */
PyErr_Format(va_alist) va_dcl
#endif
{
  va_list va;
  PyObject *args=0, *retval=0;
#ifdef HAVE_STDARG_PROTOTYPES
  va_start(va, format);
#else
  PyObject *ErrType;
  char *stringformat, *format;
  va_start(va);
  ErrType = va_arg(va, PyObject *);
  stringformat   = va_arg(va, char *);
  format   = va_arg(va, char *);
#endif
  
  if(format) args = Py_VaBuildValue(format, va);
  va_end(va);
  if(format && ! args) return NULL;
  if(stringformat && !(retval=PyString_FromString(stringformat))) return NULL;

  if(retval)
    {
      if(args)
	{
	  PyObject *v;
	  v=PyString_Format(retval, args);
	  Py_DECREF(retval);
	  Py_DECREF(args);
	  if(! v) return NULL;
	  retval=v;
	}
    }
  else
    if(args) retval=args;
    else
      {
	PyErr_SetObject(ErrType,Py_None);
	return NULL;
      }
  PyErr_SetObject(ErrType,retval);
  Py_DECREF(retval);
  return NULL;
}
