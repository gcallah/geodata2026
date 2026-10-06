from http.client import (
    BAD_REQUEST,
    CREATED,
    FORBIDDEN,
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
