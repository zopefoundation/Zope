/***********************************************************
     Copyright 

       Copyright 1997 Digital Creations, L.L.C., 910 Princess Anne
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
   
      Digital Creations L.L.C.  
      info@digicool.com
      (540) 371-6909

******************************************************************/


static char Missing_module_documentation[] = 
""
"\n$Id: Missing.c,v 1.1 1997/07/01 21:36:34 jim Exp $"
;

#include "ExtensionClass.h"

static PyObject *ErrorObject;

/* ----------------------------------------------------- */

static void PyVar_Assign(PyObject **v, PyObject *e) { Py_XDECREF(*v); *v=e;}
#define ASSIGN(V,E) PyVar_Assign(&(V),(E))
#define UNLESS(E) if(!(E))
#define UNLESS_ASSIGN(V,E) ASSIGN(V,E); UNLESS(V)

/* Declarations for objects of type Missing */

typedef struct {
  PyObject_HEAD
} Missing;

static void
Missing_dealloc(Missing *self)
{
  PyMem_DEL(self);
}

static PyObject *
Missing_repr(Missing *self)
{
  return PyString_FromString("Missing.Value");
}

static PyObject *
Missing_str(Missing *self)
{
  return PyString_FromString("");
}

/* Code to access Missing objects as numbers */

static PyObject *
Missing_bin(PyObject *v, PyObject *w)
{
  return v;
}

static PyObject *
Missing_pow(PyObject *v, PyObject *w, PyObject *z)
{
  return v;
}				

static PyObject *
Missing_un(PyObject *v)
{
  return v;
}

static int
Missing_nonzero(PyObject *v)
{
  return 0;
}

static int
Missing_coerce(PyObject **pv, PyObject **pw)
{
  Py_INCREF(*pv);
  Py_INCREF(*pv);
  *pw=*pv;
  return 0;
}

static PyObject *
Missing_int(Missing *v)
{
  PyErr_SetString(PyExc_TypeError,
		  "Missing objects do not support conversion to integer");
  return NULL;
}

static PyObject *
Missing_long(Missing *v)
{
  PyErr_SetString(PyExc_TypeError,
		  "Missing objects do not support conversion to long");
  return NULL;
}

static PyObject *
Missing_float(Missing *v)
{
  PyErr_SetString(PyExc_TypeError,
		  "Missing objects do not support conversion to float");
  return NULL;
}

static PyObject *
Missing_oct(Missing *v)
{ 
  PyErr_SetString(PyExc_TypeError,
	  "Missing objects do not support conversion to an octal string");
  return NULL;
}

static PyObject *
Missing_hex(Missing *v)
{
  PyErr_SetString(PyExc_TypeError,
     	"Missing objects do not support conversion to hexadecimal strings");
  return NULL;
}

static PyNumberMethods Missing_as_number = {
	(binaryfunc)Missing_bin,	/*nb_add*/
	(binaryfunc)Missing_bin,	/*nb_subtract*/
	(binaryfunc)Missing_bin,	/*nb_multiply*/
	(binaryfunc)Missing_bin,	/*nb_divide*/
	(binaryfunc)Missing_bin,	/*nb_remainder*/
	(binaryfunc)Missing_bin,	/*nb_divmod*/
	(ternaryfunc)Missing_pow,	/*nb_power*/
	(unaryfunc)Missing_un,	/*nb_negative*/
	(unaryfunc)Missing_un,	/*nb_positive*/
	(unaryfunc)Missing_un,	/*nb_absolute*/
	(inquiry)Missing_nonzero,	/*nb_nonzero*/
	(unaryfunc)Missing_un,	/*nb_invert*/
	(binaryfunc)Missing_bin,	/*nb_lshift*/
	(binaryfunc)Missing_bin,	/*nb_rshift*/
	(binaryfunc)Missing_bin,	/*nb_and*/
	(binaryfunc)Missing_bin,	/*nb_xor*/
	(binaryfunc)Missing_bin,	/*nb_or*/
	(coercion)Missing_coerce,	/*nb_coerce*/
	(unaryfunc)Missing_int,	/*nb_int*/
	(unaryfunc)Missing_long,	/*nb_long*/
	(unaryfunc)Missing_float,	/*nb_float*/
	(unaryfunc)Missing_oct,	/*nb_oct*/
	(unaryfunc)Missing_hex,	/*nb_hex*/
};

/* ------------------------------------------------------- */

static char Missingtype__doc__[] = 
"Represent totally unknown quantities\n"
"\n"
"Missing values are used to represent numberic quantities that are\n"
"unknown.  They support all mathematical operations except\n"
"conversions by returning themselves.\n"
;

static PyExtensionClass MissingType = {
  PyObject_HEAD_INIT(NULL)
  0,					/*ob_size*/
  "Missing",				/*tp_name*/
  sizeof(Missing),			/*tp_basicsize*/
  0,					/*tp_itemsize*/
  /* methods */
  (destructor)Missing_dealloc,		/*tp_dealloc*/
  (printfunc)0,				/*tp_print*/
  (getattrfunc)0,			/*obsolete tp_getattr*/
  (setattrfunc)0,			/*obsolete tp_setattr*/
  (cmpfunc)0,				/*tp_compare*/
  (reprfunc)Missing_repr,		/*tp_repr*/
  &Missing_as_number,			/*tp_as_number*/
  0,					/*tp_as_sequence*/
  0,					/*tp_as_mapping*/
  (hashfunc)0,				/*tp_hash*/
  (ternaryfunc)0,			/*tp_call*/
  (reprfunc)Missing_str,		/*tp_str*/
  (getattrofunc)0,			/*tp_getattro*/
  (setattrofunc)0,			/*tp_setattro*/
  
  /* Space for future expansion */
  0L,0L,
  Missingtype__doc__, /* Documentation string */
  METHOD_CHAIN(NULL)
};

/* End of code for Missing objects */
/* -------------------------------------------------------- */


/* List of methods defined in the module */

static struct PyMethodDef Module_Level__methods[] = {  
  {NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

/* Initialization function for the module (*must* be called initMissing) */

void
initMissing()
{
  PyObject *m, *d;
  char *rev="$Revision: 1.1 $";

  /* Create the module and add the functions */
  m = Py_InitModule4("Missing", Module_Level__methods,
		     Missing_module_documentation,
		     (PyObject*)NULL,PYTHON_API_VERSION);

  /* Add some symbolic constants to the module */
  d = PyModule_GetDict(m);

  PyExtensionClass_Export(d,"Missing",MissingType);

  ErrorObject = PyString_FromString("Missing.error");
  PyDict_SetItemString(d, "error", ErrorObject);

  PyDict_SetItemString(d, "__version__",
		       PyString_FromStringAndSize(rev+11,strlen(rev+11)-2));
  

  PyDict_SetItemString(d, "Value",
		       PyObject_CallObject((PyObject*)&MissingType, NULL));
  
	
  /* Check for errors */
  if (PyErr_Occurred())
    Py_FatalError("can't initialize module Missing");
}

/*****************************************************************************
Revision Log:

  $Log: Missing.c,v $
  Revision 1.1  1997/07/01 21:36:34  jim
  *** empty log message ***


*****************************************************************************/
