/*
**	cAccessControl.c
**
**	Access control acceleration routines

  Copyright (c) 2001, Zope Foundation and Contributors.  
  All rights reserved.
  
  Redistribution and use in source and binary forms, with or without
  modification, are permitted provided that the following conditions are
  met:
  
    o Redistributions of source code must retain the above copyright
      notice, this list of conditions, and the disclaimer that follows.
  
    o Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions, and the following disclaimer in
      the documentation and/or other materials provided with the
      distribution.
  
    o Neither the name of Digital Creations nor the names of its
      contributors may be used to endorse or promote products derived
      from this software without specific prior written permission.
  
  
  THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS AND CONTRIBUTORS *AS
  IS* AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
  TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
  PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL
  CREATIONS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
  INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
  BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
  OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
  TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
  USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
  DAMAGE.

  If you have questions regarding this software,
  contact:
 
    Digital Creations L.C.  
    info@digicool.com
 
    (540) 371-6909

*/

#include "ExtensionClass/ExtensionClass.h"
#include "Acquisition/Acquisition.h"

#include <stdio.h>
#include <stdlib.h>

#if PY_VERSION_HEX < 0x02050000 && !defined(PY_SSIZE_T_MIN)
typedef int Py_ssize_t;
typedef Py_ssize_t (*lenfunc)(PyObject *);
typedef PyObject *(*ssizeargfunc)(PyObject *, Py_ssize_t);
typedef PyObject *(*ssizessizeargfunc)(PyObject *, Py_ssize_t, Py_ssize_t);
typedef int(*ssizeobjargproc)(PyObject *, Py_ssize_t, PyObject *);
typedef int(*ssizessizeobjargproc)(PyObject *, Py_ssize_t, Py_ssize_t, PyObject *);
#define PY_SSIZE_T_MAX INT_MAX
#define PY_SSIZE_T_MIN INT_MIN
#endif


static void
PyVar_Assign(PyObject **v,  PyObject *e)
{
  Py_XDECREF(*v);
  *v=e;
}

#define ASSIGN(V,E) PyVar_Assign(&(V),(E))
#define UNLESS(E) if (!(E))
#define OBJECT(o) ((PyObject *) (o))

static PyObject *
callfunction1(PyObject *function, PyObject *arg)
{
  PyObject *t, *r;
  t = PyTuple_New(1);
  if (t == NULL)
    return NULL;
  Py_INCREF(arg);
  PyTuple_SET_ITEM(t, 0, arg);
  r = PyObject_CallObject(function, t);
  Py_DECREF(t);
  return r;
}

static PyObject *
callmethod1(PyObject *self, PyObject *name, PyObject *arg)
{
  UNLESS(self = PyObject_GetAttr(self,name)) return NULL;
  ASSIGN(self, callfunction1(self, arg));
  return self;
}

static PyObject *
callfunction2(PyObject *function, PyObject *arg0, PyObject *arg1)
{
  PyObject *t, *r;
  t = PyTuple_New(2);
  if (t == NULL)
    return NULL;
  Py_INCREF(arg0);
  Py_INCREF(arg1);
  PyTuple_SET_ITEM(t, 0, arg0);
  PyTuple_SET_ITEM(t, 1, arg1);
  r = PyObject_CallObject(function, t);
  Py_DECREF(t);
  return r;
}

static PyObject *
callfunction3(PyObject *function, 
              PyObject *arg0, PyObject *arg1, 
              PyObject *arg2
              )
{
  PyObject *t, *r;
  t = PyTuple_New(3);
  if (t == NULL)
    return NULL;
  Py_INCREF(arg0);
  Py_INCREF(arg1);
  Py_INCREF(arg2);
  PyTuple_SET_ITEM(t, 0, arg0);
  PyTuple_SET_ITEM(t, 1, arg1);
  PyTuple_SET_ITEM(t, 2, arg2);
  r = PyObject_CallObject(function, t);
  Py_DECREF(t);
  return r;
}

static PyObject *
callfunction4(PyObject *function, 
              PyObject *arg0, PyObject *arg1, 
              PyObject *arg2, PyObject *arg3 
              )
{
  PyObject *t, *r;
  t = PyTuple_New(4);
  if (t == NULL)
    return NULL;
  Py_INCREF(arg0);
  Py_INCREF(arg1);
  Py_INCREF(arg2);
  Py_INCREF(arg3);
  PyTuple_SET_ITEM(t, 0, arg0);
  PyTuple_SET_ITEM(t, 1, arg1);
  PyTuple_SET_ITEM(t, 2, arg2);
  PyTuple_SET_ITEM(t, 3, arg3);
  r = PyObject_CallObject(function, t);
  Py_DECREF(t);
  return r;
}

static PyObject *
callfunction5(PyObject *function, 
              PyObject *arg0, PyObject *arg1, 
              PyObject *arg2, PyObject *arg3, PyObject *arg4 
              )
{
  PyObject *t, *r;
  t = PyTuple_New(5);
  if (t == NULL)
    return NULL;
  Py_INCREF(arg0);
  Py_INCREF(arg1);
  Py_INCREF(arg2);
  Py_INCREF(arg3);
  Py_INCREF(arg4);
  PyTuple_SET_ITEM(t, 0, arg0);
  PyTuple_SET_ITEM(t, 1, arg1);
  PyTuple_SET_ITEM(t, 2, arg2);
  PyTuple_SET_ITEM(t, 3, arg3);
  PyTuple_SET_ITEM(t, 4, arg4);
  r = PyObject_CallObject(function, t);
  Py_DECREF(t);
  return r;
}

static PyObject *
callfunction6(PyObject *function, 
              PyObject *arg0, PyObject *arg1, 
              PyObject *arg2, PyObject *arg3,
              PyObject *arg4, PyObject *arg5
              )
{
  PyObject *t, *r;
  t = PyTuple_New(6);
  if (t == NULL)
    return NULL;
  Py_INCREF(arg0);
  Py_INCREF(arg1);
  Py_INCREF(arg2);
  Py_INCREF(arg3);
  Py_INCREF(arg4);
  Py_INCREF(arg5);
  PyTuple_SET_ITEM(t, 0, arg0);
  PyTuple_SET_ITEM(t, 1, arg1);
  PyTuple_SET_ITEM(t, 2, arg2);
  PyTuple_SET_ITEM(t, 3, arg3);
  PyTuple_SET_ITEM(t, 4, arg4);
  PyTuple_SET_ITEM(t, 5, arg5);
  r = PyObject_CallObject(function, t);
  Py_DECREF(t);
  return r;
}

static int 
unpacktuple2(PyObject *args, char *name, int min, 
             PyObject **a0, PyObject **a1)
{ 
  int l;
  l=PyTuple_Size(args);
  if (l < 0) return -1;
  if (l < min) 
    {
      PyErr_Format(PyExc_TypeError, "expected %d arguments, got %d", min, l);
      return -1;
    }
  if (l > 0) *a0=PyTuple_GET_ITEM(args, 0);
  if (l > 1) *a1=PyTuple_GET_ITEM(args, 1);
  return 0;
}

static int 
unpacktuple3(PyObject *args, char *name, int min, 
             PyObject **a0, PyObject **a1, PyObject **a2)
{ 
  int l;
  l=PyTuple_Size(args);
  if (l < 0) return -1;
  if (l < min) 
    {
      PyErr_Format(PyExc_TypeError, "expected %d arguments, got %d", min, l);
      return -1;
    }
  if (l > 0) *a0=PyTuple_GET_ITEM(args, 0);
  if (l > 1) *a1=PyTuple_GET_ITEM(args, 1);
  if (l > 2) *a2=PyTuple_GET_ITEM(args, 2);
  return 0;
}

static int 
unpacktuple4(PyObject *args, char *name, int min, 
             PyObject **a0, PyObject **a1, PyObject **a2, PyObject **a3)
{ 
  int l;
  l=PyTuple_Size(args);
  if (l < 0) return -1;
  if (l < min) 
    {
      PyErr_Format(PyExc_TypeError, "expected %d arguments, got %d", min, l);
      return -1;
    }
  if (l > 0) *a0=PyTuple_GET_ITEM(args, 0);
  if (l > 1) *a1=PyTuple_GET_ITEM(args, 1);
  if (l > 2) *a2=PyTuple_GET_ITEM(args, 2);
  if (l > 3) *a3=PyTuple_GET_ITEM(args, 3);
  return 0;
}

static int 
unpacktuple5(PyObject *args, char *name, int min, 
             PyObject **a0, PyObject **a1, PyObject **a2, 
             PyObject **a3, PyObject **a4)
{ 
  int l;
  l=PyTuple_Size(args);
  if (l < 0) return -1;
  if (l < min) 
    {
      PyErr_Format(PyExc_TypeError, "expected %d arguments, got %d", min, l);
      return -1;
    }
  if (l > 0) *a0=PyTuple_GET_ITEM(args, 0);
  if (l > 1) *a1=PyTuple_GET_ITEM(args, 1);
  if (l > 2) *a2=PyTuple_GET_ITEM(args, 2);
  if (l > 3) *a3=PyTuple_GET_ITEM(args, 3);
  if (l > 4) *a4=PyTuple_GET_ITEM(args, 4);
  return 0;
}

static int 
unpacktuple6(PyObject *args, char *name, int min, 
             PyObject **a0, PyObject **a1, PyObject **a2, 
             PyObject **a3, PyObject **a4, PyObject **a5)
{ 
  int l;
  l=PyTuple_Size(args);
  if (l < 0) return -1;
  if (l < min) 
    {
      PyErr_Format(PyExc_TypeError, "expected %d arguments, got %d", min, l);
      return -1;
    }
  if (l > 0) *a0=PyTuple_GET_ITEM(args, 0);
  if (l > 1) *a1=PyTuple_GET_ITEM(args, 1);
  if (l > 2) *a2=PyTuple_GET_ITEM(args, 2);
  if (l > 3) *a3=PyTuple_GET_ITEM(args, 3);
  if (l > 4) *a4=PyTuple_GET_ITEM(args, 4);
  if (l > 5) *a5=PyTuple_GET_ITEM(args, 5);
  return 0;
}



/*
** Structures 
*/

typedef struct {
	PyObject_HEAD
} ZopeSecurityPolicy;

typedef struct {
	PyObject_HEAD
        PyObject *thread_id;
        PyObject *context;
        PyObject *policy;
        PyObject *validate;
        PyObject *checkPermission;
} SecurityManager;

typedef struct {
	PyObject_HEAD
	PyObject *__name__;
	PyObject *_p;
	PyObject *__roles__;
} PermissionRole;

typedef struct {
	PyObject_HEAD
	PyObject *_p;
	PyObject *_pa;
	PyObject *__roles__;
	PyObject *_v;
} imPermissionRole;

/*
** Prototypes
*/

static PyObject *ZopeSecurityPolicy_validate(PyObject *self, PyObject *args);
static void ZopeSecurityPolicy_dealloc(ZopeSecurityPolicy *self);


static PyObject *PermissionRole_init(PermissionRole *self, PyObject *args);
static PyObject *PermissionRole_of(PermissionRole *self, PyObject *parent);
static PyObject *
PermissionRole_rolesForPermissionOn(PermissionRole *self, PyObject *value);
static void PermissionRole_dealloc(PermissionRole *self);

static PyObject *PermissionRole_getattro(PermissionRole *self, PyObject *name);

static PyObject *imPermissionRole_of(imPermissionRole *self, PyObject *parent);
static Py_ssize_t imPermissionRole_length(imPermissionRole *self);
static PyObject *imPermissionRole_get(imPermissionRole *self,
	Py_ssize_t item);
static void imPermissionRole_dealloc(imPermissionRole *self);

static PyObject *rolesForPermissionOn(PyObject *self, PyObject *args);
static PyObject *module_guarded_getattr(PyObject *self, PyObject *args);
static PyObject *module_aq_validate(PyObject *self, PyObject *args);
static PyObject *module_setDefaultBehaviors(PyObject *self, PyObject *args);
static PyObject *c_rolesForPermissionOn(PyObject *self, PyObject *perm,
                                        PyObject *object, PyObject *deflt);

static PyObject *permissionName(PyObject *name);

static PyObject *SecurityManager_validate(SecurityManager *self, 
                                          PyObject *args);
static PyObject *SecurityManager_DTMLValidate(SecurityManager *self,
                                              PyObject *args);
static PyObject *SecurityManager_checkPermission(SecurityManager *self, 
                                                 PyObject *args);
static void SecurityManager_dealloc(SecurityManager *self);
static PyObject *SecurityManager_getattro(SecurityManager *self, 
                                          PyObject *name);
static int SecurityManager_setattro(SecurityManager *self, 
                                    PyObject *name, PyObject *value);

static getattrofunc ExtensionClassGetattro;


/*
** Constants
*/

static PyMethodDef cAccessControl_methods[] = {
	{"rolesForPermissionOn", 
		(PyCFunction)rolesForPermissionOn,
		METH_VARARGS,
		""
	},
        {"guarded_getattr", 
		(PyCFunction)module_guarded_getattr,
		METH_VARARGS,
		""
        },               
        {"aq_validate", 
		(PyCFunction)module_aq_validate,
		METH_VARARGS,
		""
        },
	{"setDefaultBehaviors",
		(PyCFunction)module_setDefaultBehaviors,
		METH_VARARGS,
		""
	},
	{ NULL, NULL }
};

static char ZopeSecurityPolicy__doc__[] = "ZopeSecurityPolicy C implementation";

static PyMethodDef ZopeSecurityPolicy_methods[] = {
	{"validate",
		(PyCFunction)ZopeSecurityPolicy_validate,
		METH_VARARGS,
		""
	},
	{ NULL, NULL }
};

static PyExtensionClass ZopeSecurityPolicyType = {
	PyObject_HEAD_INIT(NULL) 0,
	"ZopeSecurityPolicy",			/* tp_name	*/
	sizeof(ZopeSecurityPolicy),		/* tp_basicsize	*/
	0,					/* tp_itemsize	*/
	/* Standard methods 	*/
	(destructor) ZopeSecurityPolicy_dealloc,/* tp_dealloc	*/
	NULL,					/* tp_print	*/
	NULL,					/* tp_getattr	*/
	NULL,					/* tp_setattr	*/
	NULL,					/* tp_compare	*/
	NULL,					/* tp_repr	*/
	/* Method suites	*/
	NULL,					/* tp_as_number	*/
	NULL,					/* tp_as_sequence*/
	NULL,					/* tp_as_mapping */
	/* More standard ops  	*/
	NULL,					/* tp_hash	*/
	NULL,					/* tp_call	*/
	NULL,					/* tp_str	*/
	NULL,					/* tp_getattro	*/
	NULL,					/* tp_setattro	*/
	/* Reserved fields	*/
	0,					/* tp_xxx3	*/
	0,					/* tp_xxx4	*/
	/* Docstring		*/
	ZopeSecurityPolicy__doc__,		/* tp_doc	*/
#ifdef COUNT_ALLOCS
	0,					/* tp_alloc	*/
	0,					/* tp_free	*/
	0,					/* tp_maxalloc	*/
	NULL,					/* tp_next	*/
#endif
	METHOD_CHAIN(ZopeSecurityPolicy_methods),/* methods	*/
	(void *)(EXTENSIONCLASS_BINDABLE_FLAG),		/* flags	*/
};


static char SecurityManager__doc__[] = "ZopeSecurityPolicy C implementation";

static PyMethodDef SecurityManager_methods[] = {
	{"validate",
		(PyCFunction)SecurityManager_validate,
		METH_VARARGS,
		""
	},
	{"DTMLValidate",
		(PyCFunction)SecurityManager_DTMLValidate,
		METH_VARARGS,
		""
	},
	{"checkPermission",
		(PyCFunction)SecurityManager_checkPermission,
		METH_VARARGS,
		""
	},
	{ NULL, NULL }
};

static PyExtensionClass SecurityManagerType = {
	PyObject_HEAD_INIT(NULL) 0,
	"SecurityManager",			/* tp_name	*/
	sizeof(SecurityManager),		/* tp_basicsize	*/
	0,					/* tp_itemsize	*/
	/* Standard methods 	*/
	(destructor) SecurityManager_dealloc,/* tp_dealloc	*/
	NULL,					/* tp_print	*/
	NULL,					/* tp_getattr	*/
	NULL,					/* tp_setattr	*/
	NULL,					/* tp_compare	*/
	NULL,					/* tp_repr	*/
	/* Method suites	*/
	NULL,					/* tp_as_number	*/
	NULL,					/* tp_as_sequence*/
	NULL,					/* tp_as_mapping */
	/* More standard ops  	*/
	NULL,					/* tp_hash	*/
	NULL,					/* tp_call	*/
	NULL,					/* tp_str	*/
	(getattrofunc)SecurityManager_getattro,	/* tp_getattro	*/
	(setattrofunc)SecurityManager_setattro,	/* tp_setattro	*/
	/* Reserved fields	*/
	0,					/* tp_xxx3	*/
	0,					/* tp_xxx4	*/
	/* Docstring		*/
	SecurityManager__doc__,		/* tp_doc	*/
#ifdef COUNT_ALLOCS
	0,					/* tp_alloc	*/
	0,					/* tp_free	*/
	0,					/* tp_maxalloc	*/
	NULL,					/* tp_next	*/
#endif
	METHOD_CHAIN(SecurityManager_methods),	/* methods	*/
	0,					/* flags	*/
};


static char PermissionRole__doc__[] = "PermissionRole C implementation";

static PyMethodDef PermissionRole_methods[] = {
	{"__init__",
		(PyCFunction)PermissionRole_init,
		METH_VARARGS,
		""
	},
	{"__of__",
		(PyCFunction)PermissionRole_of,
		METH_O,
		""
	},
	{"rolesForPermissionOn",
		(PyCFunction)PermissionRole_rolesForPermissionOn,
		METH_O,
		""
	},
	{ NULL, NULL }
};

static PyExtensionClass PermissionRoleType = {
	PyObject_HEAD_INIT(NULL) 0,
	"PermissionRole",			/* tp_name	*/
	sizeof(PermissionRole),			/* tp_basicsize	*/
	0,					/* tp_itemsize	*/
	/* Standard methods 	*/
	(destructor) PermissionRole_dealloc,	/* tp_dealloc	*/
	NULL,					/* tp_print	*/
	NULL,					/* tp_getattr	*/
	NULL,					/* tp_setattr	*/
	NULL,					/* tp_compare	*/
	NULL,					/* tp_repr	*/
	/* Method suites	*/
	NULL,					/* tp_as_number	*/
	NULL,					/* tp_as_sequence*/
	NULL,					/* tp_as_mapping */
	/* More standard ops  	*/
	NULL,					/* tp_hash	*/
	NULL,					/* tp_call	*/
	NULL,					/* tp_str	*/
	(getattrofunc) PermissionRole_getattro,	/* tp_getattro	*/
	NULL,					/* tp_setattro	*/
	/* Reserved fields	*/
	0,					/* tp_xxx3	*/
	0,					/* tp_xxx4	*/
	/* Docstring		*/
	PermissionRole__doc__,			/* tp_doc	*/
#ifdef COUNT_ALLOCS
	0,					/* tp_alloc	*/
	0,					/* tp_free	*/
	0,					/* tp_maxalloc	*/
	NULL,					/* tp_next	*/
#endif
	METHOD_CHAIN(PermissionRole_methods),	/* methods	*/
	(void *)(EXTENSIONCLASS_BINDABLE_FLAG)/*|
	EXTENSIONCLASS_INSTDICT_FLAG*/,		/* flags	*/
	NULL,					/* Class dict	*/
	0,					/* bases	*/
	NULL,					/* reserved	*/
};

static char imPermissionRole__doc__[] = "imPermissionRole C implementation";

static PyMethodDef imPermissionRole_methods[] = {
	{"__of__",
		(PyCFunction)imPermissionRole_of,
		METH_O,
		""
	},
	{"rolesForPermissionOn",
		(PyCFunction)imPermissionRole_of,
		METH_O,
		""
	},
	{ NULL, NULL }
};

static PySequenceMethods imSequenceMethods = {
	(lenfunc) imPermissionRole_length,	/* sq_length	*/
	(binaryfunc) NULL,			/* sq_concat	*/
	(ssizeargfunc) NULL,			/* sq_repeat	*/
	(ssizeargfunc) imPermissionRole_get,	/* sq_item	*/
	(ssizessizeargfunc) NULL,			/* sq_slice	*/
	(ssizeobjargproc)  NULL,			/* sq_ass_item	*/
	(ssizessizeobjargproc) NULL,		/* sq_ass_slice */
	(objobjproc) NULL,			/* sq_contains	*/
	(binaryfunc) NULL,			/* sq_inplace_concat */
	(ssizeargfunc) NULL			/* sq_inplace_repeat */
};

static PyExtensionClass imPermissionRoleType = {
	PyObject_HEAD_INIT(NULL) 0,
	"imPermissionRole",			/* tp_name	*/
	sizeof(imPermissionRole),		/* tp_basicsize	*/
	0,					/* tp_itemsize	*/
	/* Standard methods 	*/
	(destructor) imPermissionRole_dealloc,	/* tp_dealloc	*/
	NULL,					/* tp_print	*/
	NULL,					/* tp_getattr	*/
	NULL,	                                /* tp_setattr	*/
	NULL,					/* tp_compare	*/
	NULL,					/* tp_repr	*/
	/* Method suites	*/
	NULL,					/* tp_as_number	*/
	&imSequenceMethods,			/* tp_as_sequence*/
	NULL,			                /* tp_as_mapping */
	/* More standard ops  	*/
	NULL,					/* tp_hash	*/
	NULL,					/* tp_call	*/
	NULL,					/* tp_str	*/
	NULL,					/* tp_getattro	*/
	NULL,					/* tp_setattro	*/
	/* Reserved fields	*/
	0,					/* tp_xxx3	*/
	0,					/* tp_xxx4	*/
	/* Docstring		*/
	imPermissionRole__doc__,		/* tp_doc	*/
#ifdef COUNT_ALLOCS
	0,					/* tp_alloc	*/
	0,					/* tp_free	*/
	0,					/* tp_maxalloc	*/
	NULL,					/* tp_next	*/
#endif
	METHOD_CHAIN(imPermissionRole_methods), /* methods	*/
	(void *)(EXTENSIONCLASS_BINDABLE_FLAG),		/* flags	*/
};


/* --------------------------------------------------------------
** STATIC OBJECTS
** --------------------------------------------------------------
*/

static PyObject *Containers = NULL;
static PyObject *ContainerAssertions = NULL;
static PyObject *Unauthorized = NULL;
static PyObject *warn= NULL;
static PyObject *NoSequenceFormat = NULL;
static PyObject *_what_not_even_god_should_do = NULL;
static PyObject *Anonymous = NULL;
static PyObject *AnonymousTuple = NULL;
static PyObject *ManagerTuple = NULL;
static PyObject *imPermissionRoleObj = NULL;
static PyObject *defaultPermission = NULL;
static PyObject *__roles__ = NULL;
static PyObject *__of__ = NULL;
static PyObject *__allow_access_to_unprotected_subobjects__ = NULL;
static PyObject *stack_str = NULL;
static PyObject *user_str = NULL;
static PyObject *validate_str = NULL;
static PyObject *_proxy_roles_str = NULL;
static PyObject *allowed_str = NULL;
static PyObject *getOwner_str = NULL;
static PyObject *getPhysicalRoot_str = NULL;
static PyObject *checkPermission_str = NULL;
static PyObject *getSecurityManager = NULL;
static PyObject *unrestrictedTraverse_str = NULL;
static PyObject *aq_validate = NULL;
static PyObject *aq_parent_str = NULL;
static PyObject *_check_context_str = NULL;
static PyObject *getRoles = NULL;
static PyObject *getWrappedOwner_str = NULL;

static int ownerous = 1;
static int authenticated = 1;

/* --------------------------------------------------------------
** ZopeSecurityPolicy Methods
** --------------------------------------------------------------
*/

/* ZopeSecurityPolicy_setup
**
** Setup for ZopeSecurityPolicy -- load all necessary objects from
** elsewhere... (e.g. imports)
*/

static int 
ZopeSecurityPolicy_setup(void) {
        UNLESS (NoSequenceFormat = PyString_FromString(
                    "'%s' passed as roles"
                    " during validation of '%s' is not a sequence."
                    )) return -1;

	UNLESS (defaultPermission = Py_BuildValue("(s)", "Manager")) return -1;
	UNLESS (_what_not_even_god_should_do = Py_BuildValue("[]")) return -1;
	UNLESS (__roles__ = PyString_FromString("__roles__")) return -1;
	UNLESS (__of__ = PyString_FromString("__of__")) return -1;
	UNLESS (Anonymous = PyString_FromString("Anonymous")) return -1;
	UNLESS (AnonymousTuple = Py_BuildValue("(O)", Anonymous)) return -1;
	UNLESS (ManagerTuple = Py_BuildValue("(s)", "Manager")) return -1;
	UNLESS (stack_str = PyString_FromString("stack")) return -1;
	UNLESS (user_str = PyString_FromString("user")) return -1;
	UNLESS (validate_str = PyString_FromString("validate")) return -1;
	UNLESS (_proxy_roles_str = PyString_FromString("_proxy_roles"))
          return -1;
	UNLESS (allowed_str = PyString_FromString("allowed")) return -1;
	UNLESS (getOwner_str = PyString_FromString("getOwner")) return -1;
	UNLESS (getWrappedOwner_str = PyString_FromString("getWrappedOwner")) 
	  return -1;
	UNLESS (getPhysicalRoot_str = PyString_FromString("getPhysicalRoot")) 
	  return -1;
	UNLESS (aq_parent_str = PyString_FromString("aq_parent")) return -1;
	UNLESS (_check_context_str = PyString_FromString("_check_context")) 
	  return -1;
	UNLESS (unrestrictedTraverse_str = PyString_FromString(
					   "unrestrictedTraverse")) 
	  return -1;

	UNLESS (checkPermission_str = PyString_FromString("checkPermission")) 
          return -1;
        UNLESS (__allow_access_to_unprotected_subobjects__ = 
                PyString_FromString(
                "__allow_access_to_unprotected_subobjects__"))
          return -1;

	return 0;
}

/*
** unauthErr
**
** Generate the unauthorized error 
*/ 

static void unauthErr(PyObject *name, PyObject *value) {

        PyObject *v;

        if ((v=Py_BuildValue("OO", name, value)))
          {
            PyErr_SetObject(Unauthorized, v);
            Py_DECREF(v);
          }
}

/*
** ZopeSecurityPolicy_validate
*/

static PyObject *ZopeSecurityPolicy_validate(PyObject *self, PyObject *args) {
	PyObject *accessed = NULL;  /* Note: accessed is not used. */
	PyObject *container = NULL;
	PyObject *name = NULL;
	PyObject *value = NULL;
	PyObject *context = NULL;
	PyObject *roles = NULL;	
        /* Import from SimpleObject Policy._noroles */
        /* Note that _noroles means missing roles, spelled with a NULL in C.
           Jim. */
	PyObject *containerbase = NULL;
	PyObject *accessedbase = NULL;
	PyObject *p = NULL;
	PyObject *rval = NULL;
	PyObject *stack = NULL;
	PyObject *user = NULL;

	PyObject *method = NULL;
	PyObject *tmp = NULL;


        int i, l, contains;
        PyObject *r;

	/*| def validate(self, accessed, container, name, value, context
	**|	roles=_noroles ...
	*/

	if (unpacktuple6(args, "validate", 5, &accessed, &container,
                         &name, &value, &context, &roles) < 0) 
          return NULL;

	/*| # Provide special rules for acquisition attributes
	**| if type(name) in (StringType, UnicodeType):
	**|     if name[:3] == 'aq_' and name not in valid_aq_:
	**|	   raise Unauthorized(name, value)
	*/ 

	if (PyString_Check(name) || PyUnicode_Check(name)) {
	    char *sname = PyString_AsString(name);
	    /* Conversion to string may have failed, e.g. if name is Unicode
	     * and can't be bashed into the default encoding.  Unclear what
	     * to do then.  It's arguably conservative to raise Unauthorized
	     * in this case.
	     */
	    if (sname == NULL || 
     	            /* or starts with "aq_" */
     	            (sname[0] == 'a' && sname[1] == 'q' && sname[2] == '_' &&
     	                 /* and isn't aq_{parent, inner, explicit} */
     	                 strcmp(sname + 3, "parent") &&
     	                 strcmp(sname + 3, "inner") &&
     	                 strcmp(sname + 3, "explicit")
     	            )
     	        )
     	    {
                /* Access control violation */
		unauthErr(name, value);
		return NULL;  /* roles is not owned yet */
	    }
	}
	Py_XINCREF(roles);	/* Convert the borrowed ref to a real one */

	/*| containerbase = aq_base(container)
	**| accessedbase = aq_base(accessed)
	**| if accessedbase is accessed:
        **|     # accessed is not a wrapper, so assume that the
        **|     # value could not have been acquired.
	**|     accessedbase = container
	*/

	containerbase = aq_base(container);
	if (containerbase == NULL) goto err;
	
	if (aq_isWrapper(accessed))
		accessedbase = aq_base(accessed);
	else {
		Py_INCREF(container);
		accessedbase = container;
	}

	/*| # If roles weren't passed in, we'll try to get them from
	**| # the object
	**|
	**| if roles is _noroles:
	**|    roles = getRoles(container, name, value, _noroles)
	*/

        if (roles == NULL) {
	  roles = callfunction4(getRoles, container, name, value, getRoles);
	  if (roles == getRoles) {
	    Py_DECREF(roles);
            roles = NULL;
	  }
          if (roles == NULL)
            PyErr_Clear();
	}

	/*| # We still might not have any roles
	**| 
	**| if roles is _noroles:
	*/

	if (roles == NULL) {

		/*| # We have an object without roles and we didn't get
		**| # a list of roles passed in.  Presumably, the value
		**| # is some simple object like a string or a list.
		**| # We'll try to get roles from it's container
		**|
		**| if container is None: raise Unauthorized(name, value)
		*/

		if (container == Py_None)  {
			unauthErr(name, value);
			goto err;
		}

		/*| roles = getattr(container, "__roles__", _noroles)
		**| if roles is _noroles:
		**|    if containerbase is container:
                **|       # Container is not wrapped.
		**|       if containerbase is not accessedbase:
                **|           raise Unauthorized(name, value)
		**|    else:
		**|       # Try to acquire roles
		**|      try: roles = container.aq_aquire('__roles__')
		**|      except AttributeError:
		**|         if containerbase is not accessedbase:
                **|             raise Unauthorized(name, value)
		*/

                roles = PyObject_GetAttr(container, __roles__);
		if (roles == NULL) {
			PyErr_Clear();

			if (!aq_isWrapper(container)) {
				if (containerbase != accessedbase)  {
				  unauthErr(name, value);
				  goto err;
				}
			} 
                        else {
				roles = aq_acquire(container, __roles__);
				if (roles == NULL) {
                                  if (PyErr_ExceptionMatches(
                                      PyExc_AttributeError))
                                    {
                                        PyErr_Clear();
				        if (containerbase != accessedbase) {
					  unauthErr(name, value);
					  goto err;
					}
                                    }
                                  else
                                    goto err;
				}
			}

		}

		/*| # We need to make sure that we are allowed to get
		**| # unprotected attributes from the container.  We are
		**| # allowed for certain simple containers and if the
		**| # container says we can.  Simple containers may also
		**| # impose name restrictions.
		**|
		**| p = Containers(type(container), None)
		**| if p is None:
		**|    p = getattr(container,
		**|        "__allow_access_to_unprotected_subobjects__", None)
		*/

		p = callfunction2(Containers, OBJECT(container->ob_type),
                                  Py_None);
		if (p == NULL)
                  goto err;

		if (p == Py_None) {
                        ASSIGN(p, PyObject_GetAttr(container,
				__allow_access_to_unprotected_subobjects__));
			if (p == NULL) 
                          PyErr_Clear();
		}

		/*| if p is not None:
		**|    tp = type(p)
		**|    if tp is not IntType:
		**|       if tp is DictType:
                **|         if (isinstance(name, StringType) or
                **|             isinstance(name, UnicodeType)):
                **|             p=p.get(name, None)
                **|         else:
                **|             p = 1
		**|       else:
		**|          p = p(name, value)
		*/

		if (p) 
                  {
                    if (! PyInt_Check(p)) 
                      {
                        if (PyDict_Check(p)) 
                          {
                            if (PyString_Check(name) || PyUnicode_Check(name))
                              {
                                ASSIGN(p, PyObject_GetItem(p, name));
                                if (p == NULL)
                                  PyErr_Clear();
                              }
                            else
                              {
                                ASSIGN(p, PyInt_FromLong(1));
                                if (p == NULL)
                                  goto err;
                              }
                          } 
                        else 
                          {
                            ASSIGN(p, callfunction2(p, name, value));
                            if (p == NULL)
                              goto err;
                          }
                      }
                  }

		/*| if not p:
		**|     raise Unauthorized, cleanupName(name, value)
		*/
               
		if (p == NULL || ! PyObject_IsTrue(p)) {
                  Py_XDECREF(p);
                  unauthErr(name, value);
                  goto err;
		}
                else
                  Py_DECREF(p);

		/*| if roles is _noroles: return 1
		*/

		if (roles == NULL) {
			rval = PyInt_FromLong(1);
			goto err;
		}

		/*| # We are going to need a security-aware object to pass
		**| # to allowed().  We'll use the container
		**| 
		**| value = container
		*/

		value = container; 	/* Both are borrowed references */

	} /* if (roles == NULL) */

	/*| # Short-circuit tests if we can
	**| try:
	**|    if roles is None or 'Anonymous' in roles: return 1
	**| except TypeError:
	**|     LOG.warn('"%s' passed as roles"
	**|		" during validation of '%s' is not a sequence." % 
	**|		('roles', name))
	**|	raise
	*/

	if (roles == Py_None) {
		rval = PyInt_FromLong(1);
		goto err;
	}
        else
        {
          int i;
          i = PySequence_Contains(roles, Anonymous);
          if (i > 0)
            {
              rval = PyInt_FromLong(1);
              goto err;
            }
          else if (i < 0)
            { /* Error */
              PyObject *m, *t, *v, *tb;

              if (!PyErr_ExceptionMatches(PyExc_TypeError))
                goto err;
              PyErr_Fetch(&t, &v, &tb);
              
              m=PyObject_Repr(roles);
              if (m) ASSIGN(m, Py_BuildValue("OO", m, name));
              if (m) ASSIGN(m, PyString_Format(NoSequenceFormat, m));
              if (m) ASSIGN(m, PyObject_CallFunction(warn, "O", m));
              Py_XDECREF(m);
              PyErr_Restore(t, v, tb);
              goto err;
            }
        }

	/*| # Check executable security
	**| stack = context.stack
	**| if stack:
	*/

	stack = PyObject_GetAttr(context, stack_str);
	if (stack == NULL) goto err;

	if (PyObject_IsTrue(stack)) {
		PyObject *eo;
		PyObject *owner;
		PyObject *proxy_roles;

	/*|    eo = stack[-1]
	**|    # If the executable had an owner, can it execute?
	**|    owner = eo.getOwner()
	**|    if (owner is not None) and not owner.allowed(value, roles)
	**| 	  # We don't want someone to acquire if they can't 
	**|	  # get an unacquired!
	**|       raise Unauthorized, ('You are not authorized to'
	**|	      'access <em>%s</em>.' % cleanupName(name, value))
	*/

		eo = PySequence_GetItem(stack, -1);
		if (eo == NULL) goto err;

		if (ownerous) {	/* Tabbing not adjusted for diff reasons*/

                owner = PyObject_GetAttr(eo, getOwner_str);
                if (owner) ASSIGN(owner, PyObject_CallObject(owner, NULL));
                if (owner ==NULL) 
                  {
                    Py_DECREF(eo);
                    goto err;
                  }

		if (owner != Py_None) {
                  ASSIGN(owner,PyObject_GetAttr(owner, allowed_str));
                  if (owner)
                    ASSIGN(owner, callfunction2(owner, value, roles));
                  if (owner == NULL)
                    {
                      Py_DECREF(eo);
                      goto err;
                    }

                  if (! PyObject_IsTrue(owner))
                    {
                      Py_DECREF(owner);
                      Py_DECREF(eo);
                      unauthErr(name, value);
                      goto err;
                    }
		}
		Py_DECREF(owner);

		} /* End of if ownerous */

	/*|    # Proxy roles, which are a lot safer now
	**|    proxy_roles = getattr(eo, "_proxy_roles", None)
	**|    if proxy_roles:
	**|        # Verify that the owner actually can state the proxy role
	**|        # in the context of the accessed item; users in subfolders
	**|        # should not be able to use proxy roles to access items 
	**|        # above their subfolder!
	**|        owner = eo.getWrappedOwner()
	**|                        
	**|        if owner is not None:
        **|            if container is not containerbase:
	**|                if not owner._check_context(container):
	**|                    # container is higher up than the owner, 
	**|                    # deny access
	**|                    raise Unauthorized(name, value)
	**|
	**|        for r in proxy_roles:
	**|            if r in roles:
        **|                return 1
	**|
	**|        raise Unauthorized(name, value)
	*/
		proxy_roles = PyObject_GetAttr(eo, _proxy_roles_str);

		if (proxy_roles == NULL) 
                  {
		    Py_DECREF(eo);
                    PyErr_Clear();
                  }
                else if (PyObject_IsTrue(proxy_roles)) 
                  {

		    method = PyObject_GetAttr(eo, getWrappedOwner_str);
		    if (method == NULL) {
		      Py_DECREF(eo);
		      Py_DECREF(proxy_roles);
		      goto err;
		    }

		    owner = PyObject_CallObject(method, NULL);
		    Py_DECREF(method);
		    if (owner == NULL) {
		      Py_DECREF(eo);
		      Py_DECREF(proxy_roles);
		      goto err;
		    }

		    Py_DECREF(eo);

		    if (owner != Py_None) {

		      if (containerbase != container) {

			tmp = callmethod1(owner,_check_context_str,
					  container
					  );
			if (tmp == NULL) {
			  Py_DECREF(proxy_roles);
			  Py_DECREF(owner);
			  goto err;
			}

			if (!PyObject_IsTrue(tmp)) {
			  Py_DECREF(proxy_roles);
			  Py_DECREF(owner);
			  Py_DECREF(tmp);
			  unauthErr(name, value);
			  goto err;
			}
			Py_DECREF(tmp);
		      }

		      Py_DECREF(owner);
		    }


                    contains = 0;
                    if (PyTuple_Check(proxy_roles)) 
                      {
                        l=PyTuple_GET_SIZE(proxy_roles);
                        for (i=0; i < l; i++)
                          {
                            r=PyTuple_GET_ITEM(proxy_roles, i);
                            if ((contains = PySequence_Contains(roles, r)))
                              break;
                          }
                      }
                    else 
                      {
                        l=PySequence_Size(proxy_roles);
                        if (l < 0) contains = -1;
                        for (i=0; i < l; i++)
                          {
                            if ((r=PySequence_GetItem(proxy_roles, i)))
                              {
                                contains = PySequence_Contains(roles, r);
                                Py_DECREF(r);
                              }
                            else
                              contains = -1;
                            if (contains < 0)                          
                              break;
                          }
                      }
                    Py_DECREF(proxy_roles);

                    if (contains > 0)
                      rval = PyInt_FromLong(contains);
                    else if (contains == 0) {
		      unauthErr(name, value);
                    }
                    goto err;
                  }
                else {
                  Py_DECREF(eo);
                  Py_DECREF(proxy_roles);
                }
	} /* End of stack check */

	/*| try:
	**|    if context.user.allowed(value, roles): return 1
	**| except AttributeError: pass
	*/
	if (authenticated) { /* Authentication skip for public only access */
	user = PyObject_GetAttr(context, user_str);
        if (user) ASSIGN(user, PyObject_GetAttr(user, allowed_str));
        if (user == NULL)
          {
            if (PyErr_ExceptionMatches(PyExc_AttributeError))
              PyErr_Clear();
            else
              goto err;
          }
        else
          {
            ASSIGN(user, callfunction2(user, value, roles));
            if (user == NULL) goto err;
            if (PyObject_IsTrue(user))
              {
                rval = PyInt_FromLong(1);
                Py_DECREF(user);
                goto err;
              }
            Py_DECREF(user);
          }
        } /* End of authentiction skip for public only access */

	/*| raise Unauthorized(name, value)
	*/

        unauthErr(name, value);
  err:
	Py_XDECREF(containerbase);
	Py_XDECREF(accessedbase);
	Py_XDECREF(stack);
	Py_XDECREF(roles);

	return rval;
}


/*
** ZopeSecurityPolicy_dealloc
**
*/

static void ZopeSecurityPolicy_dealloc(ZopeSecurityPolicy *self) {

	Py_DECREF(self->ob_type);	/* Extensionclass init incref'd */
	PyObject_DEL(self);  
}




/* SecurityManager */

#define CHECK_SECURITY_MANAGER_STATE(self, R) \
  UNLESS (self->policy) { \
      PyErr_SetString(PyExc_AttributeError, "_policy"); return R; } \
  UNLESS (self->context) { \
      PyErr_SetString(PyExc_AttributeError, "_policy"); return R; }

#define GET_SECURITY_MANAGER_VALIDATE(self, R) \
  if (self->validate == NULL && \
      ((self->validate = PyObject_GetAttr(self->policy, validate_str)) \
        == NULL)) return R;


static PyObject *
SecurityManager_validate(SecurityManager *self, PyObject *args)
{
  PyObject *accessed=Py_None, *container=Py_None, *name=Py_None, 
    *value=Py_None, *roles=NULL;
  
  if (unpacktuple5(args, "validate", 0,
                       &accessed, &container, &name, &value, &roles) < 0)
    return NULL;

  CHECK_SECURITY_MANAGER_STATE(self, NULL);
  GET_SECURITY_MANAGER_VALIDATE(self, NULL);
  
  if (roles== NULL)
    return callfunction5(self->validate, 
                         accessed, container, name, value, self->context);
  return callfunction6(self->validate, 
                       accessed, container, name, value, self->context, roles);
}

static PyObject *
SecurityManager_DTMLValidate(SecurityManager *self, PyObject *args)
{
  PyObject *accessed=Py_None, *container=Py_None, *name=Py_None, 
    *value=Py_None, *md=NULL;
  
  if (unpacktuple5(args, "DTMLValidate", 0,
                   &accessed, &container, &name, &value, &md) < 0)
    return NULL;

  CHECK_SECURITY_MANAGER_STATE(self, NULL);
  GET_SECURITY_MANAGER_VALIDATE(self, NULL);
  
  return callfunction5(self->validate, 
                       accessed, container, name, value, self->context);
}

static PyObject *
SecurityManager_checkPermission(SecurityManager *self, PyObject *args)
{
  PyObject *permission, *object;
  
  if (unpacktuple2(args, "checkPermission", 2, &permission, &object) < 0)
    return NULL;

  CHECK_SECURITY_MANAGER_STATE(self, NULL);
  if (self->checkPermission == NULL && 
      ((self->checkPermission = PyObject_GetAttr(self->policy, 
                                                 checkPermission_str)) 
       == NULL)) return NULL;

  return callfunction3(self->checkPermission, 
                       permission, object, self->context);
}

static void 
SecurityManager_dealloc(SecurityManager *self)
{
  Py_XDECREF(self->thread_id);
  Py_XDECREF(self->context);
  Py_XDECREF(self->policy);
  Py_XDECREF(self->validate);
  Py_XDECREF(self->checkPermission);
  Py_DECREF(self->ob_type);	/* Extensionclass init incref'd */
  PyObject_DEL(self);  
}

static PyObject *
SecurityManager_getattro(SecurityManager *self, PyObject *name)
{
  if (PyString_Check(name) || PyUnicode_Check(name))  {
    char *name_s = PyString_AsString(name); 

    if (name_s == NULL)
        return NULL;

    if (name_s[0] == '_') {
      if (! strcmp(name_s, "_thread_id") && self->thread_id) {
          Py_INCREF(self->thread_id);
          return self->thread_id;
      }
      else if (! strcmp(name_s, "_context") && self->context) {
          Py_INCREF(self->context);
          return self->context;
      }
      else if (! strcmp(name_s, "_policy") && self->policy) {
          Py_INCREF(self->policy);
          return self->policy;
      }
    }
  }

  return Py_FindAttr(OBJECT(self), name);
}

static int 
SecurityManager_setattro(SecurityManager *self, PyObject *name, PyObject *v)
{
  if (PyString_Check(name) || PyUnicode_Check(name)) {
    char *name_s = PyString_AsString(name);

    if (name_s == NULL)
        return -1;

    if (name_s[0] == '_')
    {
      if (! strcmp(name_s, "_thread_id"))
        {
          Py_INCREF(v);
          ASSIGN(self->thread_id, v);
          return 0;
        }
      else if (! strcmp(name_s, "_context"))
        {
          Py_INCREF(v);
          ASSIGN(self->context, v);
          return 0;
        }
      else if (! strcmp(name_s, "_policy"))
        {
          Py_INCREF(v);
          ASSIGN(self->policy, v);
          if (self->validate)
            {
              Py_DECREF(self->validate);
              self->validate=0;
            }
          if (self->checkPermission)
            {
              Py_DECREF(self->checkPermission);
              self->checkPermission=0;
            }
          return 0;
        }
    }
  }

  PyErr_SetObject(PyExc_AttributeError, name);
  return -1;
}




/*
** PermissionRole_init
**
*/

static PyObject *PermissionRole_init(PermissionRole *self, PyObject *args) {

	PyObject *name = NULL;
	PyObject *deflt = NULL;

	/*|def __init__(self, name, default=('Manager',)):
	**|  self.__name__ = name
	**|  self._p = "_" + string.translate(name, name_trans) + "_Permission"
	**|  self._d = default
	*/ 

	if (unpacktuple2(args, "__init__", 1, &name, &deflt) < 0) return NULL;

	if (deflt == NULL) deflt = defaultPermission;

        UNLESS(self->_p = permissionName(name)) return NULL;

	self->__name__ = name;
	Py_INCREF(name);

	self->__roles__ = deflt;
	Py_INCREF(deflt);

	Py_INCREF(Py_None);
	return Py_None;
}

/*
    def __of__(self, parent):
*/
static PyObject *
PermissionRole_of(PermissionRole *self, PyObject *parent) {

	imPermissionRole *r = NULL;
	PyObject *_p = NULL;
	PyObject *result = NULL;

	/*| r = imPermissionRole()
	*/

        r = (imPermissionRole*)PyObject_CallObject(imPermissionRoleObj, NULL);
	if (r == NULL) return NULL;

	/*| r._p = self._p
	*/

	r->_p = self->_p;
	Py_INCREF(r->_p);

	/*| r._pa = parent
	*/

	r->_pa = parent;
	Py_INCREF(parent);
	
	/*| r._d = self._d
	*/

	r->__roles__ = self->__roles__;
	Py_INCREF(r->__roles__);


	/*| p = getattr(parent, 'aq_inner', None)
	**| if p is not None:
	**|	return r.__of__(p)
	**| else:
	**|	return r
	*/


	if (aq_isWrapper(parent)) {
		_p = aq_inner(parent);
		result = callmethod1(OBJECT(r), __of__, _p);
		Py_DECREF(_p);
		/* Dont need goto */
	} else {
		result = OBJECT(r);
		Py_INCREF(r);
	}

	Py_DECREF(r);

	return result;
}

/*
    def rolesForPermissionOn(self, value):
        return rolesForPermissionOn(None, value, self._d, self._p)
*/
static PyObject *
PermissionRole_rolesForPermissionOn(PermissionRole *self, PyObject *value)
{
  return c_rolesForPermissionOn(NULL, value, self->__roles__, self->_p);
}



/*
** PermissionRole_dealloc
**
*/

static void PermissionRole_dealloc(PermissionRole *self) {

	Py_XDECREF(self->__name__);

	Py_XDECREF(self->_p);

	Py_XDECREF(self->__roles__);

	Py_XDECREF(self->ob_type);	/* Extensionclass init incref'd */

	PyObject_DEL(self);  
}


/* for DocFinder */
/*
** PermissionRole_getattro
**
*/

static PyObject *
PermissionRole_getattro(PermissionRole *self, PyObject *name) {
  	PyObject  *result = NULL;
        char      *name_s = PyString_AsString(name);

	/* see whether we know the attribute */
	/* we support both the old "_d" (from the Python implementation)
	   and the new "__roles__"
	*/

    	if (name_s == NULL)
    		PyErr_Clear(); /* defer to ExtensionClassGetattro */
	else if (name_s[0] == '_') {
		if (! strcmp(name_s, "__name__")) 
			result = self->__name__;
		else if (! strcmp(name_s, "__roles__"))
			result = self->__roles__;
		else if (! strcmp(name_s, "_p"))
			result = self->_p;
		else if (! strcmp(name_s, "_d"))
			result = self->__roles__;
	}

	if (result) {
		Py_INCREF(result);
		return result;
	}
	else
		return ExtensionClassGetattro((PyObject *)self, name);
}


/*
    def __of__(self, value):
        return rolesForPermissionOn(None, value, self._d, self._p)
*/
static PyObject *
imPermissionRole_of(imPermissionRole *self, PyObject *value) {
  return c_rolesForPermissionOn(NULL, value, self->__roles__, self->_p);
}

/*
** imPermissionRole_length
*/
static Py_ssize_t imPermissionRole_length(imPermissionRole *self) {

	Py_ssize_t l;
	PyObject *v;
	PyObject *pa;

	/*|
	**| try:
	**|     v=self._v
	**| except:
	**|     v = self._v = self.__of__(self._pa)
	**|     del self._pa
	**|
	**| return len(v)
	*/

	v = self->_v;
	if (v == NULL) {
		pa = self->_pa;
                if (pa == NULL) {
                  PyErr_SetString(PyExc_AttributeError, "_pa");
                  return -1;
                }
		v = callmethod1(OBJECT(self), __of__, pa);
                if (v == NULL)
                  return -1;
		self->_v = v;
		Py_DECREF(pa);
		self->_pa = NULL;
	}

	l = PyObject_Length(v);

	return l;
}

/*
** imPermissionRole_get
*/

static PyObject *imPermissionRole_get(imPermissionRole *self,
	Py_ssize_t item) {

	PyObject *v;
	PyObject *pa;
	PyObject *result;

	/*| try:
	**|	v = self._v
	**| except:
	**|	v = self._v = self.__of__(self._pa)
	**|	del self._pa
	**| return v[i]
	*/

	v = self->_v;

	if (v == NULL) {
                pa = self->_pa;
                if (pa == NULL) {
                  PyErr_SetString(PyExc_AttributeError, "_pa");
                  return NULL;
                }
                v = callmethod1(OBJECT(self), __of__, pa);
                if (v == NULL)
                  return NULL;
                self->_v = v;
                Py_DECREF(pa);
                self->_pa = NULL;
	}

	result = PySequence_GetItem(v, item);

	return result;
}

/*
** imPermissionRole_dealloc
**
*/

static void imPermissionRole_dealloc(imPermissionRole *self) {
	Py_XDECREF(self->_p);

	Py_XDECREF(self->_pa);

	Py_XDECREF(self->__roles__);

	Py_XDECREF(self->_v);

	Py_DECREF(self->ob_type);	/* Extensionclass init incref'd */

	PyObject_DEL(self);  
}

/*
** rolesForPermissionOn
*/ 

static PyObject *rolesForPermissionOn(PyObject *self, PyObject *args) {
	PyObject *perm = NULL;
	PyObject *object = NULL;
	PyObject *deflt = NULL;
	PyObject *n = NULL;

	/*|def rolesForPermissionOn(perm, object, default=('Manager',)):
	**|
	**| """Return the roles that have the permisson on the given object"""
	*/

	if (unpacktuple4(args, "rolesForPermissionOn", 2, 
                         &perm, &object, &deflt, &n) < 0)
		return NULL;
        return c_rolesForPermissionOn(perm, object, deflt, n);
}

/* 
def rolesForPermissionOn(perm, object, default=_default_roles, n=None):
    """Return the roles that have the given permission on the given object
    """
*/
static PyObject *
c_rolesForPermissionOn(PyObject *perm, PyObject *object, 
                       PyObject *_default_roles, PyObject *n)
{
  PyObject *r, *result = NULL;

  /*
    n = n or '_' + string.translate(perm, name_trans) + "_Permission"
  */
  if (n)
    Py_INCREF(n);
  else
    {
      n = permissionName(perm);
      if (n == NULL)
        return NULL;
    }

  Py_INCREF(object);

  /*
    r = None
  */
  r = Py_None;
  Py_INCREF(r);

  /*
    while 1:
  */
  while (1)
    {
      /*
        if hasattr(object, n):
            roles = getattr(object, n)
      */
      PyObject *roles = PyObject_GetAttr(object, n);
      if (roles != NULL)
        {

          /*
            if roles is None:
                return 'Anonymous',
           */
          if (roles == Py_None)
            {
              Py_DECREF(roles);
              result = AnonymousTuple;
              Py_INCREF(result);
              goto end;
            }

          /*
            t = type(roles)
           */
          /*
            if t is tuple:
                # If we get a tuple, then we don't acquire
                if r is None:
                    return roles
                return r+list(roles)
           */
          if (PyTuple_Check(roles))
            {
              if (r == Py_None)
                result = roles;
              else
                {
                  PyObject *list_roles = PySequence_List(roles);
                  Py_DECREF(roles);
                  if (list_roles == NULL)
                    goto end;
                  result = PySequence_Concat(r, list_roles);
                  Py_DECREF(list_roles);
                }
              goto end;
            }


          /*
            if t is str:
                # We found roles set to a name.  Start over
                # with the new permission name.  If the permission
                # name is '', then treat as private!
                if roles:
                    n = roles
                else:
                    return _what_not_even_god_should_do
           */
          if (PyString_Check(roles))
            {
              if (PyString_GET_SIZE(roles))
                {
                  Py_DECREF(n);
                  n = roles;
                }
              else
                {
                  Py_DECREF(roles);
                  result = _what_not_even_god_should_do;
                  Py_INCREF(result);
                  goto end;
                }
            }
          
          /*
            elif roles:
                if r is None:
                    r = list(roles)
                else: r = r + list(roles)
          */
          else 
  	    {
	      int bool = PyObject_IsTrue(roles);
	      if (bool < 0)
		  goto end;
	      if (bool)
	        {
		    PyObject *list_roles = PySequence_List(roles);
		    Py_DECREF(roles);
		    if (list_roles == NULL)
			goto end;
		    if (r == Py_None)
		      {
			  Py_DECREF(r);
			  r = list_roles;
		      }
		    else
		      {
			  PyObject *tmp = PySequence_Concat(r, list_roles);
			  Py_DECREF(list_roles);
			  if (tmp == NULL)
			      goto end;
			  Py_DECREF(r);
			  r = tmp;
		      }
		}
            }
        }

      else                      /* roles == NULL */
        PyErr_Clear();

      
      /*
        object = aq_inner(object)
        if object is None:
            break
        object = aq_parent(object)
       */
      {
        PyObject *tobj = aq_inner(object);
        if (tobj == NULL) 
          goto end;
        Py_DECREF(object);
        object = tobj;
        
        if (object == Py_None) 
          break;

        tobj = aq_parent(object);
        if (tobj == NULL) 
          goto end;
        Py_DECREF(object);
        object = tobj;
      }
    }

  /*
    if r is None:
        return default

    return r
  */

  if (r == Py_None)
    {
      result = _default_roles;
      if (result == NULL)
        result = ManagerTuple;
      Py_INCREF(result);
      goto end;
    }

  Py_INCREF(r);
  result = r;
   
 end:
  Py_DECREF(n);
  Py_DECREF(object);
  Py_DECREF(r);
  return result;
}  


/*
** permissionName
**
** Can silently truncate permission names if they are really long
*/

static PyObject *permissionName(PyObject *name) {
	char namebuff[512];
	register int len = sizeof(namebuff) - 1;
	char *c = namebuff;
	char *in;
	char r;

	*c = '_';

	c++;
	len--;

	in = PyString_AsString(name);
        if (in == NULL)
          return NULL;
	
	while (len && *in) {
		r = *(in++);
		if (!isalnum(r)) r='_';
		*(c++) = r;
		len--;
	}

	if (len) {
		in = "_Permission";
		while (len && *in) {
			*(c++) = *(in++);
			len--;
		}
	}

	*c = '\0';	/* Saved room in len */

	return PyString_FromString(namebuff);

}

/* def guarded_getattr(inst, name, default=_marker): */
static PyObject *
guarded_getattr(PyObject *inst, PyObject *name, PyObject *default_, 
                PyObject *validate)
{
  PyObject *v=0, *t=0;
  int i;

  /* if name[:1] != '_': */
  if (PyString_Check(name) || PyUnicode_Check(name)) {
    char *name_s = PyString_AsString(name);

    if (name_s == NULL)
        return NULL;

    if (name_s[0] != '_')
    {

      /*
        # Try to get the attribute normally so that unusual
        # exceptions are caught early.
        try: v = getattr(inst, name)
        except AttributeError:
            if default is not _marker:
                return default
            raise
       */

      v=PyObject_GetAttr(inst, name);
      if (v==NULL)
        {
          if (default_ && PyErr_Occurred() == PyExc_AttributeError)
            {
              PyErr_Clear();
              Py_INCREF(default_);
              return default_;
            }
          return NULL;
        }

      /*

        assertion = Containers(type(inst))
      */
      t = PyDict_GetItem(ContainerAssertions, OBJECT(inst->ob_type));
      if (t != NULL)
        {

      /*
        if isinstance(assertion, dict):
            # We got a table that lets us reason about individual
            # attrs
            assertion = assertion.get(name)
            if assertion:
                # There's an entry, but it may be a function.
                if callable(assertion):
                    return assertion(inst, name)

                # Nope, it's boolean
                return v
            raise Unauthorized, name
      */
          if (PyDict_Check(t))
            {
              PyObject *attrv;
              
              attrv = PyDict_GetItem(t, name);
              if (attrv != NULL)
                {
                  i=PyObject_IsTrue(attrv);
                  if (i < 0) goto err;
                  if (i) 
                    {
                      if (attrv->ob_type->tp_call)
                        {
                          Py_DECREF(v);
                          v = callfunction2(attrv, inst, name);
                          return v;
                        }
                      return v;
                    }
                }
              Py_DECREF(v);
              goto unauth;
            }

      /*
        if assertion:
            if callable(assertion):
                factory = assertion(name, v)
                if callable(factory):
                    return factory(inst, name)
                assert factory == 1
            assert callable == 1
            return v

      */
          if (PyCallable_Check(t))
            {
              PyObject *factory;

              factory = callfunction2(t, name, v);
              if (factory == NULL) 
                goto err;

              if (PyCallable_Check(factory))
                {
                  Py_DECREF(v);
                  v = callfunction2(factory, inst, name);
                }
              Py_DECREF(factory);
            }
          return v;
        }

      /* 
        # See if we can get the value doing a filtered acquire.
        # aq_acquire will either return the same value as held by
        # v or it will return an Unauthorized raised by validate.
        validate = SecurityManagement.getSecurityManager().validate
        aq_acquire(inst, name, aq_validate, validate)
        
        return v
      */

      t = aq_Acquire(inst, name, aq_validate, validate, 1, NULL, 0);
      if (t == NULL)
        {
        Py_DECREF(v);
        return NULL;
        }
      Py_DECREF(t);

      return v;
            
      unauthErr(name, v);
    err:
      Py_DECREF(v);
      return NULL;
    }
  }

 unauth:
  /* raise Unauthorized, name */
  PyErr_SetObject(Unauthorized, name);
  return NULL;
}

static PyObject *
module_guarded_getattr(PyObject *ignored, PyObject *args)
{
  PyObject *inst, *name, *default_=0, *validate;

  if (unpacktuple3(args, "guarded_getattr", 2, &inst, &name, &default_) < 0)
    return NULL;

  /*
        validate = getSecurityManager().validate
  */
  validate=PyObject_CallObject(getSecurityManager, NULL);
  if (! validate) return NULL;
  ASSIGN(validate, PyObject_GetAttr(validate, validate_str));
  if (! validate) return NULL;
  ASSIGN(validate, guarded_getattr(inst, name, default_, validate));

  return validate;
}

/*
    def aq_validate(inst, obj, name, v, validate):
        return validate(inst, obj, name, v)
 */
static PyObject *
module_aq_validate(PyObject *ignored, PyObject *args)
{
  PyObject *inst=NULL, *obj=NULL, *name=NULL, *v=NULL, *validate=NULL;

  if (unpacktuple5(args, "validate", 0,
                   &inst, &obj, &name, &v, &validate) < 0) return NULL;
  return callfunction4(validate, inst, obj, name, v);
}

static PyObject *
module_setDefaultBehaviors(PyObject *ignored, PyObject *args)
{
  PyObject *result = NULL;
  int own, auth, verbose;

  if (PyArg_ParseTuple(args, "iii:setDefaultBehaviors", &own, &auth,
                       &verbose)) {
    if (verbose) {
      PyErr_SetString(PyExc_NotImplementedError,
                      "This security policy implementation does not implement "
                      "the verbose option.  To enable verbose security "
                      "exceptions, add 'security-policy-implementation "
                      "python' to etc/zope.conf.");
      return NULL;
    }
    ownerous = own;
    authenticated = authenticated;
    result = Py_None;
    Py_INCREF(result);
  }
  return result;
}

static PyObject *
dtml_guarded_getattr(PyObject *self, PyObject *args)
{
  PyObject *ob, *name, *default_=0, *validate;

  if (unpacktuple3(args, "guarded_getattr", 2, &ob, &name, &default_) < 0)
    return NULL;

  
  UNLESS (validate = PyObject_GetAttr(self, validate_str)) 
    {
      /* This section is pure paranoia at this point. It was necessary
         while debugging. */
      PyErr_Clear();
      validate=PyObject_CallObject(getSecurityManager, NULL);
      if (! validate) return NULL;
      ASSIGN(validate, PyObject_GetAttr(validate, validate_str));
      if (! validate) return NULL;
    }

  ASSIGN(validate, guarded_getattr(ob, name, default_, validate));

  return validate;
}


static struct PyMethodDef dtml_methods[] = {
  {"guarded_getattr", (PyCFunction)dtml_guarded_getattr, 
   METH_VARARGS|METH_KEYWORDS, "" },
  {NULL,	NULL}
};


/* ----------------------------------------------------------------
** Module initialization
** ----------------------------------------------------------------
*/
#define IMPORT(module, name) if ((module = PyImport_ImportModule(name)) == NULL) return;
#define GETATTR(module, name) if ((name = PyObject_GetAttrString(module, #name)) == NULL) return;

void initcAccessControl(void) {
	PyObject *module;
	PyObject *dict;
        PURE_MIXIN_CLASS(RestrictedDTMLMixin,
                         "A mix-in for derivatives of DT_String.String "
                         "that adds Zope security."
                         , dtml_methods);

	if (!ExtensionClassImported) return;

	if (ZopeSecurityPolicy_setup() < 0) return;

	ExtensionClassGetattro= Py_FindAttr;

	module = Py_InitModule3("cAccessControl",
		cAccessControl_methods,
		"cAccessControl.c\n");

	aq_init(); /* For Python <= 2.1.1, aq_init() should be after
                      Py_InitModule(). */

	dict = PyModule_GetDict(module);

	PyDict_SetItemString(dict, "_what_not_even_god_should_do",
		_what_not_even_god_should_do);

        PyExtensionClass_Export(dict, "RestrictedDTMLMixin",
                                RestrictedDTMLMixinType);

	PyExtensionClass_Export(dict, "ZopeSecurityPolicy",
		ZopeSecurityPolicyType);

        PyExtensionClass_Export(dict,"SecurityManager",
                SecurityManagerType);

	PyExtensionClass_Export(dict, "PermissionRole",
		PermissionRoleType);

	PyExtensionClass_Export(dict, "imPermissionRole",
		imPermissionRoleType);

 	imPermissionRoleObj = PyMapping_GetItemString(dict, 
                                                      "imPermissionRole");

        aq_validate = PyMapping_GetItemString(dict, "aq_validate");

	/*| from SimpleObjectPolicies import Containers
	*/

	IMPORT(module, "AccessControl.SimpleObjectPolicies");
	GETATTR(module, Containers);
	GETATTR(module, ContainerAssertions);
	Py_DECREF(module);
	module = NULL;


	/*| from ZopeSecurityPolicy import getRoles
	*/

	IMPORT(module, "AccessControl.ZopeSecurityPolicy");
	GETATTR(module, getRoles);
	Py_DECREF(module);
	module = NULL;


	/*| from unauthorized import Unauthorized
	*/

	IMPORT(module, "AccessControl.unauthorized");
	GETATTR(module, Unauthorized);
	Py_DECREF(module);
	module = NULL;

	/*| from AccessControl.SecurityManagement import getSecurityManager
	*/

	IMPORT(module, "AccessControl.SecurityManagement");
	GETATTR(module, getSecurityManager);
	Py_DECREF(module);
	module = NULL;

	/*| from logger_wrapper import warn
	*/

	IMPORT(module, "AccessControl.logger_wrapper");
	GETATTR(module, warn);
	Py_DECREF(module);
	module = NULL;
}

