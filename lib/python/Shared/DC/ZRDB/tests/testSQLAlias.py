#!/usr/bin/env python
#----------------------------------------------------------------------
# Unit tests for SQLAlias objects
#----------------------------------------------------------------------
# __version__ = "$Revision: 1.2 $"[11:-2]

from unittest import TestSuite, TestCase
from Shared.DC.ZRDB.RDB import SQLAlias, NoBrains
from Acquisition import Implicit
from Record import Record
import sys, ExtensionClass



# A plain extension class to use in comparison with the
# Record extension class.
class TestObject(ExtensionClass.Base):
    pass

# A helper to set up an initialized TestObject.
def make_object():
    object=TestObject()
    dict = object.__dict__
    dict['RealName']='RealName value'
    dict['realname']=SQLAlias('RealName')
    return object


# Mimic the record objects created on the fly within the
# DatabaseResults class in RDB.py with a simple schema.
class r(Record, Implicit, NoBrains, NoBrains):
    'Result record class'
    __record_schema__={'RealName' : 0}

# A helper to set up an initialized record object.
def make_record():
    object=r()
    dict = object.__dict__
    dict['RealName']='RealName value'
    dict['realname']=SQLAlias('RealName')
    return object


# A helper to get the refcount of the SQLAlias class.
def refcount():
    return sys.getrefcount(SQLAlias)



class ClassMemLeakTest(TestCase):
    """Test for memory leak of SQLAliases accessed through a
       basic ExtensionClass instance."""

    def runTest(self):
        # get starting refcount
        start_refs=refcount()
        
        # set up the instance with an alias, access through the
        # alias, then delete the instance; refcount should be
        # back to start_refs after the delete.
        object=make_object()
        value=object.realname
        del object

        # check the refcount
        assert start_refs == refcount(), \
        'SQLAlias leaked after access through extension class instance!'


class RecordMemLeakTest(TestCase):
    """Test for memory leak of SQLAliases accessed through a
       Record instance."""
    
    def runTest(self):
        # get starting refcount
        start_refs=refcount()
        
        # set up the instance with an alias, access through the
        # alias, then delete the instance; refcount should be
        # back to start_refs after the delete.
        object=make_record()
        value=object.realname
        del object

        # check the refcount
        assert start_refs == refcount(), \
        'SQLAlias leaked after access through a Record instance!'



def test_suite():
    suite=TestSuite()
    suite.addTest(ClassMemLeakTest())
    suite.addTest(RecordMemLeakTest())
    return suite


if __name__=='__main__':
    # Run tests if run as a standalone script
    from unittest import TextTestRunner
    TextTestRunner().run(test_suite())

