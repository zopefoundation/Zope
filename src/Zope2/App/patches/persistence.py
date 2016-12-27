# Has this patch been applied yet?
_patched = False


def apply_patches():
    global _patched
    if _patched:
        return
    _patched = True

    from Persistence import Persistent
    from AccessControl.class_init import InitializeClass
    Persistent.__class_init__ = InitializeClass
