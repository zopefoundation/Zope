# The code in this file is executed after being compiled as restricted code,
# and given a globals() dict with our idea of safe builtins, and the
# Zope production implementations of the special restricted-Python functions
# (like _getitem_ and _getiter_, etc).
#
# This isn't trying to provoke security problems, it's just trying to verify
# that Python code continues to work as intended after all the transformations,
# and with all the special wrappers we supply.

def f1():
    next = iter(xrange(3)).next
    assert next() == 0
    assert next() == 1
    assert next() == 2
    try:
        next()
    except StopIteration:
        pass
    else:
        assert 0, "expected StopIteration"
f1()

def f2():
    assert map(lambda x: x+1, range(3)) == range(1, 4)
f2()

def f3():
    assert filter(None, range(10)) == range(1, 10)
f3()

def f4():
    assert [i+1 for i in range(3)] == range(*(1, 4))
f4()

def f5():
    x = range(5)
    def add(a, b):
        return a+b
    assert sum(x) == reduce(add, x, 0)
f5()

def f6():
    class C:
       def display(self):
            return str(self.value)
    c1 = C()
    c2 = C()
    c1.value = 12
    assert getattr(c1, 'value') == 12
    assert c1.display() == '12'
    assert not hasattr(c2, 'value')
    setattr(c2, 'value', 34)
    assert c2.value == 34
    assert hasattr(c2, 'value')
    del c2.value
    assert not hasattr(c2, 'value')

    # OK, if we can't set new attributes, at least verify that we can't.
    #try:
    #    c1.value = 12
    #except TypeError:
    #    pass
    #else:
    #    assert 0, "expected direct attribute creation to fail"

    #try:
    #    setattr(c1, 'value', 12)
    #except TypeError:
    #    pass
    #else:
    #    assert 0, "expected indirect attribute creation to fail"

    assert getattr(C, "display", None) == getattr(C, "display")
    delattr(C, "display")

    #try:
    #    setattr(C, "display", lambda self: "replaced")
    #except TypeError:
    #    pass
    #else:
    #    assert 0, "expected setattr() attribute replacement to fail"

    #try:
    #    delattr(C, "display")
    #except TypeError:
    #    pass
    #else:
    #    assert 0, "expected delattr() attribute deletion to fail"
f6()

def f7():
    d = apply(dict, [((1, 2), (3, 4))]) # {1: 2, 3: 4}
    expected = {'k': [1, 3],
                'v': [2, 4],
                'i': [(1, 2), (3, 4)]}
    for meth, kind in [('iterkeys', 'k'),
                       ('iteritems', 'i'),
                       ('itervalues', 'v'),
                       ('keys', 'k'),
                       ('items', 'i'),
                       ('values', 'v')]:
        access = getattr(d, meth)
        result = list(access())
        result.sort()
        assert result == expected[kind], (meth, kind, result, expected[kind])
f7()

def f8():
    import math
    ceil = getattr(math, 'ceil')
    smallest = 1e100
    smallest_index = None
    largest = -1e100
    largest_index = None
    all = []
    for i, x in enumerate((2.2, 1.1, 3.3, 5.5, 4.4)):
        all.append(x)
        effective = ceil(x)
        if effective < smallest:
            assert min(effective, smallest) == effective
            smallest = effective
            smallest_index = i
        if effective > largest:
            assert max(effective, largest) == effective
            largest = effective
            largest_index = i
    assert smallest == 2
    assert smallest_index == 1
    assert largest == 6
    assert largest_index == 3

    assert min([ceil(x) for x in all]) == smallest
    assert max(map(ceil, all)) == largest
f8()

# After all the above, these wrappers were still untouched:
#     ['DateTime', '_print_', 'reorder', 'same_type', 'test']
# So do something to touch them.
def f9():
    d = DateTime()
    print d # this one provoked _print_

    # Funky.  This probably isn't an intended use of reorder, but I'm
    # not sure why it exists.
    assert reorder('edcbaxyz', 'abcdef', 'c') == zip('abde', 'abde')

    assert test(0, 'a', 0, 'b', 1, 'c', 0, 'd') == 'c'
    assert test(0, 'a', 0, 'b', 0, 'c', 0, 'd', 'e') == 'e'
    # Unclear that the next one is *intended* to return None (it falls off
    # the end of test's implementation without explicitly returning anything).
    assert test(0, 'a', 0, 'b', 0, 'c', 0, 'd') == None

    assert same_type(3, 2, 1), 'expected same type'
    assert not same_type(3, 2, 'a'), 'expected not same type'
f9()

def f10():
    assert iter(enumerate(iter(iter(range(9))))).next() == (0, 0)
f10()

def f11():
    x = 1
    x += 1
f11()

def f12():
    try:
        all
    except NameError:
        pass # Python < 2.5
    else:
        assert all([True, True, True]) == True
        assert all([True, False, True]) == False
f12()

def f13():
    try:
        any
    except NameError:
        pass # Python < 2.5
    else:
        assert any([True, True, True]) == True
        assert any([True, False, True]) == True
        assert any([False, False, False]) == False
f13()

