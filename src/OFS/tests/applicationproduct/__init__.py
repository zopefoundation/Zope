""" This product uses the application during product initialization
    to create a subfolder in the root folder. This is similar to what
    Producs.Sessions and Products.TemporaryFolder are doing.
"""


def initialize(context):
    import transaction
    from OFS.Folder import Folder

    app = context.getApplication()
    folder = Folder('some_folder')
    app._setObject('some_folder', folder)
    transaction.commit()
