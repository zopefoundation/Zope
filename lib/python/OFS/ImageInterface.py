from Zope.Interfaces.Interface import Interface

from FileInterface import FileInterface

class Image:
    """
    Description of the Image interface
    """

    __extends__ = (FileInterface,)
    
    def update_data(self, data, content_type=None, size=None):
        """

        Replaces the Image with 'data'.

        """

    def tag(self, height=None, width=None, alt=None,
            scale=0, xscale=0, yscale=0, **args):
        """

        Generate an HTML IMG tag for this image, with customization.
        Arguments to self.tag() can be any valid attributes of an IMG
        tag.  'src' will always be an absolute pathname, to prevent
        redundant downloading of images. Defaults are applied
        intelligently for 'height', 'width', and 'alt'. If specified,
        the 'scale', 'xscale', and 'yscale' keyword arguments will be
        used to automatically adjust the output height and width
        values of the image tag.

        """
        
ImageInterface=Interface(Image) # create the interface object



