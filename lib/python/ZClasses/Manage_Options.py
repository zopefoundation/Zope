from OFS.SimpleItem import Item
import Globals, Acquisition

class Manage_Options(Globals.Persistent, Item, Acquisition.Implicit):
    """Provide very simple tabular editing
    """
    id='instance__manage_options'
    title='Instance view definitions'
    meta_type=title
    names='Permission name', 'Permission methods'
    data=()
    ddata=()
    manage_options=(
        {'label': 'Options', 'action': 'manage_main'},
        )
    icon=''


    def __getitem__(self, i): return self.ddata[i]
    def __len__(self): return len(self.data)

    manage_main=Globals.HTMLFile('method_select', globals(),
                                 selectops='')
    def manage_edit(self, REQUEST, names=[], newname='', newmethods=[]):
        " "
        data=[]
        for i in range(len(names)):
            name=names[i]
            methods=REQUEST.get('methods%s' % i, None)
            if methods: data.append((name, tuple(methods)))
        if newname and newmethods:
            data.append((newname, tuple(newmethods)))

        self.data=data
	__traceback_info__=data
        self.ddata=map(lambda i:
                       {'label': i[0], 'action': i[1][0]},
                       data)
        
        return self.manage_main(self, REQUEST)
