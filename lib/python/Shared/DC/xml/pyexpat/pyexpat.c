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
#include "xmlparse.h"
#include <setjmp.h>

/*
** The version number should match the one in _checkversion
*/
#define VERSION "1.3"

static PyObject *ErrorObject;

/* ----------------------------------------------------- */

/* Declarations for objects of type xmlparser */

typedef struct {
	PyObject_HEAD
	XML_Parser itself;
	PyObject *StartElementHandler;
	PyObject *EndElementHandler;
	PyObject *CharacterDataHandler;
	PyObject *ProcessingInstructionHandler;
	int jmpbuf_valid;
	jmp_buf jmpbuf;
} xmlparseobject;

staticforward PyTypeObject Xmlparsetype;

/* Callback routines */
static void
my_StartElementHandler(userdata, name, atts)
	void *userdata;
	char *name;
	char **atts;
{
	xmlparseobject *self = (xmlparseobject *)userdata;
	PyObject *args;
	PyObject *rv;
	PyObject *attrs_obj;
	int attrs_len;
	char **attrs_p;
	

	if (self->StartElementHandler
	    && self->StartElementHandler != Py_None) {
		for(attrs_len=0, attrs_p = atts;
		    *attrs_p;
		    attrs_p++, attrs_len++);
		if( (attrs_obj = PyList_New(attrs_len)) == NULL )
			return;
		for(attrs_len=0, attrs_p = atts; *attrs_p;
		    attrs_p++, attrs_len++) {
			PyList_SetItem(attrs_obj, attrs_len,
				       PyString_FromString(*attrs_p));
		}
		
		args = Py_BuildValue("(sO)", name, attrs_obj);
		Py_XDECREF(attrs_obj);
		if (!args) return;
		rv = PyEval_CallObject(self->StartElementHandler, args);
		Py_XDECREF(args);
		if (rv == NULL) {
			if (self->jmpbuf_valid)
				longjmp(self->jmpbuf, 1);
			PySys_WriteStderr("Exception in StartElementHandler()\n");
			PyErr_Clear();
		}
		Py_XDECREF(rv);
	}
}

static void
my_EndElementHandler(userdata, name)
	void *userdata;
	char *name;
{
	xmlparseobject *self = (xmlparseobject *)userdata;
	PyObject *args;
	PyObject *rv;

	if (self->EndElementHandler
	    && self->EndElementHandler != Py_None) {
		args = Py_BuildValue("(s)", name);
		if (!args) return;
		rv = PyEval_CallObject(self->EndElementHandler, args);
		Py_XDECREF(args);
		if (rv == NULL) {
			if (self->jmpbuf_valid)
				longjmp(self->jmpbuf, 1);
			PySys_WriteStderr("Exception in EndElementHandler()\n");
			PyErr_Clear();
		}
		Py_XDECREF(rv);
	}
}


static void
my_CharacterDataHandler(userdata, data, len)
	void *userdata;
	char *data;
	int len;
{
	xmlparseobject *self = (xmlparseobject *)userdata;
	PyObject *args;
	PyObject *rv;

	if (self->CharacterDataHandler
	    && self->CharacterDataHandler != Py_None) {
		args = Py_BuildValue("(s#)", data, len);
		if (!args) return;
		rv = PyEval_CallObject(self->CharacterDataHandler, args);
		Py_XDECREF(args);
		if (rv == NULL) {
			if (self->jmpbuf_valid)
				longjmp(self->jmpbuf, 1);
			PySys_WriteStderr("Exception in CharacterDataHandler()\n");
			PyErr_Clear();
		}
		Py_XDECREF(rv);
	}
}

static void
my_ProcessingInstructionHandler(userdata, target, data)
	void *userdata;
	char *target;
	char *data;
{
	xmlparseobject *self = (xmlparseobject *)userdata;
	PyObject *args;
	PyObject *rv;

	if (self->ProcessingInstructionHandler
	    && self->ProcessingInstructionHandler != Py_None) {
		args = Py_BuildValue("(ss)", target, data);
		if (!args) return;
		rv = PyEval_CallObject(self->ProcessingInstructionHandler,
				       args);
		Py_XDECREF(args);
		if (rv == NULL) {
			if (self->jmpbuf_valid)
				longjmp(self->jmpbuf, 1);
			PySys_WriteStderr("Exception in ProcessingInstructionHandler()\n");
			PyErr_Clear();
		}
		Py_XDECREF(rv);
	}
}


/* ---------------------------------------------------------------- */

static char xmlparse_Parse__doc__[] = 
"(data [,isfinal]) - Parse XML data"
;

static PyObject *
xmlparse_Parse(self, args)
	xmlparseobject *self;
	PyObject *args;
{
	char *s;
	int slen;
	int isFinal = 0;
	int rv;
	
	if (!PyArg_ParseTuple(args, "s#|i", &s, &slen, &isFinal))
		return NULL;
	if (setjmp(self->jmpbuf)) {
		/* Error in callback routine */
		return NULL;
	}
	self->jmpbuf_valid = 1;
	rv = XML_Parse(self->itself, s, slen, isFinal);
	self->jmpbuf_valid = 0;
	return Py_BuildValue("i", rv);
}


static struct PyMethodDef xmlparse_methods[] = {
	{"Parse",	(PyCFunction)xmlparse_Parse,
	 	METH_VARARGS,	xmlparse_Parse__doc__},
 
	{NULL,		NULL}		/* sentinel */
};

/* ---------- */


static xmlparseobject *
newxmlparseobject(encoding)
	char *encoding;
{
	xmlparseobject *self;
	
	self = PyObject_NEW(xmlparseobject, &Xmlparsetype);
	if (self == NULL)
		return NULL;
	self->StartElementHandler = Py_None;
	Py_INCREF(Py_None);
	self->EndElementHandler = Py_None;
	Py_INCREF(Py_None);
	self->CharacterDataHandler = Py_None;
	Py_INCREF(Py_None);
	self->ProcessingInstructionHandler = Py_None;
	Py_INCREF(Py_None);
	if ((self->itself = XML_ParserCreate(encoding)) == NULL ) {
		PyErr_SetString(PyExc_RuntimeError, "XML_ParserCreate failed");
		Py_DECREF(self);
		return NULL;
	}

	XML_SetUserData(self->itself, (void *)self);
	XML_SetElementHandler(self->itself, my_StartElementHandler,
			      my_EndElementHandler);
	XML_SetCharacterDataHandler(self->itself, my_CharacterDataHandler);
	XML_SetProcessingInstructionHandler(self->itself,
					    my_ProcessingInstructionHandler);

	return self;
}


static void
xmlparse_dealloc(self)
	xmlparseobject *self;
{
	Py_XDECREF(self->StartElementHandler);
	Py_XDECREF(self->EndElementHandler);
	Py_XDECREF(self->CharacterDataHandler);
	Py_XDECREF(self->ProcessingInstructionHandler);
	if (self->itself)
		XML_ParserFree(self->itself);
	self->itself = NULL;
	PyMem_DEL(self);
}

static PyObject *
xmlparse_getattr(self, name)
	xmlparseobject *self;
	char *name;
{
	long rv;
	
	if (strcmp(name, "StartElementHandler") == 0) {
		Py_INCREF(self->StartElementHandler);
		return self->StartElementHandler;
	}
	if (strcmp(name, "EndElementHandler") == 0) {
		Py_INCREF(self->EndElementHandler);
		return self->EndElementHandler;
	}
	if (strcmp(name, "CharacterDataHandler") == 0) {
		Py_INCREF(self->CharacterDataHandler);
		return self->CharacterDataHandler;
	}
	if (strcmp(name, "ProcessingInstructionHandler") == 0) {
		Py_INCREF(self->ProcessingInstructionHandler);
		return self->ProcessingInstructionHandler;
	}

	if (strcmp(name, "ErrorCode") == 0)
		return Py_BuildValue("l",
				(long)XML_GetErrorCode(self->itself));
	if (strcmp(name, "ErrorLineNumber") == 0)
		return Py_BuildValue("l",
				(long)XML_GetErrorLineNumber(self->itself));
	if (strcmp(name, "ErrorColumnNumber") == 0)
		return Py_BuildValue("l",
				(long)XML_GetErrorColumnNumber(self->itself));
	if (strcmp(name, "ErrorByteIndex") == 0)
		return Py_BuildValue("l",
				XML_GetErrorByteIndex(self->itself));

	return Py_FindMethod(xmlparse_methods, (PyObject *)self, name);
}

static int
xmlparse_setattr(self, name, v)
	xmlparseobject *self;
	char *name;
	PyObject *v;
{
	/* Set attribute 'name' to value 'v'. v==NULL means delete */
	if (v==NULL) {
		PyErr_SetString(PyExc_RuntimeError, "Cannot delete attribute");
		return -1;
	}
	
	if (strcmp(name, "StartElementHandler") == 0) {
		Py_XDECREF(self->StartElementHandler);
		self->StartElementHandler = v;
		Py_INCREF(v);
		return 0;
	}
	if (strcmp(name, "EndElementHandler") == 0) {
		Py_XDECREF(self->EndElementHandler);
		self->EndElementHandler = v;
		Py_INCREF(v);
		return 0;
	}
	if (strcmp(name, "CharacterDataHandler") == 0) {
		Py_XDECREF(self->CharacterDataHandler);
		self->CharacterDataHandler = v;
		Py_INCREF(v);
		return 0;
	}
	if (strcmp(name, "ProcessingInstructionHandler") == 0) {
		Py_XDECREF(self->ProcessingInstructionHandler);
		self->ProcessingInstructionHandler = v;
		Py_INCREF(v);
		return 0;
	}
	return -1;
}

static char Xmlparsetype__doc__[] = 
"XML parser"
;

static PyTypeObject Xmlparsetype = {
	PyObject_HEAD_INIT(NULL)
	0,				/*ob_size*/
	"xmlparser",			/*tp_name*/
	sizeof(xmlparseobject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)xmlparse_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)xmlparse_getattr,	/*tp_getattr*/
	(setattrfunc)xmlparse_setattr,	/*tp_setattr*/
	(cmpfunc)0,		/*tp_compare*/
	(reprfunc)0,		/*tp_repr*/
	0,			/*tp_as_number*/
	0,		/*tp_as_sequence*/
	0,		/*tp_as_mapping*/
	(hashfunc)0,		/*tp_hash*/
	(ternaryfunc)0,		/*tp_call*/
	(reprfunc)0,		/*tp_str*/

	/* Space for future expansion */
	0L,0L,0L,0L,
	Xmlparsetype__doc__ /* Documentation string */
};

/* End of code for xmlparser objects */
/* -------------------------------------------------------- */


static char pyexpat_ParserCreate__doc__[] =
"([encoding]) - Return a new XML parser object"
;

static PyObject *
pyexpat_ParserCreate(self, args)
	PyObject *self;	/* Not used */
	PyObject *args;
{
	char *encoding  = NULL;
	
	if (!PyArg_ParseTuple(args, "|s", encoding))
		return NULL;
	return (PyObject *)newxmlparseobject(encoding);
}

static char pyexpat_ErrorString__doc__[] =
"(errno) Returns string error for given number"
;

static PyObject *
pyexpat_ErrorString(self, args)
	PyObject *self;	/* Not used */
	PyObject *args;
{
	long code;
	
	if (!PyArg_ParseTuple(args, "l", &code))
		return NULL;
	return Py_BuildValue("z", XML_ErrorString((int)code));
}

/* List of methods defined in the module */

static struct PyMethodDef pyexpat_methods[] = {
	{"ParserCreate",	(PyCFunction)pyexpat_ParserCreate,
	 	METH_VARARGS,	pyexpat_ParserCreate__doc__},
	{"ErrorString",	(PyCFunction)pyexpat_ErrorString,
	 	METH_VARARGS,	pyexpat_ErrorString__doc__},
 
	{NULL,	 (PyCFunction)NULL, 0, NULL}		/* sentinel */
};


/* Initialization function for the module (*must* be called initpyexpat) */

static char pyexpat_module_documentation[] = 
""
;

void
initpyexpat()
{
	PyObject *m, *d;

	Xmlparsetype.ob_type = &PyType_Type;

	/* Create the module and add the functions */
	m = Py_InitModule4("pyexpat", pyexpat_methods,
		pyexpat_module_documentation,
		(PyObject*)NULL,PYTHON_API_VERSION);

	/* Add some symbolic constants to the module */
	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("pyexpat.error");
	PyDict_SetItemString(d, "error", ErrorObject);

	/* XXXX Add constants here */
	PyDict_SetItemString(d, "version", PyString_FromString(VERSION));
		
#define MYCONST(name) \
	PyDict_SetItemString(d, #name, PyInt_FromLong(name))
		
	MYCONST(XML_ERROR_NONE);
	MYCONST(XML_ERROR_NO_MEMORY);
	MYCONST(XML_ERROR_SYNTAX);
	MYCONST(XML_ERROR_NO_ELEMENTS);
	MYCONST(XML_ERROR_INVALID_TOKEN);
	MYCONST(XML_ERROR_UNCLOSED_TOKEN);
	MYCONST(XML_ERROR_PARTIAL_CHAR);
	MYCONST(XML_ERROR_TAG_MISMATCH);
	MYCONST(XML_ERROR_DUPLICATE_ATTRIBUTE);
	MYCONST(XML_ERROR_JUNK_AFTER_DOC_ELEMENT);
	MYCONST(XML_ERROR_PARAM_ENTITY_REF);
	MYCONST(XML_ERROR_UNDEFINED_ENTITY);
	MYCONST(XML_ERROR_RECURSIVE_ENTITY_REF);
	MYCONST(XML_ERROR_ASYNC_ENTITY);
	MYCONST(XML_ERROR_BAD_CHAR_REF);
	MYCONST(XML_ERROR_BINARY_ENTITY_REF);
	MYCONST(XML_ERROR_ATTRIBUTE_EXTERNAL_ENTITY_REF);
	MYCONST(XML_ERROR_MISPLACED_XML_PI);
	MYCONST(XML_ERROR_UNKNOWN_ENCODING);
	MYCONST(XML_ERROR_INCORRECT_ENCODING);

	
	/* Check for errors */
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module pyexpat");
}

