
import Basic, Util

class Mapping(Basic.Base):
    "anything supporting __getitem__"

class Sized(Basic.Base):
    "anything supporting __len"

class MutableMapping(Basic.Mutable):
    "Has __setitem__ and __delitem__"

class Sequence(Mapping):
    "Keys must be integers in a sequence starting at 0."

class Sequential(Sequence):
    "Keys must be used in order"

Util.assertTypeImplements(type(()), (Sequence, Sized, Basic.HashKey))
Util.assertTypeImplements(type([]), (Sequence, Sized, MutableMapping))
Util.assertTypeImplements(type({}), (Mapping, Sized, MutableMapping))

