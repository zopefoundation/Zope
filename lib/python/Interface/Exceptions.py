
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

class InvalidInterface(Exception): pass
