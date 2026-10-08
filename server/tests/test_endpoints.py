from http.client import (
    BAD_REQUEST,
    CONFLICT,
    CREATED,
    FORBIDDEN,
    METHOD_NOT_ALLOWED,
    NOT_ACCEPTABLE,
    NOT_FOUND,
    OK,
    SERVICE_UNAVAILABLE,
    UNAUTHORIZED,
)

from unittest.mock import patch

import pytest

import counties.query as cqry
import security.security as sec
import server.endpoints as ep
import states.query as sqry

TEST_CLIENT = ep.app.test_client()

TEST_USER = 'test@example.com'
TEST_AUTH_CODE = 'test-auth-code'
AUTH_HEADERS = {
    ep.USER_ID_HDR: TEST_USER,
    ep.AUTH_CODE_HDR: TEST_AUTH_CODE,
}


def test_hello():
    resp = TEST_CLIENT.get(ep.HELLO_EP)
    resp_json = resp.get_json()
    assert ep.HELLO_RESP in resp_json


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_get_states(mock_is_db_up):
    resp = TEST_CLIENT.get(ep.STATES_EP)
    assert resp.status_code == OK
    resp_json = resp.get_json()
    assert ep.STATES_RESP in resp_json
    assert isinstance(resp_json[ep.STATES_RESP], dict)


@patch('states.query.is_db_up', return_value=False, autospec=True)
def test_get_states_db_unavailable(mock_is_db_up):
    resp = TEST_CLIENT.get(ep.STATES_EP)
    assert resp.status_code == SERVICE_UNAVAILABLE


@pytest.fixture
def temp_state():
    yield dict(sqry.TEST_STATE)
    with patch('states.query.is_db_up', return_value=True, autospec=True):
        sqry.delete(sqry.TEST_STATE['state_code'])


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_create_state(mock_is_db_up, temp_state):
    resp = TEST_CLIENT.post(ep.STATES_EP, json=temp_state,
                           headers=AUTH_HEADERS)
    assert resp.status_code == CREATED
    assert sqry.exists(temp_state['state_code'])


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_create_state_bad_data(mock_is_db_up, temp_state):
    temp_state['population'] = -1
    resp = TEST_CLIENT.post(ep.STATES_EP, json=temp_state,
                           headers=AUTH_HEADERS)
    assert resp.status_code == BAD_REQUEST


@patch('states.query.is_db_up', return_value=False, autospec=True)
def test_create_state_db_unavailable(mock_is_db_up, temp_state):
    resp = TEST_CLIENT.post(ep.STATES_EP, json=temp_state,
                           headers=AUTH_HEADERS)
    assert resp.status_code == SERVICE_UNAVAILABLE


@patch('states.query.is_db_up', return_value=True, autospec=True)
@pytest.mark.parametrize('missing', [ep.USER_ID_HDR, ep.AUTH_CODE_HDR])
def test_create_state_missing_auth_header(mock_is_db_up, missing,
                                          temp_state):
    headers = {k: v for k, v in AUTH_HEADERS.items() if k != missing}
    resp = TEST_CLIENT.post(ep.STATES_EP, json=temp_state, headers=headers)
    assert resp.status_code == UNAUTHORIZED
    assert not sqry.exists(temp_state['state_code'])


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_create_state_empty_auth_header(mock_is_db_up, temp_state):
    headers = dict(AUTH_HEADERS)
    headers[ep.AUTH_CODE_HDR] = ''
    resp = TEST_CLIENT.post(ep.STATES_EP, json=temp_state, headers=headers)
    assert resp.status_code == UNAUTHORIZED
    assert not sqry.exists(temp_state['state_code'])


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_create_state_creds_not_in_body(mock_is_db_up, temp_state):
    """
    Credentials must come in the headers; putting them in the body
    does not count.
    """
    body = dict(temp_state)
    body[ep.USER_ID_HDR] = TEST_USER
    body[ep.AUTH_CODE_HDR] = TEST_AUTH_CODE
    resp = TEST_CLIENT.post(ep.STATES_EP, json=body)
    assert resp.status_code == UNAUTHORIZED
    assert not sqry.exists(temp_state['state_code'])


@patch('security.security.is_permitted', return_value=False, autospec=True)
@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_create_state_not_permitted(mock_is_db_up, mock_is_permitted,
                                    temp_state):
    resp = TEST_CLIENT.post(ep.STATES_EP, json=temp_state,
                            headers=AUTH_HEADERS)
    assert resp.status_code == FORBIDDEN
    assert not sqry.exists(temp_state['state_code'])


@patch('security.security.is_permitted', return_value=True, autospec=True)
@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_create_state_checks_permission(mock_is_db_up, mock_is_permitted,
                                        temp_state):
    TEST_CLIENT.post(ep.STATES_EP, json=temp_state, headers=AUTH_HEADERS)
    mock_is_permitted.assert_called_once_with(sec.STATES, sec.CREATE,
                                              TEST_USER,
                                              auth_code=TEST_AUTH_CODE)


@pytest.fixture
def existing_state(temp_state):
    with patch('states.query.is_db_up', return_value=True, autospec=True):
        sqry.create(**temp_state)
    return temp_state


def state_url(state_code):
    return f'{ep.STATES_EP}/{state_code}'


def updated_fields():
    return {
        'population': 2000000,
        'capital': 'New Capital',
        'area_sq_miles': 60000.5,
        'name': 'New Name',
    }


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_update_state(mock_is_db_up, existing_state):
    code = existing_state['state_code']
    resp = TEST_CLIENT.put(state_url(code), json=updated_fields(),
                           headers=AUTH_HEADERS)
    assert resp.status_code == OK
    assert sqry.STATE_TEST_DATA[code] == updated_fields()
    assert resp.get_json()[ep.STATES_RESP] == updated_fields()


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_update_state_matching_code_in_body(mock_is_db_up, existing_state):
    code = existing_state['state_code']
    body = updated_fields()
    body['state_code'] = code
    resp = TEST_CLIENT.put(state_url(code), json=body, headers=AUTH_HEADERS)
    assert resp.status_code == OK
    assert sqry.STATE_TEST_DATA[code] == updated_fields()


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_update_state_cannot_change_code(mock_is_db_up, existing_state):
    code = existing_state['state_code']
    before = dict(sqry.STATE_TEST_DATA[code])
    body = updated_fields()
    body['state_code'] = 'ZZ'
    resp = TEST_CLIENT.put(state_url(code), json=body, headers=AUTH_HEADERS)
    assert resp.status_code == BAD_REQUEST
    assert sqry.STATE_TEST_DATA[code] == before
    assert not sqry.exists('ZZ')


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_update_state_not_found(mock_is_db_up, temp_state):
    code = temp_state['state_code']
    resp = TEST_CLIENT.put(state_url(code), json=updated_fields(),
                           headers=AUTH_HEADERS)
    assert resp.status_code == NOT_FOUND
    assert not sqry.exists(code)


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_update_state_bad_data(mock_is_db_up, existing_state):
    code = existing_state['state_code']
    before = dict(sqry.STATE_TEST_DATA[code])
    body = updated_fields()
    body['population'] = -1
    resp = TEST_CLIENT.put(state_url(code), json=body, headers=AUTH_HEADERS)
    assert resp.status_code == BAD_REQUEST
    assert sqry.STATE_TEST_DATA[code] == before


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_update_state_db_unavailable(mock_is_db_up, existing_state):
    code = existing_state['state_code']
    before = dict(sqry.STATE_TEST_DATA[code])
    mock_is_db_up.return_value = False
    resp = TEST_CLIENT.put(state_url(code), json=updated_fields(),
                           headers=AUTH_HEADERS)
    assert resp.status_code == SERVICE_UNAVAILABLE
    assert sqry.STATE_TEST_DATA[code] == before


@patch('states.query.update', return_value=None, autospec=True)
@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_update_state_db_down_during_update(mock_is_db_up, mock_update,
                                            existing_state):
    resp = TEST_CLIENT.put(state_url(existing_state['state_code']),
                           json=updated_fields(), headers=AUTH_HEADERS)
    assert resp.status_code == SERVICE_UNAVAILABLE


@patch('states.query.is_db_up', return_value=True, autospec=True)
@pytest.mark.parametrize('missing', [ep.USER_ID_HDR, ep.AUTH_CODE_HDR])
def test_update_state_missing_auth_header(mock_is_db_up, missing,
                                          existing_state):
    code = existing_state['state_code']
    before = dict(sqry.STATE_TEST_DATA[code])
    headers = {k: v for k, v in AUTH_HEADERS.items() if k != missing}
    resp = TEST_CLIENT.put(state_url(code), json=updated_fields(),
                           headers=headers)
    assert resp.status_code == UNAUTHORIZED
    assert sqry.STATE_TEST_DATA[code] == before


@patch('security.security.is_permitted', return_value=False, autospec=True)
@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_update_state_not_permitted(mock_is_db_up, mock_is_permitted,
                                    existing_state):
    code = existing_state['state_code']
    before = dict(sqry.STATE_TEST_DATA[code])
    resp = TEST_CLIENT.put(state_url(code), json=updated_fields(),
                           headers=AUTH_HEADERS)
    assert resp.status_code == FORBIDDEN
    assert sqry.STATE_TEST_DATA[code] == before


@patch('security.security.is_permitted', return_value=True, autospec=True)
@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_update_state_checks_permission(mock_is_db_up, mock_is_permitted,
                                        existing_state):
    TEST_CLIENT.put(state_url(existing_state['state_code']),
                    json=updated_fields(), headers=AUTH_HEADERS)
    mock_is_permitted.assert_called_once_with(sec.STATES, sec.UPDATE,
                                              TEST_USER,
                                              auth_code=TEST_AUTH_CODE)


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_put_on_states_collection_not_allowed(mock_is_db_up, existing_state):
    resp = TEST_CLIENT.put(ep.STATES_EP, json=existing_state,
                           headers=AUTH_HEADERS)
    assert resp.status_code == METHOD_NOT_ALLOWED


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_delete_state(mock_is_db_up, existing_state):
    code = existing_state['state_code']
    expected = dict(sqry.STATE_TEST_DATA[code])
    resp = TEST_CLIENT.delete(state_url(code), headers=AUTH_HEADERS)
    assert resp.status_code == OK
    assert resp.get_json()[ep.STATES_RESP] == expected
    assert code not in sqry.STATE_TEST_DATA


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_delete_state_leaves_other_states(mock_is_db_up, existing_state):
    code = existing_state['state_code']
    others = {k: dict(v) for k, v in sqry.STATE_TEST_DATA.items()
              if k != code}
    TEST_CLIENT.delete(state_url(code), headers=AUTH_HEADERS)
    assert sqry.STATE_TEST_DATA == others


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_delete_state_with_counties(mock_is_db_up):
    assert cqry.has_counties('AL')
    before = dict(sqry.STATE_TEST_DATA['AL'])
    resp = TEST_CLIENT.delete(state_url('AL'), headers=AUTH_HEADERS)
    assert resp.status_code == CONFLICT
    assert sqry.STATE_TEST_DATA['AL'] == before


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_delete_state_not_found(mock_is_db_up):
    assert 'ZZ' not in sqry.STATE_TEST_DATA
    resp = TEST_CLIENT.delete(state_url('ZZ'), headers=AUTH_HEADERS)
    assert resp.status_code == NOT_FOUND


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_delete_state_db_unavailable(mock_is_db_up, existing_state):
    code = existing_state['state_code']
    mock_is_db_up.return_value = False
    resp = TEST_CLIENT.delete(state_url(code), headers=AUTH_HEADERS)
    assert resp.status_code == SERVICE_UNAVAILABLE
    assert code in sqry.STATE_TEST_DATA


@patch('states.query.delete', return_value=None, autospec=True)
@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_delete_state_db_down_during_delete(mock_is_db_up, mock_delete,
                                            existing_state):
    resp = TEST_CLIENT.delete(state_url(existing_state['state_code']),
                              headers=AUTH_HEADERS)
    assert resp.status_code == SERVICE_UNAVAILABLE


@patch('states.query.is_db_up', return_value=True, autospec=True)
@pytest.mark.parametrize('missing', [ep.USER_ID_HDR, ep.AUTH_CODE_HDR])
def test_delete_state_missing_auth_header(mock_is_db_up, missing,
                                          existing_state):
    code = existing_state['state_code']
    headers = {k: v for k, v in AUTH_HEADERS.items() if k != missing}
    resp = TEST_CLIENT.delete(state_url(code), headers=headers)
    assert resp.status_code == UNAUTHORIZED
    assert code in sqry.STATE_TEST_DATA


@patch('security.security.is_permitted', return_value=False, autospec=True)
@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_delete_state_not_permitted(mock_is_db_up, mock_is_permitted,
                                    existing_state):
    code = existing_state['state_code']
    resp = TEST_CLIENT.delete(state_url(code), headers=AUTH_HEADERS)
    assert resp.status_code == FORBIDDEN
    assert code in sqry.STATE_TEST_DATA


@patch('security.security.is_permitted', return_value=True, autospec=True)
@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_delete_state_checks_permission(mock_is_db_up, mock_is_permitted,
                                        existing_state):
    TEST_CLIENT.delete(state_url(existing_state['state_code']),
                       headers=AUTH_HEADERS)
    mock_is_permitted.assert_called_once_with(sec.STATES, sec.DELETE,
                                              TEST_USER,
                                              auth_code=TEST_AUTH_CODE)


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_delete_on_states_collection_not_allowed(mock_is_db_up,
                                                 existing_state):
    resp = TEST_CLIENT.delete(ep.STATES_EP, headers=AUTH_HEADERS)
    assert resp.status_code == METHOD_NOT_ALLOWED
    assert existing_state['state_code'] in sqry.STATE_TEST_DATA


# counties.query uses needs_db from states.query, so that is where
# is_db_up must be patched for county endpoints too.
DB_UP = 'states.query.is_db_up'

TEST_CTY = cqry.TEST_COUNTY
CTY_ST_CODE = TEST_CTY['state_code']
CTY_NAME = TEST_CTY['name']


def county_url(state_code, name):
    return f'{ep.COUNTIES_EP}/{state_code}/{name}'


def stored_county(state_code=CTY_ST_CODE, name=CTY_NAME):
    return cqry.COUNTY_TEST_DATA[state_code][name]


def county_exists(state_code=CTY_ST_CODE, name=CTY_NAME):
    return name in cqry.COUNTY_TEST_DATA.get(state_code, {})


def updated_county_fields():
    return {
        'population': 60000,
        'area_sq_miles': 700.25,
        'metro_area': '',
    }


@pytest.fixture
def temp_county():
    yield dict(TEST_CTY)
    with patch(DB_UP, return_value=True, autospec=True):
        cqry.delete(CTY_ST_CODE, CTY_NAME)


@pytest.fixture
def existing_county(temp_county):
    with patch(DB_UP, return_value=True, autospec=True):
        cqry.create(**temp_county)
    return temp_county


@patch(DB_UP, return_value=True, autospec=True)
def test_get_counties(mock_is_db_up):
    resp = TEST_CLIENT.get(ep.COUNTIES_EP)
    assert resp.status_code == OK
    counties = resp.get_json()[ep.COUNTIES_RESP]
    assert counties == cqry.COUNTY_TEST_DATA


@patch(DB_UP, return_value=False, autospec=True)
def test_get_counties_db_unavailable(mock_is_db_up):
    resp = TEST_CLIENT.get(ep.COUNTIES_EP)
    assert resp.status_code == SERVICE_UNAVAILABLE


@patch(DB_UP, return_value=True, autospec=True)
def test_create_county(mock_is_db_up, temp_county):
    resp = TEST_CLIENT.post(ep.COUNTIES_EP, json=temp_county,
                            headers=AUTH_HEADERS)
    assert resp.status_code == CREATED
    assert county_exists()
    assert resp.get_json()[ep.COUNTIES_RESP] == stored_county()


@patch(DB_UP, return_value=True, autospec=True)
def test_create_county_bad_data(mock_is_db_up, temp_county):
    temp_county['population'] = -1
    resp = TEST_CLIENT.post(ep.COUNTIES_EP, json=temp_county,
                            headers=AUTH_HEADERS)
    assert resp.status_code == BAD_REQUEST
    assert not county_exists()


@patch(DB_UP, return_value=True, autospec=True)
def test_create_county_state_not_found(mock_is_db_up, temp_county):
    temp_county['state_code'] = 'ZZ'
    assert not sqry.exists('ZZ')
    resp = TEST_CLIENT.post(ep.COUNTIES_EP, json=temp_county,
                            headers=AUTH_HEADERS)
    assert resp.status_code == NOT_FOUND
    assert not county_exists('ZZ')


@patch(DB_UP, return_value=True, autospec=True)
def test_create_county_dup(mock_is_db_up, existing_county):
    before = dict(stored_county())
    resp = TEST_CLIENT.post(ep.COUNTIES_EP, json=existing_county,
                            headers=AUTH_HEADERS)
    assert resp.status_code == BAD_REQUEST
    assert stored_county() == before


@patch(DB_UP, return_value=True, autospec=True)
def test_create_county_no_body(mock_is_db_up):
    resp = TEST_CLIENT.post(ep.COUNTIES_EP, headers=AUTH_HEADERS)
    assert resp.status_code == BAD_REQUEST


@patch(DB_UP, return_value=False, autospec=True)
def test_create_county_db_unavailable(mock_is_db_up, temp_county):
    resp = TEST_CLIENT.post(ep.COUNTIES_EP, json=temp_county,
                            headers=AUTH_HEADERS)
    assert resp.status_code == SERVICE_UNAVAILABLE
    assert not county_exists()


@patch(DB_UP, return_value=True, autospec=True)
@pytest.mark.parametrize('missing', [ep.USER_ID_HDR, ep.AUTH_CODE_HDR])
def test_create_county_missing_auth_header(mock_is_db_up, missing,
                                           temp_county):
    headers = {k: v for k, v in AUTH_HEADERS.items() if k != missing}
    resp = TEST_CLIENT.post(ep.COUNTIES_EP, json=temp_county,
                            headers=headers)
    assert resp.status_code == UNAUTHORIZED
    assert not county_exists()


@patch('security.security.is_permitted', return_value=False, autospec=True)
@patch(DB_UP, return_value=True, autospec=True)
def test_create_county_not_permitted(mock_is_db_up, mock_is_permitted,
                                     temp_county):
    resp = TEST_CLIENT.post(ep.COUNTIES_EP, json=temp_county,
                            headers=AUTH_HEADERS)
    assert resp.status_code == FORBIDDEN
    assert not county_exists()


@patch('security.security.is_permitted', return_value=True, autospec=True)
@patch(DB_UP, return_value=True, autospec=True)
def test_create_county_checks_permission(mock_is_db_up, mock_is_permitted,
                                         temp_county):
    TEST_CLIENT.post(ep.COUNTIES_EP, json=temp_county, headers=AUTH_HEADERS)
    mock_is_permitted.assert_called_once_with(sec.COUNTIES, sec.CREATE,
                                              TEST_USER,
                                              auth_code=TEST_AUTH_CODE)


@patch(DB_UP, return_value=True, autospec=True)
def test_update_county(mock_is_db_up, existing_county):
    resp = TEST_CLIENT.put(county_url(CTY_ST_CODE, CTY_NAME),
                           json=updated_county_fields(),
                           headers=AUTH_HEADERS)
    assert resp.status_code == OK
    assert stored_county() == updated_county_fields()
    assert resp.get_json()[ep.COUNTIES_RESP] == updated_county_fields()


@patch(DB_UP, return_value=True, autospec=True)
def test_update_county_matching_ids_in_body(mock_is_db_up, existing_county):
    body = updated_county_fields()
    body['state_code'] = CTY_ST_CODE
    body['name'] = CTY_NAME
    resp = TEST_CLIENT.put(county_url(CTY_ST_CODE, CTY_NAME), json=body,
                           headers=AUTH_HEADERS)
    assert resp.status_code == OK
    assert stored_county() == updated_county_fields()


@patch(DB_UP, return_value=True, autospec=True)
@pytest.mark.parametrize('field, new_value', [
    ('state_code', 'ZZ'),
    ('name', 'Other County'),
])
def test_update_county_cannot_change_ids(mock_is_db_up, field, new_value,
                                         existing_county):
    before = dict(stored_county())
    body = updated_county_fields()
    body[field] = new_value
    resp = TEST_CLIENT.put(county_url(CTY_ST_CODE, CTY_NAME), json=body,
                           headers=AUTH_HEADERS)
    assert resp.status_code == BAD_REQUEST
    assert stored_county() == before


@patch(DB_UP, return_value=True, autospec=True)
def test_update_county_not_found(mock_is_db_up, temp_county):
    resp = TEST_CLIENT.put(county_url(CTY_ST_CODE, CTY_NAME),
                           json=updated_county_fields(),
                           headers=AUTH_HEADERS)
    assert resp.status_code == NOT_FOUND
    assert not county_exists()


@patch(DB_UP, return_value=True, autospec=True)
def test_update_county_wrong_state(mock_is_db_up, existing_county):
    """
    A county is found by state code and name together.
    """
    resp = TEST_CLIENT.put(county_url('AK', CTY_NAME),
                           json=updated_county_fields(),
                           headers=AUTH_HEADERS)
    assert resp.status_code == NOT_FOUND
    assert not county_exists('AK')


@patch(DB_UP, return_value=True, autospec=True)
def test_update_county_bad_data(mock_is_db_up, existing_county):
    before = dict(stored_county())
    body = updated_county_fields()
    body['population'] = -1
    resp = TEST_CLIENT.put(county_url(CTY_ST_CODE, CTY_NAME), json=body,
                           headers=AUTH_HEADERS)
    assert resp.status_code == BAD_REQUEST
    assert stored_county() == before


@patch(DB_UP, return_value=True, autospec=True)
def test_update_county_db_unavailable(mock_is_db_up, existing_county):
    before = dict(stored_county())
    mock_is_db_up.return_value = False
    resp = TEST_CLIENT.put(county_url(CTY_ST_CODE, CTY_NAME),
                           json=updated_county_fields(),
                           headers=AUTH_HEADERS)
    assert resp.status_code == SERVICE_UNAVAILABLE
    assert stored_county() == before


@patch('counties.query.update', return_value=None, autospec=True)
@patch(DB_UP, return_value=True, autospec=True)
def test_update_county_db_down_during_update(mock_is_db_up, mock_update,
                                             existing_county):
    resp = TEST_CLIENT.put(county_url(CTY_ST_CODE, CTY_NAME),
                           json=updated_county_fields(),
                           headers=AUTH_HEADERS)
    assert resp.status_code == SERVICE_UNAVAILABLE


@patch(DB_UP, return_value=True, autospec=True)
@pytest.mark.parametrize('missing', [ep.USER_ID_HDR, ep.AUTH_CODE_HDR])
def test_update_county_missing_auth_header(mock_is_db_up, missing,
                                           existing_county):
    before = dict(stored_county())
    headers = {k: v for k, v in AUTH_HEADERS.items() if k != missing}
    resp = TEST_CLIENT.put(county_url(CTY_ST_CODE, CTY_NAME),
                           json=updated_county_fields(), headers=headers)
    assert resp.status_code == UNAUTHORIZED
    assert stored_county() == before


@patch('security.security.is_permitted', return_value=False, autospec=True)
@patch(DB_UP, return_value=True, autospec=True)
def test_update_county_not_permitted(mock_is_db_up, mock_is_permitted,
                                     existing_county):
    before = dict(stored_county())
    resp = TEST_CLIENT.put(county_url(CTY_ST_CODE, CTY_NAME),
                           json=updated_county_fields(),
                           headers=AUTH_HEADERS)
    assert resp.status_code == FORBIDDEN
    assert stored_county() == before


@patch('security.security.is_permitted', return_value=True, autospec=True)
@patch(DB_UP, return_value=True, autospec=True)
def test_update_county_checks_permission(mock_is_db_up, mock_is_permitted,
                                         existing_county):
    TEST_CLIENT.put(county_url(CTY_ST_CODE, CTY_NAME),
                    json=updated_county_fields(), headers=AUTH_HEADERS)
    mock_is_permitted.assert_called_once_with(sec.COUNTIES, sec.UPDATE,
                                              TEST_USER,
                                              auth_code=TEST_AUTH_CODE)


@patch(DB_UP, return_value=True, autospec=True)
def test_put_on_counties_collection_not_allowed(mock_is_db_up,
                                                existing_county):
    resp = TEST_CLIENT.put(ep.COUNTIES_EP, json=existing_county,
                           headers=AUTH_HEADERS)
    assert resp.status_code == METHOD_NOT_ALLOWED


@patch(DB_UP, return_value=True, autospec=True)
def test_delete_county(mock_is_db_up, existing_county):
    expected = dict(stored_county())
    resp = TEST_CLIENT.delete(county_url(CTY_ST_CODE, CTY_NAME),
                              headers=AUTH_HEADERS)
    assert resp.status_code == OK
    assert resp.get_json()[ep.COUNTIES_RESP] == expected
    assert not county_exists()


@patch(DB_UP, return_value=True, autospec=True)
def test_delete_county_leaves_other_counties(mock_is_db_up, existing_county):
    others = {st: {nm: dict(d) for nm, d in cties.items()
                   if (st, nm) != (CTY_ST_CODE, CTY_NAME)}
              for st, cties in cqry.COUNTY_TEST_DATA.items()}
    TEST_CLIENT.delete(county_url(CTY_ST_CODE, CTY_NAME),
                       headers=AUTH_HEADERS)
    assert cqry.COUNTY_TEST_DATA == others


@patch(DB_UP, return_value=True, autospec=True)
@pytest.mark.parametrize('state_code, name', [
    ('AL', 'No Such County'),
    ('ZZ', 'Autauga'),
])
def test_delete_county_not_found(mock_is_db_up, state_code, name):
    resp = TEST_CLIENT.delete(county_url(state_code, name),
                              headers=AUTH_HEADERS)
    assert resp.status_code == NOT_FOUND


@patch(DB_UP, return_value=True, autospec=True)
def test_delete_county_db_unavailable(mock_is_db_up, existing_county):
    mock_is_db_up.return_value = False
    resp = TEST_CLIENT.delete(county_url(CTY_ST_CODE, CTY_NAME),
                              headers=AUTH_HEADERS)
    assert resp.status_code == SERVICE_UNAVAILABLE
    assert county_exists()


@patch('counties.query.delete', return_value=None, autospec=True)
@patch(DB_UP, return_value=True, autospec=True)
def test_delete_county_db_down_during_delete(mock_is_db_up, mock_delete,
                                             existing_county):
    resp = TEST_CLIENT.delete(county_url(CTY_ST_CODE, CTY_NAME),
                              headers=AUTH_HEADERS)
    assert resp.status_code == SERVICE_UNAVAILABLE


@patch(DB_UP, return_value=True, autospec=True)
@pytest.mark.parametrize('missing', [ep.USER_ID_HDR, ep.AUTH_CODE_HDR])
def test_delete_county_missing_auth_header(mock_is_db_up, missing,
                                           existing_county):
    headers = {k: v for k, v in AUTH_HEADERS.items() if k != missing}
    resp = TEST_CLIENT.delete(county_url(CTY_ST_CODE, CTY_NAME),
                              headers=headers)
    assert resp.status_code == UNAUTHORIZED
    assert county_exists()


@patch('security.security.is_permitted', return_value=False, autospec=True)
@patch(DB_UP, return_value=True, autospec=True)
def test_delete_county_not_permitted(mock_is_db_up, mock_is_permitted,
                                     existing_county):
    resp = TEST_CLIENT.delete(county_url(CTY_ST_CODE, CTY_NAME),
                              headers=AUTH_HEADERS)
    assert resp.status_code == FORBIDDEN
    assert county_exists()


@patch('security.security.is_permitted', return_value=True, autospec=True)
@patch(DB_UP, return_value=True, autospec=True)
def test_delete_county_checks_permission(mock_is_db_up, mock_is_permitted,
                                         existing_county):
    TEST_CLIENT.delete(county_url(CTY_ST_CODE, CTY_NAME),
                       headers=AUTH_HEADERS)
    mock_is_permitted.assert_called_once_with(sec.COUNTIES, sec.DELETE,
                                              TEST_USER,
                                              auth_code=TEST_AUTH_CODE)


@patch(DB_UP, return_value=True, autospec=True)
def test_delete_on_counties_collection_not_allowed(mock_is_db_up,
                                                   existing_county):
    resp = TEST_CLIENT.delete(ep.COUNTIES_EP, headers=AUTH_HEADERS)
    assert resp.status_code == METHOD_NOT_ALLOWED
    assert county_exists()


def test_county_endpoints_listed():
    resp = TEST_CLIENT.get(ep.ENDPOINT_EP)
    endpoints = resp.get_json()[ep.ENDPOINT_RESP]
    assert ep.COUNTIES_EP in endpoints
    assert ep.COUNTY_EP in endpoints
