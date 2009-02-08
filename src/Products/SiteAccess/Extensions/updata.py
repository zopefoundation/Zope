def updata(self):
    """Convert SiteAccess objects from 1.x to 2.x"""
    _cvt_btr(self.REQUEST['PARENTS'][-1])
    from App.Dialogs import MessageDialog
    return MessageDialog(title='Update Complete', message='Update Complete!',
                         action='./manage_main')

def _cvt_btr(app):
    from ZPublisher.BeforeTraverse import NameCaller
    from ZPublisher.BeforeTraverse import rewriteBeforeTraverse
    from Products.SiteAccess.AccessRule import AccessRule
    stack = [app]
    while stack:
        o = stack.pop()
        ov = getattr(o, 'objectValues', None)
        if ov is not None:
            stack.extend(list(ov()))
            btr = getattr(o, '__before_traverse__', None)
            if btr and type(btr) == type({}):
                touched = 0
                for k, v in btr.items():
                    if type(v) is type(''):
                        touched = 1
                        if k[1] == 'AccessRule':
                            btr[k] = AccessRule(v)
                        else:
                            btr[k] = NameCaller(v)
                if touched:
                    rewriteBeforeTraverse(o, btr)

if __name__ == '__main__':
    import Zope2
    import transaction
    print "Converting SiteAccess objects from 1.x to 2.x ..."
    app = Zope2.app()
    _cvt_btr(app)
    transaction.commit()
    print "Done."
