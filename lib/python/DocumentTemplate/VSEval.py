# alias module for backwards compatibility

import RestrictedPython
Eval = RestrictedPython.Eval.RestrictionCapableEval

def careful_mul(env, *factors):
    r = 1
    for factor in factors:
        r=r*factor
    return r

