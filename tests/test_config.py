# -*- coding: utf-8 -*-
from taburet.test import TestServer
from taburet.config import Configuration

def pytest_funcarg__config(request):
    s = TestServer()
    return Configuration(s.get_db('test'))

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
        assert False, 'config.NotFound must be raised'
    except config.NotFound:
        pass

def test_config_value_update(config):
    result = config.inc('param')
    assert result == 1

    result = config.inc('param')
    assert result == 2

    result = config.dec('param')
    assert result == 1

def test_config_concurrent_value_update(config):
    def updater(value, is_raced=[False]):
        if not is_raced[0]:
            config.set('param', 5)
            is_raced[0] = True
        return value + 1

    config.set('param', 1)

    result = config.update('param', 0, updater)
    assert result  == 6
