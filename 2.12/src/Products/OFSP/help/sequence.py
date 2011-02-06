"""
sequence: Sequence sorting module

  This module provides a 'sort' function for use with DTML, Page
  Templates, and Python-based Scripts.
"""

def sort(seq, sort):
    """
    Sort the sequence *seq* of objects by the optional sort schema
    *sort*.  *sort* is a sequence of tuples '(key, func, direction)'
    that describe the sort order.

    key -- Attribute of the object to be sorted.

    func -- Defines the compare function (optional).  Allowed values:

      "cmp" -- Standard Python comparison function

      "nocase" -- Case-insensitive comparison

      "strcoll" or "locale" -- Locale-aware string comparison

      "strcoll_nocase" or "locale_nocase" -- Locale-aware
      case-insensitive string comparison

      other -- A specified, user-defined comparison function, should
      return 1, 0, -1.

    direction -- defines the sort direction for the key (optional).
    (allowed values: "asc", "desc")

    DTML Examples

      Sort child object (using the 'objectValues' method) by id (using
      the 'getId' method), ignoring case::

        <dtml-in expr="_.sequence.sort(objectValues(),
                                       (('getId', 'nocase'),))">
          <dtml-var getId> <br>
        </dtml-in>

      Sort child objects by title (ignoring case) and date (from newest
      to oldest)::

        <dtml-in expr="_.sequence.sort(objectValues(),
                                       (('title', 'nocase'),
                                        ('bobobase_modification_time',
                                        'cmp', 'desc')
                                       ))">
          <dtml-var title> <dtml-var bobobase_modification_time> <br>
        </dtml-in>

    Page Template Examples

      You can use the 'sequence.sort' function in Python expressions
      to sort objects. Here's an example that mirrors the DTML example
      above::

        <table tal:define="objects here/objectValues;
                           sort_on python:(('title', 'nocase', 'asc'),
                                           ('bobobase_modification_time', 'cmp', 'desc'));
                           sorted_objects python:sequence.sort(objects, sort_on)">
          <tr tal:repeat="item sorted_objects">
            <td tal:content="item/title">title</td>
            <td tal:content="item/bobobase_modification_time">
              modification date</td>
          </tr>
        </table>

      This example iterates over a sorted list of object, drawing a
      table row for each object. The objects are sorted by title and
      modification time.

    See Also

      "Python cmp function":http://www.python.org/doc/lib/built-in-funcs.html

    """
