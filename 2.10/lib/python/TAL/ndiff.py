#! /usr/bin/env python
# BBB 2005/05/01 -- to be removed after 12 months
import zope.deprecation
zope.deprecation.moved('zope.tal.ndiff', '2.12')

if __name__ == '__main__':
    import sys
    args = sys.argv[1:]
    if "-profile" in args:
        import profile, pstats
        args.remove("-profile")
        statf = "ndiff.pro"
        profile.run("main(args)", statf)
        stats = pstats.Stats(statf)
        stats.strip_dirs().sort_stats('time').print_stats()
    else:
        main(args)
