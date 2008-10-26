# alias module for backwards compatibility

from DocumentTemplate.DT_Util import Eval

def careful_mul(env, *factors):
    r = 1
    for factor in factors:
        r=r*factor
    return r
