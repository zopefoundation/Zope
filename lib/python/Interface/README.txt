Python Interfaces - The Scarecrow Implementation

This document describes my implementation of the Python interfaces
scarecrow proposal.  

Status

  This is a first-cut implementation of the proposal.  My primary goal
  is to shed light on some ideas and to provide a framework for
  concrete discussion.

  This implementation has had minimal testing. I expect many aspects
  of the implementation to evolve over time.

Basic assumptions:

  Interfaces are *not* classes:
    
    o Interfaces have their own "hierarchy" (DAG really)
    
    o Interfaces are objects that provide a protocol for
    	querying attributes (including methods) defined by an
    	an interface:
    
    	  names() -- return a sequence of defined names
    
    	  getDescriptionFor(name, [default]) --
    	     Get a description of a name.
    
    o You cannot mix interfaces and classes in base-class lists.
    
  There are utilities and methods for computing implied interfaces
  from classes and for computing "defered" classes from interfaces.

  Why aren't interface classes?  Interfaces perform a different
  function that classes.  Classes are for sharing implementation.
  Interfaces are for denoting, defining, and documenting abstract
  behavior.      

Details

  Software layout

    There is an 'Interface' package that exports a variety of useful
    facilities.  These are described below.

  Creating Interfaces

    Interfaces can be created in several ways.  The class statement
    can be used with one or more interfaces provided as base classes.
    This approach is convenient, syntactically, although it is a
    little missleading, since interfaces are *not* classes.  A minimal
    interface that can be used as a base is Interface.Base.
  
    You can also call Interface.new:
  
      new(name, [bases, attrs, __doc__]) --
  
	Create a new interface.  The arguments are:
  
	  name -- the interface name
  
	  bases -- a sequence of "base" interfaces.  Base interfaces
	    are "extended" by the new interface.
  
	  attrs -- an object that conforms to
	    'Interfaces.Standard.Dictionary' that provides attributes
	    defined by an interface.  The attributes should be
	    'Interface.Attribute objects'.
  
    Finally you can compute an implied interface from a class by calling
    'Interface.impliedInterface': 
  
      impliedInterface(klass, [__name__, __doc__])
  
	 klass -- a class from which to create an interface.
  
	 __name__ -- The name of the interface.  The default name is the
	    class name with the suffix "Interface".
  
	__doc__ -- a doc string for the interface.  The default doc
	    string is the class doc string.
  
	The generated interface has attributes for each public method
	defined in or inherited by the interface. A method is considered
	public if it has a non-empty doc string and if it's name does
	not begin with '_' or does begin and end with '__' and is
	greater than 4 characters in length.
  
    Note that computing an interface from a class does not automatically
    assert that the class implements an interface.

    Here's an example:

      class X:

        def foo(self, a, b):
          ...

      XInterface=Interface.impliedInterface(X)
      X.__implements__=XInterface

  Interface assertions

    Objects can assert that they implement one or more interfaces.
    They do this by by defining an '__interfaces__' attribute that is
    bound to an interface assertion.

    An *interface assertion* is either: 

      - an Interface or

      - a sequence of interface assertions.

    Here are some examples of interface assertions:

      I1

      I1, I2

      I1, (I2, I3)

    where I1, I2, and I3 are interfaces.

    Classes may provide (default) assertions for their instances
    (and subclass instances).  The usual inheritence rules apply.
    Note that the definition of interface assertions makes composition
    of interfaces straightforword.  For example:

      class A:

        __implements__ = I1, I2 

        ...

      class B

        __implements__ = I3, I4

      class C(A. B):
        ...

      class D:
        
        __implements__ = I5

      class E:

        __implements__ = I5, A.__implements__
      
  Special-case handling of classes

    Special handling is required for Python classes to make assertions
    about the interfaces a class implements, as opposed to the
    interfaces that the instances of the class implement.  You cannot
    simply define an '__implements__' attribute for the class because
    class "attributes" apply to instances.

    By default, classes are assumed to implement the Interface.Standard.Class
    interface.  A class may override the default by providing a
    '__class_implements__' attribute which will be treated as if it were
    the '__implements__' attribute of the class.

  Testing assertions

    You can test whether an object implements an interface by calling
    the 'implementedBy' method of the interface and passing the
    object::

      I1.implementedBy(x)

    Similarly, you can test whether, by default, instances of a class
    implement an interface by calling the 'implementedByInstancesOf'
    method on the interface and passing the class::
  
      I1.implementedByInstancesOf(A)

  Testing interfaces

    You can test whether one interface extends another by calling the
    extends method on an interface:

      I1.extends(I2)

    Note that an interface does not extend itself.

  Interface attributes

    The purpose of an interface is to describe behavior, not to
    provide implementation.  In a similar fashion the attributes of
    an interface describe and document the attributes provided by an
    object that implements the interface.

    There are currently two kinds of supported attributes:

      Interface.Attribute -- The objects describe interface
        attributes.  They define at least names and doc strings and
        may define other information as well.

      Interface.Method -- These are interface attributes that
        describe methods.  They *may* define information about method
        signatures. (Note Methods are kinds of Attributes.)

    When a class statement is used to define an interface, method
    definitions may be provided.  These get converted to Method
    objects during interface creation.  For examle:

      class I1(Interface.Base):
         
        __name__=Attribute("The object's name")

        def foo(self, a, b):
           "blah blah"

    defines an interface, 'I1' that has two attributes, '__name__' and
    'foo'. The attribute 'foo' is a Method instance.  It is *not* a
    Python method.

    It is my expectation that Attribute objects will eventually be
    able to provide all sorts of interesting meta-data.  

  Defered classes

    You cannot use interfaces as base classes.  You can, however, 
    create "defered" classes from an interface:

      class StackInterface(Interface.Base):

         def push(self, v):
            "Add a value to the top of a stack"

         def pop(self):
            "Remove and return an object from the top of the stack"

      class Stack(StackInterface.defered()):
         "This is supposed to implement a stack"

         __implements__=StackInterface

    Attempts to call methods inherited from a defered class will
    raise Interface.BrokenImplementation exceptions.

  Trial baloon: abstract implementations

    Tim Peter's has expressed the desire to provide abstract
    implementations in an interface definitions, where, presumably, an
    abstract implementation uses only features defined by the
    interface.  For example:

      class ListInterface(Interface.Standard.MutableSequence):

        def append(self, v):
           "add a value to the end of the object"

	def push(self, v):
           "add a value to the end of the object"
           self.append(v)

    Perhaps if a method definition has a body (other than a doc
    string) then the corresponding method in the defered class
    will not be defered. This would not be hard to do in CPython
    if I cheat and sniff at method bytecodes.

  Standard interfaces

    The module Interface.Standard defines interfaces for standard
    python obnjects.

    This module, and the modules it uses need a lot more work!

  Handling existing built-in types

    A hack is provided to allow implementation assertions to be made
    for builtin types.  Interfaces.assertTypeImplements can be called
    to assert that instances of a built-in type implement one or more
    interfaces::

       Util.assertTypeImplements(
         type(1L), 
         (AbritraryPrecision, BitNumber, Signed))


    

Issues

  o What should the objects that define attributes look like?
    They shouldn't *be* the attributes, but should describe the
    the attributes.

    Note that we've made a first cut with 'Attribute' and
    'Method' objects.

  o There are places in the current implementation that use
    'isinstance' that should be changed to use interface
    checks.

  o When the interface interfaces are finalized, C implementations
    will be highly desirable for performance reasons.

  o Alot more work is needed on the standard interface hierarchy.    

  ...
