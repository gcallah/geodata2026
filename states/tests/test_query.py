from unittest.mock import patch

import pytest

import counties.query as cqry
import states.query as qry

TEST_ST = qry.TEST_STATE


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_check_valid_state(mock_is_db_up):
    ret = qry.check_valid_state(TEST_ST[qry.STATE_CODE],
                                TEST_ST[qry.POPULATION],
                                TEST_ST[qry.CAPITAL],
                                TEST_ST[qry.AREA],
                                TEST_ST[qry.NAME],
                                TEST_ST[qry.LATITUDE],
                                TEST_ST[qry.LONGITUDE])
    assert ret


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_check_valid_state_bad_pop(mock_is_db_up):
    with pytest.raises(ValueError):
        ret = qry.check_valid_state(TEST_ST[qry.STATE_CODE],
                                    -23423,
                                    TEST_ST[qry.CAPITAL],
                                    TEST_ST[qry.AREA],
                                    TEST_ST[qry.NAME],
                                    TEST_ST[qry.LATITUDE],
                                    TEST_ST[qry.LONGITUDE])


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_check_valid_state_code_too_short(mock_is_db_up):
    with pytest.raises(ValueError):
        ret = qry.check_valid_state('',
                                    TEST_ST[qry.POPULATION],
                                    TEST_ST[qry.CAPITAL],
                                    TEST_ST[qry.AREA],
                                    TEST_ST[qry.NAME],
                                    TEST_ST[qry.LATITUDE],
                                    TEST_ST[qry.LONGITUDE])


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_check_valid_state_code_too_long(mock_is_db_up):
    with pytest.raises(ValueError):
        ret = qry.check_valid_state('X' * qry.STATE_CODE_LEN * 2,
                                    TEST_ST[qry.POPULATION],
                                    TEST_ST[qry.CAPITAL],
                                    TEST_ST[qry.AREA],
                                    TEST_ST[qry.NAME],
                                    TEST_ST[qry.LATITUDE],
                                    TEST_ST[qry.LONGITUDE])


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_query(mock_is_db_up):
    states = qry.read()
    assert isinstance(states, dict)


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_check_valid_state_dup_code(mock_is_db_up):
    with pytest.raises(ValueError):
        qry.check_valid_state('AL',
                              TEST_ST[qry.POPULATION],
                              TEST_ST[qry.CAPITAL],
                              TEST_ST[qry.AREA],
                              TEST_ST[qry.NAME],
                              TEST_ST[qry.LATITUDE],
                              TEST_ST[qry.LONGITUDE])


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_check_valid_state_no_capital(mock_is_db_up):
    with pytest.raises(ValueError):
        qry.check_valid_state(TEST_ST[qry.STATE_CODE],
                              TEST_ST[qry.POPULATION],
                              '',
                              TEST_ST[qry.AREA],
                              TEST_ST[qry.NAME],
                              TEST_ST[qry.LATITUDE],
                              TEST_ST[qry.LONGITUDE])


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_check_valid_state_bad_area(mock_is_db_up):
    with pytest.raises(ValueError):
        qry.check_valid_state(TEST_ST[qry.STATE_CODE],
                              TEST_ST[qry.POPULATION],
                              TEST_ST[qry.CAPITAL],
                              0,
                              TEST_ST[qry.NAME],
                              TEST_ST[qry.LATITUDE],
                              TEST_ST[qry.LONGITUDE])


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_check_valid_state_no_name(mock_is_db_up):
    with pytest.raises(ValueError):
        qry.check_valid_state(TEST_ST[qry.STATE_CODE],
                              TEST_ST[qry.POPULATION],
                              TEST_ST[qry.CAPITAL],
                              TEST_ST[qry.AREA],
                              '',
                              TEST_ST[qry.LATITUDE],
                              TEST_ST[qry.LONGITUDE])


@pytest.fixture
def temp_state():
    yield TEST_ST
    with patch('states.query.is_db_up', return_value=True, autospec=True):
        qry.delete(TEST_ST[qry.STATE_CODE])


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_create(mock_is_db_up, temp_state):
    ret = qry.create(**temp_state)
    assert ret[qry.NAME] == temp_state[qry.NAME]
    assert qry.exists(temp_state[qry.STATE_CODE])


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_create_dup(mock_is_db_up, temp_state):
    qry.create(**temp_state)
    with pytest.raises(ValueError):
        qry.create(**temp_state)


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_delete(mock_is_db_up, temp_state):
    code = temp_state[qry.STATE_CODE]
    qry.create(**temp_state)
    assert code in qry.STATE_TEST_DATA
    deleted = qry.delete(code)
    assert deleted[qry.NAME] == temp_state[qry.NAME]
    assert code not in qry.STATE_TEST_DATA
    assert not qry.exists(code)


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_delete_leaves_other_states(mock_is_db_up, temp_state):
    qry.create(**temp_state)
    others = {k: v for k, v in qry.STATE_TEST_DATA.items()
              if k != temp_state[qry.STATE_CODE]}
    qry.delete(temp_state[qry.STATE_CODE])
    assert qry.STATE_TEST_DATA == others


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_delete_state_with_counties(mock_is_db_up):
    assert cqry.has_counties('AL')
    before = dict(qry.STATE_TEST_DATA['AL'])
    with pytest.raises(ValueError):
        qry.delete('AL')
    assert qry.STATE_TEST_DATA['AL'] == before


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_delete_state_after_counties_gone(mock_is_db_up, temp_state):
    code = temp_state[qry.STATE_CODE]
    qry.create(**temp_state)
    county = {**cqry.TEST_COUNTY, cqry.STATE_CODE: code}
    cqry.create(**county)
    with pytest.raises(ValueError):
        qry.delete(code)
    cqry.delete(code, county[qry.NAME])
    assert qry.delete(code)[qry.NAME] == temp_state[qry.NAME]
    assert not qry.exists(code)


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_delete_missing(mock_is_db_up):
    assert 'ZZ' not in qry.STATE_TEST_DATA
    assert qry.delete('ZZ') is None


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_delete_db_down(mock_is_db_up, temp_state):
    qry.create(**temp_state)
    mock_is_db_up.return_value = False
    assert qry.delete(temp_state[qry.STATE_CODE]) is None
    assert temp_state[qry.STATE_CODE] in qry.STATE_TEST_DATA


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_check_valid_state_update_missing(mock_is_db_up):
    with pytest.raises(ValueError):
        qry.check_valid_state('ZZ',
                              TEST_ST[qry.POPULATION],
                              TEST_ST[qry.CAPITAL],
                              TEST_ST[qry.AREA],
                              TEST_ST[qry.NAME],
                              TEST_ST[qry.LATITUDE],
                              TEST_ST[qry.LONGITUDE],
                              is_update=True)


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_check_valid_state_update_existing(mock_is_db_up):
    assert qry.check_valid_state('AL',
                                 TEST_ST[qry.POPULATION],
                                 TEST_ST[qry.CAPITAL],
                                 TEST_ST[qry.AREA],
                                 TEST_ST[qry.NAME],
                                 TEST_ST[qry.LATITUDE],
                                 TEST_ST[qry.LONGITUDE],
                                 is_update=True)


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_update(mock_is_db_up, temp_state):
    code = temp_state[qry.STATE_CODE]
    qry.create(**temp_state)
    ret = qry.update(code, 2000000, 'New Capital', 60000.5, 'New Name',
                     33.5, -87.5)
    assert qry.STATE_TEST_DATA[code] == {
        qry.POPULATION: 2000000,
        qry.CAPITAL: 'New Capital',
        qry.AREA: 60000.5,
        qry.NAME: 'New Name',
        qry.LATITUDE: 33.5,
        qry.LONGITUDE: -87.5,
    }
    assert ret == qry.STATE_TEST_DATA[code]


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_update_leaves_other_states(mock_is_db_up, temp_state):
    qry.create(**temp_state)
    others = {k: dict(v) for k, v in qry.STATE_TEST_DATA.items()
              if k != temp_state[qry.STATE_CODE]}
    qry.update(temp_state[qry.STATE_CODE], 1, 'C', 1.0, 'N', 0.0, 0.0)
    for code, data in others.items():
        assert qry.STATE_TEST_DATA[code] == data


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_update_missing(mock_is_db_up):
    assert 'ZZ' not in qry.STATE_TEST_DATA
    with pytest.raises(ValueError):
        qry.update('ZZ', 1, 'C', 1.0, 'N', 0.0, 0.0)
    assert 'ZZ' not in qry.STATE_TEST_DATA


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_update_invalid_leaves_state_unchanged(mock_is_db_up, temp_state):
    code = temp_state[qry.STATE_CODE]
    qry.create(**temp_state)
    before = dict(qry.STATE_TEST_DATA[code])
    with pytest.raises(ValueError):
        qry.update(code, -1, 'C', 1.0, 'N', 0.0, 0.0)
    assert qry.STATE_TEST_DATA[code] == before


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_update_db_down(mock_is_db_up, temp_state):
    code = temp_state[qry.STATE_CODE]
    qry.create(**temp_state)
    before = dict(qry.STATE_TEST_DATA[code])
    mock_is_db_up.return_value = False
    assert qry.update(code, 1, 'C', 1.0, 'N', 0.0, 0.0) is None
    assert qry.STATE_TEST_DATA[code] == before


def test_create_db_down(temp_state):
    with patch('states.query.is_db_up', return_value=False, autospec=True):
        assert qry.create(**temp_state) is None
    assert temp_state[qry.STATE_CODE] not in qry.STATE_TEST_DATA


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


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_main(mock_is_db_up, capsys):
    qry.main()
    out = capsys.readouterr().out
    for code in qry.STATE_TEST_DATA:
        assert f'State: {code}' in out


@pytest.mark.parametrize('val, expected', [
    (1, True),
    (1.5, True),
    (-2, True),
    (True, False),
    ('1', False),
    (None, False),
])
def test_is_number(val, expected):
    assert qry.is_number(val) is expected


def state_args(**changes):
    """
    Return TEST_STATE's fields as check_valid_state arguments,
    with any given changes (keyed by field name) applied.
    """
    return {**TEST_ST, **changes}


@patch('states.query.is_db_up', return_value=True, autospec=True)
@pytest.mark.parametrize('fld_nm, val', [
    (qry.LATITUDE, qry.MIN_LATITUDE),
    (qry.LATITUDE, qry.MAX_LATITUDE),
    (qry.LATITUDE, 0),
    (qry.LONGITUDE, qry.MIN_LONGITUDE),
    (qry.LONGITUDE, qry.MAX_LONGITUDE),
    (qry.LONGITUDE, 0),
])
def test_check_valid_state_lat_long_bounds_ok(mock_is_db_up, fld_nm, val):
    assert qry.check_valid_state(**state_args(**{fld_nm: val}))


@patch('states.query.is_db_up', return_value=True, autospec=True)
@pytest.mark.parametrize('fld_nm, val', [
    (qry.LATITUDE, qry.MIN_LATITUDE - 0.1),
    (qry.LATITUDE, qry.MAX_LATITUDE + 0.1),
    (qry.LATITUDE, '40'),
    (qry.LATITUDE, None),
    (qry.LATITUDE, True),
    (qry.LONGITUDE, qry.MIN_LONGITUDE - 0.1),
    (qry.LONGITUDE, qry.MAX_LONGITUDE + 0.1),
    (qry.LONGITUDE, '-100'),
    (qry.LONGITUDE, None),
    (qry.LONGITUDE, False),
])
def test_check_valid_state_bad_lat_long(mock_is_db_up, fld_nm, val):
    with pytest.raises(ValueError):
        qry.check_valid_state(**state_args(**{fld_nm: val}))


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_create_stores_lat_long(mock_is_db_up, temp_state):
    ret = qry.create(**temp_state)
    assert ret[qry.LATITUDE] == temp_state[qry.LATITUDE]
    assert ret[qry.LONGITUDE] == temp_state[qry.LONGITUDE]


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_create_bad_lat_long_not_stored(mock_is_db_up, temp_state):
    with pytest.raises(ValueError):
        qry.create(**state_args(**{qry.LATITUDE: 91}))
    assert temp_state[qry.STATE_CODE] not in qry.STATE_TEST_DATA
