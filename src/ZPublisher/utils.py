##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import base64
import logging

import transaction
from Acquisition import aq_inner
from Acquisition import aq_parent


AC_LOGGER = logging.getLogger('event.AccessControl')


def recordMetaData(object, request):
    if hasattr(object, 'getPhysicalPath'):
        path = '/'.join(object.getPhysicalPath())
    else:
        # Try hard to get the physical path of the object,
        # but there are many circumstances where that's not possible.
        to_append = ()

        if hasattr(object, '__self__') and hasattr(object, '__name__'):
            # object is a Python method.
            to_append = (object.__name__,)
            object = object.__self__

        while object is not None and not hasattr(object, 'getPhysicalPath'):
            if getattr(object, '__name__', None) is None:
                object = None
                break
            to_append = (object.__name__,) + to_append
            object = aq_parent(aq_inner(object))

        if object is not None:
            path = '/'.join(object.getPhysicalPath() + to_append)
        else:
            # As Jim would say, "Waaaaaaaa!"
            # This may cause problems with virtual hosts
            # since the physical path is different from the path
            # used to retrieve the object.
            path = request.get('PATH_INFO')

    T = transaction.get()
    T.note(safe_unicode(path))
    auth_user = request.get('AUTHENTICATED_USER', None)
    if auth_user:
        auth_folder = aq_parent(auth_user)
        if auth_folder is None:
            AC_LOGGER.warning(
                'A user object of type %s has no aq_parent.',
                type(auth_user))
            auth_path = request.get('AUTHENTICATION_PATH')
        else:
            auth_path = '/'.join(auth_folder.getPhysicalPath()[1:-1])
        user_id = auth_user.getId()
        user_id = safe_unicode(user_id) if user_id else 'None'
        T.setUser(user_id, safe_unicode(auth_path))


def safe_unicode(value):
    if isinstance(value, str):
        return value
    elif isinstance(value, bytes):
        try:
            value = str(value, 'utf-8')
        except UnicodeDecodeError:
            value = value.decode('utf-8', 'replace')
    return value


def basic_auth_encode(user, password=None):
    # user / password and the return value are of type str
    value = user
    if password is not None:
        value = value + ':' + password
    header = b'Basic ' + base64.b64encode(value.encode('latin-1'))
    header = header.decode('latin-1')
    return header


def basic_auth_decode(token):
    # token and the return values are of type str
    if not token:
        return None
    if not token[:6].lower() == 'basic ':
        return None
    value = token.split()[-1]  # Strip 'Basic '
    plain = base64.b64decode(value)
    plain = plain.decode('latin-1')
    user, password = plain.split(':', 1)  # Split at most once
    return (user, password)
