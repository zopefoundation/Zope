from macro import add_macro
def main():
    def setq((x),v):
        x = v
        return v
    add_macro(setq)

    def pre_incr((x)):
        x = x + 1
        return x
    add_macro(pre_incr)

    def post_incr((x)):
        t = x
        x = x + 1
        return t
    add_macro(post_incr)

    def pre_decr((x)):
        x = x - 1
        return x
    add_macro(pre_decr)

    def post_decr((x)):
        t = x
        x = x + 1
        return t
    add_macro(post_decr)

    def add_set((x),v):
        x = x + v
        return x
    add_macro(add_set)

    def sub_set((x),v):
        x = x - v
        return x
    add_macro(sub_set)

    def mul_set((x),v):
        x = x * v
        return x
    add_macro(mul_set)

    def div_set((x),v):
        x = x / v
        return x
    add_macro(div_set)

    def mod_set((x),v):
        x = x % v
        return x
    add_macro(mod_set)

main()

def test():
    from macro import expand

    def f(x):
        i = 0
        while pre_incr(i) < len(x):
            if setq(c, x[i]) == 3:
                print c, 42
    x = expand(f)
    return x
    x(range(10))
        
