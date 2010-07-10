##############################################################################
#
# Copyright (c) 2004, 2005 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Restricted python test helpers

Based on Plone's RestrictedPythonTestCase, with kind permission by the
Plone developers.
"""
from AccessControl import Unauthorized

def addPythonScript(folder, id, params='', body=''):
    """Add a PythonScript to folder."""
    # clean up any 'ps' that's already here..
    try:
        folder._getOb(id)
        folder.manage_delObjects([id])
    except AttributeError:
        pass # it's okay, no 'ps' exists yet
    factory = folder.manage_addProduct['PythonScripts']
    factory.manage_addPythonScript(id)
    folder[id].ZPythonScript_edit(params, body)

def checkRestricted(folder, psbody):
    """Perform a check by running restricted Python code."""
    addPythonScript(folder, 'ps', body=psbody)
    try:
        folder.ps()
    except Unauthorized, e:
        raise AssertionError, e

def checkUnauthorized(folder, psbody):
    """Perform a check by running restricted Python code.  Expect to
    encounter an Unauthorized exception."""
    addPythonScript(folder, 'ps', body=psbody)
    try:
        folder.ps()
    except Unauthorized:
        pass
    else:
        raise AssertionError, "Authorized but shouldn't be"
