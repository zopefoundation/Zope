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


logger = logging.getLogger('ZPublisher')
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
    header = b'Basic ' + base64.b64encode(value.encode())
    header = header.decode()
    return header


def basic_auth_decode(token):
    # token and the return values are of type str
    if not token:
        return None
    if not token[:6].lower() == 'basic ':
        return None
    value = token.split()[-1]  # Strip 'Basic '
    plain = base64.b64decode(value).decode()
    user, password = plain.split(':', 1)  # Split at most once
    return (user, password)


def _string_tuple(value):
    if not value:
        return ()
    return tuple([safe_unicode(element) for element in value])


def fix_properties(obj, path=None):
    """Fix properties on object.

    This does two things:

    1. Make sure lines contain only strings, instead of bytes,
       or worse: a combination of strings and bytes.
    2. Replace deprecated ulines, utext, utoken, and ustring properties
       with their non-unicode variant, using native strings.

    See https://github.com/zopefoundation/Zope/issues/987

    Since Zope 5.3, a lines property stores strings instead of bytes.
    But there is no migration yet.  (We do that here.)
    Result is that getProperty on an already created lines property
    will return the old value with bytes, but a newly created lines property
    will return strings.  And you might get combinations.

    Also since Zope 5.3, the ulines property type is deprecated.
    You should use a lines property instead.
    Same for a few others: utext, utoken, ustring.
    The unicode variants are planned to be removed in Zope 6.

    Intended usage:
    app.ZopeFindAndApply(app, apply_func=fix_properties)
    """
    if path is None:
        # When using ZopeFindAndApply, path is always given.
        # But we may be called by other code.
        if hasattr(object, 'getPhysicalPath'):
            path = '/'.join(object.getPhysicalPath())
        else:
            # Some simple object, for example in tests.
            # We don't care about the path then, it is only shown in logs.
            path = "/dummy"

    if not hasattr(obj, "_updateProperty"):
        # Seen with portal_url tool, most items in portal_skins,
        # catalog lexicons, workflow states/transitions/variables, etc.
        return
    try:
        prop_map = obj.propertyMap()
    except (AttributeError, TypeError, KeyError, ValueError):
        # If getting the property map fails, there is nothing we can do.
        # Problems seen in practice:
        # - Object does not inherit from PropertyManager,
        #   for example 'MountedObject'.
        # - Object is a no longer existing skin layer.
        logger.warning("Error getting property map from %s", path)
        return

    for prop_info in prop_map:
        # Example: {'id': 'title', 'type': 'string', 'mode': 'w'}
        prop_id = prop_info.get("id")
        current = obj.getProperty(prop_id)
        if current is None:
            continue
        new_type = prop_type = prop_info.get("type")
        if prop_type == "lines":
            new = _string_tuple(current)
        elif prop_type == "ulines":
            new_type = "lines"
            new = _string_tuple(current)
        elif prop_type == "utokens":
            new_type = "tokens"
            new = _string_tuple(current)
        elif prop_type == "utext":
            new_type = "text"
            new = safe_unicode(current)
        elif prop_type == "ustring":
            new_type = "string"
            new = safe_unicode(current)
        else:
            continue
        if prop_type != new_type:
            # Replace with non-unicode variant.
            # This could easily lead to:
            # Exceptions.BadRequest: Invalid or duplicate property id.
            #   obj._delProperty(prop_id)
            #   obj._setProperty(prop_id, new, new_type)
            # So fix it by using internal details.
            for prop in obj._properties:
                if prop.get("id") == prop_id:
                    prop["type"] = new_type
                    obj._p_changed = True
                    break
            else:
                # This probably cannot happen.
                # If it does, we want to know.
                logger.warning(
                    "Could not change property %s from %s to %s for %s",
                    prop_id,
                    prop_type,
                    new_type,
                    path,
                )
                continue
            obj._updateProperty(prop_id, new)
            logger.info(
                "Changed property %s from %s to %s for %s",
                prop_id,
                prop_type,
                new_type,
                path,
            )
            continue
        if current != new:
            obj._updateProperty(prop_id, new)
            logger.info(
                "Changed property %s at %s so value fits the type %s: %r",
                prop_id,
                path,
                prop_type,
                new,
            )
