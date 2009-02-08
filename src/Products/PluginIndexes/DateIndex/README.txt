DateIndex README

  Overview

    Normal FieldIndexes *can* be used to index values which are DateTime
    instances, but they are hideously expensive:

    o DateTime instances are *huge*, both in RAM and on disk.

    o DateTime instances maintain an absurd amount of precision, far
      beyond any reasonable search criteria for "normal" cases.

    DateIndex is a pluggable index which addresses these two issues
    as follows:

    o It normalizes the indexed value to an integer representation
      with a granularity of one minute.

    o It normalizes the 'query' value into the same form.

    o Objects which return 'None' for the index query are omitted from
      the index.
