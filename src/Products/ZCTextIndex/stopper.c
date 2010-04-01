/*****************************************************************************

  Copyright (c) 2002 Zope Foundation and Contributors.
  All Rights Reserved.
  
  This software is subject to the provisions of the Zope Public License,
  Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
  WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
  WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
  FOR A PARTICULAR PURPOSE
  
 ****************************************************************************/

/*  stopper.c
 *
 *  Fast version of the StopWordRemover object.
 */

#include "Python.h"

static PyObject *
stopper_process(PyObject *unused, PyObject *args)
{
    PyObject *result = NULL;
    PyObject *dict;
    PyObject *seq;
    int len, i;

    if (!PyArg_ParseTuple(args, "O!O:process", &PyDict_Type, &dict, &seq))
        return NULL;
    seq = PySequence_Fast(seq,
                          "process() requires a sequence as argument 2");
    if (seq == NULL)
        return NULL;
    result = PyList_New(0);
    if (result == NULL)
        goto finally;
#if PY_VERSION_HEX >= 0x02020000
    /* Only available in Python 2.2 and newer. */
    len = PySequence_Fast_GET_SIZE(seq);
#else
    len = PyObject_Length(seq);
#endif
    for (i = 0; i < len; ++i) {
        PyObject *s = PySequence_Fast_GET_ITEM(seq, i);
        /*
         * PyDict_GetItem() returns NULL if there isn't a matching
         * item, but without setting an exception, so this does what
         * we want.
         */
        if (PyDict_GetItem(dict, s) == NULL) {
            if (PyList_Append(result, s) < 0) {
                Py_DECREF(result);
                result = NULL;
                goto finally;
            }
        }
    }
 finally:
    Py_DECREF(seq);
    return result;
}

static PyMethodDef stopper_functions[] = {
    {"process", stopper_process, METH_VARARGS,
     "process(dict, [str, ...]) --> [str, ...]\n"
     "Remove stop words (the keys of dict) from the input list of strings\n"
     " to create a new list."},
    {NULL}
};

void
initstopper(void)
{
    Py_InitModule3("stopper", stopper_functions,
                   "Fast StopWordRemover implementation.");
}
