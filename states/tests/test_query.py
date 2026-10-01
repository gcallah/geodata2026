from unittest.mock import patch

import pytest

import states.query as qry

TEST_ST = qry.TEST_STATE


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_check_valid_state(mock_is_db_up):
    ret = qry.check_valid_state(TEST_ST['state_code'],
                                TEST_ST['population'],
                                TEST_ST['capital'],
                                TEST_ST['area_sq_miles'],
                                TEST_ST['name'])
    assert ret


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_check_valid_state_bad_pop(mock_is_db_up):
    with pytest.raises(ValueError):
        ret = qry.check_valid_state(TEST_ST['state_code'],
                                    -23423,
                                    TEST_ST['capital'],
                                    TEST_ST['area_sq_miles'],
                                    TEST_ST['name'])


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_check_valid_state_code_too_short(mock_is_db_up):
    with pytest.raises(ValueError):
        ret = qry.check_valid_state('',
                                    TEST_ST['population'],
                                    TEST_ST['capital'],
                                    TEST_ST['area_sq_miles'],
                                    TEST_ST['name'])


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_check_valid_state_code_too_long(mock_is_db_up):
    with pytest.raises(ValueError):
        ret = qry.check_valid_state('X' * qry.STATE_CODE_LEN * 2,
                                    TEST_ST['population'],
                                    TEST_ST['capital'],
                                    TEST_ST['area_sq_miles'],
                                    TEST_ST['name'])


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_query(mock_is_db_up):
    states = qry.read()
    assert isinstance(states, dict)


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_check_valid_state_dup_code(mock_is_db_up):
    with pytest.raises(ValueError):
        qry.check_valid_state('AL',
                              TEST_ST['population'],
                              TEST_ST['capital'],
                              TEST_ST['area_sq_miles'],
                              TEST_ST['name'])


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_check_valid_state_no_capital(mock_is_db_up):
    with pytest.raises(ValueError):
        qry.check_valid_state(TEST_ST['state_code'],
                              TEST_ST['population'],
                              '',
                              TEST_ST['area_sq_miles'],
                              TEST_ST['name'])


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_check_valid_state_bad_area(mock_is_db_up):
    with pytest.raises(ValueError):
        qry.check_valid_state(TEST_ST['state_code'],
                              TEST_ST['population'],
                              TEST_ST['capital'],
                              0,
                              TEST_ST['name'])


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_check_valid_state_no_name(mock_is_db_up):
    with pytest.raises(ValueError):
        qry.check_valid_state(TEST_ST['state_code'],
                              TEST_ST['population'],
                              TEST_ST['capital'],
                              TEST_ST['area_sq_miles'],
                              '')


@pytest.fixture
def temp_state():
    yield TEST_ST
    with patch('states.query.is_db_up', return_value=True, autospec=True):
        qry.delete(TEST_ST['state_code'])


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_create(mock_is_db_up, temp_state):
    ret = qry.create(**temp_state)
    assert ret['name'] == temp_state['name']
    assert qry.exists(temp_state['state_code'])


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_create_dup(mock_is_db_up, temp_state):
    qry.create(**temp_state)
    with pytest.raises(ValueError):
        qry.create(**temp_state)


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_delete(mock_is_db_up, temp_state):
    code = temp_state['state_code']
    qry.create(**temp_state)
    assert code in qry.STATE_TEST_DATA
    deleted = qry.delete(code)
    assert deleted['name'] == temp_state['name']
    assert code not in qry.STATE_TEST_DATA
    assert not qry.exists(code)


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_delete_leaves_other_states(mock_is_db_up, temp_state):
    qry.create(**temp_state)
    others = {k: v for k, v in qry.STATE_TEST_DATA.items()
              if k != temp_state['state_code']}
    qry.delete(temp_state['state_code'])
    assert qry.STATE_TEST_DATA == others


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_delete_missing(mock_is_db_up):
    assert 'ZZ' not in qry.STATE_TEST_DATA
    assert qry.delete('ZZ') is None


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_delete_db_down(mock_is_db_up, temp_state):
    qry.create(**temp_state)
    mock_is_db_up.return_value = False
    assert qry.delete(temp_state['state_code']) is None
    assert temp_state['state_code'] in qry.STATE_TEST_DATA


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_check_valid_state_update_missing(mock_is_db_up):
    with pytest.raises(ValueError):
        qry.check_valid_state('ZZ',
                              TEST_ST['population'],
                              TEST_ST['capital'],
                              TEST_ST['area_sq_miles'],
                              TEST_ST['name'],
                              is_update=True)


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_check_valid_state_update_existing(mock_is_db_up):
    assert qry.check_valid_state('AL',
                                 TEST_ST['population'],
                                 TEST_ST['capital'],
                                 TEST_ST['area_sq_miles'],
                                 TEST_ST['name'],
                                 is_update=True)


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_update(mock_is_db_up, temp_state):
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


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_update_leaves_other_states(mock_is_db_up, temp_state):
    qry.create(**temp_state)
    others = {k: dict(v) for k, v in qry.STATE_TEST_DATA.items()
              if k != temp_state['state_code']}
    qry.update(temp_state['state_code'], 1, 'C', 1.0, 'N')
    for code, data in others.items():
        assert qry.STATE_TEST_DATA[code] == data


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_update_missing(mock_is_db_up):
    assert 'ZZ' not in qry.STATE_TEST_DATA
    with pytest.raises(ValueError):
        qry.update('ZZ', 1, 'C', 1.0, 'N')
    assert 'ZZ' not in qry.STATE_TEST_DATA


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_update_invalid_leaves_state_unchanged(mock_is_db_up, temp_state):
    code = temp_state['state_code']
    qry.create(**temp_state)
    before = dict(qry.STATE_TEST_DATA[code])
    with pytest.raises(ValueError):
        qry.update(code, -1, 'C', 1.0, 'N')
    assert qry.STATE_TEST_DATA[code] == before


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_update_db_down(mock_is_db_up, temp_state):
    code = temp_state['state_code']
    qry.create(**temp_state)
    before = dict(qry.STATE_TEST_DATA[code])
    mock_is_db_up.return_value = False
    assert qry.update(code, 1, 'C', 1.0, 'N') is None
    assert qry.STATE_TEST_DATA[code] == before


def test_create_db_down(temp_state):
    with patch('states.query.is_db_up', return_value=False, autospec=True):
        assert qry.create(**temp_state) is None
    assert temp_state['state_code'] not in qry.STATE_TEST_DATA


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_needs_db_calls_fn_when_up(mock_is_db_up):
    @qry.needs_db
    def fn(x, y=0):
        return x + y
    assert fn(1, y=2) == 3


def test_needs_db_returns_none_when_down():
    calls = []

    @qry.needs_db
    def fn():
        calls.append(1)
        return 'called'
    with patch('states.query.is_db_up', return_value=False, autospec=True):
        assert fn() is None
    assert calls == []


def test_needs_db_keeps_name():
    assert qry.create.__name__ == 'create'
    assert 'Create a new state' in qry.create.__doc__


@pytest.mark.parametrize('fn, args', [
    (qry.read, ()),
    (qry.exists, ('AL',)),
    (qry.delete, ('AL',)),
])
def test_db_down_returns_none(fn, args):
    before = dict(qry.STATE_TEST_DATA)
    with patch('states.query.is_db_up', return_value=False, autospec=True):
        assert fn(*args) is None
    assert qry.STATE_TEST_DATA == before
