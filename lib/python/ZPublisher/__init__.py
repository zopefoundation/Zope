from Publish import publish_module

def test(*args, **kw):
    global test
    import Test
    test=Test.publish
    return apply(test, args, kw)

def Main(*args, **kw):
    global test
    import Test
    test=Test.publish
    return apply(test, ('Main',)+args, kw)
