/*
**	cAccessControl.c
**
**	Access control acceleration routines

  Copyright (c) 2001, Digital Creations, Fredericksburg, VA, USA.  
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

  $Id: cAccessControl.c,v 1.6 2001/06/29 22:18:48 matt Exp $

  If you have questions regarding this software,
  contact:
 
    Digital Creations L.C.  
    info@digicool.com
 
    (540) 371-6909

*/

#include <stdio.h>

#include "ExtensionClass.h"

#define OBJECT(o) ((PyObject *) (o))

#ifdef win32
#define PUBLIC
#else
#define PUBLIC
#endif

/*
** Structures 
*/

typedef struct {
	PyObject_HEAD
} ZopeSecurityPolicy;

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
static PyObject *ZopeSecurityPolicy_checkPermission(PyObject *self,
	PyObject *args);
static void ZopeSecurityPolicy_dealloc(ZopeSecurityPolicy *self);


static PyObject *PermissionRole_getattr(PermissionRole *self, char *name);
static int PermissionRole_setattr(PermissionRole *self, char *name,
	PyObject *value);
static PyObject *PermissionRole_init(PermissionRole *self, PyObject *args);
static PyObject *PermissionRole_of(PermissionRole *self, PyObject *args);
static void PermissionRole_dealloc(PermissionRole *self);

static PyObject *imPermissionRole_getattr(imPermissionRole *self, char *name);
static int imPermissionRole_setattr(imPermissionRole *self, char *name,
	PyObject *value);
static PyObject *imPermissionRole_of(imPermissionRole *self, PyObject *args);
static int imPermissionRole_length(imPermissionRole *self);
static PyObject *imPermissionRole_getitem(imPermissionRole *self,
	PyObject *item);
static PyObject *imPermissionRole_get(imPermissionRole *self,
	int item);
static void imPermissionRole_dealloc(imPermissionRole *self);

static PyObject *rolesForPermissionOn(PyObject *self, PyObject *args);

static PyObject *permissionName(PyObject *name);
/*
** Constants
*/

static PyMethodDef cAccessControl_methods[] = {
	{"rolesForPermissionOn", 
		(PyCFunction)rolesForPermissionOn,
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
	{"checkPermission",
		(PyCFunction)ZopeSecurityPolicy_checkPermission,
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
	EXTENSIONCLASS_BINDABLE_FLAG,		/* flags	*/
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
		METH_VARARGS,
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
	(getattrfunc) PermissionRole_getattr,	/* tp_getattr	*/
	(setattrfunc) PermissionRole_setattr,	/* tp_setattr	*/
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
	PermissionRole__doc__,			/* tp_doc	*/
#ifdef COUNT_ALLOCS
	0,					/* tp_alloc	*/
	0,					/* tp_free	*/
	0,					/* tp_maxalloc	*/
	NULL,					/* tp_next	*/
#endif
	METHOD_CHAIN(PermissionRole_methods),	/* methods	*/
	EXTENSIONCLASS_BINDABLE_FLAG/*|
	EXTENSIONCLASS_INSTDICT_FLAG*/,		/* flags	*/
	NULL,					/* Class dict	*/
	NULL,					/* bases	*/
	NULL,					/* reserved	*/
};

static char imPermissionRole__doc__[] = "imPermissionRole C implementation";

static PyMethodDef imPermissionRole_methods[] = {
	{"__of__",
		(PyCFunction)imPermissionRole_of,
		METH_VARARGS,
		""
	},
	{ NULL, NULL }
};

static PySequenceMethods imSequenceMethods = {
	(inquiry) imPermissionRole_length,	/* sq_length	*/
	(binaryfunc) NULL,			/* sq_concat	*/
	(intargfunc) NULL,			/* sq_repeat	*/
	(intargfunc) imPermissionRole_get,	/* sq_item	*/
	(intintargfunc) NULL,			/* sq_slice	*/
	(intobjargproc)  NULL,			/* sq_ass_item	*/
	(intintobjargproc) NULL,		/* sq_ass_slice */
	(objobjproc) NULL,			/* sq_contains	*/
	(binaryfunc) NULL,			/* sq_inplace_concat */
	(intargfunc) NULL			/* sq_inplace_repeat */
};


static PyMappingMethods imMappingMethods = {
	(inquiry) imPermissionRole_length,	/* mp_length	*/
	(binaryfunc) imPermissionRole_getitem,	/* mp_subscript	*/
	(objobjargproc) NULL			/* mp_ass_subscr*/
};

static PyExtensionClass imPermissionRoleType = {
	PyObject_HEAD_INIT(NULL) 0,
	"imPermissionRole",			/* tp_name	*/
	sizeof(imPermissionRole),		/* tp_basicsize	*/
	0,					/* tp_itemsize	*/
	/* Standard methods 	*/
	(destructor) imPermissionRole_dealloc,	/* tp_dealloc	*/
	NULL,					/* tp_print	*/
	(getattrfunc) imPermissionRole_getattr,	/* tp_getattr	*/
	(setattrfunc) imPermissionRole_setattr,	/* tp_setattr	*/
	NULL,					/* tp_compare	*/
	NULL,					/* tp_repr	*/
	/* Method suites	*/
	NULL,					/* tp_as_number	*/
	&imSequenceMethods,			/* tp_as_sequence*/
	&imMappingMethods,			/* tp_as_mapping */
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
	EXTENSIONCLASS_BINDABLE_FLAG/*|
	EXTENSIONCLASS_INSTDICT_FLAG*/,		/* flags	*/
	NULL,					/* Class dict	*/
	NULL,					/* bases	*/
	NULL,					/* reserved	*/
};


/* --------------------------------------------------------------
** STATIC OBJECTS
** --------------------------------------------------------------
*/

static PyObject *Containers = NULL;
static PyObject *aq_base = NULL;
static PyObject *_noroles = NULL;
static PyObject *Unauthorized = NULL;
static PyObject *LOG = NULL;
static PyObject *PROBLEM = NULL;
static PyObject *_what_not_even_god_should_do = NULL;
static PyObject *Anonymous = NULL;
static PyObject *imPermissionRoleObj = NULL;
static PyObject *defaultPermission = NULL;

/* --------------------------------------------------------------
** ZopeSecurityPolicy Methods
** --------------------------------------------------------------
*/

/* ZopeSecurityPolicy_setup
**
** Setup for ZopeSecurityPolicy -- load all necessary objects from
** elsewhere... (e.g. imports)
*/

static int ZopeSecurityPolicy_setup(void) {
	PyObject *module;

#define IMPORT(module, name) if ((module = PyImport_ImportModule(name)) == NULL) Py_FatalError("ZopeSecurityPolicy failed to load module " #name)
#define GETATTR(module, name) if ((name = PyObject_GetAttrString(module, #name)) == NULL) Py_FatalError("ZopeSecurity policy failed to load attribute " #name)

	/*| from SimpleObjectPolicies import Containers, _noroles
	*/

	IMPORT(module, "AccessControl.SimpleObjectPolicies");
	GETATTR(module, Containers);
	GETATTR(module, _noroles);
	Py_DECREF(module);
	module = NULL;

	/*| from AccessControl import Unauthorized
	*/

	IMPORT(module, "AccessControl");
	GETATTR(module, Unauthorized);
	Py_DECREF(module);
	module = NULL;

	/*| from zLOG import LOG, PROBLEM
	*/

	IMPORT(module, "zLOG");
	GETATTR(module, LOG);
	GETATTR(module, PROBLEM);
	Py_DECREF(module);
	module = NULL;

	/*| from Acquisition import aq_base
	*/

	IMPORT(module,"Acquisition");
	GETATTR(module, aq_base);
	Py_DECREF(module);
	module = NULL;

	defaultPermission = Py_BuildValue("(s)", "Manager");
	_what_not_even_god_should_do = Py_BuildValue("[]");

	return 1;

}

/*
** unauthErr
**
** Generate the unauthorized error 
*/ 

static void unauthErr(PyObject *name, PyObject *value) {

	char msgbuff[512];
	PyObject *_name = NULL;
	PyObject *_name1 = NULL;
	char *s;

	/*| _name = name
	**| if _name is None and value is not None
	**|    try: _name = value.id
	**|    except:
	**|       try:
	**|          _name = value.__name__
	**|          except: pass
	**|    if callable(_name):
	**|       try: _name = _name()
	**|          except: pass
	**| return _name
	*/

	_name = name;
	Py_INCREF(_name);

	if (_name == Py_None && value != Py_None) {
		Py_DECREF(_name);
		_name = PyObject_GetAttrString(value,"id");
		if (_name == NULL) {
			PyErr_Clear();
			_name = PyObject_GetAttrString(value,"__name__");
		}
		
		if (_name != NULL && PyCallable_Check(_name)) {
			_name1 = PyObject_CallObject(_name, NULL);
			Py_DECREF(_name);
			_name = _name1;
		}
	}
	if (_name == NULL) {
		Py_INCREF(Py_None);
		_name = Py_None;
	}

	_name1 = PyObject_Str(_name);
	if (_name1 == NULL) s = "None";
	else s = PyString_AsString(_name1);

	snprintf(msgbuff,sizeof(msgbuff)-1,
		"You are not authorized to access <em>%s</em>.", s);

	Py_XDECREF(_name1);
	_name1 = PyString_FromString(msgbuff);

	PyErr_SetObject(Unauthorized, _name1);

	Py_DECREF(_name);
	Py_DECREF(_name1);
}


/*
** ZopeSecurityPolicy_validate
*/

static PyObject *ZopeSecurityPolicy_validate(PyObject *self, PyObject *args) {
	PyObject *accessed = NULL;
	PyObject *container = NULL;
	PyObject *name = NULL;
	PyObject *value = NULL;
	PyObject *context = NULL;
	PyObject *roles = NULL;	/* Import from SimpleObject Policy._noroles */
	PyObject *containerbase = NULL;
	PyObject *accessedbase = NULL;
	PyObject *p = NULL;
	PyObject *rval = NULL;
	PyObject *stack = NULL;
	PyObject *user = NULL;
	char *sname;


	/*| def validate(self, accessed, container, name, value, context
	**|	roles=_noroles ...
	*/

	if (!PyArg_ParseTuple(args, "OOOOO|O", &accessed, &container,
		&name, &value, &context, &roles)) return NULL;

	Py_XINCREF(roles);	/* Convert the borrowed ref to a real one */

	/*| # Provide special rules for acquisition attributes
	**| if type(name) is StringType:
	**|     if name[:3] == 'aq_' and name not in valid_aq_:
	**|	   return 0
	*/ 

	if (PyString_Check(name)) {		/* XXX what about unicode? */
		sname = PyString_AsString(name);
		if (strncmp(sname,"aq_", 4) == 0) {
			if (!strncmp(sname,"aq_parent", 10) &&
				!strncmp(sname,"aq_explicit", 12)) {
				/* Access control violation, return 0 */

				rval = PyInt_FromLong(0);
				goto err;
			}
		}
	}

	/*| containerbase = aq_base(container)
	**| accessedbase = getattr(accessed, 'aq_base', container)
	*/

	containerbase = PyObject_CallFunction(aq_base, "O", container);
	if (containerbase == NULL) goto err;
	
	accessedbase = PyObject_GetAttrString(accessed, "aq_base");
	if (accessedbase == NULL) {
		PyErr_Clear();
		Py_INCREF(container);
		accessedbase = container;
	}


	/*| # If roles weren't passed in, we'll try to get them from
	**| # the object
	**|
	**| if roles is _noroles:
	**|    roles = getattr(value, "__roles__", _noroles)
	*/

	if (roles == NULL || roles == _noroles) {
		Py_XDECREF(roles);
		roles = PyObject_GetAttrString(value, "__roles__");
		if (roles == NULL) {
			PyErr_Clear();
			Py_INCREF(_noroles);
			roles = _noroles;
		}
	}

	/*| # We still might not have any roles
	**| 
	**| if roles is _noroles:
	*/

	if (roles == _noroles) {

		/*| # We have an object without roles and we didn't get
		**| # a list of roles passed in.  Presumably, the value
		**| # is some simple object like a string or a list.
		**| # We'll try to get roles from it's container
		**|
		**| if container is None: return 0  # Bail if no container
		*/

		if (container == Py_None)  {
			rval= PyInt_FromLong(0);
			goto err;
		}

		/*| roles = getattr(container, "__roles__", _noroles)
		**| if roles is _noroles:
		**|    aq = getattr(container, 'aq_acquire', None)
		**|    if aq is None:
		**|       roles = _noroles
		**|       if containerbase is not accessedbase: return 0
		**|    else:
		**|       # Try to acquire roles
		**|      try: roles = aq('__roles__')
		**|      except AttributeError:
		**|	    roles = _noroles
		**|         if containerbase is not accessedbase: return 0
		*/

		Py_XDECREF(roles);

		roles = PyObject_GetAttrString(container, "__roles__");
		if (roles == NULL) {
			PyErr_Clear();
			Py_INCREF(_noroles);
			roles = _noroles;
		}

		if (roles == _noroles) {
			PyObject *aq;

			aq = PyObject_GetAttrString(container, "aq_acquire");
			if (aq == NULL) {
				PyErr_Clear();
				Py_DECREF(roles);
				if (containerbase != accessedbase)  {
					rval = PyInt_FromLong(0);
					goto err;
				}

				Py_INCREF(_noroles);
				roles = _noroles;
			} else {
				Py_DECREF(roles);
				roles = PyObject_CallFunction(aq, "s",
					"__roles__");
				Py_DECREF(aq); 
				aq = NULL;
				if (roles == NULL) {
					/* XXX not JUST AttributeError*/
					/* XXX should we clear the error? */
				        if (containerbase != accessedbase) {
						rval = PyInt_FromLong(0);
						goto err;
					}
					Py_INCREF(_noroles);
					roles = _noroles;
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

		/** XXX do we need to incref this stuff?  I dont think so */
		p = PyObject_CallFunction(Containers, "OO", 
			container->ob_type, Py_None);

		if (p == NULL)  goto err;

		if (p == Py_None) {
			Py_DECREF(p);
			p = PyObject_GetAttrString(container,
				"__allow_access_to_unprotected_subobjects__");
			if (p == NULL) {
				PyErr_Clear();
				Py_INCREF(Py_None);
				p = Py_None;
			}
		}

		/*| if p is not None:
		**|    tp = type(p)
		**|    if tp is not IntType:
		**|       if tp is DictType:
		**|          p = p.get(name, None)
		**|       else:
		**|          p = p(name, value)
		*/

		if (p != Py_None) {
			if (!PyInt_Check(p)) {
				PyObject *temp;
				if (PyDict_Check(p)) {
					temp = PyObject_GetItem(p, name);
					Py_DECREF(p);
					if (temp == NULL) {
						Py_INCREF(Py_None);
						p = Py_None;
					} else p = temp;
				} else {
					temp = PyObject_CallFunction(p,
						"OO", name, value);
					Py_DECREF(p);
					if (temp == NULL) {
						goto err;
					}
					p = temp;
				}
			}
		}

		/*| if not p:
		**|    if containerbase is accessedbase:
		**|	  raise Unauthorized, cleanupName(name, value)
		**|    else:
		**|       return 0
		*/

		if (p == NULL || !PyObject_IsTrue(p)) {
			Py_XDECREF(p);
			if (containerbase == accessedbase) {
				unauthErr(name, value);
				goto err;

			} else {
				rval = PyInt_FromLong(0);
				goto err;
			}
		}

		/*| if roles is _noroles: return 1
		*/

		if (roles == _noroles) {
			rval = PyInt_FromLong(1);
			goto err;
		}

		/*| # We are going to need a security-aware object to pass
		**| # to allowed().  We'll use the container
		**| 
		**| value = container
		*/

		value = container; 	/* Both are borrowed references */

	} /* if (roles == _noroles) */

	/*| # Short-circuit tests if we can
	**| try:
	**|    if roles is None or 'Anonymous' in roles: return 1
	**| except TypeError:
	**|     LOG("Zope Security Policy", PROBLEM, '"%s' passed as roles"
	**|		" during validation of '%s' is not a sequence." % 
	**|		('roles', name))
	**|	raise
	*/

	if (roles == Py_None) {
		rval = PyInt_FromLong(1);
		goto err;
	}

	if (!PySequence_Check(roles)) {
		char pbuff[512];
		PyObject *rolerepr = NULL;
		rolerepr = PyObject_Repr(roles);
		snprintf(pbuff, sizeof(pbuff)-1,
			"'%s' passed as roles during validation of '%s'"
			" is not a sequence.", PyString_AsString(rolerepr),
			PyString_AsString(name));
		Py_XDECREF(rolerepr);

		PyObject_CallFunction(LOG, "sOs", "Zope Security Policy",
			PROBLEM, pbuff);

		PyErr_SetObject(PyExc_TypeError, roles);
		goto err;
	} else {
		int i;
		int found = 0;
		int pl;
		PyObject *item;
		pl = PySequence_Length(roles);
		/* Iterate through the sequence looking for "Anonymous" */
		for (i = 0; i < pl; i++) {
			item = PySequence_GetItem(roles, i);
			if (PyString_Check(item)) { 	/* XXX No unicode */
				if (strncmp(PyString_AsString(item),
					"Anonymous", 10) == 0) found = 1;
			}
			Py_DECREF(item);
			if (found) {
				rval = PyInt_FromLong(1);
				goto err;
			}
		}
	}

	/*| # Check executable security
	**| stack = context.stack
	**| if stack:
	*/

	stack = PyObject_GetAttrString(context, "stack");
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
	**|	  if accessedbase is containerbase:
	**|	     raise Unauthorized, ('You are not authorized to'
	**|		'access <em>%s</em>.' % cleanupName(name, value))
	**|       return 0
	*/

		eo = PySequence_GetItem(stack, -1);
		if (eo == NULL) goto err;

		owner = PyObject_CallMethod(eo, "getOwner", NULL);
		if (owner == NULL) {
			Py_DECREF(eo);
			goto err;
		}

		if (owner != Py_None) {
			PyObject *allowed;
			allowed = PyObject_CallMethod(owner, "allowed", "OO",
				value, roles);
			if (allowed == NULL) {
				Py_DECREF(eo);
				Py_DECREF(owner);
				goto err;
			}
			if (!PyObject_IsTrue(allowed)) {

				Py_DECREF(allowed);
				Py_DECREF(owner);
				Py_DECREF(eo);
				if (accessedbase == containerbase) {
					unauthErr(name, value);
				} else rval = PyInt_FromLong(0);
				goto err;
			}
			Py_DECREF(allowed);
		}
		Py_DECREF(owner);

	/*|    # Proxy roles, which are a lot safer now
	**|    proxy_roles = getattr(eo, "_proxy_roles", None)
	**|    if proxy_roles:
	**|       for r in proxy_roles:
	**|          if r in roles: return 1
	**|
	**|       # proxy roles actually limit access!
	**|       if accessedbase is containerbase:
	**|	     raise Unauthorized, ('You are not authorized to access'
	**|		'<em>%s</em>.' % cleanupName(name, value))
	**|
	**|	  return 0
	*/
		proxy_roles = PyObject_GetAttrString(eo, "_proxy_roles");
		if (proxy_roles == NULL) {
			PyErr_Clear();
			Py_INCREF(Py_None);
			proxy_roles = Py_None;
		}

		if (PyObject_IsTrue(proxy_roles)) {
			int i;
			int j;
			int pl;
			int rl;
			int found = 0;
			PyObject *r;
			PyObject *r2;
			pl = PySequence_Length(proxy_roles);
			rl = PySequence_Length(roles);
			for (i = 0; !found && i < pl; i++) {
				r = PySequence_GetItem(proxy_roles, i);
				for (j = 0; !found && j < rl; j++) {
					r2 = PySequence_GetItem(roles, j);
					if (PyObject_Compare(r, r2) == 0)
						found=1;
					Py_DECREF(r2);
				}
				Py_DECREF(r);
			}
			if (found) {
				Py_DECREF(proxy_roles);
				Py_DECREF(eo);
				rval = PyInt_FromLong(1);
				goto err;
			}

			if (accessedbase == containerbase) {
				Py_DECREF(proxy_roles);
				Py_DECREF(eo);
				unauthErr(name, value);
				goto err;
			}

			Py_DECREF(proxy_roles);
			Py_DECREF(eo);
			rval = PyInt_FromLong(0);
			goto err;

		}

		Py_DECREF(proxy_roles);
		Py_DECREF(eo);
	} /* End of stack check */

	/*| try:
	**|    if context.user.allowed(value, roles): return 1
	**| except AttributeError: pass
	*/

	user = PyObject_GetAttrString(context, "user");
	if (user != NULL) {
		PyObject *allowed;
		allowed = PyObject_CallMethod(user, "allowed", "OO",
			value, roles);
		if (allowed != NULL) {
			if (PyObject_IsTrue(allowed)) {
				Py_DECREF(allowed);
				Py_DECREF(user);
				rval = PyInt_FromLong(1);
				goto err;
			}
			Py_DECREF(allowed);
		}
		Py_DECREF(user);
	} else {
		PyErr_Clear();
	}

	/*| # we don't want someone to acquire if they can't get an
	**| # unacquired!
	**| if accessedbase is containerbase:
	**|   raise Unauthorizied, ("You are not authorized to access"
	**|	 "<em>%s</em>." % cleanupName(name, value))
	**| return 0
	*/

	if (accessedbase == containerbase) {
		unauthErr(name, value);
		goto err;
	}

	rval = PyInt_FromLong(0);

	err:

	if (rval != NULL) PyErr_Clear();

	Py_XDECREF(stack);
	Py_XDECREF(roles);
	Py_XDECREF(containerbase);
	Py_XDECREF(accessedbase);

	return rval;
}


/*
** ZopeSecurityPolicy_checkPermission
**
*/

static PyObject *ZopeSecurityPolicy_checkPermission(PyObject *self,
	PyObject *args) {

	PyObject *permission = NULL;
	PyObject *object = NULL;
	PyObject *context = NULL;
	PyObject *roles;
	PyObject *result = NULL;
	PyObject *user;
	PyObject *arg;

	/*| def checkPermission(self, permission, object, context)
	*/

	if (!PyArg_ParseTuple(args, "OOO", &permission, &object, &context))
		return NULL;

	/*| roles = rolesForPermissionOn(permission, object)
	*/

	arg = Py_BuildValue("OO", permission, object);
	roles = rolesForPermissionOn(self, arg);
	Py_DECREF(arg);

	if (roles == NULL) return NULL;

	/*| if type(roles) is StringType:
	**|	roles = [roles]
	*/

	if (PyString_Check(roles)) {
		PyObject *r;
		r = Py_BuildValue("[O]", roles);
		Py_DECREF(roles);
		roles = r;
	}

	/*| return context.user.allowed(object, roles)
	*/

	user = PyObject_GetAttrString(context, "user");
	if (user != NULL) {
		result = PyObject_CallMethod(user,"allowed", "OO", object, roles);

		Py_DECREF(user);
	}

	Py_DECREF(roles);

	return result;
}

/*
** ZopeSecurityPolicy_dealloc
**
*/

static void ZopeSecurityPolicy_dealloc(ZopeSecurityPolicy *self) {
	PyMem_DEL(self);  
}

/*
** PermissionRole_getatro
*/

static PyObject *PermissionRole_getattr(PermissionRole *self, char *name) {

#define IZZIT(n) if (strcmp(#n, name) == 0) { Py_INCREF(self->n); return self->n; }
	IZZIT(__name__);
	IZZIT(_p);
	IZZIT(__roles__);

	return Py_FindAttrString(OBJECT(self), name);
}

/*
** PermissionRole_setattro
*/

static int PermissionRole_setattr(PermissionRole *self, char *name,
	PyObject *value) {

	PyObject *sname;

#define IZZITA(n) if (strcmp(#n, name) == 0) { Py_XDECREF(self->n); Py_INCREF(value); self->n = value; return 0; }

	IZZITA(__name__);
	IZZITA(_p);
	IZZITA(__roles__);

	sname = PyString_FromString(name);

	PyErr_SetObject(PyExc_AttributeError, sname);
	Py_DECREF(sname);
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

	if (!PyArg_ParseTuple(args, "O|O", &name, &deflt)) return NULL;

	if (deflt == NULL) deflt = defaultPermission;

	self->__name__ = name;
	Py_INCREF(name);

	self->_p = permissionName(name);

	self->__roles__ = deflt;
	Py_INCREF(deflt);

	Py_INCREF(Py_None);
	return Py_None;
}

/*
** PermissionRole_of
**
*/

static PyObject *PermissionRole_of(PermissionRole *self, PyObject *args) {

	PyObject *parent = NULL;
	imPermissionRole *r = NULL;
	PyObject *_p = NULL;
	PyObject *result = NULL;

	/*|def __of__(self, parent):
	*/

	if (!PyArg_ParseTuple(args,"O", &parent)) return NULL;

	/*| r = imPermissionRole()
	*/

	r = (imPermissionRole *) PyObject_CallObject(imPermissionRoleObj,NULL);
	if (r == NULL) return NULL;

	/*| r._p = self._p
	*/

	r->_p = self->_p;
	Py_INCREF(r->_p);

	/*| r._pa = parent
	*/

	r->_pa = parent;
	Py_INCREF(r->_pa);
	
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

	_p = PyObject_GetAttrString(parent, "aq_inner");

	if (_p) {
		result = PyObject_CallMethod(OBJECT(r),"__of__","O", _p);
		Py_DECREF(_p);
		/* Dont need goto */
	} else {
		result = OBJECT(r);
		Py_INCREF(r);
		PyErr_Clear();
	}

	Py_XDECREF(r);

	return result;
}

/*
** PermissionRole_dealloc
**
*/

static void PermissionRole_dealloc(PermissionRole *self) {

	Py_XDECREF(self->__name__);

	Py_XDECREF(self->_p);

	Py_XDECREF(self->__roles__);

	PyMem_DEL(self);  
}

/*
** imPermissionRole_getatro
*/

static PyObject *imPermissionRole_getattr(imPermissionRole *self, char *name) {

	IZZIT(_p);
	IZZIT(_pa);
	IZZIT(__roles__);
	IZZIT(_v);

	return Py_FindAttrString(OBJECT(self), name);
}

/*
** imPermissionRole_setattro
*/

static int imPermissionRole_setattr(imPermissionRole *self, char *name,
	PyObject *value) {

	PyObject *sname;

	IZZITA(_p);
	IZZITA(_pa);
	IZZITA(__roles__);
	IZZITA(_v);

	sname = PyString_FromString(name);

	PyErr_SetObject(PyExc_AttributeError, sname);
	Py_DECREF(sname);
	return -1;
}

/*
** imPermissionRole_of
**
*/

static PyObject *imPermissionRole_of(imPermissionRole *self, PyObject *args) {

	PyObject *parent = NULL;
	PyObject *obj = NULL;
	PyObject *n = NULL;
	PyObject *r = NULL;
	PyObject *roles = NULL;
	PyObject *result = NULL;
	PyObject *tobj = NULL;

	/*|def __of__(self, parent):
	**| obj = parent
	**| n = self._p
	**| r = None
	*/

	if (!PyArg_ParseTuple(args, "O", &parent)) return NULL;

	obj = parent;
	Py_INCREF(obj);

	n = self->_p;
	if (n == NULL) {
		PyErr_SetString(PyExc_AttributeError, "_p");
		goto err;
	}
	Py_INCREF(n);

	r = Py_None;
	Py_INCREF(r);
	
	/*| while 1:
	*/
	
	while (1) {

	/*|    if hasattr(obj, n):
	**|       roles = getattr(obj, n)   
	**|
	**|       if roles is None: return 'Anonymous', 
	*/

		roles = PyObject_GetAttr(obj, n);
		if (roles != NULL) {

			if (roles == Py_None) {
				result = Anonymous;
				Py_INCREF(result);
				goto err;
			}

		/*|
		**|	  t = type(roles)
		**|  
		**|	  if t is TupleType:
		**|          # If we get a tuple, then we don't acquire
		**|	     if r is None: return roles
		**|	     return r + list(roles)
		*/
			if (PyTuple_Check(roles)) {
				if (r == Py_None) {
					result = roles;
					roles = NULL;	/* avoid inc/decref */
					goto err;
				} else {
					PyObject *list;
					PyObject *cat;

					list = PySequence_List(roles);
					cat = PySequence_Concat(r, list);

					Py_DECREF(list);
					result = cat;
					goto err;
				}
			}
		
		/*|
		**|       if t is StringType:
		**|          # We found roles set to a name.  Start over
		**|	     # with the new permission name.  If the permission
		**|	     # name is '', then treat as private!
		*/

			if (PyString_Check(roles)) {

		/*|
		**|          if roles:
		**|             if roles != n:
		**|                n = roles
		**|             # If we find a name that is the same as the
		**|             # current name, we just ignore it.
		**|             roles = None
		**|          else:
		**|             return _what_not_even_god_should_do
		**|
		*/
				if (PyObject_IsTrue(roles)) {
					if (PyObject_Compare(roles, n))  {
						Py_DECREF(n);
						n = roles;
						Py_INCREF(n);
					}
					Py_DECREF(roles);
					roles = Py_None;
					Py_INCREF(roles);
				} else {
					result = _what_not_even_god_should_do;
					goto err;
				}
			} else {

		/*|       elif roles:
		**|          if r is None: r = list(roles)
		**|          else: r = r+list(roles)
		*/
				if (PyObject_IsTrue(roles)) {
					if (r == Py_None) {
						Py_DECREF(r);
						r = PySequence_List(roles);
					} else {
						PyObject *list;
						PyObject *cat;

						list = PySequence_List(roles);
						cat = PySequence_Concat(r,
							list);

						Py_DECREF(list);
						Py_DECREF(r);
						r = cat;
					}
				}
			}
		}

	/*|    obj = getattr(obj, 'aq_inner', None)
	**|    if obj is None: break
	**|    obj = obj.aq_parent
	*/

		tobj = PyObject_GetAttrString(obj, "aq_inner");
		if (tobj == NULL) break;
		Py_DECREF(obj);
		obj = tobj;

		if (obj == Py_None) break;
		tobj = PyObject_GetAttrString(obj, "aq_parent");
		if (tobj == NULL) goto err;
		Py_DECREF(obj);
		obj = tobj;
		
	}	/* end while 1 */

	/*|
	**| if r is None: r = self._d
	*/

	if (r == Py_None) {
		Py_DECREF(r);
		r = self->__roles__;
		if (r == NULL) goto err;
	}

	/*|
	**| return r
	*/

	result = r;
	Py_INCREF(result);

	err:

	Py_XDECREF(n);
	Py_XDECREF(r);
	Py_XDECREF(obj);
	Py_XDECREF(roles);

	return result;
}

/*
** imPermissionRole_length
*/

static int imPermissionRole_length(imPermissionRole *self) {

	int l;
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
		if (pa == NULL) return -1;

		v = PyObject_CallMethod(OBJECT(self), "__of__", 
			"O", pa);

		self->_v = v;

		Py_XDECREF(self->_pa);
		self->_pa = NULL;
	}

	l = PyObject_Length(v);

	return l;

}

/*
** imPermissionRole_getitem
*/

static PyObject *imPermissionRole_getitem(imPermissionRole *self,
	PyObject *item) {

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
		if (pa == NULL) return NULL;

		v = PyObject_CallMethod(OBJECT(self), "__of__", 
			"O", pa);

		self->_v = v;

		Py_XDECREF(self->_pa);
		self->_pa = NULL;
	}

	result = PyObject_GetItem(v, item);

	return result;
}

/*
** imPermissionRole_get
*/

static PyObject *imPermissionRole_get(imPermissionRole *self,
	int item) {

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
		if (pa == NULL) return NULL;

		v = PyObject_CallMethod(OBJECT(self), "__of__", 
			"O", pa);

		self->_v = v;

		Py_XDECREF(self->_pa);
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
	self->_p = NULL;

	Py_XDECREF(self->_pa);
	self->_pa = NULL;

	Py_XDECREF(self->__roles__);
	self->__roles__ = NULL;

	Py_XDECREF(self->_v);
	self->_v = NULL;

	PyMem_DEL(self);  
}

/*
** rolesForPermissionOn
*/ 

static PyObject *rolesForPermissionOn(PyObject *self, PyObject *args) {
	PyObject *perm = NULL;
	PyObject *object = NULL;
	PyObject *deflt = NULL;
	imPermissionRole *im = NULL;
	PyObject *result;

	/*|def rolesForPermissionOn(perm, object, default=('Manager',)):
	**|
	**| """Return the roles that have the permisson on the given object"""
	**|
	**| im = imPermissionRole()
	**|
	**| im._p="_"+string.translate(perm, name_trans)+"_Permission"
	**| im._d = default
	**| return im.__of__(object)
	*/

	if (!PyArg_ParseTuple(args, "OO|O", &perm, &object, &deflt))
		return NULL;

	im = (imPermissionRole *) PyObject_CallObject(imPermissionRoleObj,
		NULL);
	if (im == NULL) return NULL;

	im->_p = permissionName(perm);

	if (deflt == NULL) deflt = defaultPermission;

	im->__roles__ = deflt;

	Py_INCREF(deflt);

	result = PyObject_CallMethod(OBJECT(im), "__of__", "O", object);
	Py_DECREF(im);

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

/* ----------------------------------------------------------------
** Module initialization
** ----------------------------------------------------------------
*/

PUBLIC void initcAccessControl(void) {
	PyObject *module;
	PyObject *dict;
	char *rev = "$Revision: 1.6 $";

	if (!ExtensionClassImported) return;

	ZopeSecurityPolicyType.tp_getattro =
		(getattrofunc) PyExtensionClassCAPI->getattro;

	module = Py_InitModule4("cAccessControl",
		cAccessControl_methods,
		"$Id: %\n",
		OBJECT(NULL),
		PYTHON_API_VERSION);

	dict = PyModule_GetDict(module);

	ZopeSecurityPolicyType.ob_type = &PyType_Type;
	PyDict_SetItemString(dict, "ZopeSecurityPolicyType", 
		OBJECT(&ZopeSecurityPolicyType));

	PermissionRoleType.ob_type = &PyType_Type;
	PyDict_SetItemString(dict, "PermissionRoleType", 
		OBJECT(&PermissionRoleType));

	imPermissionRoleType.ob_type = &PyType_Type;
	PyDict_SetItemString(dict, "imPermissionRoleType", 
		OBJECT(&imPermissionRoleType));

	PyDict_SetItemString(dict, "__version__",
		PyString_FromStringAndSize(rev+11,strlen(rev+11)-2));

	if (!ZopeSecurityPolicy_setup()) {
		Py_FatalError("Can't initialize module cAccessControl "
			"-- dependancies failed to load.");
		return;
	}

	PyDict_SetItemString(dict, "_what_not_even_god_should_do",
		_what_not_even_god_should_do);

	PyExtensionClass_Export(dict, "ZopeSecurityPolicy",
		ZopeSecurityPolicyType);

	PyExtensionClass_Export(dict, "PermissionRole",
		PermissionRoleType);

	PyExtensionClass_Export(dict, "imPermissionRole",
		imPermissionRoleType);

	imPermissionRoleObj = PyDict_GetItemString(dict, "imPermissionRole");

	if (PyErr_Occurred())
		Py_FatalError("Can't initialize module cAccessControl");
}

