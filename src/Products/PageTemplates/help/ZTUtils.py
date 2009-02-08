"""
ZTUtils: Page Template Utilities

  The classes in this module are available from Page Templates.

"""

class Batch:
    """
    Batch - a section of a large sequence.

    You can use batches to break up large sequences (such as search
    results) over several pages.

    Batches provide Page Templates with similar functions as those
    built-in to '<dtml-in>'.

    You can access elements of a batch just as you access elements of
    a list. For example::

      >>> b=Batch(range(100), 10)
      >>> b[5]
      4
      >>> b[10]
      IndexError: list index out of range

    Batches have these public attributes:

    start -- The first element number (counting from 1).

    first -- The first element index (counting from 0). Note that this
    is that same as start - 1.

    end -- The last element number (counting from 1).

    orphan -- The desired minimum batch size. This controls how
    sequences are split into batches. If a batch smaller than the
    orphan size would occur, then no split is performed, and a batch
    larger than the batch size results.

    overlap -- The number of elements that overlap between batches.

    length -- The actual length of the batch. Note that this can be
    different than size due to orphan settings.

    size -- The desired size. Note that this can be different than the
    actual length of the batch due to orphan settings.

    previous -- The previous batch or None if this is the first batch.

    next -- The next batch or None if this is the last batch.
    """

    def __init__(self, sequence, size, start=0, end=0,
                 orphan=0, overlap=0):
        """
        Creates a new batch given a sequence and a desired batch
        size.

        sequence -- The full sequence.

        size -- The desired batch size.

        start -- The index of the start of the batch (counting from 0).

        end -- The index of the end of the batch (counting from  0).

        orphan -- The desired minimum batch size. This controls how
        sequences are split into batches. If a batch smaller than the
        orphan size would occur, then no split is performed, and a
        batch larger than the batch size results.

        overlap -- The number of elements that overlap between
        batches.
        """
