##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
__doc__="""Implement Observable interface (see
http://www.zope.org/Members/michel/Projects/Interfaces/ObserverAndNotification)
This class is intended to be used as a mixin (note that it doesn't derive
from any Zope persistence classes, for instance).

$Id: DefaultObservable.py,v 1.3 2000/11/10 16:53:05 tseaver Exp $"""

__version__='$Revision: 1.3 $'[11:-2]

import string
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
            observer = string.join( observer, '/' ) 

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
        

#
#   Unit tests
#

if __name__ == '__main__':

    class DontGoHere( Exception ): pass
        
    class TestSubject( DefaultObservable ):

        def __init__( self, paths ):
            DefaultObservable.__init__( self, 0 )
            self.paths = paths

        def restrictedTraverse( self, path, default ):
            return self.paths.get( path, default )

    callbacks = {}

    def recordCallback( name, subject, event ):
        cbrec = callbacks.get( name, None )
        if cbrec is None:
            cbrec = callbacks[ name ] = []
        cbrec.append( ( subject, event ) )
        

    class TestObserver:

        def __call__( self, subject, event ):
            recordCallback( 'direct', subject, event )
        
        def namedCallback( self, subject, event ):
            recordCallback( 'named', subject, event )
        
        def named2Callback( self, subject, event ):
            recordCallback( 'named2', subject, event )
        
        def boundCallback( self, subject, event ):
            recordCallback( 'bound', subject, event )

    def freefuncObserver( subject, event ):
        recordCallback( 'freefunc', subject, event ) 
    
    def tryVeto( subject, event ):
        """ Simulate attempted veto. """
        raise 'Idawanna!'
    
    observer = TestObserver()

    # Simulate Zope's path traversal mechanism.
    paths = {}
    paths[ 'direct'         ] = observer
    paths[ 'direct/named'   ] = observer.namedCallback
    paths[ 'direct/named2'  ] = observer.named2Callback
    paths[ 'bound'          ] = observer.boundCallback
    paths[ 'freefunc'       ] = freefuncObserver
    paths[ 'tryVeto'        ] = tryVeto

    subject = TestSubject( paths )

    subject.registerObserver( 'direct' )
    subject.registerObserver( 'bound' )
    subject.registerObserver( 'direct/named' )
    subject.registerObserver( ( 'direct', 'named2' ) )
    subject.registerObserver( 'freefunc' )
    subject.registerObserver( 'tryVeto' )

    try:
        subject.registerObserver( 'nonesuch' )
        raise DontGoHere( 'path not found' )
    except NameError:
        pass
    except:
        import traceback
        traceback.print_exc()

    try:
        subject.registerObserver( 3.1415926 )
        raise DontGoHere( 'non-path' )
    except TypeError:
        pass
    except:
        import traceback
        traceback.print_exc()

    subject.notify( 'First event' )

    subject.unregisterObserver( 'bound' )
    subject.notify( { 'name' : 'Second event', 'value' : 42 } )

    for key in callbacks.keys():
        print '[%s]' % key
        for cb in callbacks[ key ]:
            print '    %s' % `cb`

