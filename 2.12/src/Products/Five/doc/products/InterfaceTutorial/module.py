##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

from zope.interface import Interface, implements

class IElephant(Interface):
    """An elephant is a big grey animal.
    """
    def getAngerLevel():
        "Return anger level on scale 0 (placid) to 10 (raging)"

    def trample(target):
        "Trample the target."

    def trumpet():
        "Make loud noise with trunk."

def terribleRacket():
    return "A terrible racket"

class AfricanElephant:
    implements(IElephant)

    def getAngerLevel(self):
        return 5 # always pretty stroppy

    def trample(self, target):
        target.flatten()

    def trumpet(self):
        return "A terrible racket"

class INoiseMaker(Interface):
    """Something that makes noise.
    """
    def makeNoise():
         "Returns the noise that's made."
         
class ElephantNoiseMaker:
     """Adapts elephant to noise maker.
     """
     implements(INoiseMaker)

     def __init__(self, context):
         self.context = context
         
     def makeNoise(self):
         return self.context.trumpet()
     
def demo_manual_adaptation():
    elephant = AfricanElephant()
    noise_maker = ElephantNoiseMaker(elephant)
    print noise_maker.makeNoise()
