/*****************************************************************************

  Copyright (c) 2002 Zope Corporation and Contributors.
  All Rights Reserved.

  This software is subject to the provisions of the Zope Public License,
  Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
  WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
  WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
  FOR A PARTICULAR PURPOSE

 ****************************************************************************/

#include <Python.h>

/* This helper only works for Python 2.2 and beyond.  If we're using an
 * older version of Python, stop out now so we don't leave a broken, but
 * compiled and importable module laying about.  BDBFullStorage.py has a
 * workaround for when this extension isn't available.
 */
#if PY_VERSION_HEX < 0x020200F0
#error "Must be using at least Python 2.2"
#endif

/* Increment an 8-byte unsigned integer (represented as an 8-byte raw string),
 * by a Python integer.
 * The arguments are an 8-byte Python string, and a Python int or long.
 * The result is an 8-byte Python string, representing their sum.
 * XXX It's unclear what this intends to do if the sum overflows an 8-byte
 * XXX unsigned integer.  _PyLong_AsByteArray should raise OverflowError then.
 */
static PyObject*
helper_incr(PyObject* self, PyObject* args)
{
    PyObject *pylong = NULL, *incr, *sum = NULL, *result = NULL;
    char *s, x[8];
    int len, res;

    if (!PyArg_ParseTuple(args, "s#O:incr", &s, &len, &incr))
        return NULL;

    assert(len == 8);

    /* There seems to be no direct route from byte array to long long, so
     * first convert it to a PyLongObject*, then convert /that/ thing to a
     * long long.
     */
    pylong = _PyLong_FromByteArray(s, len,
                                   0 /* big endian */,
                                   0 /* unsigned */);

    if (!pylong)
        return NULL;

    sum = PyNumber_Add(pylong, incr);
    if (!sum)
	goto err;

    res = _PyLong_AsByteArray((PyLongObject*)sum, x, 8,
                              0 /* big endian */,
                              0 /* unsigned */);
    if (res < 0)
	goto err;

    result = PyString_FromStringAndSize(x, 8);
 err:
    Py_XDECREF(pylong);
    Py_XDECREF(sum);
    return result;
}


static PyMethodDef helper_methods[] = {
    {"incr", helper_incr, METH_VARARGS},
    {NULL, NULL}                             /* sentinel */
};


DL_EXPORT(void)
init_helper(void)
{
    (void)Py_InitModule("_helper", helper_methods);
}
