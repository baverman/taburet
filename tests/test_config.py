# -*- coding: utf-8 -*-

import sys, os.path

from couchdbkit import Server

SRC_PATH = os.path.abspath(os.path.join(os.path.split(__file__)[0], '..', 'src'))
sys.path.insert(0, SRC_PATH)

from taburet.config import Configuration

def pytest_funcarg__config(request):
    s = Server()
    
    if 'test' in s:
        del s['test']
    
    db = s.create_db('test')
    
    return Configuration(db)

def test_config_must_be_able_to_save_and_get_param(config):
    config.set('param', 5)
    assert config.get('param') == 5
    
def test_config_must_be_able_to_replace_param_value(config):
    config.set('param', 'value')
    config.set('param', 'newvalue')
    
    assert config.get('param') == 'newvalue'
    
def test_config_must_return_default_value_if_param_not_found(config):
    assert config.get('nonexisted', None) == None
    assert config.get('nonexisted', False) == False
    assert config.get('nonexisted', 'default') == 'default'
    
def test_config_must_raise_exception_if_param_not_found_and_default_value_not_specified(config):
    try:
        config.get('nonexisted')
        assert False, 'Configuration.NotFound must be raised'
    except Configuration.NotFound:
        pass