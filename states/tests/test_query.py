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


def test_check_valid_state_update_missing():
    with pytest.raises(ValueError):
        qry.check_valid_state('ZZ',
                              TEST_ST['population'],
                              TEST_ST['capital'],
                              TEST_ST['area_sq_miles'],
                              TEST_ST['name'],
                              is_update=True)


def test_check_valid_state_update_existing():
    assert qry.check_valid_state('AL',
                                 TEST_ST['population'],
                                 TEST_ST['capital'],
                                 TEST_ST['area_sq_miles'],
                                 TEST_ST['name'],
                                 is_update=True)


def test_update(temp_state):
    code = temp_state['state_code']
    qry.create(**temp_state)
    ret = qry.update(code, 2000000, 'New Capital', 60000.5, 'New Name')
    assert qry.STATE_TEST_DATA[code] == {
        "population": 2000000,
        "capital": 'New Capital',
        "area_sq_miles": 60000.5,
        "name": 'New Name',
    }
    assert ret == qry.STATE_TEST_DATA[code]


def test_update_leaves_other_states(temp_state):
    qry.create(**temp_state)
    others = {k: dict(v) for k, v in qry.STATE_TEST_DATA.items()
              if k != temp_state['state_code']}
    qry.update(temp_state['state_code'], 1, 'C', 1.0, 'N')
    for code, data in others.items():
        assert qry.STATE_TEST_DATA[code] == data


def test_update_missing():
    assert 'ZZ' not in qry.STATE_TEST_DATA
    with pytest.raises(ValueError):
        qry.update('ZZ', 1, 'C', 1.0, 'N')
    assert 'ZZ' not in qry.STATE_TEST_DATA


def test_update_invalid_leaves_state_unchanged(temp_state):
    code = temp_state['state_code']
    qry.create(**temp_state)
    before = dict(qry.STATE_TEST_DATA[code])
    with pytest.raises(ValueError):
        qry.update(code, -1, 'C', 1.0, 'N')
    assert qry.STATE_TEST_DATA[code] == before


def test_update_db_down(temp_state):
    code = temp_state['state_code']
    qry.create(**temp_state)
    before = dict(qry.STATE_TEST_DATA[code])
    with patch('states.query.is_db_up', return_value=False, autospec=True):
        assert qry.update(code, 1, 'C', 1.0, 'N') is None
    assert qry.STATE_TEST_DATA[code] == before


def test_create_db_down(temp_state):
    with patch('states.query.is_db_up', return_value=False, autospec=True):
        assert qry.create(**temp_state) is None
    assert temp_state['state_code'] not in qry.STATE_TEST_DATA
