from unittest.mock import patch

import pytest

import states.query as qry

TEST_ST = qry.TEST_STATE


def test_check_valid_state():
    ret = qry.check_valid_state(TEST_ST['state_code'],
                                TEST_ST['population'],
                                TEST_ST['capital'],
                                TEST_ST['area_sq_miles'],
                                TEST_ST['name'])
    assert ret


def test_check_valid_state_bad_pop():
    with pytest.raises(ValueError):
        ret = qry.check_valid_state(TEST_ST['state_code'],
                                    -23423,
                                    TEST_ST['capital'],
                                    TEST_ST['area_sq_miles'],
                                    TEST_ST['name'])


def test_check_valid_state_code_too_short():
    with pytest.raises(ValueError):
        ret = qry.check_valid_state('',
                                    TEST_ST['population'],
                                    TEST_ST['capital'],
                                    TEST_ST['area_sq_miles'],
                                    TEST_ST['name'])


def test_check_valid_state_code_too_long():
    with pytest.raises(ValueError):
        ret = qry.check_valid_state('X' * qry.STATE_CODE_LEN * 2,
                                    TEST_ST['population'],
                                    TEST_ST['capital'],
                                    TEST_ST['area_sq_miles'],
                                    TEST_ST['name'])


def test_query():
    states = qry.read()
    assert isinstance(states, dict)


def test_check_valid_state_dup_code():
    with pytest.raises(ValueError):
        qry.check_valid_state('AL',
                              TEST_ST['population'],
                              TEST_ST['capital'],
                              TEST_ST['area_sq_miles'],
                              TEST_ST['name'])


def test_check_valid_state_no_capital():
    with pytest.raises(ValueError):
        qry.check_valid_state(TEST_ST['state_code'],
                              TEST_ST['population'],
                              '',
                              TEST_ST['area_sq_miles'],
                              TEST_ST['name'])


def test_check_valid_state_bad_area():
    with pytest.raises(ValueError):
        qry.check_valid_state(TEST_ST['state_code'],
                              TEST_ST['population'],
                              TEST_ST['capital'],
                              0,
                              TEST_ST['name'])


def test_check_valid_state_no_name():
    with pytest.raises(ValueError):
        qry.check_valid_state(TEST_ST['state_code'],
                              TEST_ST['population'],
                              TEST_ST['capital'],
                              TEST_ST['area_sq_miles'],
                              '')


@pytest.fixture
def temp_state():
    yield TEST_ST
    qry.delete(TEST_ST['state_code'])


def test_create(temp_state):
    ret = qry.create(**temp_state)
    assert ret['name'] == temp_state['name']
    assert qry.exists(temp_state['state_code'])


def test_create_dup(temp_state):
    qry.create(**temp_state)
    with pytest.raises(ValueError):
        qry.create(**temp_state)


def test_delete(temp_state):
    code = temp_state['state_code']
    qry.create(**temp_state)
    assert code in qry.STATE_TEST_DATA
    deleted = qry.delete(code)
    assert deleted['name'] == temp_state['name']
    assert code not in qry.STATE_TEST_DATA
    assert not qry.exists(code)


def test_delete_leaves_other_states(temp_state):
    qry.create(**temp_state)
    others = {k: v for k, v in qry.STATE_TEST_DATA.items()
              if k != temp_state['state_code']}
    qry.delete(temp_state['state_code'])
    assert qry.STATE_TEST_DATA == others


def test_delete_missing():
    assert 'ZZ' not in qry.STATE_TEST_DATA
    assert qry.delete('ZZ') is None


def test_delete_db_down(temp_state):
    qry.create(**temp_state)
    with patch('states.query.is_db_up', return_value=False, autospec=True):
        assert qry.delete(temp_state['state_code']) is None
    assert temp_state['state_code'] in qry.STATE_TEST_DATA
