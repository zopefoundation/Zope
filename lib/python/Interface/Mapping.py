import Basic, Util

class Mapping(Basic.Base):
    "anything supporting __getitem__"

    def __getitem__(key):
        """Get the value for the given key

        Raise a key error if the key if not in the collection.
        """

class QueryMapping(Mapping):

    def has_key(key):
        """Check whether the object has an item with the given key"""


    def get(key, default=None):
        """Get the value for the given key

        Return the default if the key is not in the  collection.
        """

class Sized(Basic.Base):
    "anything supporting __len"

    def __len__():
        """Return the number of items in the container"""

class MutableMapping(Basic.Mutable):
    "Has __setitem__ and __delitem__"

    def __setitem__(key, value):
        """Set the value for the given key"""

    def __delitem__(key):
        """delete the value for the given key

        Raise a key error if the key if not in the collection."""

class EnumerableMapping(Mapping):

    def keys():
        """Return an Sequence containing the keys in the collection

        The type of the IReadSequence is not specified. It could be a
        list or a tuple or some other type.
        """

class MinimalDictionary(QueryMapping, Sized, MutableMapping,
                        EnumerableMapping):
    """Provide minimal dictionary-like behavior
    """

    def values():
        """Return a IReadSequence containing the values in the collection

        The type of the IReadSequence is not specified. It could be a
        list or a tuple or some other type.
        """

    def items():
        """Return a IReadSequence containing the items in the collection

        An item is a key-value tuple.

        The type of the IReadSequence is not specified. It could be a
        list or a tuple or some other type.
        """


class Sequence(Mapping):
    "Keys must be integers in a sequence starting at 0."

class Sequential(Sequence):
    "Keys must be used in order"

Util.assertTypeImplements(type(()), (Sequence, Sized, Basic.HashKey))
Util.assertTypeImplements(type([]), (Sequence, Sized, MutableMapping))
Util.assertTypeImplements(type({}), (Mapping, Sized, MutableMapping))
