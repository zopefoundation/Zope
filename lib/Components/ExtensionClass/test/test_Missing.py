from Missing import Value

assert Value != 12
assert 12 != Value
assert u"abc" != Value
assert Value != u"abc"

assert 1 + Value == Value
assert Value + 1 == Value
assert Value == 1 + Value
assert Value == Value + 1
