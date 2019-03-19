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

from zope.deferredimport import deprecated


# BBB Zope 5.0
deprecated(
    'Please import from ZServer.ZPublisher.Publish.',
    _default_debug_mode='ZServer.ZPublisher.Publish:_default_debug_mode',
    _default_realm='ZServer.ZPublisher.Publish:_default_realm',
    call_object='ZServer.ZPublisher.Publish:call_object',
    DefaultTransactionsManager=(
        'ZServer.ZPublisher.Publish:DefaultTransactionsManager'),
    dont_publish_class='ZServer.ZPublisher.Publish:dont_publish_class',
    get_module_info='ZServer.ZPublisher.Publish:get_module_info',
    missing_name='ZServer.ZPublisher.Publish:missing_name',
    publish='ZServer.ZPublisher.Publish:publish',
    publish_module='ZServer.ZPublisher.Publish:publish_module',
    publish_module_standard=(
        'ZServer.ZPublisher.Publish:publish_module_standard'),
    set_default_debug_mode=(
        'ZServer.ZPublisher.Publish:set_default_debug_mode'),
    set_default_authentication_realm=(
        'ZServer.ZPublisher.Publish:set_default_authentication_realm'),
)

# BBB Zope 5.0
deprecated(
    'Please import from ZPublisher.',
    Retry='ZPublisher:Retry',
)
