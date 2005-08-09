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
	PyObject *CommentHandler;
	PyObject *StartCdataSectionHandler;
	PyObject *EndCdataSectionHandler;
	PyObject *DefaultHandler;
	PyObject *UnparsedEntityDeclHandler;
	PyObject *NotationDeclHandler;
        PyObject *StartNamespaceDeclHandler;
        PyObject *EndNamespaceDeclHandler;
        PyObject *NotStandaloneHandler;
        int attrdict;
	int jmpbuf_valid;
	jmp_buf jmpbuf;
} xmlparseobject;

staticforward PyTypeObject Xmlparsetype;

/* Callback routines */
static void
my_StartElementHandler(void *userdata, const char *name, const char **atts) {
	xmlparseobject *self = (xmlparseobject *)userdata;
	PyObject *args;
	PyObject *rv;
	PyObject *attrs_obj;
	int attrs_len;
	const char **attrs_p;
	const char **attrs_k = atts;

	if (self->StartElementHandler != Py_None) {
	        if (self->attrdict) {
		        if( (attrs_obj = PyDict_New()) == NULL ) 
			        goto err;
			for(attrs_len=0, attrs_p = atts; 
			    *attrs_p;
			    attrs_p++, attrs_len++) {
			        if (attrs_len%2) {
  				        rv=PyString_FromString(*attrs_p);  
					if (! rv) {
					        Py_DECREF(attrs_obj);
						goto err;
					}
					if (PyDict_SetItemString(
					       attrs_obj,
					       (char*)*attrs_k, rv)
					    < 0) {
					        Py_DECREF(attrs_obj);
						goto err;
					}
					Py_DECREF(rv);
				}
				else attrs_k=attrs_p;
			}
		}
		else {
		        for(attrs_len=0, attrs_p = atts;
			    *attrs_p;
			    attrs_p++, attrs_len++);
			if( (attrs_obj = PyList_New(attrs_len)) == NULL ) 
			        goto err;
			for(attrs_len=0, attrs_p = atts; *attrs_p;
			    attrs_p++, attrs_len++) {
			        rv=PyString_FromString(*attrs_p);
				if (! rv) {
				        Py_DECREF(attrs_obj);
					goto err;
				}
				PyList_SET_ITEM(attrs_obj, attrs_len, rv);
			}
		}
		
		args = Py_BuildValue("(sO)", name, attrs_obj);
		Py_DECREF(attrs_obj);
		if (!args) goto err;
		rv = PyEval_CallObject(self->StartElementHandler, args);
		Py_DECREF(args);
		if (rv == NULL) goto err;
		Py_DECREF(rv);
	}
	return;
err:
	if (self->jmpbuf_valid) longjmp(self->jmpbuf, 1);
	PySys_WriteStderr("Exception in StartElementHandler()\n");
	PyErr_Clear();
}

static void
my_EndElementHandler(void *userdata, const char *name) {
	xmlparseobject *self = (xmlparseobject *)userdata;
	PyObject *args;
	PyObject *rv;

	if (self->EndElementHandler != Py_None) {
		args = Py_BuildValue("(s)", name);
		if (!args) goto err;
		rv = PyEval_CallObject(self->EndElementHandler, args);
		Py_DECREF(args);
		if (rv == NULL) goto err;
		Py_DECREF(rv);
	}
	return;
err:
	if (self->jmpbuf_valid) longjmp(self->jmpbuf, 1);
	PySys_WriteStderr("Exception in EndElementHandler()\n");
	PyErr_Clear();
}

static void
my_DefaultHandler(void *userdata, const char *data, int len) {
	xmlparseobject *self = (xmlparseobject *)userdata;
	PyObject *args;
	PyObject *rv;

	if (self->DefaultHandler != Py_None) {
		args = Py_BuildValue("(s#)", data, len);
		if (!args) goto err;
		rv = PyEval_CallObject(self->DefaultHandler, args);
		Py_XDECREF(args);
		if (rv == NULL) goto err;
		Py_XDECREF(rv);
	}
	return;
err:
	if (self->jmpbuf_valid) longjmp(self->jmpbuf, 1);
	PySys_WriteStderr("Exception in DefaultHandler()\n");
	PyErr_Clear();
}

static void
my_CharacterDataHandler(void *userdata, const char *data, int len) {
	xmlparseobject *self = (xmlparseobject *)userdata;
	PyObject *args;
	PyObject *rv;

	if (self->CharacterDataHandler != Py_None) {
		args = Py_BuildValue("(s#)", data, len);
		if (!args) goto err;
		rv = PyEval_CallObject(self->CharacterDataHandler, args);
		Py_DECREF(args);
		if (rv == NULL) goto err;
		Py_DECREF(rv);
	}
	else my_DefaultHandler(userdata, data, len);
	return;
err:
	if (self->jmpbuf_valid) longjmp(self->jmpbuf, 1);
	PySys_WriteStderr("Exception in CharacterDataHandler()\n");
	PyErr_Clear();
}

static void
my_ProcessingInstructionHandler(void *userdata, 
				const char *target, const char *data) {
	xmlparseobject *self = (xmlparseobject *)userdata;
	PyObject *args;
	PyObject *rv;

	if (self->ProcessingInstructionHandler != Py_None) {
		args = Py_BuildValue("(ss)", target, data);
		if (!args) goto err;
		rv = PyEval_CallObject(self->ProcessingInstructionHandler,
				       args);
		Py_DECREF(args);
		if (rv == NULL) goto err;
		Py_DECREF(rv);
	}
	return;
err:
	if (self->jmpbuf_valid) longjmp(self->jmpbuf, 1);
	PySys_WriteStderr("Exception in ProcessingInstructionHandler()\n");
	PyErr_Clear();
}

static void
my_CommentHandler(void *userdata, const char *data) {
	xmlparseobject *self = (xmlparseobject *)userdata;
	PyObject *args;
	PyObject *rv;

	if (self->CommentHandler != Py_None) {
		args = Py_BuildValue("(s)", data);
		if (!args) goto err;
		rv = PyEval_CallObject(self->CommentHandler, args);
		Py_DECREF(args);
		if (rv == NULL) goto err;
		Py_DECREF(rv);
	}
	return;
err:
	if (self->jmpbuf_valid) longjmp(self->jmpbuf, 1);
	PySys_WriteStderr("Exception in CommentHandler()\n");
	PyErr_Clear();
}

static void
my_StartCdataSectionHandler(void *userdata) {
        xmlparseobject *self = (xmlparseobject *)userdata;
	PyObject *rv;

	if (self->StartCdataSectionHandler != Py_None) {
		rv = PyEval_CallObject(self->StartCdataSectionHandler, NULL);
		if (rv == NULL) goto err;
		Py_DECREF(rv);
	}
	return;
err:
	if (self->jmpbuf_valid) longjmp(self->jmpbuf, 1);
	PySys_WriteStderr("Exception in StartCdataSectionHandler()\n");
	PyErr_Clear();
}

static void
my_EndCdataSectionHandler(void *userdata) {
        xmlparseobject *self = (xmlparseobject *)userdata;
	PyObject *rv;

	if (self->EndCdataSectionHandler != Py_None) {
		rv = PyEval_CallObject(self->EndCdataSectionHandler, NULL);
		if (rv == NULL) goto err;
		Py_DECREF(rv);
	}
	return;
err:
	if (self->jmpbuf_valid) longjmp(self->jmpbuf, 1);
	PySys_WriteStderr("Exception in EndCdataSectionHandler()\n");
	PyErr_Clear();
}

static void
my_UnparsedEntityDeclHandler(void * userdata, 
			     const char *entityName,		
			     const char *base,
			     const char *systemId,
			     const char *publicId,
			     const char *notationName)
{
        xmlparseobject *self = (xmlparseobject *)userdata;
	PyObject *args, *rv=0;
  
	if (self->UnparsedEntityDeclHandler != Py_None) {
	        args = Py_BuildValue("sssss", 
				     entityName, base, systemId, 
				     publicId, notationName);
		if (args == NULL) goto err;
		rv = PyEval_CallObject(self->UnparsedEntityDeclHandler, 
				       args);
		Py_DECREF(args);
		if (rv == NULL) goto err;
		Py_DECREF(rv);
	}
	return;
err:
  if (self->jmpbuf_valid) longjmp(self->jmpbuf, 1);
  PySys_WriteStderr("Exception in UnparsedEntityDeclHandler()\n");
  PyErr_Clear();

}

static void
my_NotationDeclHandler(void * userdata, 
		       const char *notationName,		
		       const char *base,
		       const char *systemId,
		       const char *publicId)
{
        xmlparseobject *self = (xmlparseobject *)userdata;
	PyObject *args, *rv=0;
  
	if (self->NotationDeclHandler != Py_None) {
	        args = Py_BuildValue("ssss", 
				     notationName, base, systemId, publicId);
		if (args == NULL) goto err;
		rv = PyEval_CallObject(self->NotationDeclHandler, args);
		Py_DECREF(args);
		if (rv == NULL) goto err;
		Py_DECREF(rv);
	}
	return;
err:
	if (self->jmpbuf_valid) longjmp(self->jmpbuf, 1);
	PySys_WriteStderr("Exception in NotationDeclHandler()\n");
	PyErr_Clear();
}

static void
my_StartNamespaceDeclHandler(void *userdata, 
			     const char *prefix, const char *uri) {
	xmlparseobject *self = (xmlparseobject *)userdata;
	PyObject *args;
	PyObject *rv;

	if (self->StartNamespaceDeclHandler != Py_None) {
		args = Py_BuildValue("(ss)", prefix, uri);
		if (!args) goto err;
		rv = PyEval_CallObject(self->StartNamespaceDeclHandler, args);
		Py_DECREF(args);
		if (rv == NULL) goto err;
		Py_DECREF(rv);
	}
	return;
err:
	if (self->jmpbuf_valid) longjmp(self->jmpbuf, 1);
	PySys_WriteStderr("Exception in StartNamespaceDeclHandler()\n");
	PyErr_Clear();
}

static void
my_EndNamespaceDeclHandler(void *userdata, const char *prefix) {
	xmlparseobject *self = (xmlparseobject *)userdata;
	PyObject *args;
	PyObject *rv;

	if (self->EndNamespaceDeclHandler != Py_None) {
		args = Py_BuildValue("(s)", prefix);
		if (!args) goto err;
		rv = PyEval_CallObject(self->EndNamespaceDeclHandler, args);
		Py_DECREF(args);
		if (rv == NULL) goto err;
		Py_DECREF(rv);
	}
	return;
err:
	if (self->jmpbuf_valid) longjmp(self->jmpbuf, 1);
	PySys_WriteStderr("Exception in EndNamespaceDeclHandler()\n");
	PyErr_Clear();
}

static int
my_NotStandaloneHandler(void *userdata) {
        xmlparseobject *self = (xmlparseobject *)userdata;
	PyObject *rv;
	int irv;

	if (self->NotStandaloneHandler != Py_None) {
		rv = PyEval_CallObject(self->StartCdataSectionHandler, NULL);
		if (rv == NULL) goto err;
		irv=PyObject_IsTrue(rv);
		Py_DECREF(rv);
		return irv;
	}
	return 1;
err:
	if (self->jmpbuf_valid) longjmp(self->jmpbuf, 1);
	PySys_WriteStderr("Exception in NotStandaloneHandler()\n");
	PyErr_Clear();
	return 0;
}

/* ---------------------------------------------------------------- */

static char xmlparse_Parse__doc__[] = 
"(data [,isfinal]) - Parse XML data"
;

static PyObject *
xmlparse_Parse(xmlparseobject *self, PyObject *args) {
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
newxmlparseobject(char *encoding, char *namespace_separator, int attrdict) {
	xmlparseobject *self;
	
	self = PyObject_NEW(xmlparseobject, &Xmlparsetype);
	if (self == NULL)
		return NULL;

#define INIT_HANDLER(N) self->N=Py_None; Py_INCREF(Py_None)
	INIT_HANDLER(StartElementHandler);
	INIT_HANDLER(EndElementHandler);
	INIT_HANDLER(CharacterDataHandler);
	INIT_HANDLER(ProcessingInstructionHandler);
	INIT_HANDLER(CommentHandler);
	INIT_HANDLER(StartCdataSectionHandler);
	INIT_HANDLER(EndCdataSectionHandler);
	INIT_HANDLER(DefaultHandler);
	INIT_HANDLER(UnparsedEntityDeclHandler);
	INIT_HANDLER(NotationDeclHandler);
	INIT_HANDLER(StartNamespaceDeclHandler);
	INIT_HANDLER(EndNamespaceDeclHandler);
	INIT_HANDLER(NotStandaloneHandler);
#undef  INIT_HANDLER

	self->attrdict=attrdict;

	if (namespace_separator) {
	        if ((self->itself = XML_ParserCreateNS(encoding, 
						       *namespace_separator))
		    == NULL ) {
		        PyErr_SetString(PyExc_RuntimeError, 
					"XML_ParserCreateNS failed");
			Py_DECREF(self);
			return NULL;
		}
	}
	else {
	        if ((self->itself = XML_ParserCreate(encoding)) == NULL ) {
		        PyErr_SetString(PyExc_RuntimeError, 
					"XML_ParserCreate failed");
			Py_DECREF(self);
			return NULL;
		}
	}

	XML_SetUserData(self->itself, (void *)self);

	return self;
}


static void
xmlparse_dealloc(xmlparseobject *self) {
	Py_DECREF(self->StartElementHandler);
	Py_DECREF(self->EndElementHandler);
	Py_DECREF(self->CharacterDataHandler);
	Py_DECREF(self->ProcessingInstructionHandler);
	Py_DECREF(self->CommentHandler);
	Py_DECREF(self->StartCdataSectionHandler);
	Py_DECREF(self->EndCdataSectionHandler);
	Py_DECREF(self->DefaultHandler);
	Py_DECREF(self->UnparsedEntityDeclHandler);
	Py_DECREF(self->NotationDeclHandler);
	Py_DECREF(self->StartNamespaceDeclHandler);
	Py_DECREF(self->EndNamespaceDeclHandler);
	Py_DECREF(self->NotStandaloneHandler);

	if (self->itself)
		XML_ParserFree(self->itself);
	self->itself = NULL;
	PyMem_DEL(self);
}

static PyObject *
xmlparse_getattr(xmlparseobject *self, char *name) {

#define GET_HANDLER(N) \
	if (strcmp(name, #N) == 0) { \
		Py_INCREF(self->N); \
		return self->N; \
	} 
	GET_HANDLER(StartElementHandler);
	GET_HANDLER(EndElementHandler);
	GET_HANDLER(CharacterDataHandler);
	GET_HANDLER(ProcessingInstructionHandler);
	GET_HANDLER(CommentHandler);
	GET_HANDLER(StartCdataSectionHandler);
	GET_HANDLER(EndCdataSectionHandler);
	GET_HANDLER(DefaultHandler);
	GET_HANDLER(UnparsedEntityDeclHandler);
	GET_HANDLER(NotationDeclHandler);
	GET_HANDLER(StartNamespaceDeclHandler);
	GET_HANDLER(EndNamespaceDeclHandler);
	GET_HANDLER(NotStandaloneHandler);
#undef  GET_HANDLER

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

	if (strcmp(name, "__members__") == 0)
	        return Py_BuildValue("sssssssssssssssss",
				     "StartElementHandler",
				     "EndElementHandler",
				     "CharacterDataHandler",
				     "ProcessingInstructionHandler",
				     "CommentHandler",
				     "StartCdataSectionHandler",
				     "EndCdataSectionHandler",
				     "DefaultHandler",
				     "UnparsedEntityDeclHandler",
				     "NotationDeclHandler",
				     "StartNamespaceDeclHandler",
				     "EndNamespaceDeclHandler",
				     "NotStandaloneHandler",
				     "ErrorCode", "ErrorLineNumber", 
				     "ErrorColumnNumber", "ErrorByteIndex");

	return Py_FindMethod(xmlparse_methods, (PyObject *)self, name);
}

static int
xmlparse_setattr(xmlparseobject *self, char *name, PyObject *v) {
	/* Set attribute 'name' to value 'v'. v==NULL means delete */
	if (v==NULL) v=Py_None;

#define XMLSETHANDLERS(N) XML_Set ## N(self->itself, \
				       my_Start ## N, my_End ## N)

#define SET_HANDLER(N) Py_XDECREF(self->N); self->N = v; Py_INCREF(v);

	if (strncmp(name, "Start", 5)==0) {
	        if (strcmp(name+5, "ElementHandler") == 0) {
		        SET_HANDLER(StartElementHandler);
			XMLSETHANDLERS(ElementHandler);
			return 0;
		}
	        if (strcmp(name+5, "CdataSectionHandler") == 0) {
		        SET_HANDLER(StartCdataSectionHandler);
			XMLSETHANDLERS(CdataSectionHandler);
			return 0;
		}
	        if (strcmp(name+5, "NamespaceDeclHandler") == 0) {
		        SET_HANDLER(StartNamespaceDeclHandler);
			XMLSETHANDLERS(NamespaceDeclHandler);
			return 0;
		}
	}

	else if (strncmp(name, "End", 3)==0) {
	        if (strcmp(name+3, "ElementHandler") == 0) {
		        SET_HANDLER(EndElementHandler);
			XMLSETHANDLERS(ElementHandler);
			return 0;
		}
	        if (strcmp(name+3, "CdataSectionHandler") == 0) {
		        SET_HANDLER(EndCdataSectionHandler);
			XMLSETHANDLERS(CdataSectionHandler);
			return 0;
		}
	        if (strcmp(name+3, "NamespaceDeclHandler") == 0) {
		        SET_HANDLER(EndNamespaceDeclHandler);
			XMLSETHANDLERS(NamespaceDeclHandler);
			return 0;
		}
	}
#undef SET_HANDLER
#undef XMLSETHANDLERS

	else {

#define SET_HANDLER(N) \
		if (strcmp(name, #N) == 0) { \
			Py_XDECREF(self->N); \
			self->N = v; \
			Py_INCREF(v); \
			XML_Set ## N(self->itself, my_ ## N); \
			return 0; \
		}

		SET_HANDLER(CharacterDataHandler);
		SET_HANDLER(ProcessingInstructionHandler);
		SET_HANDLER(CommentHandler);
		SET_HANDLER(DefaultHandler);
		SET_HANDLER(UnparsedEntityDeclHandler);
		SET_HANDLER(NotationDeclHandler);
		SET_HANDLER(NotStandaloneHandler);
	}
#undef SET_HANDLER

	PyErr_SetString(PyExc_AttributeError, name);
	return -1;
}

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
	"XML parser"
};

/* End of code for xmlparser objects */
/* -------------------------------------------------------- */


static char pyexpat_ParserCreate__doc__[] =
"([encoding, namespace_separator]) - Return a new XML parser object"
;

static PyObject *
pyexpat_ParserCreate(PyObject *notused, PyObject *args, PyObject *kw) {
	char *encoding  = NULL, *namespace_separator=NULL;
	PyObject *attrdict=NULL;
	static char *kwlist[] = {"encoding", "namespace_separator", 
				"attrdict", NULL};

	if (!PyArg_ParseTupleAndKeywords(args, kw, "|zsO", kwlist,
					 &encoding, &namespace_separator,
					 &attrdict))
		return NULL;
	return (PyObject *)newxmlparseobject(encoding, namespace_separator,
					     attrdict 
					     ? PyObject_IsTrue(attrdict)
					     : 0);
}

static char pyexpat_ErrorString__doc__[] =
"(errno) Returns string error for given number"
;

static PyObject *
pyexpat_ErrorString(PyObject *notused, PyObject *args) {
	long code;
	
	if (!PyArg_ParseTuple(args, "l", &code))
		return NULL;
	return Py_BuildValue("z", XML_ErrorString((int)code));
}

/* List of methods defined in the module */

static struct PyMethodDef pyexpat_methods[] = {
	{"ParserCreate",	(PyCFunction)pyexpat_ParserCreate,
	 	METH_VARARGS | METH_KEYWORDS,	pyexpat_ParserCreate__doc__},
	{"ErrorString",	(PyCFunction)pyexpat_ErrorString,
	 	METH_VARARGS,	pyexpat_ErrorString__doc__},
 
	{NULL,	 (PyCFunction)NULL, 0, NULL}		/* sentinel */
};


/* Initialization function for the module (*must* be called initpyexpat) */

static char pyexpat_module_documentation[] = 
"$Id$"
;

void
initdcpyexpat(void) {
	PyObject *m, *d;
	static const char *rev="$Revision: 1.4 $";

	Xmlparsetype.ob_type = &PyType_Type;

	m = Py_InitModule4("dcpyexpat", pyexpat_methods,
		pyexpat_module_documentation,
		(PyObject*)NULL,PYTHON_API_VERSION);

	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("pyexpat.error");
	PyDict_SetItemString(d, "error", ErrorObject);
	PyDict_SetItemString(d, "API_Revision", PyString_FromString(rev));
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

