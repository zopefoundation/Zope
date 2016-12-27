# Import all patches.
import publishing

# Have the patches been applied yet?
_patched = False


def apply_patches():
    global _patched
    if _patched:
        return
    _patched = True

    publishing.apply_patches()
