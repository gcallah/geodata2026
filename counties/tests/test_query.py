from copy import deepcopy
from unittest.mock import patch

import pytest

import counties.query as qry
import states.query as sqry

# counties.query uses needs_db from states.query, so that is where
# is_db_up must be patched.
DB_UP = 'states.query.is_db_up'

TEST_CTY = qry.TEST_COUNTY
TEST_ST_CODE = TEST_CTY['state_code']
TEST_NAME = TEST_CTY['name']


def valid_args(**changes):
    """
    Return TEST_COUNTY's fields as check_valid_county arguments,
    with any given changes applied.
    """
    args = dict(TEST_CTY)
    args.update(changes)
    return args


@pytest.fixture
def temp_county():
    yield TEST_CTY
    with patch(DB_UP, return_value=True, autospec=True):
        qry.delete(TEST_ST_CODE, TEST_NAME)


@patch(DB_UP, return_value=True, autospec=True)
def test_read(mock_is_db_up):
    counties = qry.read()
    assert isinstance(counties, dict)
    assert 'Autauga' in counties['AL']


@patch(DB_UP, return_value=True, autospec=True)
def test_exists(mock_is_db_up):
    assert qry.exists('AL', 'Autauga')


@patch(DB_UP, return_value=True, autospec=True)
def test_exists_missing_county(mock_is_db_up):
    assert not qry.exists('AL', 'No Such County')


@patch(DB_UP, return_value=True, autospec=True)
def test_exists_missing_state(mock_is_db_up):
    assert 'ZZ' not in qry.COUNTY_TEST_DATA
    assert not qry.exists('ZZ', 'Autauga')


@patch(DB_UP, return_value=True, autospec=True)
def test_check_valid_county(mock_is_db_up):
    assert qry.check_valid_county(**valid_args())


@patch(DB_UP, return_value=True, autospec=True)
def test_check_valid_county_no_metro_area(mock_is_db_up):
    assert qry.check_valid_county(**valid_args(metro_area=''))


@patch(DB_UP, return_value=True, autospec=True)
def test_check_valid_county_int_area(mock_is_db_up):
    assert qry.check_valid_county(**valid_args(area_sq_miles=600))


@patch(DB_UP, return_value=True, autospec=True)
@pytest.mark.parametrize('field, bad_value', [
    ('state_code', ''),
    ('state_code', 'X' * qry.STATE_CODE_LEN * 2),
    ('state_code', 12),
    ('name', ''),
    ('name', None),
    ('population', -1),
    ('population', 1.5),
    ('population', True),
    ('area_sq_miles', 0),
    ('area_sq_miles', -1.5),
    ('area_sq_miles', '600'),
    ('area_sq_miles', True),
    ('metro_area', None),
])
def test_check_valid_county_bad_field(mock_is_db_up, field, bad_value):
    with pytest.raises(ValueError):
        qry.check_valid_county(**valid_args(**{field: bad_value}))


@patch(DB_UP, return_value=True, autospec=True)
def test_check_valid_county_state_not_found(mock_is_db_up):
    with pytest.raises(qry.NotFoundError):
        qry.check_valid_county(**valid_args(state_code='ZZ'))


@patch(DB_UP, return_value=True, autospec=True)
def test_check_valid_county_bad_code_before_state_check(mock_is_db_up):
    """
    A malformed state code is bad data (ValueError), not a missing state.
    """
    with pytest.raises(ValueError):
        qry.check_valid_county(**valid_args(state_code='ZZZ'))


@patch(DB_UP, return_value=True, autospec=True)
def test_check_valid_county_dup(mock_is_db_up):
    with pytest.raises(ValueError):
        qry.check_valid_county(**valid_args(name='Autauga'))


@patch(DB_UP, return_value=True, autospec=True)
def test_check_valid_county_same_name_other_state(mock_is_db_up):
    assert qry.check_valid_county(**valid_args(state_code='AK',
                                               name='Autauga'))


@patch(DB_UP, return_value=True, autospec=True)
def test_check_valid_county_update_missing(mock_is_db_up):
    with pytest.raises(ValueError):
        qry.check_valid_county(**valid_args(), is_update=True)


@patch(DB_UP, return_value=True, autospec=True)
def test_check_valid_county_update_existing(mock_is_db_up):
    assert qry.check_valid_county(**valid_args(name='Autauga'),
                                  is_update=True)


@patch(DB_UP, return_value=True, autospec=True)
def test_create(mock_is_db_up, temp_county):
    ret = qry.create(**temp_county)
    assert ret['population'] == temp_county['population']
    assert qry.exists(TEST_ST_CODE, TEST_NAME)


@patch(DB_UP, return_value=True, autospec=True)
def test_create_first_county_in_state(mock_is_db_up):
    assert 'AK' not in qry.COUNTY_TEST_DATA
    qry.create(**valid_args(state_code='AK'))
    assert qry.exists('AK', TEST_NAME)
    qry.delete('AK', TEST_NAME)
    assert 'AK' not in qry.COUNTY_TEST_DATA


@patch(DB_UP, return_value=True, autospec=True)
def test_create_state_not_found(mock_is_db_up):
    assert not sqry.exists('ZZ')
    before = deepcopy(qry.COUNTY_TEST_DATA)
    with pytest.raises(qry.NotFoundError):
        qry.create(**valid_args(state_code='ZZ'))
    assert qry.COUNTY_TEST_DATA == before


@patch(DB_UP, return_value=True, autospec=True)
def test_create_dup(mock_is_db_up, temp_county):
    qry.create(**temp_county)
    with pytest.raises(ValueError):
        qry.create(**temp_county)


@patch(DB_UP, return_value=True, autospec=True)
def test_create_invalid(mock_is_db_up):
    before = deepcopy(qry.COUNTY_TEST_DATA)
    with pytest.raises(ValueError):
        qry.create(**valid_args(population=-1))
    assert qry.COUNTY_TEST_DATA == before


def test_create_db_down(temp_county):
    with patch(DB_UP, return_value=False, autospec=True):
        assert qry.create(**temp_county) is None
    with patch(DB_UP, return_value=True, autospec=True):
        assert not qry.exists(TEST_ST_CODE, TEST_NAME)


@patch(DB_UP, return_value=True, autospec=True)
def test_update(mock_is_db_up, temp_county):
    qry.create(**temp_county)
    ret = qry.update(TEST_ST_CODE, TEST_NAME, 60000, 700.25, '')
    assert qry.COUNTY_TEST_DATA[TEST_ST_CODE][TEST_NAME] == {
        "population": 60000,
        "area_sq_miles": 700.25,
        "metro_area": '',
    }
    assert ret == qry.COUNTY_TEST_DATA[TEST_ST_CODE][TEST_NAME]


@patch(DB_UP, return_value=True, autospec=True)
def test_update_leaves_other_counties(mock_is_db_up, temp_county):
    qry.create(**temp_county)
    others = deepcopy(qry.COUNTY_TEST_DATA)
    del others[TEST_ST_CODE][TEST_NAME]
    qry.update(TEST_ST_CODE, TEST_NAME, 1, 1.0, 'M')
    for st_code, counties in others.items():
        for name, data in counties.items():
            assert qry.COUNTY_TEST_DATA[st_code][name] == data


@patch(DB_UP, return_value=True, autospec=True)
def test_update_missing(mock_is_db_up):
    before = deepcopy(qry.COUNTY_TEST_DATA)
    with pytest.raises(ValueError):
        qry.update('ZZ', TEST_NAME, 1, 1.0, '')
    assert qry.COUNTY_TEST_DATA == before


@patch(DB_UP, return_value=True, autospec=True)
def test_update_invalid_leaves_county_unchanged(mock_is_db_up, temp_county):
    qry.create(**temp_county)
    before = dict(qry.COUNTY_TEST_DATA[TEST_ST_CODE][TEST_NAME])
    with pytest.raises(ValueError):
        qry.update(TEST_ST_CODE, TEST_NAME, -1, 1.0, '')
    assert qry.COUNTY_TEST_DATA[TEST_ST_CODE][TEST_NAME] == before


@patch(DB_UP, return_value=True, autospec=True)
def test_update_db_down(mock_is_db_up, temp_county):
    qry.create(**temp_county)
    before = dict(qry.COUNTY_TEST_DATA[TEST_ST_CODE][TEST_NAME])
    mock_is_db_up.return_value = False
    assert qry.update(TEST_ST_CODE, TEST_NAME, 1, 1.0, '') is None
    assert qry.COUNTY_TEST_DATA[TEST_ST_CODE][TEST_NAME] == before


@patch(DB_UP, return_value=True, autospec=True)
def test_delete(mock_is_db_up, temp_county):
    qry.create(**temp_county)
    deleted = qry.delete(TEST_ST_CODE, TEST_NAME)
    assert deleted['population'] == temp_county['population']
    assert TEST_NAME not in qry.COUNTY_TEST_DATA[TEST_ST_CODE]
    assert not qry.exists(TEST_ST_CODE, TEST_NAME)


@patch(DB_UP, return_value=True, autospec=True)
def test_delete_leaves_other_counties(mock_is_db_up, temp_county):
    qry.create(**temp_county)
    others = deepcopy(qry.COUNTY_TEST_DATA)
    del others[TEST_ST_CODE][TEST_NAME]
    qry.delete(TEST_ST_CODE, TEST_NAME)
    assert qry.COUNTY_TEST_DATA == others


@patch(DB_UP, return_value=True, autospec=True)
def test_delete_missing_county(mock_is_db_up):
    before = deepcopy(qry.COUNTY_TEST_DATA)
    assert qry.delete('AL', 'No Such County') is None
    assert qry.COUNTY_TEST_DATA == before


@patch(DB_UP, return_value=True, autospec=True)
def test_delete_missing_state(mock_is_db_up):
    before = deepcopy(qry.COUNTY_TEST_DATA)
    assert qry.delete('ZZ', TEST_NAME) is None
    assert qry.COUNTY_TEST_DATA == before


@pytest.mark.parametrize('fn, args', [
    (qry.read, ()),
    (qry.exists, ('AL', 'Autauga')),
    (qry.delete, ('AL', 'Autauga')),
])
def test_db_down_returns_none(fn, args):
    before = deepcopy(qry.COUNTY_TEST_DATA)
    with patch(DB_UP, return_value=False, autospec=True):
        assert fn(*args) is None
    assert qry.COUNTY_TEST_DATA == before


@patch(DB_UP, return_value=True, autospec=True)
def test_main(mock_is_db_up, capsys):
    qry.main()
    out = capsys.readouterr().out
    assert 'County: Autauga, AL' in out
    assert 'Population: 58805' in out
    assert 'Metro area: (none)' in out
