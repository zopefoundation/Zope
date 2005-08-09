DateRangeIndex README

  Overview

    Zope applications frequently wish to perform efficient queries
    against a pair of date attributes/methods, representing a time
    interval (e.g., effective / expiration dates).  This query *can*
    be done using a pair of indexes, but this implementation is
    hideously expensive:

    o DateTime instances are *huge*, both in RAM and on disk.

    o DateTime instances maintain an absurd amount of precision, far
      beyond any reasonable search criteria for "normal" cases.

    o Results must be fetched and intersected between two indexes.

    o Handling objects which do not specify both endpoints (i.e.,
      where the interval is open or half-open) is iffy, as the
      default value needs to be coerced into a different abnormal
      value for each end to permit ordered comparison.

    o The *very* common case of the open interval (neither endpoint
      specified) should be optimized.

    DateRangeIndex is a pluggable index which addresses these issues
    as follows:

    o It groups the "open" case into a special set, '_always'.

    o It maintains separate ordered sets for each of the "half-open"
      cases.

    o It performs the expensive "intersect two range search" operation
      only on the (usually small) set of objects which provide a
      closed interval.

    o It flattens the key values into integers with granularity of
      one minute.

    o It normalizes the 'query' value into the same form.
