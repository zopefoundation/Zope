/*

  $Id: cStringIO.c,v 1.2 1996/07/18 13:08:34 jfulton Exp $

  A simple fast partial StringIO replacement.



     Copyright 

       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
       rights reserved.  Copyright in this software is owned by DCLC,
       unless otherwise indicated. Permission to use, copy and
       distribute this software is hereby granted, provided that the
       above copyright notice appear in all copies and that both that
       copyright notice and this permission notice appear. Note that
       any product, process or technology described in this software
       may be the subject of other Intellectual Property rights
       reserved by Digital Creations, L.C. and are not licensed
       hereunder.

     Trademarks 

       Digital Creations & DCLC, are trademarks of Digital Creations, L.C..
       All other trademarks are owned by their respective companies. 

     No Warranty 

       The software is provided "as is" without warranty of any kind,
       either express or implied, including, but not limited to, the
       implied warranties of merchantability, fitness for a particular
       purpose, or non-infringement. This software could include
       technical inaccuracies or typographical errors. Changes are
       periodically made to the software; these changes will be
       incorporated in new editions of the software. DCLC may make
       improvements and/or changes in this software at any time
       without notice.

     Limitation Of Liability 

       In no event will DCLC be liable for direct, indirect, special,
       incidental, economic, cover, or consequential damages arising
       out of the use of or inability to use this software even if
       advised of the possibility of such damages. Some states do not
       allow the exclusion or limitation of implied warranties or
       limitation of liability for incidental or consequential
       damages, so the above limitation or exclusion may not apply to
       you.

    If you have questions regarding this software,
    contact:
   
      Jim Fulton, jim@digicool.com
      Digital Creations L.C.  
   
      (540) 371-6909


  $Log: cStringIO.c,v $
  Revision 1.2  1996/07/18 13:08:34  jfulton
  *** empty log message ***

  Revision 1.1  1996/07/15 17:06:33  jfulton
  Initial version.


*/
static char cStringIO_module_documentation[] = 
"A simple fast partial StringIO replacement.\n"
"\n"
"This module provides a simple useful replacement for\n"
"the StringIO module that is written in C.  It does not provide the\n"
"full generality if StringIO, but it provides anough for most\n"
"applications and is especially useful in conjuction with the\n"
"pickle module.\n"
"\n"
"Usage:\n"
"\n"
"  from cStringIO import StringIO\n"
"\n"
"  an_output_stream=StringIO()\n"
"  an_output_stream.write(some_stuff)\n"
"  ...\n"
"  value=an_output_stream.getvalue() # str(an_output_stream) works too!\n"
"\n"
"  an_input_stream=StringIO(a_string)\n"
"  spam=an_input_stream.readline()\n"
"  spam=an_input_stream.read(5)\n"
"  an_input_stream.reset()           # OK, start over, note no seek yet\n"
"  spam=an_input_stream.read()       # and read it all\n"
"  \n"
"If someone else wants to provide a more complete implementation,\n"
"go for it. :-)  \n"
;

#include "Python.h"

static PyObject *ErrorObject;

#define ASSIGN(V,E) {PyObject *__e; __e=(E); Py_XDECREF(V); (V)=__e;}
#define UNLESS(E) if(!(E))
#define UNLESS_ASSIGN(V,E) ASSIGN(V,E) UNLESS(V)

/* ----------------------------------------------------- */

/* Declarations for objects of type StringO */

typedef struct {
  PyObject_HEAD
  char *buf;
  int pos, size;
} Oobject;

staticforward PyTypeObject Otype;

/* ---------------------------------------------------------------- */

/* Declarations for objects of type StringI */

typedef struct {
  PyObject_HEAD
  char *buf;
  int pos,size;
  PyObject *pbuf;
} Iobject;

staticforward PyTypeObject Itype;



/* ---------------------------------------------------------------- */

static char O_reset__doc__[] = 
"reset() -- Reset the file position to the beginning"
;

static PyObject *
O_reset(self, args)
	Oobject *self;
	PyObject *args;
{
  self->pos=0;
  Py_INCREF(Py_None);
  return Py_None;
}

static char O_write__doc__[] = 
"write(s) -- Write a string to the file"
"\n\nNote (hack:) writing None resets the buffer"
;

static PyObject *
O_write(self, args)
	Oobject *self;
	PyObject *args;
{
  PyObject *s;
  char *c, *b;
  int l, newl;

  UNLESS(PyArg_Parse(args, "O", &s)) return NULL;
  if(s!=Py_None)
    {
      UNLESS(-1 != (l=PyString_Size(s))) return NULL;
      UNLESS(c=PyString_AsString(s)) return NULL;
      newl=self->pos+l;
	if(newl > self->size)
	  {
	    self->size*=2;
	    if(self->size < newl) self->size=newl;
	    UNLESS(self->buf=(char*)realloc(self->buf, self->size*sizeof(char)))
	      {
		PyErr_SetString(PyExc_MemoryError,"out of memory");
		self->size=self->pos=0;
		return NULL;
	      }
	  }
      memcpy(self->buf+self->pos,c,l);
      self->pos+=l;
    }
  else
    {
      self->pos=0;
    }

  Py_INCREF(self);
  return self;
}

static PyObject *
O_repr(self)
	Oobject *self;
{
  return PyString_FromStringAndSize(self->buf,self->pos);
}

static PyObject *
O_getval(self,args)
	Oobject *self;
	PyObject *args;
{
  return PyString_FromStringAndSize(self->buf,self->pos);
}

static struct PyMethodDef O_methods[] = {
  {"write",	O_write,	0,	O_write__doc__},
  {"reset",	O_reset,	0,	O_reset__doc__},
  {"getvalue",	O_getval,	0,	"getvalue() -- Get the string value"},
  {NULL,		NULL}		/* sentinel */
};

/* ---------- */


static Oobject *
newOobject(int size)
{
  Oobject *self;
	
  self = PyObject_NEW(Oobject, &Otype);
  if (self == NULL)
    return NULL;
  self->pos=0;
  UNLESS(self->buf=malloc(size*sizeof(char)))
    {
      PyErr_SetString(PyExc_MemoryError,"out of memory");
      self->size=0;
      return NULL;
    }
  self->size=size;
  return self;
}


static void
O_dealloc(self)
	Oobject *self;
{
  free(self->buf);
  PyMem_DEL(self);
}

static PyObject *
O_getattr(self, name)
	Oobject *self;
	char *name;
{
  return Py_FindMethod(O_methods, (PyObject *)self, name);
}

static char Otype__doc__[] = 
"Simple type for output to strings."
;

static PyTypeObject Otype = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"StringO",			/*tp_name*/
	sizeof(Oobject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)O_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)O_getattr,	/*tp_getattr*/
	(setattrfunc)0,	/*tp_setattr*/
	(cmpfunc)0,		/*tp_compare*/
	(reprfunc)O_repr,		/*tp_repr*/
	0,			/*tp_as_number*/
	0,		/*tp_as_sequence*/
	0,		/*tp_as_mapping*/
	(hashfunc)0,		/*tp_hash*/
	(binaryfunc)0,		/*tp_call*/
	(reprfunc)0,		/*tp_str*/

	/* Space for future expansion */
	0L,0L,0L,0L,
	Otype__doc__ /* Documentation string */
};

/* End of code for StringO objects */
/* -------------------------------------------------------- */

static char I_read__doc__[] = 
"read([s]) -- Read s characters, or the rest of the string"
;

static PyObject *
I_read(self, args)
	Iobject *self;
	PyObject *args;
{
  int n=-1;
  PyObject *s;

  UNLESS(PyArg_ParseTuple(args, "|i", &n)) return NULL;
  if(n < 0) n=self->size-self->pos;
  s=PyString_FromStringAndSize(self->buf+self->pos, n);
  self->pos+=n;
  return s;
}


static char I_readline__doc__[] = 
"readline() -- Read one line"
;

static PyObject *
I_readline(self, args)
	Iobject *self;
	PyObject *args;
{
  PyObject *r;
  char *n, *s;
  int l;

  for(n=self->buf+self->pos, s=self->buf+self->size; n < s && *n != '\n'; n++);
  if(n < s) n++;
  r=PyString_FromStringAndSize(self->buf+self->pos, n - self->buf - self->pos);
  self->pos=n-self->buf;
  return r;
}


static struct PyMethodDef I_methods[] = {
  {"read",	I_read,	1,	I_read__doc__},
  {"readline",	I_readline,	0,	I_readline__doc__},
  {"reset",	O_reset,	0,	O_reset__doc__},  
  {NULL,		NULL}		/* sentinel */
};

/* ---------- */


static Iobject *
newIobject(PyObject *s)
{
  Iobject *self;
  char *buf;
  int size;
	
  UNLESS(buf=PyString_AsString(s)) return NULL;
  UNLESS(-1 != (size=PyString_Size(s))) return NULL;
  UNLESS(self = PyObject_NEW(Iobject, &Itype)) return NULL;
  Py_INCREF(s);
  self->buf=buf;
  self->size=size;
  self->pbuf=s;
  self->pos=0;
  
  return self;
}


static void
I_dealloc(self)
	Iobject *self;
{
  Py_DECREF(self->pbuf);
  PyMem_DEL(self);
}

static PyObject *
I_getattr(self, name)
	Iobject *self;
	char *name;
{
  return Py_FindMethod(I_methods, (PyObject *)self, name);
}

static char Itype__doc__[] = 
"Simple type for treating strings as input file streams"
;

static PyTypeObject Itype = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"StringI",			/*tp_name*/
	sizeof(Iobject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)I_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)I_getattr,	/*tp_getattr*/
	(setattrfunc)0,	/*tp_setattr*/
	(cmpfunc)0,		/*tp_compare*/
	(reprfunc)0,		/*tp_repr*/
	0,			/*tp_as_number*/
	0,		/*tp_as_sequence*/
	0,		/*tp_as_mapping*/
	(hashfunc)0,		/*tp_hash*/
	(binaryfunc)0,		/*tp_call*/
	(reprfunc)0,		/*tp_str*/

	/* Space for future expansion */
	0L,0L,0L,0L,
	Itype__doc__ /* Documentation string */
};

/* End of code for StringI objects */
/* -------------------------------------------------------- */


static char IO_StringIO__doc__[] =
"StringIO([s]) -- Return a StringIO-like stream for reading or writing"
;

static PyObject *
IO_StringIO(self, args)
	PyObject *self;	/* Not used */
	PyObject *args;
{
  PyObject *s=0;

  UNLESS(PyArg_ParseTuple(args, "|O", &s)) return NULL;
  if(s) return newIobject(s);
  return newOobject(128);
}

/* List of methods defined in the module */

static struct PyMethodDef IO_methods[] = {
	{"StringIO",	IO_StringIO,	1,	IO_StringIO__doc__},
	{NULL,		NULL}		/* sentinel */
};


/* Initialization function for the module (*must* be called initcStringIO) */

void
initcStringIO()
{
	PyObject *m, *d;

	/* Create the module and add the functions */
	m = Py_InitModule4("cStringIO", IO_methods,
		cStringIO_module_documentation,
		(PyObject*)NULL,PYTHON_API_VERSION);

	/* Add some symbolic constants to the module */
	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("cStringIO.error");
	PyDict_SetItemString(d, "error", ErrorObject);
							     
	/* XXXX Add constants here */
	
	/* Check for errors */
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module cStringIO");
}

