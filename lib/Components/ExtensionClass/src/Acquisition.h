/*

  Copyright (c) 1996-2001, Digital Creations, Fredericksburg, VA, USA.  
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

  $Id: Acquisition.h,v 1.2 2001/10/19 15:12:24 shane Exp $

  If you have questions regarding this software,
  contact:
 
    Digital Creations L.C.  
    info@digicool.com
 
    (540) 371-6909

*/

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
#define aq_get(obj, name, deflt, containment) (AcquistionCAPI == NULL ? NULL : (AcquisitionCAPI->AQ_Get(obj, name, deflt, containment)))
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
