#ifndef INTSET_H
#define INTSET_H

#define INTSET_DATA_TYPE int

typedef struct {
  cPersistent_HEAD
  int size, len;
  INTSET_DATA_TYPE *data;
} intSet;

#define INTSET(O) ((intSet*)(O))

static PyObject *intSetType = NULL;

#endif /* INTSET_H */
