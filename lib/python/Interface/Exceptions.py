
class DoesNotImplement(Exception):
    """ This object does not implement """
    def __init__(self, interface):
        self.interface = interface

    def __str__(self):
        return """An object does not implement interface %(interface)s

        """ % self.__dict__

class BrokenImplementation(Exception):
    """An attribute is not completely implemented.
    """

    def __init__(self, interface, name):
        self.interface=interface
        self.name=name

    def __str__(self):
        return """An object has failed to implement interface %(interface)s

        The %(name)s attribute was not provided.
        """ % self.__dict__

class BrokenMethodImplementation(BrokenImplementation):
    """An method is not completely implemented.
    """

    def __init__(self, method):
        self.method=method

    def __str__(self):
        return """An object has failed to implement the method %(method)s

        The signature is incorrect.
        """ % self.__dict__

class InvalidInterface(Exception): pass


