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
"""Implement Observable interface (see
http://www.zope.org/Members/michel/Projects/Interfaces/ObserverAndNotification)
This class is intended to be used as a mixin (note that it doesn't
derive from any Zope persistence classes, for instance).
"""

from types import StringType

class DefaultObservable:
    """
    See the Interfaces wiki for design notes:

http://www.zope.org/Members/michel/Projects/Interfaces/ObserverAndNotification

    DefaultObservable is intended to be used as a mix-in, like so::

        from OFS.SimpleItem import SimpleItem
        from OFS.DefaultObservable import DefaultObservable

        class Foo( SimpleItem, DefaultObservable ):
            '''
                Some foo or other
            '''
            ...
            def bar( self, ... ):
                '''
                '''
                ...
                self.notify( "bar" )

    Clients register with a Foo instance using the methods of the
    Observable interface, e.g.::

        foo.registerObserver( self.getPhysicalPath() + ( 'watchFoo',) )

    When the Foo instance has its 'bar()' method called, it will
    notify all registered observers, passing 'bar' as the event;  in
    this case, the client's 'watchFoo()' method will be called, with
    the foo object and 'bar' passed as parameters.
    """

    def __init__( self, debug=0 ):
        self._observers = []
        self._debug = debug

    def _normalize( self, observer ):

        # Assert that observer is a string or a sequence of strings.
        if type( observer ) != StringType:
            observer = '/'.join( observer)

        return observer

    #
    #   Observable interface methods.
    #
    def registerObserver( self, observer ):

        normal = self._normalize( observer )
        if self.restrictedTraverse( normal, None ):
            self._observers.append( normal )
        else:
            raise NameError, observer

    def unregisterObserver( self, observer ):

        self._observers.remove( self._normalize( observer ) )

    #
    #   Convenience method for derivatives.
    #
    def notify( self, event=None ):

        bozos = []

        for observer in self._observers:

            obj = self.restrictedTraverse( observer, None )

            if obj is not None:
                try:
                    obj( self, event )
                except:
                    bozos.append( observer ) # Veto not allowed!
                    if self._debug:
                        import traceback
                        traceback.print_exc()
            else:
                bozos.append( observer )

        for bozo in bozos:
            try: # avoid race condition if unregister() called before now
                self._observers.remove( bozo )
            except:
                pass
