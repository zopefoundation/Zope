from TransienceInterfaces import Transient, DictionaryLike, ItemWithId,\
     TTWDictionary, ImmutablyValuedMappingOfPickleableObjects,\
     StringKeyedHomogeneousItemContainer, TransientItemContainer
from OFS.Item import SimpleItem
from Persistent import Persistence
from Acquisition import Implicit

class TransientObjectContainer(SimpleItem):
    """ akin to Session Data Container """
    __implements__ = (ItemWithId,
                      StringKeyedHomogeneousItemContainer,
                      TransientItemContainer
                      )

class TransientObject(Persistent, Implicit):
    """ akin to Session Data Object """
    __implements__ = (ItemWithId, # randomly generate an id
                      Transient,
                      DictionaryLike,
                      TTWDictionary,
                      ImmutablyValuedMappingOfPickleableObjects
                      )
    
