from http.client import (
    BAD_REQUEST,
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
