
# Product registry and new product factory model.  There will be a new
# mechanism for defining actions for meta types.  If an action is of
# the form:
#
#  manage_addProduct-name-factoryid
#
# Then the machinery that invokes an add-product form
# will return:
# ....what?

from OFS.Folder import Folder

class ProductRegistry:
    # This class implements a protocol for registering products that
    # are defined through the web.  It also provides methods for
    # getting hold of the Product Registry, Control_Panel.Products.

    # This class is a mix-in class for the top-level application object.

    def _getProducts(self): return self.Control_Panel.Products

    _product_meta_types=()
    
    def _manage_remove_product_meta_type(self, product, id, meta_type):
        self._product_meta_types=filter(lambda mt, nmt=meta_type:
                                        mt['name']!=nmt,
                                        self._product_meta_types)
        
    def _manage_add_product_meta_type(self, product, id, meta_type):
        if filter(lambda mt, nmt=meta_type:
                  mt['name']==nmt,
                  self.all_meta_types()):
            raise 'Type Exists', (
                'The type <em>%s</em> is already defined.')
        
        self._product_meta_types=self._product_meta_types+({
            'name': meta_type,
            'action': ('manage_addProduct/%s/%s' % (product.id, id)),
            },)
