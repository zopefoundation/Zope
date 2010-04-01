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
from module import INoiseMaker, IElephant, AfricanElephant

class IChicken(Interface):
    def getConfusionLevel():
        "Get the confusion level of this chicken, 0 asleep, 10 frantic"

    def cluck():
        """Return clucking sound of the chicken.
        """

class Chicken:
    implements(IChicken)

    def __init__(self, confusion_level):
        self._confusion_level = confusion_level
        
    def getConfusionLevel(self):
        return self._confusion_level
    
    def cluck(self):
        return ' '.join(["cluck"] * self.getConfusionLevel())

class IndianElephant:
    implements(IElephant)

    def __init__(self, anger_level):
        self._anger_level = anger_level

    def hit(self):
        """Hit the indian elephant with a stick.
        """
        if self._anger_level <= 10:
            self._anger_level += 1

    def getAngerLevel(self):
        return self._anger_level

    def trumpet(self):
        return "t" + ("o" * self._anger_level) + "t"
    
class ChickenNoiseMaker:
    implements(INoiseMaker)
    
    def __init__(self, context):
        self.context = context

    def makeNoise(self):
        return self.context.cluck()

def demo_animal_farm():
    animal_farm = [Chicken(5), AfricanElephant(),
                   Chicken(3), IndianElephant(3)]
    
    for animal in animal_farm:
        noise_maker = INoiseMaker(animal)
        print noise_maker.makeNoise()

