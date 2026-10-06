"""
This is the file containing all of the endpoints for our flask app.
The endpoint called `endpoints` will return all available endpoints.
"""
from http import HTTPStatus

from flask import Flask, request
from flask_restx import Resource, Api, fields  # Namespace
from flask_cors import CORS

import werkzeug.exceptions as wz

import security.security as sec
import states.query as sqry

app = Flask(__name__)
CORS(app)
api = Api(app)

ENDPOINT_EP = '/endpoints'
ENDPOINT_RESP = 'Available endpoints'
HELLO_EP = '/hello'
HELLO_RESP = 'hello'
STATES_EP = '/states'
STATE_EP = f'{STATES_EP}/<state_code>'
STATES_RESP = 'States:'
MESSAGE = 'Message'
USER_ID_HDR = 'X-User-Id'
AUTH_CODE_HDR = 'X-Auth-Code'

AUTH_HDRS = api.parser()
AUTH_HDRS.add_argument(USER_ID_HDR, location='headers', required=True)
AUTH_HDRS.add_argument(AUTH_CODE_HDR, location='headers', required=True)


def check_permission(feature_name: str, action: str):
    """
    Read the user ID and auth code from the request headers and check that
    the user may perform `action` on `feature_name`.
    Raises 401 if credentials are missing, 403 if not permitted.
    """
    user_id = request.headers.get(USER_ID_HDR)
    auth_code = request.headers.get(AUTH_CODE_HDR)
    if not user_id or not auth_code:
        raise wz.Unauthorized(f'{USER_ID_HDR} and {AUTH_CODE_HDR} headers '
                              + 'are required.')
    if not sec.is_permitted(feature_name, action, user_id,
                            auth_code=auth_code):
        raise wz.Forbidden('User not permitted to do this.')


@api.route(HELLO_EP)
class HelloWorld(Resource):
    """
    The purpose of the HelloWorld class is to have a simple test to see if the
    app is working at all.
    """
    def get(self):
        """
        A trivial endpoint to see if the server is running.
        """
        return {HELLO_RESP: 'world'}


@api.route(ENDPOINT_EP)
class Endpoints(Resource):
    """
    This class will serve as live, fetchable documentation of what endpoints
    are available in the system.
    """
    def get(self):
        """
        The `get()` method will return a sorted list of available endpoints.
        """
        endpoints = sorted(rule.rule for rule in api.app.url_map.iter_rules())
        return {"Available endpoints": endpoints}


STATE_CREATE_FLDS = api.model('CreateState', {
    'state_code': fields.String(required=True),
    'population': fields.Integer(required=True),
    'capital': fields.String(required=True),
    'area_sq_miles': fields.Float(required=True),
    'name': fields.String(required=True),
})

STATE_UPDATE_FLDS = api.model('UpdateState', {
    'population': fields.Integer(required=True),
    'capital': fields.String(required=True),
    'area_sq_miles': fields.Float(required=True),
    'name': fields.String(required=True),
})


@api.route(STATES_EP)
class States(Resource):
    """
    The get method will return a list of all states in the database.
    """
    @api.response(HTTPStatus.OK.value, 'Success')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    def get(self):
        """
        The get method will return a list of all states in the database.
        """
        states = sqry.read()
        if states is None:
            raise wz.ServiceUnavailable('Database may be down.')
        return {STATES_RESP: states}

    @api.expect(AUTH_HDRS, STATE_CREATE_FLDS)
    @api.response(HTTPStatus.CREATED.value, 'Created')
    @api.response(HTTPStatus.BAD_REQUEST.value, 'Bad Request')
    @api.response(HTTPStatus.UNAUTHORIZED.value, 'Unauthorized')
    @api.response(HTTPStatus.FORBIDDEN.value, 'Forbidden')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    def post(self):
        """
        Add a new state.
        Requires X-User-Id and X-Auth-Code headers.
        """
        check_permission(sec.STATES, sec.CREATE)
        data = request.get_json(silent=True) or {}
        try:
            new_state = sqry.create(data.get('state_code'),
                                    data.get('population'),
                                    data.get('capital'),
                                    data.get('area_sq_miles'),
                                    data.get('name'))
        except ValueError as err:
            raise wz.BadRequest(str(err))
        if new_state is None:
            raise wz.ServiceUnavailable('Database may be down.')
        return {MESSAGE: 'State added.', STATES_RESP: new_state}, \
            HTTPStatus.CREATED


@api.route(STATE_EP)
class State(Resource):
    """
    Operations on a single state, identified by its state code.
    """
    @api.expect(AUTH_HDRS, STATE_UPDATE_FLDS)
    @api.response(HTTPStatus.OK.value, 'Success')
    @api.response(HTTPStatus.BAD_REQUEST.value, 'Bad Request')
    @api.response(HTTPStatus.UNAUTHORIZED.value, 'Unauthorized')
    @api.response(HTTPStatus.FORBIDDEN.value, 'Forbidden')
    @api.response(HTTPStatus.NOT_FOUND.value, 'Not Found')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    def put(self, state_code):
        """
        Update an existing state.
        The state code cannot be changed.
        Requires X-User-Id and X-Auth-Code headers.
        """
        check_permission(sec.STATES, sec.UPDATE)
        data = request.get_json(silent=True) or {}
        if data.get('state_code', state_code) != state_code:
            raise wz.BadRequest('The state code cannot be changed.')
        state_exists = sqry.exists(state_code)
        if state_exists is None:
            raise wz.ServiceUnavailable('Database may be down.')
        if not state_exists:
            raise wz.NotFound(f'State {state_code} not found.')
        try:
            updated = sqry.update(state_code,
                                  data.get('population'),
                                  data.get('capital'),
                                  data.get('area_sq_miles'),
                                  data.get('name'))
        except ValueError as err:
            raise wz.BadRequest(str(err))
        if updated is None:
            raise wz.ServiceUnavailable('Database may be down.')
        return {MESSAGE: 'State updated.', STATES_RESP: updated}
