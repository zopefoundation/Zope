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

  $Id: cAccessControl.c,v 1.11 2001/10/19 15:12:25 shane Exp $

  If you have questions regarding this software,
  contact:
 
    Digital Creations L.C.  
    info@digicool.com
 
    (540) 371-6909

*/

#include <stdio.h>

#include "ExtensionClass.h"
#include "Acquisition.h"


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
callmethod1(PyObject *self, PyObject *name, PyObject *arg)
{
  UNLESS(self = PyObject_GetAttr(self,name)) return NULL;
  name = PyTuple_New(1);
  if (name == NULL) {
    Py_DECREF(self);
    return NULL;
  }
  Py_INCREF(arg);
  PyTuple_SET_ITEM(name, 0, arg);
  ASSIGN(self, PyObject_CallObject(self, name));
  Py_DECREF(name);
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


static PyObject *PermissionRole_init(PermissionRole *self, PyObject *args);
static PyObject *PermissionRole_of(PermissionRole *self, PyObject *args);
static void PermissionRole_dealloc(PermissionRole *self);

static PyObject *imPermissionRole_of(imPermissionRole *self, PyObject *args);
static int imPermissionRole_length(imPermissionRole *self);
static PyObject *imPermissionRole_get(imPermissionRole *self,
	int item);
static void imPermissionRole_dealloc(imPermissionRole *self);

static PyObject *rolesForPermissionOn(PyObject *self, PyObject *args);
static PyObject *c_rolesForPermissionOn(PyObject *self, PyObject *perm,
                                        PyObject *object, PyObject *deflt);

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
	EXTENSIONCLASS_BINDABLE_FLAG,		/* flags	*/
};


/* --------------------------------------------------------------
** STATIC OBJECTS
** --------------------------------------------------------------
*/

static PyObject *Containers = NULL;
static PyObject *Unauthorized = NULL;
static PyObject *LOG = NULL;
static PyObject *PROBLEM = NULL;
static PyObject *NoSequenceFormat = NULL;
static PyObject *_what_not_even_god_should_do = NULL;
static PyObject *Anonymous = NULL;
static PyObject *AnonymousTuple = NULL;
static PyObject *imPermissionRoleObj = NULL;
static PyObject *defaultPermission = NULL;
static PyObject *__roles__ = NULL;
static PyObject *__of__ = NULL;
static PyObject *__allow_access_to_unprotected_subobjects__ = NULL;
static PyObject *stack_str = NULL;
static PyObject *user_str = NULL;
static PyObject *_proxy_roles_str = NULL;
static PyObject *allowed_str = NULL;
static PyObject *getOwner_str = NULL;

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
	UNLESS (AnonymousTuple = Py_BuildValue("(s)", "Anonymous")) return -1;
	UNLESS (stack_str = PyString_FromString("stack")) return -1;
	UNLESS (user_str = PyString_FromString("user")) return -1;
	UNLESS (_proxy_roles_str = PyString_FromString("_proxy_roles"))
          return -1;
	UNLESS (allowed_str = PyString_FromString("allowed")) return -1;
	UNLESS (getOwner_str = PyString_FromString("getOwner")) return -1;
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
	PyObject *accessed = NULL;
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
	char *sname;


	/*| def validate(self, accessed, container, name, value, context
	**|	roles=_noroles ...
	*/

	if (!PyArg_ParseTuple(args, "OOOOO|O", &accessed, &container,
		&name, &value, &context, &roles)) return NULL;

	/*| # Provide special rules for acquisition attributes
	**| if type(name) is StringType:
	**|     if name[:3] == 'aq_' and name not in valid_aq_:
	**|	   return 0
	*/ 

	if (PyString_Check(name)) {		/* XXX what about unicode? */
		sname = PyString_AS_STRING(name);
		if (*sname == 'a' && sname[1]=='q' && sname[2]=='_') {
			if (strcmp(sname,"aq_parent")   != 0 &&
                            strcmp(sname,"aq_explicit") != 0) {
				/* Access control violation, return 0 */
				return PyInt_FromLong(0);
			}
		}
	}

	Py_XINCREF(roles);	/* Convert the borrowed ref to a real one */

	/*| containerbase = aq_base(container)
	**| accessedbase = getattr(accessed, 'aq_base', container)
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
	**|    roles = getattr(value, "__roles__", _noroles)
	*/

        if (roles == NULL) {
          roles = PyObject_GetAttr(value, __roles__);
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
                roles = PyObject_GetAttr(container, __roles__);
		if (roles == NULL) {
			PyErr_Clear();

			if (!aq_isWrapper(container)) {
				if (containerbase != accessedbase)  {
					rval = PyInt_FromLong(0);
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
						rval = PyInt_FromLong(0);
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

		/** XXX do we need to incref this stuff?  I dont think so */
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
		**|          p = p.get(name, None)
		**|       else:
		**|          p = p(name, value)
		*/

		if (p) {
			if (! PyInt_Check(p)) {
				if (PyDict_Check(p)) {
                                        ASSIGN(p, PyObject_GetItem(p, name));
                                        if (p == NULL)
                                          PyErr_Clear();
				} else {
                                  ASSIGN(p, callfunction2(p, name, value));
                                  if (p == NULL)
                                    goto err;
				}
			}
		}

		/*| if not p:
		**|    if containerbase is accessedbase:
		**|	  raise Unauthorized, cleanupName(name, value)
		**|    else:
		**|       return 0
		*/
               
		if (p == NULL || ! PyObject_IsTrue(p)) {
			Py_XDECREF(p);
			if (containerbase == accessedbase) {
				unauthErr(name, value);
				goto err;
			} else {
				rval = PyInt_FromLong(0);
				goto err;
			}
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
	**|     LOG("Zope Security Policy", PROBLEM, '"%s' passed as roles"
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
              if (m) ASSIGN(m, PyObject_CallFunction(LOG, "sOO",
                     "Zope Security Policy", PROBLEM, m)); 
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
	**|	  if accessedbase is containerbase:
	**|	     raise Unauthorized, ('You are not authorized to'
	**|		'access <em>%s</em>.' % cleanupName(name, value))
	**|       return 0
	*/

		eo = PySequence_GetItem(stack, -1);
		if (eo == NULL) goto err;

                owner = PyObject_GetAttr(eo, getOwner_str);
                if (owner) ASSIGN(owner, PyObject_CallObject(owner, NULL));
                if (owner ==NULL) 
                  {
                    Py_DECREF(eo);
                    goto err;
                  }

		if (owner != Py_None) {
                  owner = PyObject_GetAttr(owner, allowed_str);
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
                      if (accessedbase == containerbase) {
                        unauthErr(name, value);
                      } 
                      else rval = PyInt_FromLong(0);
                      goto err;
                    }
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
		proxy_roles = PyObject_GetAttr(eo, _proxy_roles_str);
                Py_DECREF(eo);
		if (proxy_roles == NULL) 
                  {
                    PyErr_Clear();
                  }
                else if (PyObject_IsTrue(proxy_roles)) 
                  {
                    int i, l, contains=0;
                    PyObject *r;
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
                      if (accessedbase == containerbase) {
                        unauthErr(name, value);
                      }
                      else rval = PyInt_FromLong(contains);
                    }
                    goto err;
                  }
                else 
                  Py_DECREF(proxy_roles);
	} /* End of stack check */

	/*| try:
	**|    if context.user.allowed(value, roles): return 1
	**| except AttributeError: pass
	*/
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

	/*| # we don't want someone to acquire if they can't get an
	**| # unacquired!
	**| if accessedbase is containerbase:
	**|   raise Unauthorizied, ("You are not authorized to access"
	**|	 "<em>%s</em>." % cleanupName(name, value))
	**| return 0
	*/


        if (accessedbase == containerbase) 
          unauthErr(name, value);
        else
          rval = PyInt_FromLong(0);        
  err:

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

	/*| def checkPermission(self, permission, object, context)
	*/

	if (!PyArg_ParseTuple(args, "OOO", &permission, &object, &context))
		return NULL;

	/*| roles = rolesForPermissionOn(permission, object)
	*/

	roles = c_rolesForPermissionOn(self, permission, object, OBJECT(NULL));
	if (roles == NULL)
          return NULL;

	/*| if type(roles) is StringType:
	**|	roles = [roles]
	*/

	if (PyString_Check(roles)) {
          PyObject *r;

          r = PyList_New(1);
          if (r == NULL) {
            Py_DECREF(roles);
            return NULL;
          }
          /* Note: ref to roles is passed to the list object. */
          PyList_SET_ITEM(r, 0, roles);
          roles = r;
	}

	/*| return context.user.allowed(object, roles)
	*/

	user = PyObject_GetAttr(context, user_str);
	if (user != NULL) {
          ASSIGN(user, PyObject_GetAttr(user, allowed_str));
          if (user != NULL) {
            result = callfunction2(user, object, roles);
            Py_DECREF(user);
          }
	}

	Py_DECREF(roles);

	return result;
}

/*
** ZopeSecurityPolicy_dealloc
**
*/

static void ZopeSecurityPolicy_dealloc(ZopeSecurityPolicy *self) {

	Py_DECREF(self->ob_type);	/* Extensionclass init incref'd */

	PyMem_DEL(self);  
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

        UNLESS(self->_p = permissionName(name)) return NULL;

	self->__name__ = name;
	Py_INCREF(name);

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
** PermissionRole_dealloc
**
*/

static void PermissionRole_dealloc(PermissionRole *self) {

	Py_DECREF(self->__name__);

	Py_DECREF(self->_p);

	Py_DECREF(self->__roles__);

	Py_DECREF(self->ob_type);	/* Extensionclass init incref'd */

	PyMem_DEL(self);  
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
                /* XXX Should not be possible */
		PyErr_SetString(PyExc_AttributeError, "_p");
                Py_DECREF(obj);
                return NULL;
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
				result = AnonymousTuple;
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
					list = PySequence_List(roles);
                                        if (list != NULL) {
                                          result = PySequence_Concat(r, list);
                                          Py_DECREF(list);
                                        }
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
                                  if (PyObject_Compare(roles, n) != 0)  {
                                    Py_DECREF(n);
                                    n = roles;
                                    Py_INCREF(n);
                                  }
                                  Py_DECREF(roles);
                                  roles = Py_None;
                                  Py_INCREF(roles);
				} else {
                                  result = _what_not_even_god_should_do;
                                  Py_INCREF(result);
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

                              list = PySequence_List(roles);
                              if (list != NULL) {
                                ASSIGN(r, PySequence_Concat(r, list));
                                Py_DECREF(list);
                                if (r == NULL)
                                  goto err;
                              }
                              else
                                goto err;
                            }
                          }
			}
		}
                else
                  PyErr_Clear();

	/*|    obj = getattr(obj, 'aq_inner', None)
	**|    if obj is None: break
	**|    obj = obj.aq_parent
	*/

		if (!aq_isWrapper(obj)) break;
		tobj = aq_inner(obj);
		if (tobj == NULL) goto err;
		Py_DECREF(obj);
		obj = tobj;

		if (obj == Py_None) break;
		if (!aq_isWrapper(obj)) break;
		tobj = aq_parent(obj);
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

	PyMem_DEL(self);  
}

/*
** rolesForPermissionOn
*/ 

static PyObject *rolesForPermissionOn(PyObject *self, PyObject *args) {
	PyObject *perm = NULL;
	PyObject *object = NULL;
	PyObject *deflt = NULL;

	/*|def rolesForPermissionOn(perm, object, default=('Manager',)):
	**|
	**| """Return the roles that have the permisson on the given object"""
	*/

	if (!PyArg_ParseTuple(args, "OO|O", &perm, &object, &deflt))
		return NULL;
        return c_rolesForPermissionOn(self, perm, object, deflt);
}


static PyObject *
c_rolesForPermissionOn(PyObject *self, PyObject *perm, PyObject *object,
                       PyObject *deflt) {
	imPermissionRole *im = NULL;
	PyObject *result;

	/*| im = imPermissionRole()
	**|
	**| im._p="_"+string.translate(perm, name_trans)+"_Permission"
	**| im._d = default
	**| return im.__of__(object)
	*/

        im = (imPermissionRole*)PyObject_CallObject(imPermissionRoleObj, NULL);
	if (im == NULL)
          return NULL;

	im->_p = permissionName(perm);
        if (im->_p == NULL) {
          Py_DECREF(im);
          return NULL;
        }

	if (deflt == NULL) deflt = defaultPermission;
	im->__roles__ = deflt;
	Py_INCREF(deflt);

	result = callmethod1(OBJECT(im), __of__, object);
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

/* ----------------------------------------------------------------
** Module initialization
** ----------------------------------------------------------------
*/
#define IMPORT(module, name) if ((module = PyImport_ImportModule(name)) == NULL) return;
#define GETATTR(module, name) if ((name = PyObject_GetAttrString(module, #name)) == NULL) return;

void initcAccessControl(void) {
	PyObject *module;
	PyObject *dict;
	char *rev = "$Revision: 1.11 $";

	if (!ExtensionClassImported) return;

	if (ZopeSecurityPolicy_setup() < 0) return;

	ZopeSecurityPolicyType.tp_getattro =
		(getattrofunc) PyExtensionClassCAPI->getattro;

	PermissionRoleType.tp_getattro =
		(getattrofunc) PyExtensionClassCAPI->getattro;

	imPermissionRoleType.tp_getattro =
		(getattrofunc) PyExtensionClassCAPI->getattro;

	module = Py_InitModule3("cAccessControl",
		cAccessControl_methods,
		"$Id: cAccessControl.c,v 1.11 2001/10/19 15:12:25 shane Exp $\n");

	aq_init(); /* For Python <= 2.1.1, aq_init() should be after
                      Py_InitModule(). */

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

	PyDict_SetItemString(dict, "_what_not_even_god_should_do",
		_what_not_even_god_should_do);

	PyExtensionClass_Export(dict, "ZopeSecurityPolicy",
		ZopeSecurityPolicyType);

	PyExtensionClass_Export(dict, "PermissionRole",
		PermissionRoleType);

	PyExtensionClass_Export(dict, "imPermissionRole",
		imPermissionRoleType);

 	imPermissionRoleObj = PyDict_GetItemString(dict, "imPermissionRole");

	/*| from SimpleObjectPolicies import Containers
	*/

	IMPORT(module, "AccessControl.SimpleObjectPolicies");
	GETATTR(module, Containers);
	Py_DECREF(module);
	module = NULL;

	/*| from unauthorized import Unauthorized
	*/

	IMPORT(module, "AccessControl.unauthorized");
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
}

