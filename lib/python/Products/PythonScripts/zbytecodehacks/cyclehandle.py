class CycleHandle:
    '''CycleHandles are proxies for cycle roots

A CycleHandle subclass should create one or more workers, and pass them
to _set_workers.  These workers can then participate in cycles, as long
as deleting all of the worker's attributes will break the cycle.  When a 
CycleHandle instance goes away, it deletes all attributes of all of
its workers.  You could also explicitly call drop_workers.

For example,
>>> class Ham:
...     def __del__(self):
...         print 'A ham has died!'
...            
>>> ct = CycleHandle()
>>> ct._set_workers(Ham(), Ham())
>>> ct._workers[0].ham2 = ct._workers[1]
>>> ct._workers[1].ham1 = ct._workers[0]
>>> del ct
A ham has died!
A ham has died!
'''
    _workers = ()
    def _set_workers(self, *workers):
        self.__dict__['_workers'] = workers
    def _not_mutable(self, *x):
        raise TypeError, 'CycleHandle is not mutable'
    __delattr__ = _not_mutable
    def __setattr__(self, attr, val):
        for worker in self._workers:
            if hasattr(worker, '__setattr__'):
                return getattr(worker, '__setattr__')(attr, val)
    _not_mutable_defs = ('__delslice__', '__setslice__', '__delitem__',
                         '__setitem__')
    def __getattr__(self, attr):
        for worker in self._workers:
            if hasattr(worker, attr):
                return getattr(worker, attr)
        if attr in self._not_mutable_defs:
            return self._not_mutable
        raise AttributeError, attr
    def _drop_workers(self):
        for worker in self._workers:
            worker.__dict__.clear()
        self.__dict__['_workers'] = ()
    def __del__(self, drop_workers=_drop_workers):
        drop_workers(self)

def _test():
    import doctest, cyclehandle
    return doctest.testmod(cyclehandle)

if __name__ == "__main__":
    _test()
