
class InterfaceBase:

    __meta_data = {}

    def getName(self):
        """ Returns the name of the object. """
        return self.__name__

    def getDoc(self):
        """ Returns the documentation for the object. """
        return self.__doc__

    def getKey(self, key):
        """ Returns the value associated with 'key'. """
        return self.__meta_data[key]

    def getKeys(self):
        """ Returns a list of all keys. """
        return self.__meta_data.keys()

    def setKey(self, key, value):
        """ Associates 'value' with 'key'. """
        self.__meta_data[key] = value





