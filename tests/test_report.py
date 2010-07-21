# -*- coding: utf-8 -*-
import sys, os.path

SRC_PATH = os.path.abspath(os.path.join(os.path.split(__file__)[0], '..', 'src'))
sys.path.insert(0, SRC_PATH)

from taburet.report import *

def pytest_funcarg__sheet(request):
    return Worksheet('some') 

def test_cell_access(sheet):
    sheet[0:0].value = 5
    sheet[1:3].value = 'значение'
    
    assert sheet._cells[0][0].value == 5
    assert sheet._cells[1][3].value == 'значение'
    
def test_row_access(sheet):
    assert sheet[3:].index == 3
    
def test_column_access(sheet):
    assert sheet[:5].index == 5    