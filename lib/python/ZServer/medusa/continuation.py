# -*- Mode: Python; tab-width: 4 -*-

# [ based on async_lib/consumer.py:function_chain.py ]

class continuation:

    'Package up a continuation as an object.'
    'Also a convenient place to store state.'
    
    def __init__ (self, fun, *args):
        self.funs = [(fun, args)]
        
    def __call__ (self, *args):
        fun, init_args = self.funs[0]
        self.funs = self.funs[1:]
        if self.funs:
            apply (fun, (self,)+ init_args + args)
        else:
            apply (fun, init_args + args)
            
    def chain (self, fun, *args):
        self.funs.insert (0, (fun, args))
        return self
        
    def abort (self, *args):
        fun, init_args = self.funs[-1]
        apply (fun, init_args + args)
