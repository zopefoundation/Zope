from OFS.SimpleItem import Item
import Globals, Acquisition

class Ac_Permissions(Globals.Persistent, Item, Acquisition.Implicit):
    """Provide very simple tabular editing
    """
    id='instance____ac_permissions__'
    title='Instance Permissions'
    meta_type=title
    names='Permission name', 'Permission methods'
    data=()
    manage_options=(
        {'label': 'Permissions', 'action': 'manage_main'},
        )
    icon=''

    def __getitem__(self, i): return self.data[i]
    def __len__(self): return length(self.data)

    manage_main=Globals.HTMLFile('method_select', globals(),
                                 selectops='multiple size=5')
    def manage_edit(self, REQUEST, names=[], newname='', newmethods=[]):
        " "
        data=[]
        for i in range(len(names)):
            name=names[i]
            methods=REQUEST.get('methods%s' % i, None)
            if methods: data.append((name, tuple(methods)))
        if newname and newmethods:
            data.append(newname, tuple(newmethods))

        self.data=data
        return self.manage_main(self, REQUEST)
