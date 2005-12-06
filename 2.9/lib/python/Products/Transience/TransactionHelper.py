import time

class PreventTransactionCommit(Exception):
    def __init__(self, reason):
        self. reason = reason

    def __str__(self):
        return "Uncommittable transaction: " % self.reason
    
class UncommittableJar:
    """ A jar that cannot be committed """
    def __init__(self, reason):
        self.reason = reason
        self.time = time.time()
        
    def sortKey(self):
        return str(id(self))

    def tpc_begin(self, *arg, **kw):
        pass

    def commit(self, obj, transaction):
        pass

    def tpc_vote(self, transaction):
        raise PreventTransactionCommit(self.reason)

    def abort(*args):
        pass

class makeTransactionUncommittable:
    """
    - register an uncommittable object with the provided transaction
      which prevents the commit of that transaction
    """
    def __init__(self, transaction, reason):
        self._p_jar = UncommittableJar(reason)
        transaction.register(self)
        
