/*****************************************************************************

  Copyright (c) 1996-2002 Zope Foundation and Contributors.
  All Rights Reserved.

  This software is subject to the provisions of the Zope Public License,
  Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
  WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
  WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
  FOR A PARTICULAR PURPOSE

 ****************************************************************************/

#ifndef __ACQUISITION_H_
#define __ACQUISITION_H_

typedef struct {
	PyObject *(*AQ_Acquire) (PyObject *obj, PyObject *name, PyObject *filter,
		PyObject *extra, int explicit, PyObject *deflt,
		int containment);
	PyObject *(*AQ_Get) (PyObject *obj, PyObject *name, PyObject *deflt,
		int containment);
	int (*AQ_IsWrapper) (PyObject *obj);
	PyObject *(*AQ_Base) (PyObject *obj);
	PyObject *(*AQ_Parent) (PyObject *obj);
	PyObject *(*AQ_Self) (PyObject *obj);
	PyObject *(*AQ_Inner) (PyObject *obj);
	PyObject *(*AQ_Chain) (PyObject *obj, int containment);
} ACQUISITIONCAPI;

#ifndef _IN_ACQUISITION_C

#define aq_Acquire(obj, name, filter, extra, explicit, deflt, containment ) (AcquisitionCAPI == NULL ? NULL : (AcquisitionCAPI->AQ_Acquire(obj, name, filter, extra, explicit, deflt, containment)))
#define aq_acquire(obj, name) (AcquisitionCAPI == NULL ? NULL : (AcquisitionCAPI->AQ_Acquire(obj, name, NULL, NULL, 1, NULL, 0)))
#define aq_get(obj, name, deflt, containment) (AcquisitionCAPI == NULL ? NULL : (AcquisitionCAPI->AQ_Get(obj, name, deflt, containment)))
#define aq_isWrapper(obj)   (AcquisitionCAPI == NULL ? -1 : (AcquisitionCAPI->AQ_IsWrapper(obj)))
#define aq_base(obj)   (AcquisitionCAPI == NULL ? NULL : (AcquisitionCAPI->AQ_Base(obj)))
#define aq_parent(obj) (AcquisitionCAPI == NULL ? NULL : (AcquisitionCAPI->AQ_Parent(obj)))
#define aq_self(obj)   (AcquisitionCAPI == NULL ? NULL : (AcquisitionCAPI->AQ_Self(obj)))
#define aq_inner(obj)  (AcquisitionCAPI == NULL ? NULL : (AcquisitionCAPI->AQ_Inner(obj)))
#define aq_chain(obj, containment) (AcquisitionCAPI == NULL ? NULL : (AcquisitionCAPI->AQ_CHain(obj, containment)))

static ACQUISITIONCAPI *AcquisitionCAPI = NULL;

#define aq_init() { \
    PyObject *module; \
    PyObject *api; \
    if (! (module = PyImport_ImportModule("Acquisition"))) return; \
    if (! (api = PyObject_GetAttrString(module,"AcquisitionCAPI"))) return; \
    Py_DECREF(module); \
    AcquisitionCAPI = PyCObject_AsVoidPtr(api); \
    Py_DECREF(api); \
}



#endif

#endif
