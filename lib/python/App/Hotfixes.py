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

from version_txt import getZopeVersion
from logging import getLogger


LOG = getLogger('Hotfixes')

merged_hotfixes = {
    'Hotfix_2001-09-28': 1,
    'Hotfix_2002-03-01': 1,
    'Hotfix_2002-04-15': 1,
    'Hotfix_2002-06-14': 1,
    }


APPLY = 1
ALREADY_MERGED = 0
OUTDATED_ZOPE = None


def isMerged(name):
    return merged_hotfixes.get(name, 0)


def logHotfix(id, apply_hotfix):
    if apply_hotfix:
        LOG.info('Applying %s' % id)
    elif apply_hotfix is OUTDATED_ZOPE:
        LOG.warn('Not applying %s.  It is not designed for '
            'this version of Zope.  Please uninstall the hotfix product.'
            % id)
    else:  # ALREADY_MERGED
        LOG.warn('Not applying %s.  The fix has already been '
            'merged into Zope.  Please uninstall the hotfix product.'
            % id)


def beforeApplyHotfix(id, req_major, req_minor, req_micro):
    major, minor, micro = getZopeVersion()[:3]
    if major > 0 and (
        (major * 10000 + minor * 100 + micro) <
        (req_major * 10000 + req_minor * 100 + req_micro)):
        # The version of Zope is too old for this hotfix.
        apply_hotfix = OUTDATED_ZOPE
    elif isMerged(id):
        apply_hotfix = ALREADY_MERGED
    else:
        apply_hotfix = APPLY
    logHotfix(id, apply_hotfix)
    return apply_hotfix
