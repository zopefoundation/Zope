from distutils.core import setup, Extension
setup(name="ExtensionClass", version="2.0",
      ext_modules=[
         Extension("_ExtensionClass", ["_ExtensionClass.c"],
                   depends = ["ExtensionClass.h", "pickle/pickle.c"],
                   ),
         ])

