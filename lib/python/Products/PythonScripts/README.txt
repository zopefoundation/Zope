Python Scripts


  The Python Scripts product provides support for restricted execution of
  Python scripts, exposing them as callable objects within the Zope 
  environment.

  Providing access to extra modules

    Python script objects have a limited number of "safe" modules 
    available to them by default. In the course of working with Zope,
    you will probably wish to make other modules available to script
    objects. 

    The Utility.py module in the PythonScripts products provides a 
    simple way to make modules available for use by script objects 
    on a site-wide basis. Before making a module available to Python
    scripts, you should carefully consider the potential for abuse 
    or misuse of the module, since all users with permission to 
    create and edit Python scripts will be able to use any functions
    and classes defined in the module. In some cases, you may want to
    create a custom module that just imports a subset of names from 
    another module and make that custom module available to reduce 
    the risk of abuse.

    The easiest way to make modules available to Python scripts on 
    your site is to create a new directory in your Products directory
    containing an "__init__.py" file. At Zope startup time, this 
    "product" will be imported, and any module assertions you make
    in the __init__.py will take effect. Here's how to do it:

      o In your Products directory (either in lib/python of your 
        Zope installation or in the root of your Zope install,
        depending on your deployment model), create a new directory
        with a name like "GlobalModules".

      o In the new directory, create a file named "__init__.py".

      o Edit the __init__.py file, and add calls to the 'allow_module'
        function (located in the Products.PythonScripts.Utility module),
        passing the names of modules to be enabled for use by scripts.
        For example:

          # Global module assertions for Python scripts
          from Products.PythonScripts.Utility import allow_module

          allow_module('base64')
          allow_module('re')
          allow_module('DateTime.DateTime')

        This example adds the modules 'base64', 're' and the 'DateTime'
        module in the 'DateTime' package for use by Python scripts. Note
        that for packages (dotted names), each module in the package path
        will become available to script objects.

      o Restart your Zope server. After restarting, the modules you enabled
        in your custom product will be available to Python scripts.

    NB --  Placing security assestions within the package/module you are trying 
           to import will not work unless that package/module is located in
           your Products directory.
 
           This is because that package/module would have to be imported for its
           included security assertions to take effect, but to do
           that would require importing a module without any security
           declarations, which defeats the point of the restricted
           python environment.

           Products work differently as they are imported at Zope startup.
           By placing a package/module in your Products directory, you are
           asserting, among other things, that it is safe for Zope to check 
           that package/module for security assertions. As a result, please 
           be careful when place packages or modules that are not Zope Products 
           in the Products directory.
        
