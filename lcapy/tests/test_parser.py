from nose.tools import *
import sys
sys.path.append('..')

from lcapy.parser import Parser
import lcapy.schemcpts as schemcpts
import lcapy.grammar as grammar

parser = Parser(schemcpts, grammar)
parse = parser.parse

@raises(ValueError)
def test_Exception1():
    '''Test missing arg'''

    parse('V1 2')

@raises(ValueError)
def test_Exception2():
    '''Test too many args'''

    parse('V1 2 3 4 5 6')

@raises(ValueError)
def test_Exception3():
    '''Test too many args'''

    parse('V1 2 3 dc 4 5 6')

@raises(ValueError)
def test_Exception4():
    '''Test unknown component'''

    parse('A1 1 2')

def test_V1():
    '''Test voltage source'''
    
    assert_equals(type(parse('V1 1 2')), schemcpts.newclasses['V'], 'Class not V')


def test_Vdc1():
    '''Test dc voltage source'''
    
    assert_equals(type(parse('V1 1 2 dc')), schemcpts.newclasses['Vdc'], 'Class not V')




    
