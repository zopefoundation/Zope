# Import all patches.
from . import persistence
from . import publishing


# Have the patches been applied yet?
_patched = False


def apply_patches():
    global _patched
    if _patched:
        return
    _patched = True

    persistence.apply_patches()
    publishing.apply_patches()
